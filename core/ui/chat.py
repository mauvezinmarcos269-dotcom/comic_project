import streamlit as st
from core.agent.llm_router import ask_with_llm_router
from core.ui.export_utils import generate_chat_pdf, REPORTLAB_AVAILABLE

def init_chat():
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "欢迎使用美漫销量智能分析平台 👋\n\n你可以问我：\n- 漫威和DC在过去十年谁更具统治力？\n- 帮我找出销量前20的明星编剧",
            "chart": None,
            "evidence": None
        }]

def render_chat(filtered_df, api_key, model_name):
    init_chat()
    
    col1, col2 = st.columns([8, 2])
    with col2:
        if st.button("🧹 清空对话", use_container_width=True):
            del st.session_state.messages
            st.rerun()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("chart") is not None: st.plotly_chart(msg["chart"], use_container_width=True)
            if msg.get("evidence") is not None: st.dataframe(msg["evidence"], use_container_width=True)

    user_query = st.chat_input("向 AI 发起深度数智对话...")
    if user_query:
        if not api_key:
            st.warning("请先在左侧边栏配置您的 API Key")
        else:
            st.session_state.messages.append({"role":"user", "content":user_query, "chart":None, "evidence":None})
            with st.chat_message("user"): st.markdown(user_query)
            
            with st.chat_message("assistant"):
                with st.spinner("数智矩阵计算中..."):
                    try:
                        result = ask_with_llm_router(user_query, filtered_df, api_key, model_name)
                        
                        answer = getattr(result, "answer", str(result))
                        chart = getattr(result, "chart", None)
                        evidence = getattr(result, "evidence", None)
                        
                        st.markdown(answer)
                        if chart: st.plotly_chart(chart, use_container_width=True)
                        if evidence is not None: st.dataframe(evidence, use_container_width=True)
                        
                        st.session_state.messages.append({"role":"assistant", "content":answer, "chart":chart, "evidence":evidence})
                    except Exception as e:
                        st.error(f"分析调度失败: {e}")

    st.divider()
    

    if REPORTLAB_AVAILABLE:
        pdf_bytes = generate_chat_pdf(st.session_state.messages)
        st.download_button("📄 导出完整聊天记录 (PDF)", pdf_bytes, "ai_chat_history.pdf")
    else:
        st.download_button("📄 导出完整聊天记录 (需安装 reportlab)", b"", disabled=True)
        st.caption("💡 终端执行 `pip install reportlab` 解锁聊天记录归档功能")