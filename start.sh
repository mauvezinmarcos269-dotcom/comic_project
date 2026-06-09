echo "正在启动美漫数据智能问数平台..."

if [ ! -f "venv/bin/activate" ]; then
    echo "[错误] 找不到虚拟环境，请先执行 ./setup.sh"
    exit 1
fi

source venv/bin/activate
streamlit run app.py