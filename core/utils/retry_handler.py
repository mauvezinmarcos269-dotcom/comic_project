import time
import requests
from core.config import RETRY_TIMES, REQUEST_TIMEOUT, REQUEST_DELAY
from core.utils.logger import logger

def retry_request(url, headers=None, params=None, timeout=None):
    if timeout is None:
        timeout = REQUEST_TIMEOUT
    
    for attempt in range(RETRY_TIMES):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                wait_time = 2 ** attempt
                logger.warning(f"触发 API 频控(429)。将在 {wait_time} 秒后进行第 {attempt+1} 次重试...")
                time.sleep(wait_time)
            else:
                logger.error(f"HTTP 异常状态码: {response.status_code}，请求 URL: {url}")
                if attempt == RETRY_TIMES - 1:
                    return None
        except requests.exceptions.Timeout:
            logger.error(f"请求超时: {url}，重试 {attempt+1}/{RETRY_TIMES}")
        except Exception as e:
            logger.error(f"网络连接层异常: {e}。当前重试轮次: ({attempt+1}/{RETRY_TIMES})")
        time.sleep(REQUEST_DELAY)
    return None