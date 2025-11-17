"""
构件测试: 测试图书馆构件中方法之间的交互。
运行命令: pytest test_component.py -v
"""

import pytest

from library import Library


@pytest.fixture
def sample_lib():
    """Fixture: Library with multiple books for interaction testing."""
    lib = Library()
    lib.add_book("Python Basics", "Alice","编程")
    lib.add_book("Advanced Java", "Bob","编程")
    lib.add_book("Python Advanced", "Charlie","编程")  # Partial match for search
    return lib


def test_add_then_search(sample_lib):
    """Component test: Add book, then search for it."""
    # 交互流程：添加 -> 搜索
    sample_lib.add_book("New Book", "Dave","神话")
    results = sample_lib.search_book("New")
    assert len(results) == 1
    assert results[0]["title"] == "New Book"


def test_add_borrow_return(sample_lib):
    """组件测试：完整生命周期：添加 -> 借阅 -> 归还。"""
    # 交互流程：添加 -> 借阅 -> 归还
    sample_lib.add_book("Temp Book", "Eve","科技")
    sample_lib.add_user("user1")
    borrow_msg = sample_lib.borrow_book("user1", "Temp Book")
    assert "Successfully borrowed" in borrow_msg
    return_msg = sample_lib.return_book("user1", "Temp Book")
    assert "Successfully returned" in return_msg
    assert sample_lib.get_available_books()[-1]["available"]  # 最后一本书是可用的


def test_remove_then_search(sample_lib):
    """组件测试：删除前后的搜索对比。"""
    # 交互流程：搜索 -> 删除 -> 搜索
    initial_results = sample_lib.search_book("Python")
    assert len(initial_results) == 2  # 包含 "Python Basics" 和 "Python Advanced"
    sample_lib.remove_book("Python Basics")
    final_results = sample_lib.search_book("Python")
    assert len(final_results) == 1  # 只剩下 "Python Advanced"


def test_borrow_unavailable_after_multiple(sample_lib):
    """组件测试：借阅一本后，尝试借阅已不可用的图书。"""
    # 交互流程：借阅 -> 借阅（失败）-> 列出可用图书
    sample_lib.add_user("user1")
    sample_lib.borrow_book("user1", "Python Basics")
    borrow_fail = sample_lib.borrow_book("user1", "Python Basics")
    assert "Error" in borrow_fail
    avail = sample_lib.get_available_books()
    assert len(avail) == 2  # "Advanced Java" 和 "Python Advanced" 仍然可用

def test_list_by_category(sample_lib):
    """组件测试：按分类列出图书。"""
    # 交互流程：按分类筛选
    filtered_books = sample_lib.filter_by_category("编程")
    assert len(filtered_books) == 3  # 所有三本书都在 "编程" 分类下

def test_search_with_author_and_category(sample_lib):
    """组件测试：使用作者和分类进行搜索。"""
    # 交互流程：搜索 -> 使用作者和分类过滤
    results = sample_lib.search_book("Python", author="Alice", category="编程")
    assert len(results) == 1
    assert results[0]["title"] == "Python Basics"

def test_search_with_non_matching_author(sample_lib):
    """组件测试：使用不匹配的作者进行搜索。"""
    # 交互流程：搜索 -> 使用不匹配的作者过滤
    results = sample_lib.search_book("Python", author="NonExistentAuthor")
    assert len(results) == 0


def test_two_users_borrow_same_book(sample_lib):
    """组件测试：两个不同的用户借阅同一本书的情况。
    
    注意：当前系统中每本书只有一个副本，所以只有第一个用户能借阅成功。
    这个测试验证了对这种情况的处理。
    """
    # 添加两个用户
    sample_lib.add_user("alice")
    sample_lib.add_user("bob")
    
    # alice 借阅 "Python Basics"
    msg1 = sample_lib.borrow_book("alice", "Python Basics")
    assert "Successfully borrowed" in msg1
    assert not sample_lib.books[0]["available"]  # 书籍标记为已借出
    
    # alice 的借阅历史中应该包含这本书
    assert "Python Basics" in sample_lib.users["alice"].borrowed_books
    
    # bob 尝试借同一本书 - 应该失败
    msg2 = sample_lib.borrow_book("bob", "Python Basics")
    assert "Error" in msg2
    assert "not found or already borrowed" in msg2
    
    # bob 的借阅历史应该是空的
    assert len(sample_lib.users["bob"].borrowed_books) == 0
    
    # alice 归还书籍
    msg3 = sample_lib.return_book("alice", "Python Basics")
    assert "Successfully returned" in msg3
    assert sample_lib.books[0]["available"]  # 书籍重新标记为可用
    
    # alice 的借阅历史应该被清空
    assert len(sample_lib.users["alice"].borrowed_books) == 0
    
    # 现在 bob 可以借这本书了
    msg4 = sample_lib.borrow_book("bob", "Python Basics")
    assert "Successfully borrowed" in msg4
    assert "Python Basics" in sample_lib.users["bob"].borrowed_books

