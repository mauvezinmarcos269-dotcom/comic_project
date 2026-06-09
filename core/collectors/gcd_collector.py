import os
from core.utils.logger import logger
from core.config import TITLE_TRANSLATIONS

try:
    from grayven.grand_comics_database import GrandComicsDatabase
    GRAYVEN_AVAILABLE = True
except ImportError:
    GRAYVEN_AVAILABLE = False
    logger.warning("Grayven 未安装，GCD 功能不可用。安装: pip install Grayven")


class GCDCollector:
    def __init__(self, email=None, password=None):
        self.session = None
        self.email = email or os.getenv("GCD_EMAIL", "")
        self.password = password or os.getenv("GCD_PASSWORD", "")
        
        if not self.email or not self.password:
            logger.info("未设置 GCD 账号，自动跳过。")
            return
            
        if GRAYVEN_AVAILABLE:
            try:
                self.session = GrandComicsDatabase(email=self.email, password=self.password, cache=None)
                logger.info("✅ GCD 初始化成功")
            except Exception as e:
                self.session = None
                logger.warning(f"GCD 登录失败: {e}")

    def fetch_issue_data(self, title, issue):
        if not self.session:
            return None
        try:
            clean_title = str(title).strip().lower()
            for cn, en in TITLE_TRANSLATIONS.items():
                if cn in clean_title:
                    clean_title = clean_title.replace(cn, en).strip()
                    break
            
            series_list = self.session.list_series(clean_title)
            if not series_list:
                return None
            series = series_list[0]
            
            issue_num = int(issue) if str(issue).isdigit() else issue
            issues = self.session.list_issues(getattr(series, 'id', clean_title), issue_num)
            if not issues:
                return None
            
            iss = issues[0]
            writers, artists = [], []
            for credit in getattr(iss, 'credits', []):
                role = getattr(credit, 'role', '').lower()
                name = getattr(credit, 'name', '')
                if 'writer' in role:
                    writers.append(name)
                if any(k in role for k in ['artist', 'penciller']):
                    artists.append(name)
            
            return {
                "Writer": "; ".join(writers) or "Unknown",
                "Artist": "; ".join(artists) or "Unknown",
                "Franchise": getattr(series, 'name', clean_title)
            }
        except Exception as e:
            logger.error(f"GCD 查询失败: {e}")
            return None


_GCD_COLLECTOR = None

def get_gcd_collector():
    global _GCD_COLLECTOR
    if _GCD_COLLECTOR is None:
        _GCD_COLLECTOR = GCDCollector()
    return _GCD_COLLECTOR

def fetch_gcd_data(title, issue):
    return get_gcd_collector().fetch_issue_data(title, issue)

def verify_with_gcd(comicvine_data, title, issue):
    gcd_data = fetch_gcd_data(title, issue)
    if not gcd_data:
        return comicvine_data, "Single Source"
    verified = comicvine_data.get("Writer") == gcd_data.get("Writer")
    return comicvine_data, "Verified" if verified else "Needs Review"
