"""
系统测试：对完整集成系统进行端到端测试。
模拟用户与 main.py 的交互（使用 monkeypatch 模拟 input() 调用）。
展示：整个系统行为；验证 UI 输出是否符合预期。
运行命令: pytest test_system.py -v
可视化：捕获打印输出；显示完整的命令流程，类似用户会话。
"""

from io import StringIO
from unittest.mock import patch

from main import main


def test_system_add_and_list(capsys):
    """系统测试：运行 main()，模拟 'add' 和 'list' 命令，检查输出。"""
    # 模拟输入：添加图书、列出图书、退出
    inputs = ['add "Test Book" "Author" "science"', "list", "quit"]

    with patch("sys.stdin", StringIO("\n".join(inputs) + "\n")):
        with patch("builtins.input", side_effect=inputs + [EOFError]):  # Handle quit
            main()

        captured = capsys.readouterr()
        output = captured.out

    assert "Added 'Test Book' by Author in science." in output
    assert "- 'Test Book' by Author in science" in output
    assert "No available books." not in output  # Should list the book


def test_system_borrow_and_return(capsys):
    """系统测试：添加、借阅、归还图书，验证消息。"""
    inputs = ["add Borrowable Writer", "borrow Borrowable", "return Borrowable", "quit"]

    with patch("sys.stdin", StringIO("\n".join(inputs) + "\n")):
        with patch("builtins.input", side_effect=inputs + [EOFError]):
            main()

        captured = capsys.readouterr()
        output = captured.out

    assert "Successfully borrowed 'Borrowable' by Writer." in output
    assert "Successfully returned 'Borrowable'." in output


def test_system_search_invalid(capsys):
    """系统测试：搜索不存在的图书，检查错误输出。"""
    inputs = ["search Nothing", "quit"]

    with patch("sys.stdin", StringIO("\n".join(inputs) + "\n")):
        with patch("builtins.input", side_effect=inputs + [EOFError]):
            main()

        captured = capsys.readouterr()
        output = captured.out

    assert "No books found." in output


def test_system_full_flow(capsys):
    """系统测试：完整流程：添加多本图书、搜索、借阅一本、列出可用图书。"""
    inputs = [
        "add Book1 A1",
        "add Book2 A2",
        "search Book",
        "borrow Book1",
        "list",
        "quit",
    ]

    with patch("sys.stdin", StringIO("\n".join(inputs) + "\n")):
        with patch("builtins.input", side_effect=inputs + [EOFError]):
            main()

        captured = capsys.readouterr()
        output = captured.out

    assert "Added 'Book1' by A1." in output
    assert "Added 'Book2' by A2." in output
    assert (
        "- 'Book1' by A1 (Available)" in output or "- 'Book1' by A1" in output
    )  # 搜索输出
    assert "Successfully borrowed 'Book1' by A1." in output
    assert "- 'Book2' by A2" in output  # 借阅后只有 Book2 可用

###已完成的功能
def test_system_add_multi_word_author(capsys):
    """系统测试：添加多单词作者名称的书籍，检查输出。"""
    inputs = ['add "软件工程" "徐浩然" "编程"', 'add "The Great Gatsby" "F. Scott Fitzgerald" "小说"', 'list', 'quit']

    with patch("sys.stdin", StringIO("\n".join(inputs) + "\n")):
        with patch("builtins.input", side_effect=inputs + [EOFError]):
            main()

        captured = capsys.readouterr()
        output = captured.out

    assert "Added '软件工程' by 徐浩然 in 编程." in output  # 检查 '软件工程' 书籍添加
    assert "Added 'The Great Gatsby' by F. Scott Fitzgerald in 小说." in output  # 检查 'The Great Gatsby' 书籍添加
    assert "- '软件工程' by 徐浩然 in 编程" in output  # 检查 '软件工程' 显示在分类中
    assert "- 'The Great Gatsby' by F. Scott Fitzgerald in 小说" in output  # 检查 'The Great Gatsby' 显示在分类中

    
def test_system_list_books_by_category(capsys):
    """系统测试：按分类列出书籍，检查输出。"""
    inputs = [
        'add "Book A" "Author A" "Fiction"',
        'add "Book B" "Author B" "Science"',
        'add "Book C" "Author C" "Fiction"',
        'list',
        'quit'
    ]

    with patch("sys.stdin", StringIO("\n".join(inputs) + "\n")):
        with patch("builtins.input", side_effect=inputs + [EOFError]):
            main()

        captured = capsys.readouterr()
        output = captured.out

    assert "- 'Book A' by Author A in Fiction" in output
    assert "- 'Book B' by Author B in Science" in output
    assert "- 'Book C' by Author C in Fiction" in output


def test_system_remove_with_confirm(capsys):
    """系统测试：删除时用户确认 Y，断言删除成功并从列表中不存在。"""
    # 命令流：添加 -> remove -> list -> quit
    inputs = [
        'add "DelBook" "AuthorD" "分类"',
        'remove DelBook',
        'list',
        'quit',
    ]

    # builtins.input 的返回序列：每次 main() 调用 input()，以及 remove_book 内的确认 input()
    side_effect = [
        inputs[0],           # add command
        inputs[1],           # remove command
        'Y',                 # confirm inside remove_book
        inputs[2],           # list command
        inputs[3],           # quit
        EOFError,
    ]

    with patch("sys.stdin", StringIO("\n".join(inputs) + "\n")):
        with patch("builtins.input", side_effect=side_effect):
            main()

        captured = capsys.readouterr()
        output = captured.out

    assert "Added 'DelBook' by AuthorD in 分类." in output
    # 删除后，列表中不应该再包含 DelBook
    assert "- 'DelBook' by AuthorD" not in output


def test_system_remove_with_reject(capsys):
    """系统测试：删除时用户拒绝 N，断言书籍仍能被 list 或 search 找到。"""
    inputs = [
        'add "KeepBook" "AuthorK" "分类"',
        'remove KeepBook',
        'list',
        'quit',
    ]

    side_effect = [
        inputs[0],
        inputs[1],
        'N',                 # reject inside remove_book
        inputs[2],
        inputs[3],
        EOFError,
    ]

    with patch("sys.stdin", StringIO("\n".join(inputs) + "\n")):
        with patch("builtins.input", side_effect=side_effect):
            main()

        captured = capsys.readouterr()
        output = captured.out

    assert "Added 'KeepBook' by AuthorK in 分类." in output
    # 用户拒绝删除，书籍仍然应在列表中
    assert "- 'KeepBook' by AuthorK" in output