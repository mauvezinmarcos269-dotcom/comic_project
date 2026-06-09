import re
from io import BytesIO

# 尝试导入 reportlab，如果未安装则不阻塞程序运行
try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    
    REPORTLAB_AVAILABLE = True
    
    # 注册原生中文支持字体，防止 PDF 乱码
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        HAS_CHINESE_FONT = True
    except Exception:
        HAS_CHINESE_FONT = False
        
except ImportError:
    REPORTLAB_AVAILABLE = False
    HAS_CHINESE_FONT = False


def clean_text_for_pdf(text):
    """清除 LLM 输出的 Markdown 符号，防止 PDF 渲染器崩溃"""
    text = str(text)
    text = re.sub(r'(\*\*|\*|#|>|`|\||-)', '', text)  # 移除 markdown 特殊符号
    return text[:2000] # 截断超长文本


def generate_dashboard_pdf(summary_dict):
    if not REPORTLAB_AVAILABLE:
        return b""
        
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    
    font_name = "STSong-Light" if HAS_CHINESE_FONT else "Helvetica"
    title_style = ParagraphStyle(name="CTitle", parent=styles["Title"], fontName=font_name)
    normal_style = ParagraphStyle(name="CNormal", parent=styles["Normal"], fontName=font_name, leading=16)

    story = [Paragraph("美漫销量商业数据分析报告", title_style), Spacer(1, 12)]
    
    for key, value in summary_dict.items():
        story.append(Paragraph(f"<b>{key}</b>: {value}", normal_style))
        story.append(Spacer(1, 8))
        
    doc.build(story)
    return buffer.getvalue()


def generate_chat_pdf(messages):
    if not REPORTLAB_AVAILABLE:
        return b""
        
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    
    font_name = "STSong-Light" if HAS_CHINESE_FONT else "Helvetica"
    title_style = ParagraphStyle(name="CTitle", parent=styles["Title"], fontName=font_name)
    normal_style = ParagraphStyle(name="CNormal", parent=styles["Normal"], fontName=font_name, leading=14)

    story = [Paragraph("AI 数智终端诊断记录", title_style), Spacer(1, 12)]
    
    for msg in messages:
        role_text = "用户" if msg['role'] == 'user' else "AI 助理"
        clean_content = clean_text_for_pdf(msg['content'])
        story.append(Paragraph(f"<b>[{role_text}]</b>: {clean_content}", normal_style))
        story.append(Spacer(1, 10))
        
    doc.build(story)
    return buffer.getvalue()