import requests
import json
import re
import time
from typing import Dict, Optional, Any, List
from bs4 import BeautifulSoup
from config import CONFIG

class QQReadAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(CONFIG.HEADERS)
        if CONFIG.COOKIES:
            self.session.cookies.update(CONFIG.COOKIES)
    
    def _request(self, method: str, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        for retry in range(CONFIG.RETRY_TIMES):
            try:
                response = self.session.request(method, url, timeout=CONFIG.TIMEOUT, **kwargs)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"请求失败 ({retry + 1}/{CONFIG.RETRY_TIMES}): {e}")
                if retry < CONFIG.RETRY_TIMES - 1:
                    time.sleep(2 ** retry)
        return None
    
    def _get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        return self._request("GET", url, params=params)
    
    def _get_web_page(self, url: str) -> Optional[str]:
        try:
            response = self.session.get(url, timeout=CONFIG.TIMEOUT)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"获取页面失败: {e}")
            return None
    
    def search_book(self, keyword: str, page: int = 1, page_size: int = 20) -> Optional[Dict[str, Any]]:
        url = f"https://book.qq.com/book-search?keyword={keyword}&pageIndex={page}&pageSize={page_size}"
        html = self._get_web_page(url)
        
        if not html:
            return None
        
        try:
            soup = BeautifulSoup(html, "lxml")
            book_list = []
            
            for item in soup.select(".search-result-item"):
                title_tag = item.select_one("h3")
                author_tag = item.select_one(".author")
                desc_tag = item.select_one(".intro")
                link_tag = item.select_one("a")
                
                if link_tag:
                    href = link_tag.get("href", "")
                    book_id_match = re.search(r'/book-detail/(\d+)', href)
                    book_id = book_id_match.group(1) if book_id_match else ""
                else:
                    book_id = ""
                
                book_info = {
                    "bookId": book_id,
                    "title": title_tag.get_text(strip=True) if title_tag else "",
                    "author": author_tag.get_text(strip=True) if author_tag else "",
                    "desc": desc_tag.get_text(strip=True)[:200] if desc_tag else "",
                }
                book_list.append(book_info)
            
            if not book_list:
                for meta in soup.find_all('meta'):
                    if meta.get('property') == 'og:novel:book_name':
                        book_list.append({
                            "bookId": "",
                            "title": meta.get('content', ""),
                            "author": "",
                            "desc": "",
                        })
            
            return {
                "code": 0,
                "data": {
                    "books": book_list,
                    "total": len(book_list),
                }
            }
        except Exception as e:
            print(f"解析搜索结果失败: {e}")
            return None
    
    def get_book_info(self, book_id: str) -> Optional[Dict[str, Any]]:
        url = f"https://book.qq.com/book-detail/{book_id}"
        html = self._get_web_page(url)
        
        if not html:
            return None
        
        try:
            soup = BeautifulSoup(html, "lxml")
            book_info = {}
            
            for meta in soup.find_all('meta'):
                prop = meta.get('property', '')
                content = meta.get('content', '')
                if prop == 'og:novel:book_name':
                    book_info['title'] = content
                elif prop == 'og:novel:author':
                    book_info['author'] = content
                elif prop == 'og:description':
                    book_info['desc'] = content
                elif prop == 'og:novel:status':
                    book_info['status'] = content
                elif prop == 'og:novel:latest_chapter_name':
                    book_info['latest_chapter'] = content
            
            title_tag = soup.select_one(".book-title")
            if title_tag and 'title' not in book_info:
                book_info['title'] = title_tag.get_text(strip=True)
            
            author_tag = soup.select_one(".book-author")
            if author_tag and 'author' not in book_info:
                book_info['author'] = author_tag.get_text(strip=True)
            
            intro_tag = soup.select_one(".book-intro")
            if intro_tag and 'desc' not in book_info:
                book_info['desc'] = intro_tag.get_text(strip=True)
            
            script_tag = soup.find("script", id="__NEXT_DATA__")
            if script_tag:
                try:
                    next_data = json.loads(script_tag.string)
                    book_data = next_data.get("props", {}).get("pageProps", {}).get("bookInfo", {})
                    if book_data:
                        if 'title' not in book_info and book_data.get("title"):
                            book_info['title'] = book_data["title"]
                        if 'author' not in book_info and book_data.get("author"):
                            book_info['author'] = book_data["author"]
                        if 'desc' not in book_info and book_data.get("intro"):
                            book_info['desc'] = book_data["intro"]
                except:
                    pass
            
            return {
                "code": 0,
                "data": book_info,
            }
        except Exception as e:
            print(f"解析书籍信息失败: {e}")
            return None
    
    def get_chapter_list(self, book_id: str) -> Optional[Dict[str, Any]]:
        url = f"https://book.qq.com/book-detail/{book_id}"
        html = self._get_web_page(url)
        
        if not html:
            return None
        
        try:
            soup = BeautifulSoup(html, "lxml")
            chapters = []
            
            script_tag = soup.find("script", id="__NEXT_DATA__")
            if script_tag:
                try:
                    next_data = json.loads(script_tag.string)
                    chapter_list = next_data.get("props", {}).get("pageProps", {}).get("chapterList", {})
                    if chapter_list:
                        for item in chapter_list.get("list", []):
                            chapter_info = {
                                "chapterId": str(item.get("chapterIdx", "")),
                                "title": item.get("chapterTitle", ""),
                                "index": item.get("chapterIdx", 0),
                            }
                            chapters.append(chapter_info)
                except Exception as e:
                    print(f"解析JSON章节数据失败: {e}")
            
            if not chapters:
                for item in soup.select(".chapter-list li a"):
                    href = item.get("href", "")
                    chapter_match = re.search(r'/book-read/(\d+)/(\d+)', href)
                    if chapter_match:
                        book_id_from_url = chapter_match.group(1)
                        chapter_index = chapter_match.group(2)
                        
                        chapter_info = {
                            "chapterId": chapter_index,
                            "title": item.get_text(strip=True),
                            "index": int(chapter_index),
                        }
                        chapters.append(chapter_info)
            
            if not chapters:
                latest_chapter_url = ""
                for meta in soup.find_all('meta'):
                    if meta.get('property') == 'og:novel:latest_chapter_url':
                        latest_chapter_url = meta.get('content', '')
                        break
                
                if latest_chapter_url:
                    match = re.search(r'/book-read/(\d+)/(\d+)', latest_chapter_url)
                    if match:
                        total_chapters = int(match.group(2))
                        for i in range(1, total_chapters + 1):
                            chapters.append({
                                "chapterId": str(i),
                                "title": f"第{i}章",
                                "index": i,
                            })
            
            if not chapters:
                js_data_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.S)
                if js_data_match:
                    try:
                        js_data = json.loads(js_data_match.group(1))
                        chapter_list = js_data.get("chapterList", {}).get("list", [])
                        for item in chapter_list:
                            chapter_info = {
                                "chapterId": str(item.get("chapterIdx", "")),
                                "title": item.get("chapterTitle", ""),
                                "index": item.get("chapterIdx", 0),
                            }
                            chapters.append(chapter_info)
                    except:
                        pass
            
            return {
                "code": 0,
                "data": {
                    "chapters": chapters,
                    "total": len(chapters),
                }
            }
        except Exception as e:
            print(f"解析章节列表失败: {e}")
            return None
    
    def get_chapter_content(self, book_id: str, chapter_id: str) -> Optional[Dict[str, Any]]:
        url = f"https://book.qq.com/book-read/{book_id}/{chapter_id}"
        html = self._get_web_page(url)
        
        if not html:
            return None
        
        try:
            soup = BeautifulSoup(html, "lxml")
            
            content_tag = soup.select_one(".chapter-content")
            title_tag = soup.select_one(".chapter-title")
            
            if content_tag:
                paragraphs = []
                for p in content_tag.select("p"):
                    text = p.get_text(strip=True)
                    if text:
                        paragraphs.append(text)
                content = "\n\n".join(paragraphs)
            else:
                content = ""
            
            title = title_tag.get_text(strip=True) if title_tag else f"第{chapter_id}章"
            
            script_tag = soup.find("script", id="__NEXT_DATA__")
            if script_tag and not content:
                try:
                    next_data = json.loads(script_tag.string)
                    chapter_data = next_data.get("props", {}).get("pageProps", {}).get("chapter", {})
                    if chapter_data:
                        content = chapter_data.get("content", "")
                        if not title:
                            title = chapter_data.get("title", f"第{chapter_id}章")
                except:
                    pass
            
            if not content:
                content_div = soup.find("div", id="chapterContent")
                if content_div:
                    paragraphs = []
                    for p in content_div.select("p"):
                        text = p.get_text(strip=True)
                        if text:
                            paragraphs.append(text)
                    content = "\n\n".join(paragraphs)
            
            return {
                "code": 0,
                "data": {
                    "content": content,
                    "title": title,
                }
            }
        except Exception as e:
            print(f"解析章节内容失败: {e}")
            return None
    
    def set_cookies(self, cookies: Dict[str, str]) -> None:
        self.session.cookies.update(cookies)
        CONFIG.set_cookies(cookies)