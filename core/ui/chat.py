import streamlit as st
import uuid
from core.agent.llm_router import ask_with_llm_router
from core.ui.export_utils import generate_chat_pdf, REPORTLAB_AVAILABLE

def build_message(role, content, chart=None, chart_key=None, evidence=None):
    """统一的消息构造器，方便后期扩展和维护"""
    return {
        "role": role,
        "content": content,
        "chart": chart,
        "chart_key": chart_key,
        "evidence": evidence
    }

def init_chat():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            build_message(
                role="assistant",
                content="欢迎使用美漫销量智能分析平台 👋\n\n你可以问我：\n- 漫威和DC在过去十年谁更具统治力？\n- 帮我找出销量前20的明星编剧"
            )
        ]

def render_chat(filtered_df, api_key, model_name):
    init_chat()
    
    col1, col2 = st.columns([8, 2])
    with col2:
        if st.button("🧹 清空对话", use_container_width=True):
            # 使用 pop 替代 del，永远安全，杜绝 KeyError
            st.session_state.pop("messages", None)
            st.rerun()

    # 渲染历史对话
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("chart") is not None: 
                st.plotly_chart(msg["chart"], use_container_width=True, key=msg.get("chart_key"))
            if msg.get("evidence") is not None: 
                st.dataframe(msg["evidence"], use_container_width=True)

    user_query = st.chat_input("向 AI 发起深度数智对话...")
    if user_query:
        if not api_key:
            st.warning("请先在左侧边栏配置您的 API Key")
        else:
            # 使用 build_message 写入用户提问
            st.session_state.messages.append(build_message(role="user", content=user_query))
            with st.chat_message("user"): 
                st.markdown(user_query)
            
            with st.chat_message("assistant"):
                with st.spinner("数智矩阵计算中..."):
                    try:
                        result = ask_with_llm_router(user_query, filtered_df, api_key, model_name)
                        
                        answer = getattr(result, "answer", str(result))
                        chart = getattr(result, "chart", None)
                        evidence = getattr(result, "evidence", None)
                        
                        # 限制 DataFrame 体积
                        if evidence is not None:
                            evidence = evidence.head(100)
                            
                        # 固化 UUID
                        current_chart_key = f"chart_{uuid.uuid4().hex}" if chart is not None else None
                        
                        st.markdown(answer)
                        if chart is not None: 
                            st.plotly_chart(chart, use_container_width=True, key=current_chart_key)
                        if evidence is not None: 
                            st.dataframe(evidence, use_container_width=True)
                        
                        # 写入 AI 回复
                        st.session_state.messages.append(build_message(
                            role="assistant", 
                            content=answer, 
                            chart=chart, 
                            chart_key=current_chart_key,
                            evidence=evidence
                        ))
                        
                    except Exception as e:
                        err_msg = f"分析调度失败: {e}"
                        st.error(err_msg)
                        # 异常时的兜底写入，保持上下文完整性
                        st.session_state.messages.append(build_message(
                            role="assistant",
                            content=err_msg
                        ))

    st.divider()
    
    if REPORTLAB_AVAILABLE:
        # 导出前构造轻量级 JSON，彻底剥离 Figure 和 DataFrame 对象，防止序列化爆炸
        export_messages = [
            {"role": msg["role"], "content": msg["content"]} 
            for msg in st.session_state.messages
        ]
        pdf_bytes = generate_chat_pdf(export_messages)
        st.download_button("📄 导出完整聊天记录 (PDF)", pdf_bytes, "ai_chat_history.pdf")
    else:
        st.download_button("📄 导出完整聊天记录 (需安装 reportlab)", b"", disabled=True)
        st.caption("💡 终端执行 `pip install reportlab` 解锁聊天记录归档功能")