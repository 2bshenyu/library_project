"""
单元测试：单独测试各个方法。
每个测试专注于一个方法，使用最小的设置（例如，空图书馆或单本书）。
演示：使用简单的夹具进行隔离；边缘情况，如重复项或不存在的项目。
运行方式: pytest test_unit.py -v
可视化：成功时为绿色，失败时为红色；显示确切的断言失败。
"""

import pytest

from library import Library
import logging


@pytest.fixture
def empty_lib():
    """一个空的图书馆实例，用于隔离测试。"""
    return Library()


@pytest.fixture
def lib_with_one_book():
    """一个包含一本书的图书馆实例（用于测试的最小状态）。"""
    lib = Library()
    lib.add_book("Python Basics", "Alice Author","编程")
    return lib


def test_add_book_success(empty_lib):
    """单元测试：成功添加新书。"""
    assert empty_lib.add_book("Test Book", "Test Author","文学")
    assert len(empty_lib.books) == 1
    assert empty_lib.books[0]["title"] == "Test Book"
    assert empty_lib.books[0]["available"] is True


def test_add_book_duplicate(empty_lib):
    """单元测试：无法添加重复书籍。"""
    empty_lib.add_book("Duplicate", "Author","文学")
    assert not empty_lib.add_book("Duplicate", "Another","文学")
    assert len(empty_lib.books) == 1  # No second book added


def test_remove_book_success(lib_with_one_book):
    """单元测试：成功删除存在的书籍。"""
    assert lib_with_one_book.remove_book("Python Basics")
    assert len(lib_with_one_book.books) == 0


def test_remove_book_not_found(empty_lib):
    """单元测试：无法删除不存在的书籍。"""
    assert not empty_lib.remove_book("Non Existent")


def test_search_book_found(lib_with_one_book):
    """单元测试：搜索部分匹配。"""
    results = lib_with_one_book.search_book("Python")
    assert len(results) == 1
    assert results[0]["title"] == "Python Basics"


def test_search_book_not_found(empty_lib):
    """单元测试：搜索返回空列表。"""
    results = empty_lib.search_book("Nothing")
    assert len(results) == 0


def test_borrow_book_success(lib_with_one_book):
    """单元测试：借阅可用书籍。"""
    lib_with_one_book.add_user("user1")
    msg = lib_with_one_book.borrow_book("user1", "Python Basics")
    assert "Successfully borrowed" in msg
    assert not lib_with_one_book.books[0]["available"]


def test_borrow_book_not_available(lib_with_one_book):
    """单元测试：无法借阅不可用书籍。"""
    lib_with_one_book.add_user("user1")
    lib_with_one_book.borrow_book("user1", "Python Basics")  # Borrow first
    msg = lib_with_one_book.borrow_book("user1", "Python Basics")
    assert "Error" in msg


def test_return_book_success(lib_with_one_book):
    """单元测试：成功归还借阅的书籍。"""
    lib_with_one_book.add_user("user1")
    lib_with_one_book.borrow_book("user1", "Python Basics")  # Borrow first
    msg = lib_with_one_book.return_book("user1", "Python Basics")
    assert "Successfully returned" in msg
    assert lib_with_one_book.books[0]["available"]


def test_return_book_not_borrowed(empty_lib):
    """单元测试：无法归还未借阅的书籍。"""
    empty_lib.add_user("user1")
    msg = empty_lib.return_book("user1", "Some Book")
    assert "Error" in msg


def test_get_available_books_empty(empty_lib):
    """Unit test: No available books in empty lib."""
    assert len(empty_lib.get_available_books()) == 0


def test_get_available_books_one(empty_lib):
    """Unit test: One available book."""
    empty_lib.add_book("Available", "Author","文学")
    assert len(empty_lib.get_available_books()) == 1


def test_add_book_logs_info(empty_lib, caplog):
    """添加书籍成功时应记录 INFO 级别日志。"""
    caplog.set_level(logging.INFO)
    assert empty_lib.add_book("Log Book", "Logger", "测试")
    # 检查是否存在 INFO 记录，且包含关键字
    found = any(record.levelno == logging.INFO and "Added book" in record.getMessage() for record in caplog.records)
    assert found, f"Expected INFO log with 'Added book', got: {[r.getMessage() for r in caplog.records]}"


def test_remove_book_not_found_logs_error(empty_lib, caplog):
    """删除不存在的书籍时应记录 ERROR 级别日志。"""
    caplog.set_level(logging.ERROR)
    assert not empty_lib.remove_book("Non Existent Book")
    found_err = any(record.levelno == logging.ERROR and "Remove failed" in record.getMessage() for record in caplog.records)
    assert found_err, f"Expected ERROR log with 'Remove failed', got: {[r.getMessage() for r in caplog.records]}"

def test_filter_by_category_success(empty_lib):
    """测试按分类过滤书籍"""
    empty_lib.add_book("Book A", "Author A", "文学")
    empty_lib.add_book("Book B", "Author B", "科技")
    empty_lib.add_book("Book C", "Author C", "文学")

    # 使用 '文学' 分类过滤书籍
    filtered = empty_lib.filter_by_category("文学")
    
    # 断言过滤后的书籍数量是2
    assert len(filtered) == 2
    
    # 提取书名列表
    titles = [book["title"] for book in filtered]
    
    # 断言过滤后的书籍中包含 'Book A' 和 'Book C'
    assert "Book A" in titles
    assert "Book C" in titles

def test_filter_by_category_not_found(empty_lib):
    """测试按分类过滤时无匹配项"""
    empty_lib.add_book("Book A", "Author A", "文学")
    
    # 尝试用 '科技' 分类过滤，应该没有匹配项
    filtered = empty_lib.filter_by_category("科技")
    
    # 断言过滤后的书籍数量为0
    assert len(filtered) == 0


def test_borrow_book_updates_user_history(lib_with_one_book):
    """单元测试：借阅图书时更新用户借阅历史。"""
    # 添加用户
    lib_with_one_book.add_user("alice")
    
    # 借阅书籍
    msg = lib_with_one_book.borrow_book("alice", "Python Basics")
    assert "Successfully borrowed" in msg
    
    # 检查用户的借阅历史
    user = lib_with_one_book.users["alice"]
    assert len(user.borrowed_books) == 1
    assert "Python Basics" in user.borrowed_books


def test_borrow_book_unknown_user(lib_with_one_book):
    """单元测试：借阅图书时如果用户不存在则失败。"""
    # 尝试用不存在的用户借阅
    msg = lib_with_one_book.borrow_book("nonexistent_user", "Python Basics")
    assert "Error" in msg
    assert "User" in msg or "not found" in msg
