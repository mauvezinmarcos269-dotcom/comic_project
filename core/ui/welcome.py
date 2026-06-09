import os
import base64
import streamlit as st

def show_welcome_page():
    image_path = os.path.join("assets", "hello.bg.jpg")
    img_base64 = ""
    if os.path.exists(image_path):
        with open(image_path, 'rb') as f:
            img_base64 = base64.b64encode(f.read()).decode()
    
    st.markdown(f"""
    <style>
    .element-container, .stButton, .stMarkdown, [data-testid="stVerticalBlock"], 
    div[data-testid="stMarkdownContainer"], .st-emotion-cache-10trblm {{
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }}

    .stApp {{
        background-image: url("data:image/jpeg;base64,{img_base64}");
        background-size: cover;
        background-position: center center;
        background-attachment: fixed;
    }}
    
    [data-testid="stSidebar"] {{ display: none; }}
    [data-testid="stHeader"] {{ background: transparent !important; display: none; }}
    footer {{ visibility: hidden; }}

    .landing-title-group {{
        position: fixed;
        left: 55.48%;
        bottom: calc(35.135% + 75px);
        transform: translateX(-50%); 
        text-align: center;
        width: max-content;
        z-index: 998;
        pointer-events: none;
    }}
    .landing-title-group h1 {{
        color: #FFFFFF !important; font-size: 4.3rem !important; font-weight: 900 !important;
        margin: 0 0 6px 0 !important; letter-spacing: 6px;
        text-shadow: 0 0 12px rgba(0, 75, 255, 0.9), 0 0 25px rgba(0, 50, 200, 0.8), 0 0 50px rgba(0, 30, 150, 0.6) !important;
    }}
    .landing-title-group p {{
        color: #9cbcd6 !important; font-size: 1.25rem !important; font-weight: 600 !important;
        letter-spacing: 3px; margin: 0 !important; text-shadow: 0px 2px 5px rgba(0,0,0,0.9) !important;
    }}

    .visual-arrow-zone {{
        position: fixed; left: 53%; bottom: 33.5%; transform: translateX(-50%);
        text-align: center; z-index: 998; pointer-events: none; 
    }}
    .arrow-down {{
        width: 24px; height: 24px; border-right: 4px solid #ffffff; border-bottom: 4px solid #ffffff;
        transform: rotate(45deg); margin: 0 auto 12px auto; animation: smooth-bounce 1.5s infinite ease-in-out;
        filter: drop-shadow(0 0 10px rgba(0, 80, 255, 1)); 
    }}
    .enter-text {{
        color: #ffffff !important; font-size: 1.15rem !important; font-weight: bold !important;
        letter-spacing: 2px; text-shadow: 0 2px 4px rgba(0,0,0,0.9), 0 0 12px rgba(0,75,200,0.8);
        white-space: nowrap;
    }}

    @keyframes smooth-bounce {{
        0%, 100% {{ transform: translateY(0) rotate(45deg); }}
        50% {{ transform: translateY(-10px) rotate(45deg); }}
    }}

    div.element-container:has(button) {{ position: fixed !important; top: 0 !important; left: 0 !important; width: 100vw !important; height: 100vh !important; z-index: 999999 !important; }}
    button {{ position: fixed !important; top: 0 !important; left: 0 !important; width: 100vw !important; height: 100vh !important; padding: 0 !important; margin: 0 !important; border: none !important; border-radius: 0 !important; background: transparent !important; background-color: transparent !important; box-shadow: none !important; outline: none !important; opacity: 0 !important; cursor: pointer !important; z-index: 999999 !important; }}
    button:hover, button:active, button:focus {{ background: transparent !important; background-color: transparent !important; opacity: 0 !important; border: none !important; box-shadow: none !important; outline: none !important; }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="landing-title-group">
        <h1>美漫销量智能问数</h1>
        <p>Comichron + ComicVine Data Engine</p>
    </div>
    <div class="visual-arrow-zone">
        <div class="arrow-down"></div>
        <div class="enter-text">✨ 点击进入</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("", key="logical_fullscreen_trigger_btn"):
        st.session_state.welcome_done = True
        st.rerun()