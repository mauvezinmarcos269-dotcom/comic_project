import os
from core.utils.logger import logger

# 尝试导入 Grayven
try:
    from grayven.grand_comics_database import GrandComicsDatabase
    GRAYVEN_AVAILABLE = True
except ImportError:
    GRAYVEN_AVAILABLE = False
    logger.warning("Grayven 未安装，GCD 功能不可用。安装: pip install Grayven")


class GCDCollector:
    def __init__(self, email=None, password=None):
        # 1. 默认将会话置为空，这是实现“失败不中断”的关键基础
        self.session = None 
        
        self.email = email or os.getenv("GCD_EMAIL", "")
        self.password = password or os.getenv("GCD_PASSWORD", "")
        
        # 2. 如果没有提供账号，直接平滑退出初始化，不报错
        if not self.email or not self.password:
            logger.info("未设置 GCD 账号，自动跳过 GCD 验证。")
            return
        
        # 3. 只有在库已安装时才尝试初始化
        if GRAYVEN_AVAILABLE:
            try:
                # 尝试连接，显式传入 cache=None 解决 Pylance 报错
                self.session = GrandComicsDatabase(
                    email=self.email,
                    password=self.password,
                    cache=None  
                )
                logger.info("✅ GCD 采集器初始化成功")
                
            except Exception as e:
                # 4. 核心优化：捕获所有登录或网络异常，记录警告但不抛出
                self.session = None  # 明确置空，以防部分初始化残留
                logger.warning(f"⚠️ Grayven 当前登录失败 ({e})，已自动跳过 GCD 验证。")
    
    def fetch_issue_data(self, title, issue):
        """获取期刊数据"""
        # 如果会话未成功初始化，直接返回 None，触发单源降级
        if not self.session:
            return None
        
        try:
            # 移除关键字参数，直接作为位置参数传入
            series_list = self.session.list_series(title)
            if not series_list:
                logger.warning(f"未找到系列: {title}")
                return None
            
            # 获取第一个匹配的系列
            series = series_list[0]
            
            # 优先尝试使用 ID 查询，如果没有 ID 再降级用 name
            series_identifier = getattr(series, 'id', getattr(series, 'name', title))
            issue_num = int(issue) if str(issue).isdigit() else issue
            
            # 移除关键字，直接按顺序传入系列标识和期号
            issues = self.session.list_issues(series_identifier, issue_num)
            
            if not issues:
                logger.warning(f"未找到期刊: {title} #{issue}")
                return None
            
            # 取第一个匹配的期刊
            iss = issues[0]
            
            writer_names = []
            artist_names = []
            
            # 获取 credits
            credits = getattr(iss, 'credits', [])
            if credits:
                for credit in credits:
                    role = getattr(credit, 'role', '')
                    name = getattr(credit, 'name', '')
                    
                    if role and 'writer' in role.lower():
                        writer_names.append(name)
                    if role and ('artist' in role.lower() or 'penciller' in role.lower()):
                        artist_names.append(name)
            
            return {
                "Writer": "; ".join(writer_names) if writer_names else "Unknown",
                "Artist": "; ".join(artist_names) if artist_names else "Unknown",
                "Franchise": getattr(series, 'name', title)
            }
        except Exception as e:
            logger.error(f"GCD 查询失败 [{title} #{issue}]: {e}")
            return None


def fetch_gcd_data(title, issue):
    """简化接口"""
    collector = GCDCollector()
    return collector.fetch_issue_data(title, issue)


def verify_with_gcd(comicvine_data, title, issue):
    """交叉验证"""
    gcd_data = fetch_gcd_data(title, issue)
    
    # 平滑降级：如果没有获取到 GCD 数据，返回原始数据并标记为 Single Source
    if not gcd_data:
        return comicvine_data, "Single Source"
    
    verified = comicvine_data.get("Writer") == gcd_data.get("Writer")
    return comicvine_data, "Verified" if verified else "Needs Review"