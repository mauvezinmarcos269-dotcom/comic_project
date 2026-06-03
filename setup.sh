echo "========================================"
echo "美漫数据分析平台 - 环境自动配置脚本"
echo "========================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 python3，请先安装 Python！"
    exit 1
fi

# 创建原生虚拟环境
if [ ! -d "venv" ]; then
    echo "[1/4] 创建独立的虚拟环境 venv..."
    python3 -m venv venv
else
    echo "[1/4] 虚拟环境已存在"
fi

# 激活并安装依赖
echo "[2/4] 安装 Python 核心依赖包 (使用清华镜像加速)..."
source venv/bin/activate
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 预加载 NLTK 数据
echo "[3/4] 预加载 NLP 模型数据..."
python3 -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True)"

# 检查配置
echo "[4/4] 检查 API 配置文件..."
if [ ! -f .env ]; then
    echo "[提醒] 未找到 .env 文件，正在自动生成..."
    echo "COMICVINE_API_KEY=your_api_key_here" > .env
fi

echo ""
echo "========================================"
echo "安装完成！"
echo "请在终端执行: ./start.sh 启动系统"
echo "========================================"