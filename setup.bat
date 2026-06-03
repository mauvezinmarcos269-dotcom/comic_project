@echo off
chcp 65001 >nul
echo ========================================
echo 美漫数据分析平台 - 环境自动配置脚本
echo ========================================
echo.

:: 检查 Python 是否安装
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.9+ 并添加到环境变量！
    pause
    exit /b 1
)

:: 创建原生虚拟环境
if not exist "venv\" (
    echo [1/4] 创建独立的虚拟环境 venv...
    python -m venv venv
) else (
    echo [1/4] 虚拟环境已存在
)

:: 激活并安装依赖
echo [2/4] 安装 Python 核心依赖包 (使用清华镜像加速)...
call venv\Scripts\activate
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

:: 预加载 NLTK 数据 (防止 NLP 模块运行时报错)
echo [3/4] 预加载 NLP 模型数据...
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True)"

:: 检查并初始化配置
echo [4/4] 检查 API 配置文件...
if not exist .env (
    echo [提醒] 未找到 .env 文件，正在自动生成...
    echo COMICVINE_API_KEY=your_api_key_here > .env
    echo 已经生成 .env，如有需要请填入真实的 API Key。
)

echo.
echo ========================================
echo 安装配置全部完成！
echo 请直接双击运行 start.bat 启动系统！
echo ========================================
pause