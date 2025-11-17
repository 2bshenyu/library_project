from typing import Optional
import logging
import os
import sqlite3

logger = logging.getLogger(__name__)

# =====================================================================
# 日志配置
# =====================================================================
# 配置默认的文件日志（写入到 library_project/logs/library.log），包含时间戳和级别
# 日志记录了所有的操作（添加、删除、搜索等），用于审计和调试
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
    """SQLite-backed Library（使用 SQLite 持久化存储的图书馆管理系统）。

    一个简单的图书馆管理系统，支持添加、删除、搜索、借阅和归还功能。
    
    核心特性：
    - 使用 SQLite3 数据库进行数据持久化存储（可选文件路径或内存数据库）。
    - 维护兼容性：保留 `books`（list of dicts）和 `users`（dict of User）属性以兼容现有测试。
    - 内存缓存与数据库同步：所有操作都会同时更新内存副本与 SQLite 数据库。
    - 灵活的搜索和过滤：支持按书名（模糊匹配）、作者、分类进行搜索。

    数据库架构：
    - books 表：存储书籍信息（id、title、author、category、available）。
      其中 title 字段为 UNIQUE 约束，确保书名唯一性。
    - users 表：存储用户信息（username），以 username 为主键。
    - borrowed 表：存储用户借阅关系（username、book_title），实现多对多关系。
      包含外键约束，确保数据参照完整性。

    使用示例：
        # 使用文件数据库（持久化）
        lib = Library(db_path="library.db")
        lib.add_book("Python 基础", "Alice", "编程")
        lib.add_user("alice")
        lib.borrow_book("alice", "Python 基础")
        lib.close()  # 必须调用 close() 以提交所有改动
        
        # 使用内存数据库（测试）
        lib_mem = Library()  # 或 Library(db_path=":memory:")
    """
    MAX_LEN = 200

    def __init__(self, db_path: Optional[str] = None):
        """初始化图书馆系统。

        参数：
            db_path (Optional[str]): SQLite 数据库文件路径。
                - 若为 None，使用内存数据库（":memory:"），适用于测试或临时数据。
                  内存数据库在程序结束时自动清空。
                - 若为文件路径，数据会持久化到该文件，程序重启后数据仍然存在。
                  若路径为相对路径，会相对于项目根目录进行解析。
                
        初始化操作流程：
            1. 创建或打开 SQLite 连接（check_same_thread=False 支持多线程访问）。
            2. 设置 row_factory 为 sqlite3.Row 以便通过列名访问行数据。
            3. 调用 _ensure_schema() 创建表结构（如不存在）。
            4. 初始化内存缓存列表 self.books 和字典 self.users。
            5. 调用 _load_state() 从数据库加载已有数据到内存。
        """
        # 处理数据库路径
        if db_path is None:
            # 默认使用内存数据库
            self.db_path = ":memory:"
        elif db_path != ":memory:":
            # 若为相对路径，相对于项目根目录
            # 确保 data 文件夹存在
            base_dir = os.path.dirname(__file__)
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            # 若 db_path 是相对路径，将其放在 data 文件夹中
            if not os.path.isabs(db_path):
                self.db_path = os.path.join(data_dir, db_path)
            else:
                self.db_path = db_path
        else:
            self.db_path = db_path
        
        # 创建或打开 SQLite 连接，check_same_thread=False 允许多线程访问
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        # 设置行工厂为 sqlite3.Row，使行数据可以通过列名索引（r["title"]）
        self.conn.row_factory = sqlite3.Row
        # 创建表结构（如不存在）
        self._ensure_schema()
        # 初始化内存缓存
        self.books = []
        self.users = {}
        # 从数据库加载状态到内存
        self._load_state()

    def _ensure_schema(self):
        """确保数据库表结构存在，若不存在则创建。
        
        此方法为幂等操作，可以安全地多次调用，不会重复创建已存在的表。
        
        创建三个主要表：
            - books: 存储所有书籍信息。
            - users: 存储所有注册用户。
            - borrowed: 存储用户借阅关系（多对多关系）。
        """
        cur = self.conn.cursor()
        
        # =====================================================================
        # 创建 books 表：存储书籍基本信息和借阅状态
        # =====================================================================
        # 表结构说明：
        #   id: INTEGER PRIMARY KEY - 自增主键，唯一标识每本书
        #   title: TEXT UNIQUE NOT NULL - 书名，唯一约束防止重复添加同名书籍
        #   author: TEXT NOT NULL - 作者名，必须提供
        #   category: TEXT - 分类（可选），允许 NULL
        #   available: INTEGER NOT NULL DEFAULT 1 - 借阅状态（1=可借，0=已借出）
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                title TEXT UNIQUE NOT NULL,
                author TEXT NOT NULL,
                category TEXT,
                available INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        
        # =====================================================================
        # 创建 users 表：存储用户信息
        # =====================================================================
        # 表结构说明：
        #   username: TEXT PRIMARY KEY - 用户名，主键，唯一标识每个用户
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY
            )
            """
        )
        
        # =====================================================================
        # 创建 borrowed 表：跟踪用户的借阅关系
        # =====================================================================
        # 表结构说明：
        #   username: TEXT - 用户名，外键关联 users(username)
        #   book_title: TEXT - 书名，外键关联 books(title)
        #   PRIMARY KEY (username, book_title) - 复合主键确保同一用户同一本书只能借一次
        #   FOREIGN KEY 约束确保参照完整性：
        #     - 若删除用户或书籍，相关借阅记录会级联删除
        #     - 防止添加不存在的用户或书籍到借阅表
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS borrowed (
                username TEXT,
                book_title TEXT,
                PRIMARY KEY (username, book_title),
                FOREIGN KEY(username) REFERENCES users(username),
                FOREIGN KEY(book_title) REFERENCES books(title)
            )
            """
        )
        self.conn.commit()

    def _load_state(self):
        """从 SQLite 数据库加载数据到内存缓存。
        
        此方法在初始化时调用，实现内存缓存与数据库的同步，用于：
        1. 读取数据库中的所有书籍，填充 self.books 列表。
           这样做是为了保持与原系统的兼容性（test fixtures 期望 self.books 是列表）。
        2. 读取所有用户，创建 User 对象，并加载每个用户的借阅历史。
        3. 为后续操作建立内存副本以加快访问速度（避免频繁查询数据库）。
        
        设计考虑：
        - 内存缓存与数据库必须保持同步，所有修改操作都要同时更新两者。
        - 对于大型库可能会占用较多内存，但确保测试速度和兼容性。
        - 可以通过调用此方法重新加载数据（清空当前内存副本）。
        """
        cur = self.conn.cursor()
        
        # =====================================================================
        # 加载所有书籍到 self.books（内存缓存）
        # =====================================================================
        # SELECT 查询获取所有书籍信息（不过滤，包括已借出的书）
        cur.execute("SELECT title, author, category, available FROM books")
        rows = cur.fetchall()
        # 将数据库行转换为字典格式，available 转为布尔值（1->True, 0->False）
        # 这与原系统的数据格式保持一致
        self.books = [
            {
                "title": r["title"],
                "author": r["author"],
                "category": r["category"],
                "available": bool(r["available"])  # 1 转为 True，0 转为 False
            }
            for r in rows
        ]

        # =====================================================================
        # 加载所有用户及其借阅历史到 self.users（内存缓存）
        # =====================================================================
        # SELECT 查询获取所有用户
        cur.execute("SELECT username FROM users")
        rows = cur.fetchall()
        for r in rows:
            # 创建 User 对象
            u = User(r["username"])
            
            # 加载该用户借阅的书籍清单
            # 从 borrowed 表查询该用户的所有借阅记录
            cur.execute("SELECT book_title FROM borrowed WHERE username = ?", (r["username"],))
            br = cur.fetchall()
            # 将借阅记录转为书名列表，存储到 User 对象的 borrowed_books 属性
            u.borrowed_books = [b["book_title"] for b in br]
            
            # 将用户对象存储到 self.users 字典（以 username 为键）
            self.users[r["username"]] = u

    def close(self):
        """关闭数据库连接。
        
        此方法应在程序结束前显式调用，以确保：
        1. 所有待提交的事务被提交到数据库（commit）。
        2. 数据库连接正确释放，避免资源泄漏。
        3. 对文件数据库模式，确保所有改动持久化到磁盘。
        
        注意：
        - 关闭后不能再进行数据库操作，必须创建新的 Library 实例。
        - 此方法有异常处理，若关闭失败不抛出异常，以避免影响程序流程。
        
        典型使用模式：
            try:
                lib = Library("data.db")
                # ... 进行各种操作 ...
            finally:
                lib.close()  # 确保在异常情况下也会被调用
        """
        try:
            # 提交所有待提交的事务
            self.conn.commit()
            # 关闭连接
            self.conn.close()
        except Exception:
            # 静默处理异常，避免在关闭时抛出错误
            pass

    def __del__(self):
        """析构函数：当对象被垃圾回收时自动关闭数据库连接。
        
        此方法提供额外的安全保障，确保即使开发者忘记显式调用 close()，
        数据库连接也会被及时释放。这是一个防御性编程实践。
        
        工作原理：
        - Python 垃圾回收时调用此方法。
        - 调用 close() 方法进行清理。
        - 有异常处理，不会因为关闭失败而抛出异常。
        
        注意：不应该依赖此方法进行关键资源清理，应该显式调用 close()。
        """
        try:
            self.close()
        except Exception:
            pass

    def add_book(self, title: str, author: str, category: Optional[str] = None) -> bool:
        """向图书馆添加新书。
        
        参数：
            title (str): 书名。必须非空且不能仅为空格。
            author (str): 作者名。必须非空且不能仅为空格。
            category (Optional[str]): 书籍分类（可选）。若提供必须非空。
            
        返回值：
            bool: 添加成功返回 True，验证失败或重复返回 False。
            
        验证规则：
            1. 书名和作者名不能为空或纯空格。
            2. 若提供分类，也不能为空或纯空格。
            3. 书名和作者名都不能超过 MAX_LEN (200) 个字符。
            4. 书名在整个图书馆中必须唯一（大小写不敏感的比较）。
               若重复，返回 False（注意：即使大小写不同也视为重复）。
            
        操作流程：
            1. 验证输入参数的合法性。
            2. 检查书名是否已存在（大小写不敏感）。
            3. 若存在则返回 False。
            4. 尝试向 books 表插入新记录。
            5. 若成功，更新内存缓存（self.books 列表）。
            6. 记录操作日志（成功或失败）。
            
        数据库操作详解：
            1. 检查重复：SELECT 1 FROM books WHERE lower(title)=lower(?)
               - 使用 lower() 实现大小写不敏感的重复检查。
               
            2. 插入新书：INSERT INTO books (title, author, category, available) VALUES (?, ?, ?, 1)
               - available 初始值为 1（表示可借阅）。
               - 使用参数化查询（?）防止 SQL 注入。
            
        错误日志：
            - 长度超限：记录 "Add failed: title/author exceed max length"
            - 重复书名：记录 "Add failed: duplicate title"
        """
        # 验证书名和作者不为空或纯空格
        if not title.strip() or not author.strip():
            return False
        # 验证分类（若提供）不为空或纯空格
        if category is not None and not category.strip():
            return False
        # 验证书名和作者长度不超过限制（防止数据库字段溢出）
        if len(title) > self.MAX_LEN or len(author) > self.MAX_LEN:
            logger.error("Add failed: title/author exceed max length (title=%d, author=%d)", len(title), len(author))
            return False

        cur = self.conn.cursor()
        
        # 检查书名是否已存在（大小写不敏感）
        # 这实现了"不区分大小写的 UNIQUE 约束"的行为
        cur.execute("SELECT 1 FROM books WHERE lower(title)=lower(?)", (title,))
        if cur.fetchone():
            logger.error("Add failed: duplicate title '%s'", title)
            return False
        
        try:
            # SQL INSERT 操作：将新书添加到 books 表
            # available 初始值为 1（可借阅状态）
            cur.execute(
                "INSERT INTO books (title, author, category, available) VALUES (?, ?, ?, 1)",
                (title, author, category)
            )
            # 提交事务到数据库
            self.conn.commit()
            # 更新内存缓存（self.books 列表）
            self.books.append({
                "title": title,
                "author": author,
                "category": category,
                "available": True  # 新书初始状态为可借
            })
            # 记录成功操作
            logger.info("Added book '%s' by '%s' in category '%s'", title, author, category)
            return True
        except sqlite3.IntegrityError:
            # 捕获唯一性约束冲突（书名已存在）
            # 这是防御性编程，不应该在执行到这里
            logger.error("Add failed: duplicate title '%s' (db constraint)", title)
            return False

    def remove_book(self, title: str, prompt: bool = False) -> bool:
        """通过书名删除图书。
        
        参数：
            title (str): 要删除的书名。
            prompt (bool): 若为 True，删除前会提示用户确认（交互式）。
                          若为 False（默认），直接删除不询问。
                          
        返回值：
            bool: 删除成功返回 True，书籍未找到或用户取消返回 False。
            
        操作流程：
            1. 若 prompt=True，向用户显示确认提示 [Y/N]。
            2. 验证书籍是否存在（使用不区分大小写的比较）。
            3. 若存在，先删除关联的借阅记录（防止外键约束冲突）。
            4. 然后删除书籍记录。
            5. 更新内存缓存（self.books）。
            6. 记录操作日志。
            
        数据库操作详解：
            1. 检查查询：SELECT 1 FROM books WHERE lower(title)=lower(?)
               - 使用 lower() 函数实现书名的大小写不敏感查询。
               
            2. 删除借阅记录：DELETE FROM borrowed WHERE book_title = ?
               - 必须先删除，因为 borrowed 表有外键约束指向 books 表。
               - 若先删除 books，外键约束会阻止此删除操作。
               
            3. 删除书籍：DELETE FROM books WHERE lower(title)=lower(?)
               - 级联效果：如果禁用外键，可能留下孤立的借阅记录。
               
        用户交互（prompt=True）：
            - 提示格式："Confirm remove 'book_name'? [Y/N]: "
            - 接受输入："y"、"yes"（不区分大小写）
            - 其他输入视为取消操作。
            
        错误处理：
            - 若输入异常（如管道中断），返回 False 并记录日志。
            - 若书籍未找到，返回 False 并记录日志。
        """
        # 若需要交互确认
        if prompt:
            try:
                # 向用户请求确认
                ans = input(f"Confirm remove '{title}'? [Y/N]: ")
            except Exception:
                # 输入异常时（如管道中断）
                logger.error("Remove aborted: confirmation input failed for '%s'", title)
                return False
            # 检查用户回复（只接受 'y' 或 'yes'，不区分大小写）
            if not ans or ans.strip().lower() not in ("y", "yes"):
                # 用户取消
                logger.info("Remove cancelled by user for '%s'", title)
                return False

        cur = self.conn.cursor()
        
        # 检查书籍是否存在（使用大小写不敏感查询）
        # 使用 SELECT 1 只返回 1 个字段，性能更高
        cur.execute("SELECT 1 FROM books WHERE lower(title)=lower(?)", (title,))
        if not cur.fetchone():
            # 书籍不存在
            logger.error("Remove failed: '%s' not found", title)
            return False
        
        # 先删除借阅记录（清理外键关联）
        # 这是必要的，因为 borrowed 表有外键约束指向 books(title)
        cur.execute("DELETE FROM borrowed WHERE book_title = ?", (title,))
        
        # 删除书籍记录
        cur.execute("DELETE FROM books WHERE lower(title)=lower(?)", (title,))
        
        # 提交事务
        self.conn.commit()
        
        # 更新内存缓存：移除匹配的书籍（大小写不敏感）
        self.books = [b for b in self.books if b["title"].lower() != title.lower()]
        
        # 记录成功操作
        logger.info("Removed book '%s'", title)
        return True

    def search_book(self, title: str, author: Optional[str] = None, category: Optional[str] = None) -> list:
        """通过书名、作者、分类搜索图书（支持模糊匹配）。
        
        参数：
            title (str): 搜索的书名。必须提供，将进行模糊匹配。
            author (Optional[str]): 可选的作者名过滤条件（模糊匹配，不区分大小写）。
            category (Optional[str]): 可选的分类过滤条件（模糊匹配，不区分大小写）。
            
        返回值：
            list: 匹配的书籍列表（字典形式），若无匹配返回空列表。
            
        搜索规则：
            - 书名必须包含 title 参数（模糊匹配，不区分大小写）。
            - 若指定 author，则书籍的作者必须包含该字符串。
            - 若指定 category，则书籍的分类必须包含该字符串。
            - 所有条件用 AND 连接（必须全部满足）。
            
        数据库操作详解：
            SQL 模板：SELECT ... WHERE lower(title) LIKE ? AND lower(author) LIKE ? AND lower(category) LIKE ?
            - LIKE 操作符用于模糊匹配，%title% 表示在任意位置包含该字符串。
            - lower() 函数将所有文本转为小写，实现大小写不敏感比较。
            - 使用参数化查询（?）防止 SQL 注入。
            - 动态 SQL 构建：根据指定的参数动态添加过滤条件。
            
        输出：
            - 显示匹配结果："已搜索 'title' by author in category"
            - 若无匹配：显示 "No books found matching the search criteria."
            
        日志：
            - 记录搜索条件和结果数量。
        """
        # 构建基础 SQL 查询（必须提供书名）
        sql = "SELECT title, author, category, available FROM books WHERE lower(title) LIKE ?"
        # LIKE 模式：%title% 表示在任意位置包含该字符串
        params = [f"%{title.lower()}%"]
        
        # 若指定了作者，添加作者过滤条件
        if author:
            sql += " AND lower(author) LIKE ?"
            params.append(f"%{author.lower()}%")
        
        # 若指定了分类，添加分类过滤条件
        if category:
            sql += " AND lower(category) LIKE ?"
            params.append(f"%{category.lower()}%")
        
        # 执行动态构建的 SQL 查询
        cur = self.conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        # 将查询结果转换为字典列表，与 self.books 格式保持一致
        found = [
            {
                "title": r["title"],
                "author": r["author"],
                "category": r["category"],
                "available": bool(r["available"])
            }
            for r in rows
        ]
        
        # 记录搜索操作
        logger.info("Search performed: title='%s' author='%s' category='%s' -> %d results", title, author, category, len(found))
        
        # 显示搜索结果
        if found:
            # 显示每本找到的书籍
            for book in found:
                print(f"已搜索 '{book['title']}' by {book['author']} in {book['category']}")
        else:
            # 未找到匹配的书籍
            print("No books found matching the search criteria.")
        
        return found

    def borrow_book(self, username: str, title: str) -> str:
        """用户借阅书籍。
        
        参数：
            username (str): 用户名。
            title (str): 要借阅的书名（大小写不敏感）。
            
        返回值：
            str: 操作结果消息。
                 成功：'Successfully borrowed \'title\' by author.'
                 失败：'Error: ...' 开头的错误消息。
            
        操作规则：
            1. 用户必须已注册（存在于 users 表和 self.users）。
            2. 书籍必须存在且可用（available=1）。
            3. 若借阅成功：
               - 书籍状态标记为已借出（available=0）。
               - 在 borrowed 表添加借阅关系记录。
               - 更新用户的 borrowed_books 列表。
            
        数据库操作详解：
            1. 检查用户是否存在：从内存缓存 self.users 查询。
               
            2. 查找书籍：SELECT title, author, available FROM books WHERE lower(title)=lower(?)
               - 检查书籍是否存在且可用（available=1）。
               
            3. 标记为已借出：UPDATE books SET available=0 WHERE lower(title)=lower(?)
               - 将 available 从 1 改为 0。
               
            4. 记录借阅关系：INSERT OR IGNORE INTO borrowed (username, book_title) VALUES (?, ?)
               - OR IGNORE：若重复借阅会忽略（由于复合主键 (username, book_title)）。
               
        内存缓存同步：
            1. 更新 self.books 中对应书籍的 available 为 False。
            2. 添加书名到 user.borrowed_books 列表。
            
        错误处理：
            - 若用户不存在：返回 "Error: User 'name' not found."
            - 若书籍不存在或已借出：返回 "Error: 'title' not found or already borrowed."
        """
        # 检查用户是否存在
        user = self.users.get(username)
        if not user:
            logger.error("Borrow failed: user '%s' not found (title='%s')", username, title)
            return f"Error: User '{username}' not found."
        
        cur = self.conn.cursor()
        
        # 查找可用的书籍（大小写不敏感查询）
        cur.execute(
            "SELECT title, author, available FROM books WHERE lower(title)=lower(?)",
            (title,)
        )
        row = cur.fetchone()
        
        # 检查书籍存在且可用
        if row and row["available"]:
            # 标记书籍为已借出（available=0）
            cur.execute(
                "UPDATE books SET available=0 WHERE lower(title)=lower(?)",
                (title,)
            )
            # 记录借阅关系到 borrowed 表
            # INSERT OR IGNORE：若复合主键 (username, book_title) 已存在则忽略
            cur.execute(
                "INSERT OR IGNORE INTO borrowed (username, book_title) VALUES (?, ?)",
                (username, row["title"])
            )
            # 提交事务
            self.conn.commit()
            
            # 更新内存缓存：修改 self.books 中对应书籍的 available 状态
            for b in self.books:
                if b["title"].lower() == title.lower():
                    b["available"] = False
                    break
            
            # 更新用户的借阅历史：添加书名到 borrowed_books 列表
            user.borrowed_books.append(row["title"])
            
            # 记录成功操作
            logger.info("User '%s' borrowed '%s'", username, row["title"])
            return f"Successfully borrowed '{title}' by {row['author']}."
        
        # 书籍不存在或已借出
        logger.error("Borrow failed: '%s' not found or already borrowed (user='%s')", title, username)
        return f"Error: '{title}' not found or already borrowed."

    def return_book(self, username: str, title: str) -> str:
        """用户归还借阅的书籍。
        
        参数：
            username (str): 用户名。
            title (str): 要归还的书名（大小写不敏感）。
            
        返回值：
            str: 操作结果消息。
                 成功：'Successfully returned \'title\'.'
                 失败：'Error: ...' 开头的错误消息。
            
        操作规则：
            1. 用户必须已注册。
            2. 书籍必须存在且已借出（available=0）。
            3. 若归还成功：
               - 书籍状态标记为可借阅（available=1）。
               - 删除借阅关系记录。
               - 更新用户的 borrowed_books 列表。
            
        数据库操作详解：
            1. 检查用户是否存在：从内存缓存 self.users 查询。
               
            2. 查找已借出的书籍：SELECT title, available FROM books WHERE lower(title)=lower(?)
               - 检查书籍是否存在且已借出（available=0）。
               
            3. 标记为可借阅：UPDATE books SET available=1 WHERE lower(title)=lower(?)
               - 将 available 从 0 改为 1。
               
            4. 删除借阅关系：DELETE FROM borrowed WHERE username=? AND book_title=?
               - 清理借阅记录。
               
        内存缓存同步：
            1. 更新 self.books 中对应书籍的 available 为 True。
            2. 从 user.borrowed_books 列表移除书名。
            
        错误处理：
            - 若用户不存在：返回 "Error: User 'name' not found."
            - 若书籍不存在或未被借出：返回 "Error: 'title' not found or not borrowed."
        """
        # 检查用户是否存在
        user = self.users.get(username)
        if not user:
            logger.error("Return failed: user '%s' not found (title='%s')", username, title)
            return f"Error: User '{username}' not found."
        
        cur = self.conn.cursor()
        
        # 查找已借出的书籍（大小写不敏感查询）
        cur.execute(
            "SELECT title, available FROM books WHERE lower(title)=lower(?)",
            (title,)
        )
        row = cur.fetchone()
        
        # 检查书籍存在且已借出
        if row and not row["available"]:
            # 标记书籍为可借阅（available=1）
            cur.execute(
                "UPDATE books SET available=1 WHERE lower(title)=lower(?)",
                (title,)
            )
            # 删除借阅关系
            cur.execute(
                "DELETE FROM borrowed WHERE username=? AND book_title=?",
                (username, row["title"])
            )
            # 提交事务
            self.conn.commit()
            
            # 更新内存缓存：修改 self.books 中对应书籍的 available 状态
            for b in self.books:
                if b["title"].lower() == title.lower():
                    b["available"] = True
                    break
            
            # 更新用户的借阅历史：移除书名从 borrowed_books 列表
            if row["title"] in user.borrowed_books:
                user.borrowed_books.remove(row["title"])
            
            # 记录成功操作
            logger.info("User '%s' returned '%s'", username, title)
            return f"Successfully returned '{title}'."
        
        # 书籍不存在或未被借出
        logger.error("Return failed: '%s' not found or not borrowed (user='%s')", title, username)
        return f"Error: '{title}' not found or not borrowed."

    def get_available_books(self) -> list:
        """获取所有可借阅的图书列表。
        
        返回值：
            list: 所有状态为"可借阅"（available=1）的书籍列表（字典形式），
                  若无可借阅书籍返回空列表。
            
        数据库操作详解：
            SQL: SELECT title, author, category, available FROM books WHERE available=1
            - WHERE available=1：只查询可借阅的书籍。
            - 不包括已借出的书籍（available=0）。
            
        返回格式：
            [
                {"title": "书名", "author": "作者", "category": "分类", "available": True},
                ...
            ]
        """
        cur = self.conn.cursor()
        # 查询所有可借阅的书籍
        cur.execute(
            "SELECT title, author, category, available FROM books WHERE available=1"
        )
        rows = cur.fetchall()
        # 将查询结果转换为字典列表
        return [
            {
                "title": r["title"],
                "author": r["author"],
                "category": r["category"],
                "available": True
            }
            for r in rows
        ]

    def filter_by_category(self, category: str):
        """按分类筛选书籍。
        
        参数：
            category (str): 书籍分类（模糊匹配，大小写不敏感）。
            
        返回值：
            list: 匹配分类的书籍列表（字典形式），若无匹配返回空列表。
            
        搜索规则：
            - 分类信息使用完全相等比较（大小写不敏感）。
            - 返回所有状态的书籍（可借阅和已借出）。
            
        数据库操作详解：
            SQL: SELECT ... FROM books WHERE lower(category)=lower(?)
            - lower() 函数将分类转为小写，实现大小写不敏感比较。
            - 使用参数化查询（?）防止 SQL 注入。
            - 注意：这是完全相等比较，不是模糊匹配（与 search_book 不同）。
            
        返回格式：
            [
                {"title": "书名", "author": "作者", "category": "分类", "available": True/False},
                ...
            ]
        """
        cur = self.conn.cursor()
        # 查询指定分类的所有书籍（包括已借出的）
        cur.execute(
            "SELECT title, author, category, available FROM books WHERE lower(category)=lower(?)",
            (category,)
        )
        rows = cur.fetchall()
        # 将查询结果转换为字典列表，与 self.books 格式保持一致
        filtered_books = [
            {
                "title": r["title"],
                "author": r["author"],
                "category": r["category"],
                "available": bool(r["available"])
            }
            for r in rows
        ]
        # 记录过滤操作
        logger.info("Filter by category: '%s' -> %d results", category, len(filtered_books))
        return filtered_books

    def add_user(self, username: str):
        """添加新用户。
        
        参数：
            username (str): 用户名。
            
        返回值：
            bool: 添加成功返回 True，用户已存在返回 False。
            
        操作流程：
            1. 检查用户是否已在内存缓存中（self.users）。
            2. 若新用户，向 users 表插入新记录。
            3. 创建 User 对象并存储到内存（self.users）。
            4. 记录操作日志。
            
        数据库操作详解：
            SQL: INSERT INTO users (username) VALUES (?)
            - username 为主键（PRIMARY KEY）。
            - 若 username 已存在会抛出 sqlite3.IntegrityError（主键约束）。
            - 使用参数化查询（?）防止 SQL 注入。
            
        内存缓存同步：
            1. 创建 User 对象（username 作为用户名，borrowed_books 初始为空列表）。
            2. 存储到 self.users[username]。
            
        错误处理：
            - 若数据库中已存在（外部添加），也会返回 False 并记录日志。
        """
        # 检查用户是否已在内存缓存中
        if username in self.users:
            logger.error("Add user failed: user '%s' already exists", username)
            return False
        
        cur = self.conn.cursor()
        try:
            # SQL INSERT 操作：将新用户添加到 users 表
            cur.execute("INSERT INTO users (username) VALUES (?)", (username,))
            # 提交事务
            self.conn.commit()
            # 创建 User 对象并存储到内存缓存
            u = User(username)
            self.users[username] = u
            # 记录成功操作
            logger.info("Added user '%s'", username)
            return True
        except sqlite3.IntegrityError:
            # 捕获主键约束冲突（用户名已存在）
            logger.error("Add user failed: user '%s' already exists (db)", username)
            return False

    def view_user_history(self, username: str) -> list:
        """查看用户的借阅历史。
        
        参数：
            username (str): 用户名。
            
        返回值：
            list: 用户借阅的书名列表；若用户不存在返回空列表。
            
        操作流程：
            1. 检查用户是否存在（从内存缓存）。
            2. 若存在，显示用户信息和借阅历史。
            3. 记录查询操作日志。
            
        输出格式：
            成功："借书的人: username, 借阅历史: [书名1, 书名2, ...]"
            失败："Error: User 'username' not found."
            
        注意：
            - 借阅历史来自内存缓存 self.users[username].borrowed_books。
            - 此方法为查询操作，不涉及数据库修改。
            - 若用户存在但借阅历史为空，返回空列表并显示空的借阅历史。
        """
        # 从内存缓存查询用户
        user = self.users.get(username)
        if user:
            # 用户存在，显示借阅历史
            logger.info("View history: user='%s' entries=%d", username, len(user.borrowed_books))
            print(f"借书的人: {username}, 借阅历史: {user.borrowed_books}")
            return user.borrowed_books
        else:
            # 用户不存在
            logger.error("View history failed: user '%s' not found", username)
            print(f"Error: User '{username}' not found.")
            return []


class User:
    """用户类：代表图书馆系统中的一个用户。
    
    此类维护用户的借阅信息，与数据库中的 users 表相对应。
    
    属性：
        username (str): 用户名，作为主键唯一标识用户。
        borrowed_books (list): 用户当前借阅的书籍名称列表。
        
    设计理由：
        - 保留此类以维护与原系统的兼容性。
        - 借阅信息同时存储在 borrowed 表（数据库）和内存缓存中。
        - borrowed_books 列表由 Library 类维护，确保与数据库同步。
    """
    
    def __init__(self, username: str):
        """初始化用户对象。
        
        参数：
            username (str): 用户名。
            
        初始化时 borrowed_books 为空列表，通过 borrow() 和 return_book() 方法修改。
        """
        self.username = username
        # 记录用户借阅的书籍（存储书名列表）
        # 此列表与数据库 borrowed 表保持同步
        self.borrowed_books = []

    def borrow(self, book):
        """将书籍添加到用户的借阅列表。
        
        参数：
            book: 书籍对象或书名（通常为字典或字符串）。
            
        注意：
        - 此方法仅更新内存，不涉及数据库操作。
        - 正常情况下应通过 Library.borrow_book() 调用，而非直接调用此方法。
        - 此方法保留以维护与原系统的兼容性。
        """
        self.borrowed_books.append(book)

    def return_book(self, book):
        """从用户的借阅列表中移除书籍。
        
        参数：
            book: 要移除的书籍对象或书名。
            
        操作：若书籍在列表中则移除，否则不做任何操作。
        
        注意：
        - 此方法仅更新内存，不涉及数据库操作。
        - 正常情况下应通过 Library.return_book() 调用，而非直接调用此方法。
        - 此方法保留以维护与原系统的兼容性。
        """
        if book in self.borrowed_books:
            # 从借阅列表中移除该书籍
            self.borrowed_books.remove(book)
        
