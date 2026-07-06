# QQ阅读小说下载器

一个命令行工具，用于从QQ阅读下载小说内容。

## 功能

- 获取书籍信息（标题、作者、简介）
- 获取章节列表
- 下载章节内容（支持 TXT/JSON/EPUB 格式）
- 多线程下载
- 交互式命令行模式

## 使用方法

### 双击运行（交互式模式）

直接双击 `qqread_downloader.exe` 文件，进入交互式命令行界面：

```
==================================================
        QQ阅读小说下载器
==================================================
输入 help 查看可用命令
输入 exit 退出程序
==================================================

> help
```

### 交互式命令列表

| 命令 | 说明 | 示例 |
|------|------|------|
| `help` | 显示帮助信息 | `help` |
| `info <书籍ID>` | 获取书籍信息 | `info 54425396` |
| `chapters <书籍ID>` | 获取章节列表 | `chapters 54425396` |
| `download <书籍ID>` | 下载全部章节（TXT格式） | `download 54425396` |
| `download <书籍ID> <格式>` | 下载指定格式 | `download 54425396 json` |
| `download <书籍ID> <格式> <开始> <结束>` | 下载指定章节范围 | `download 54425396 txt 1 10` |
| `search <关键词>` | 搜索书籍 | `search 大生意人` |
| `exit / quit` | 退出程序 | `exit` |

### 命令行运行（参数模式）

```bash
# 获取帮助信息
qqread_downloader.exe --help

# 获取书籍信息
qqread_downloader.exe --book-id 54425396 --info

# 获取章节列表
qqread_downloader.exe --book-id 54425396 --list-chapters

# 下载全部章节（TXT格式）
qqread_downloader.exe --book-id 54425396 --format txt

# 下载指定章节范围
qqread_downloader.exe --book-id 54425396 --format txt --start 1 --end 10
```

## 获取书籍ID

1. 访问 [QQ阅读搜索页面](https://book.qq.com/book-search)
2. 搜索想要下载的书籍
3. 进入书籍详情页，URL中的数字即为书籍ID

例如：`https://book.qq.com/book-detail/54425396` 中的 `54425396` 就是书籍ID

## 输出目录

下载的文件保存在 `downloads` 目录下（与exe同级目录）。

## 注意事项

- 请遵守网站的使用条款
- 仅供个人学习和研究使用
- 部分书籍可能需要登录才能访问全部章节
