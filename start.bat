@echo off
chcp 65001 >nul
echo 正在启动美漫数据智能问数平台...
echo.

if not exist "venv\Scripts\activate" (
    echo [错误] 找不到虚拟环境，请先运行 setup.bat！
    pause
    exit /b 1
)

call venv\Scripts\activate
streamlit run main.py
pause