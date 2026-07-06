import os
import time
import json
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from api import QQReadAPI
from config import CONFIG

class Downloader:
    def __init__(self):
        self.api = QQReadAPI()
        self.chapters: List[Dict[str, Any]] = []
        self.book_info: Dict[str, Any] = {}
        CONFIG.ensure_download_dir()
    
    def set_cookies(self, cookies: Dict[str, str]) -> None:
        self.api.set_cookies(cookies)
    
    def fetch_book_info(self, book_id: str) -> bool:
        print(f"正在获取书籍信息: {book_id}")
        result = self.api.get_book_info(book_id)
        if result and result.get("code") == 0:
            self.book_info = result.get("data", {})
            print(f"书籍标题: {self.book_info.get('title')}")
            print(f"作者: {self.book_info.get('author')}")
            print(f"简介: {self.book_info.get('desc', '')[:100]}...")
            return True
        print(f"获取书籍信息失败: {result}")
        return False
    
    def fetch_chapter_list(self, book_id: str) -> bool:
        print(f"正在获取章节列表: {book_id}")
        result = self.api.get_chapter_list(book_id)
        if result and result.get("code") == 0:
            self.chapters = result.get("data", {}).get("chapters", [])
            print(f"共获取到 {len(self.chapters)} 个章节")
            return True
        print(f"获取章节列表失败: {result}")
        return False
    
    def fetch_chapter_content(self, book_id: str, chapter_id: str) -> Optional[str]:
        result = self.api.get_chapter_content(book_id, chapter_id)
        if result and result.get("code") == 0:
            data = result.get("data", {})
            return data.get("content", "")
        return None
    
    def download_single_chapter(self, book_id: str, chapter: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        chapter_id = chapter.get("chapterId")
        title = chapter.get("title")
        
        try:
            content = self.fetch_chapter_content(book_id, chapter_id)
            if content:
                return {
                    "chapterId": chapter_id,
                    "title": title,
                    "content": content,
                    "index": chapter.get("index", 0),
                }
            print(f"章节 {title} 内容为空")
            return None
        except Exception as e:
            print(f"下载章节 {title} 失败: {e}")
            return None
    
    def download_all_chapters(self, book_id: str, start_chapter: int = 1, end_chapter: int = -1) -> List[Dict[str, Any]]:
        if not self.chapters:
            if not self.fetch_chapter_list(book_id):
                return []
        
        if start_chapter < 1:
            start_chapter = 1
        
        if end_chapter <= 0 or end_chapter > len(self.chapters):
            end_chapter = len(self.chapters)
        
        start_idx = start_chapter - 1
        chapters_to_download = self.chapters[start_idx:end_chapter]
        print(f"开始下载 {len(chapters_to_download)} 个章节 ({start_chapter} - {end_chapter})")
        
        results = []
        with ThreadPoolExecutor(max_workers=CONFIG.MAX_WORKERS) as executor:
            futures = {
                executor.submit(self.download_single_chapter, book_id, chapter): chapter
                for chapter in chapters_to_download
            }
            
            with tqdm(total=len(futures), desc="下载进度") as pbar:
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        results.append(result)
                    pbar.update(1)
                    time.sleep(0.1)
        
        results.sort(key=lambda x: x.get("index", 0))
        print(f"下载完成，共获取 {len(results)} 个章节")
        return results
    
    def save_chapters_to_file(self, chapters: List[Dict[str, Any]], format: str = "txt") -> str:
        book_title = self.book_info.get("title", "未知书籍").replace("/", "_").replace("\\", "_")
        author = self.book_info.get("author", "未知作者")
        
        if format == "txt":
            filename = f"{book_title}.txt"
            filepath = os.path.join(CONFIG.DOWNLOAD_DIR, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"书名：{book_title}\n")
                f.write(f"作者：{author}\n")
                f.write(f"章节数：{len(chapters)}\n")
                f.write("\n" + "=" * 50 + "\n\n")
                
                for chapter in chapters:
                    f.write(f"{chapter.get('title', '')}\n\n")
                    f.write(chapter.get("content", "") + "\n\n")
                    f.write("-" * 40 + "\n\n")
            
            print(f"书籍已保存为: {filepath}")
            return filepath
        
        elif format == "json":
            filename = f"{book_title}.json"
            filepath = os.path.join(CONFIG.DOWNLOAD_DIR, filename)
            
            book_data = {
                "title": book_title,
                "author": author,
                "chapters": chapters,
            }
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(book_data, f, ensure_ascii=False, indent=2)
            
            print(f"书籍已保存为: {filepath}")
            return filepath
        
        return ""
    
    def download_book(self, book_id: str, format: str = "txt", start_chapter: int = 0, end_chapter: int = -1) -> Optional[str]:
        if not self.fetch_book_info(book_id):
            return None
        
        chapters = self.download_all_chapters(book_id, start_chapter, end_chapter)
        
        if chapters:
            return self.save_chapters_to_file(chapters, format)
        
        return None