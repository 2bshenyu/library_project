from typing import Optional


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
            return False  # 重复的书名
        
        if len(title) > self.MAX_LEN or len(author) > self.MAX_LEN:
            return False  # 超过最大长度限制
        
        self.books.append({"title": title, "author": author, "category": category, "available": True})
        # return f"Added '{title}' by '{author}' in category '{categroy}'."
        return True

    def remove_book(self, title: str) -> bool:
        """
        通过书名删除图书。
        如果删除成功返回 True, 如果未找到返回 False。
        """
        for i, book in enumerate(self.books):
            if book["title"].lower() == title.lower():
                self.books.pop(i)
                return True
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
            return f"Error: User '{username}' not found."
        book = self.search_book(title) # 查找书籍
        if book and book[0]["available"]: # 如果书籍存在且可用
            book[0]["available"] = False # book[0] 是字典，修改其 available 属性
            user.borrowed_books.append(book[0]["title"]) 
            return f"Successfully borrowed '{title}' by {book[0]['author']}."
        return f"Error: '{title}' not found or already borrowed."

    def return_book(self, username: str, title: str) -> str:
        """
        通过书名归还图书。  
        返回成功消息或错误信息。
        用户的借阅历史会被更新。
        """
        user = self.users.get(username)
        if not user:
            return f"Error: User '{username}' not found."
        book = self.search_book(title) # 查找书籍
        if book and not book[0]["available"]: # 如果书籍存在且已借出
            book[0]["available"] = True # book[0] 是字典，修改其 available 属性
            if title in user.borrowed_books:
                user.borrowed_books.remove(title) 
            return f"Successfully returned '{title}'."  
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
        return filtered_books
    
    def add_user(self, username: str):
        """添加新用户"""
        if username in self.users:
            return False  # 用户已存在
        self.users[username] = User(username)
        return True
    def view_user_history(self, username: str) -> list:
        """查看用户的借阅历史"""
        user = self.users.get(username)
        if user:
            print(f"借书的人: {username}, 借阅历史: {user.borrowed_books}")
            for book in user.borrowed_books:
                print(f"- {book['title']} by {book['author']} in {book['category']}")
        else:
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