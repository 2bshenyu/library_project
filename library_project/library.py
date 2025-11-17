from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)

# 配置默认的文件日志（写入到 library_project/logs/library.log），包含时间戳和级别
try:
    base_dir = os.path.dirname(__file__)
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    logfile = os.path.join(logs_dir, "library.log")
    if not logger.hasHandlers():
        fh = logging.FileHandler(logfile, encoding="utf-8")
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        logger.setLevel(logging.INFO)
except Exception:
    # 日志配置失败时不阻塞功能（例如在只读文件系统）
    pass


class Library:
    """
    一个简单的图书馆管理系统。
    管理图书集合，支持添加、删除、搜索、借阅和归还功能。
    """
    MAX_LEN = 200

    def __init__(self):
        self.books = []  # 字典列表：{'title': str, 'author': str, 'available': bool}
        self.users = {}  # 用户信息字典，用户名为键，User 对象为值

    def add_book(self, title: str, author: str, category: Optional[str] = None) -> bool:
        """
        向图书馆添加新书。
        如果添加成功（书名不重复）返回 True, 否则返回 False。
        空字符串或纯空格的书名或作者名将被拒绝。
        书名和作者名的最大长度为 200 个字符。
        """
        # 检查空输入或纯空格输入
        if not title.strip() or not author.strip():
            return False
        if category is not None and not category.strip():
            return False

        if any(book["title"].lower() == title.lower() for book in self.books):
            logger.error("Add failed: duplicate title '%s'", title)
            return False  # 重复的书名
        
        if len(title) > self.MAX_LEN or len(author) > self.MAX_LEN:
            logger.error("Add failed: title/author exceed max length (title=%d, author=%d)", len(title), len(author))
            return False  # 超过最大长度限制
        
        self.books.append({"title": title, "author": author, "category": category, "available": True})
        logger.info("Added book '%s' by '%s' in category '%s'", title, author, category)
        return True

    def remove_book(self, title: str, prompt: bool = False) -> bool:
        """
        通过书名删除图书。
        如果删除成功返回 True, 如果未找到返回 False。
        """
        # 如果需要交互确认，询问用户
        if prompt:
            try:
                ans = input(f"Confirm remove '{title}'? [Y/N]: ")
            except Exception:
                logger.error("Remove aborted: confirmation input failed for '%s'", title)
                return False
            if not ans or ans.strip().lower() not in ("y", "yes"):
                logger.info("Remove cancelled by user for '%s'", title)
                return False

        for i, book in enumerate(self.books):
            if book["title"].lower() == title.lower():
                self.books.pop(i)
                logger.info("Removed book '%s'", title)
                return True
        logger.error("Remove failed: '%s' not found", title)
        return False

    def search_book(self, title: str,author:Optional[str] = None,category:Optional[str] = None) -> list:
        """
        通过书名搜索图书（不区分大小写的部分匹配）。
        返回匹配的图书列表。
        """
        foundbooks=[]
        for book in self.books: 
            if title.lower() in book["title"].lower():
                if author and author.lower() not in book["author"].lower():
                    continue
                if category and (book["category"] is None or category.lower() not in book["category"].lower()):
                    continue
                foundbooks.append(book)
        # 记录检索操作与结果数量，便于审计和排错
        logger.info("Search performed: title='%s' author='%s' category='%s' -> %d results", title, author, category, len(foundbooks))
        if foundbooks:
            for book in foundbooks:
                print(f"已搜索 '{book['title']}' by {book['author']} in {book['category']}")
            return foundbooks 
        else:
            print("No books found matching the search criteria.")
            return foundbooks 

    def borrow_book(self, username: str, title: str) -> str:
        """
        通过书名借阅图书。
        返回成功消息或错误信息。
        用户的借阅历史会被记录。
        """
        user = self.users.get(username)
        if not user:
            logger.error("Borrow failed: user '%s' not found (title='%s')", username, title)
            return f"Error: User '{username}' not found."
        book = self.search_book(title) # 查找书籍
        if book and book[0]["available"]: # 如果书籍存在且可用
            book[0]["available"] = False # book[0] 是字典，修改其 available 属性
            user.borrowed_books.append(book[0]["title"]) 
            logger.info("User '%s' borrowed '%s'", username, book[0]["title"])
            return f"Successfully borrowed '{title}' by {book[0]['author']}."
        logger.error("Borrow failed: '%s' not found or already borrowed (user='%s')", title, username)
        return f"Error: '{title}' not found or already borrowed."

    def return_book(self, username: str, title: str) -> str:
        """
        通过书名归还图书。  
        返回成功消息或错误信息。
        用户的借阅历史会被更新。
        """
        user = self.users.get(username)
        if not user:
            logger.error("Return failed: user '%s' not found (title='%s')", username, title)
            return f"Error: User '{username}' not found."
        book = self.search_book(title) # 查找书籍
        if book and not book[0]["available"]: # 如果书籍存在且已借出
            book[0]["available"] = True # book[0] 是字典，修改其 available 属性
            if title in user.borrowed_books:
                user.borrowed_books.remove(title) 
            logger.info("User '%s' returned '%s'", username, title)
            return f"Successfully returned '{title}'."  
        logger.error("Return failed: '%s' not found or not borrowed (user='%s')", title, username)
        return f"Error: '{title}' not found or not borrowed."
    
        # """
        # 通过书名归还图书。
        # 返回成功消息或错误信息。

        # """
        # for book in self.books:
        #     if book["title"].lower() == title.lower() and not book["available"]:
        #         book["available"] = True
        #         return f"Successfully returned '{title}'."
        # return f"Error: '{title}' not found or not borrowed."

    def get_available_books(self) -> list:
        """
        获取所有可借阅的图书列表。
        """
        return [book for book in self.books if book["available"]]
    
    def filter_by_category(self, category: str):
        """按分类筛选书籍"""
        filtered_books = [book for book in self.books if book.get("category") and book["category"].lower() == category.lower()]
        logger.info("Filter by category: '%s' -> %d results", category, len(filtered_books))
        return filtered_books
    
    def add_user(self, username: str):
        """添加新用户"""
        if username in self.users:
            logger.error("Add user failed: user '%s' already exists", username)
            return False  # 用户已存在
        self.users[username] = User(username)
        logger.info("Added user '%s'", username)
        return True
    def view_user_history(self, username: str) -> list:
        """查看用户的借阅历史"""
        user = self.users.get(username)
        if user:
            logger.info("View history: user='%s' entries=%d", username, len(user.borrowed_books))
            print(f"借书的人: {username}, 借阅历史: {user.borrowed_books}")
            for book in user.borrowed_books:
                print(f"- {book['title']} by {book['author']} in {book['category']}")
        else:
            logger.error("View history failed: user '%s' not found", username)
            print(f"Error: User '{username}' not found.")


class User:
    def __init__(self, username: str):
        self.username = username
        self.borrowed_books = []  # 记录用户借阅的书籍

    def borrow(self, book):
        """借阅书籍"""
        self.borrowed_books.append(book)
    
    def return_book(self, book):
        """归还书籍"""
        if book in self.borrowed_books:
            self.borrowed_books.remove(book)
