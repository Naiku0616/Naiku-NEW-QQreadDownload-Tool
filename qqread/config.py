import os
import sys
from typing import Dict, Optional

def _get_download_dir() -> str:
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(os.path.dirname(sys.executable), "downloads")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")

class Config:
    BASE_URL: str = "https://book.qq.com"
    API_BASE_URL: str = "https://book.qq.com"
    
    HEADERS: Dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://book.qq.com/",
        "Origin": "https://book.qq.com",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }
    
    COOKIES: Dict[str, str] = {}
    
    TIMEOUT: int = 30
    
    RETRY_TIMES: int = 3
    
    MAX_WORKERS: int = 5
    
    DOWNLOAD_DIR: str = _get_download_dir()
    
    @classmethod
    def set_cookies(cls, cookies: Dict[str, str]) -> None:
        cls.COOKIES = cookies
    
    @classmethod
    def ensure_download_dir(cls) -> None:
        os.makedirs(cls.DOWNLOAD_DIR, exist_ok=True)

CONFIG = Config()