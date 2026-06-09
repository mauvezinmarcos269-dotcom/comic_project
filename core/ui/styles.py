import streamlit as st

def inject_global_styles():
    """注入脱离欢迎页后的主界面通用样式"""
    st.markdown("""
    <style>
    /* 在这里可添加任何主分析界面的定制化 CSS */
    footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)