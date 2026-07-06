import argparse
import sys
import json
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from downloader import Downloader
from api import QQReadAPI

def parse_cookies(cookie_str: str) -> dict:
    cookies = {}
    if not cookie_str:
        return cookies
    
    for pair in cookie_str.split(";"):
        pair = pair.strip()
        if "=" in pair:
            key, value = pair.split("=", 1)
            cookies[key.strip()] = value.strip()
    
    return cookies

def show_help():
    help_text = """
QQ阅读小说下载器 - 命令列表

常用命令:
  info <书籍ID>          - 获取书籍信息
  chapters <书籍ID>      - 获取章节列表
  download <书籍ID>      - 下载书籍（默认TXT格式，全部章节）
  download <书籍ID> <格式> <开始> <结束>  - 下载指定章节范围
  search <关键词>        - 搜索书籍
  help                   - 显示帮助信息
  exit / quit            - 退出程序

格式选项: txt, json, epub
章节范围: 数字，如 1 10 表示第1-10章

示例:
  info 54425396
  chapters 54425396
  download 54425396
  download 54425396 txt 1 10
  search 大生意人
"""
    print(help_text)

def execute_command(cmd_parts):
    if not cmd_parts:
        return True
    
    cmd = cmd_parts[0].lower()
    
    if cmd in ['exit', 'quit']:
        print("退出程序...")
        return False
    
    elif cmd == 'help':
        show_help()
        return True
    
    elif cmd == 'info':
        if len(cmd_parts) < 2:
            print("用法: info <书籍ID>")
            return True
        book_id = cmd_parts[1]
        downloader = Downloader()
        downloader.fetch_book_info(book_id)
        return True
    
    elif cmd == 'chapters':
        if len(cmd_parts) < 2:
            print("用法: chapters <书籍ID>")
            return True
        book_id = cmd_parts[1]
        downloader = Downloader()
        downloader.fetch_chapter_list(book_id)
        for i, chapter in enumerate(downloader.chapters):
            print(f"{i + 1}. {chapter.get('title')} (ID: {chapter.get('chapterId')})")
        return True
    
    elif cmd == 'download':
        if len(cmd_parts) < 2:
            print("用法: download <书籍ID> [格式] [开始章节] [结束章节]")
            return True
        
        book_id = cmd_parts[1]
        fmt = cmd_parts[2] if len(cmd_parts) > 2 else 'txt'
        start = int(cmd_parts[3]) if len(cmd_parts) > 3 else 1
        end = int(cmd_parts[4]) if len(cmd_parts) > 4 else -1
        
        downloader = Downloader()
        filepath = downloader.download_book(
            book_id=book_id,
            format=fmt,
            start_chapter=start,
            end_chapter=end,
        )
        
        if filepath:
            print(f"\n下载完成！文件保存在: {filepath}")
        else:
            print("\n下载失败！")
        return True
    
    elif cmd == 'search':
        if len(cmd_parts) < 2:
            print("用法: search <关键词>")
            return True
        
        keyword = ' '.join(cmd_parts[1:])
        api = QQReadAPI()
        result = api.search_book(keyword)
        
        if result and result.get("code") == 0:
            books = result.get("data", {}).get("books", [])
            print(f"搜索结果 ({len(books)} 本):")
            for book in books:
                print(f"ID: {book.get('bookId')}")
                print(f"标题: {book.get('title')}")
                print(f"作者: {book.get('author')}")
                print(f"简介: {book.get('desc', '')[:100]}...")
                print("-" * 40)
        else:
            print(f"搜索失败: {result}")
        return True
    
    else:
        print(f"未知命令: {cmd}")
        print("输入 help 查看可用命令")
        return True

def main():
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description="QQ阅读小说下载器", add_help=False)
        parser.add_argument("--book-id", type=str, default="", help="书籍ID")
        parser.add_argument("--format", type=str, default="txt", choices=["txt", "json", "epub"], help="输出格式")
        parser.add_argument("--start", type=int, default=1, help="开始章节索引")
        parser.add_argument("--end", type=int, default=-1, help="结束章节索引")
        parser.add_argument("--cookies", type=str, default="", help="Cookie字符串")
        parser.add_argument("--search", type=str, default="", help="搜索书籍关键词")
        parser.add_argument("--info", action="store_true", help="只显示书籍信息")
        parser.add_argument("--list-chapters", action="store_true", help="只显示章节列表")
        parser.add_argument("--help", action="store_true", help="显示帮助信息")
        
        args = parser.parse_args()
        
        if args.help:
            show_help()
            try:
                input("\n按任意键退出...")
            except (EOFError, KeyboardInterrupt):
                pass
            return
        
        if args.search:
            api = QQReadAPI()
            if args.cookies:
                api.set_cookies(parse_cookies(args.cookies))
            
            result = api.search_book(args.search)
            if result and result.get("code") == 0:
                books = result.get("data", {}).get("books", [])
                print(f"搜索结果 ({len(books)} 本):")
                for book in books:
                    print(f"ID: {book.get('bookId')}")
                    print(f"标题: {book.get('title')}")
                    print(f"作者: {book.get('author')}")
                    print(f"简介: {book.get('desc', '')[:100]}...")
                    print("-" * 40)
            else:
                print(f"搜索失败: {result}")
            try:
                input("\n按任意键退出...")
            except (EOFError, KeyboardInterrupt):
                pass
            return
        
        if not args.book_id:
            print("错误: 请提供书籍ID (--book-id)")
            show_help()
            try:
                input("\n按任意键退出...")
            except (EOFError, KeyboardInterrupt):
                pass
            sys.exit(1)
        
        downloader = Downloader()
        
        if args.cookies:
            downloader.set_cookies(parse_cookies(args.cookies))
        
        if args.info:
            downloader.fetch_book_info(args.book_id)
            try:
                input("\n按任意键退出...")
            except (EOFError, KeyboardInterrupt):
                pass
            return
        
        if args.list_chapters:
            downloader.fetch_chapter_list(args.book_id)
            for i, chapter in enumerate(downloader.chapters):
                print(f"{i + 1}. {chapter.get('title')} (ID: {chapter.get('chapterId')})")
            try:
                input("\n按任意键退出...")
            except (EOFError, KeyboardInterrupt):
                pass
            return
        
        filepath = downloader.download_book(
            book_id=args.book_id,
            format=args.format,
            start_chapter=args.start,
            end_chapter=args.end,
        )
        
        if filepath:
            print(f"\n下载完成！文件保存在: {filepath}")
        else:
            print("\n下载失败！")
            try:
                input("\n按任意键退出...")
            except (EOFError, KeyboardInterrupt):
                pass
            sys.exit(1)
        
        try:
            input("\n按任意键退出...")
        except (EOFError, KeyboardInterrupt):
            pass
        return
    
    print("=" * 50)
    print("        QQ阅读小说下载器")
    print("=" * 50)
    print("输入 help 查看可用命令")
    print("输入 exit 退出程序")
    print("=" * 50)
    
    while True:
        try:
            command = input("\n> ").strip()
            if not command:
                continue
            
            cmd_parts = command.split()
            if not execute_command(cmd_parts):
                break
        except (EOFError, KeyboardInterrupt):
            print("\n退出程序...")
            break
        except Exception as e:
            print(f"执行命令出错: {e}")

if __name__ == "__main__":
    main()