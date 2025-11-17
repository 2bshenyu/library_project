"""
边界情况和错误处理的补充测试。
这些测试用例覆盖了一些特殊情况和边界条件。
运行命令: pytest test_edge_cases.py -v
"""

import pytest

from library import Library


@pytest.fixture
def lib():
    """创建一个基础的图书馆实例"""
    return Library()


def test_empty_input(lib):
    """测试空输入的处理"""
    assert not lib.add_book("", "","")  # 空书名和作者名
    assert not lib.add_book("Valid Title", "","")  # 空作者名
    assert not lib.add_book("", "Valid Author","")  # 空书名
    assert not lib.add_book("软件工程","徐浩然","")  # 空类别名


def test_whitespace_input(lib):
    """测试纯空格输入的处理"""
    assert not lib.add_book("   ", "author","   ")  # 纯空格书名
    assert not lib.add_book("title", "   ","    ")  # 纯空格作者名
    assert not lib.add_book("软件工程","徐浩然","   ")  # 纯空格类别名


def test_special_characters(lib):
    """测试特殊字符的处理"""
    # 标点符号
    assert lib.add_book("Book!", "Author","小说")
    assert lib.add_book("Book?", "Author","小说")
    assert lib.search_book("Book!")

    # 特殊字符
    special_title = "Book#$%^&*()"
    assert lib.add_book(special_title, "Author","文学")
    results = lib.search_book("#$%")
    assert len(results) == 1
    assert results[0]["title"] == special_title


def test_long_input(lib):
    """测试长输入的处理"""
    long_title = "A" * 100
    long_author = "B" * 300  # 超过200字符限制
    long_categroy="C"*50
    assert not lib.add_book(long_title, long_author,long_categroy)  # 应该拒绝
    long_author = "B" * 200  # 刚好200字符
    assert lib.add_book(long_title, long_author,long_categroy)  # 应该接受
    results = lib.search_book("A" * 50)
    assert len(results) == 1
    assert results[0]["title"] == long_title



def test_duplicate_with_different_case(lib):
    """测试大小写重复的处理"""
    assert lib.add_book("Python Book", "Author","科技")
    assert not lib.add_book("python book", "Different Author","adasdaDD")  # 应该检测为重复
    results = lib.search_book("python")
    assert len(results) == 1


def test_search_case_sensitivity(lib):
    """测试搜索时的大小写敏感性"""
    lib.add_book("Python Programming", "Author","科技")
    assert len(lib.search_book("python")) == 1
    assert len(lib.search_book("PYTHON")) == 1
    assert len(lib.search_book("Programming")) == 1
    assert len(lib.search_book("programming")) == 1


def test_multiple_operations_sequence(lib):
    """测试多个操作的序列"""
    # 添加书籍
    assert lib.add_book("Test Book", "Author","文学")

    # 尝试重复添加
    assert not lib.add_book("Test Book", "Author","文学")

    # 添加用户
    lib.add_user("user1")

    # 借阅
    assert "Successfully borrowed" in lib.borrow_book("user1", "Test Book")

    # 尝试重复借阅
    assert "Error" in lib.borrow_book("user1", "Test Book")

    # 归还
    assert "Successfully returned" in lib.return_book("user1", "Test Book")

    # 尝试重复归还
    assert "Error" in lib.return_book("user1", "Test Book")

    # 删除
    assert lib.remove_book("Test Book")

    # 尝试重复删除
    assert not lib.remove_book("Test Book")


def test_search_partial_match(lib):
    """测试部分匹配搜索"""
    lib.add_book("Python Programming", "Author","科技")
    lib.add_book("Java Programming", "Author","科技")
    lib.add_book("Python Basics", "Author","科技")

    results = lib.search_book("Python")
    assert len(results) == 2

    results = lib.search_book("Programming")
    assert len(results) == 2

    results = lib.search_book("Basic")
    assert len(results) == 1


def test_available_books_after_operations(lib):
    """测试各种操作后的可用书籍列表"""
    lib.add_book("Book1", "Author1","categroy1")
    lib.add_book("Book2", "Author2","categroy2")
    lib.add_user("user1")

    assert len(lib.get_available_books()) == 2

    lib.borrow_book("user1", "Book1")
    available = lib.get_available_books()
    assert len(available) == 1
    assert available[0]["title"] == "Book2"

    lib.return_book("user1", "Book1")
    assert len(lib.get_available_books()) == 2

    lib.remove_book("Book2")
    available = lib.get_available_books()
    assert len(available) == 1
    assert available[0]["title"] == "Book1"


###已完成的功能

def test_add_book_multi_word_author(lib):
    """测试添加多单词作者名称的书籍"""
    assert lib.add_book("The Great Gatsby", "F. Scott Fitzgerald","文学")
    results = lib.search_book("Gatsby")
    assert len(results) == 1
    assert results[0]["author"] == "F. Scott Fitzgerald"
