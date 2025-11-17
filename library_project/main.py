"""
图书馆管理系统的控制台界面。
这是系统的入口点，用于端到端测试。
支持的命令: add (添加)、remove (删除)、search (搜索)、borrow (借阅)、return (归还)、list (列表)、quit (退出)。
"""

import sys
import os
from library import Library
import shlex


def main():
    lib = Library()
    print("欢迎来到简易图书馆系统！")
    print("命令列表：")
    print("  add <书名> <作者> [分类]     - 添加图书")
    print("  remove <书名>               - 删除图书")
    print("  search <书名> [作者] [分类] - 搜索图书")
    print("  borrow <书名>               - 借阅（当前用户）")
    print("  return <书名>               - 归还（当前用户）")
    print("  list [分类]                 - 列出可用图书（可选分类）")
    print("  add_user <用户名>           - 注册新用户")
    print("  login <用户名>              - 切换用户")
    print("  users                       - 列出已注册用户")
    print("  history                     - 查看当前用户借阅历史")
    print("  quit                        - 退出系统")
    print("  logs [n|all]                - 查看最近 n 行日志或全部日志（默认 200 行）")
    
    # 创建默认用户用于借阅和归还操作，并维护当前登录用户
    lib.add_user("default_user")
    current_user = "default_user"

    # 翻译辅助：仅在交互式终端 (tty) 中把库返回的英文消息翻译为中文显示
    def maybe_translate(msg: str) -> str:
        try:
            is_tty = sys.stdout.isatty()
        except Exception:
            is_tty = False
        if not is_tty:
            return msg

        # 简单的关键词映射，保留未知信息原样
        if "Successfully borrowed" in msg:
            # 示例: "Successfully borrowed 'Book' by Author."
            return msg.replace("Successfully borrowed", "成功借阅")
        if "Successfully returned" in msg:
            return msg.replace("Successfully returned", "成功归还")
        if "Error: User" in msg:
            return msg.replace("Error: User", "错误: 用户")
        if "Error: '" in msg and ("not found or already borrowed" in msg or "not found or not borrowed" in msg):
            return msg.replace("Error:", "错误:")
        if msg.startswith("Added '"):
            # 保留原文但也显示中文提示
            return msg
        return msg

    while True:
        try:
            cmd_input = input("> ").strip()
            if not cmd_input:
                continue
            
            # 安全地分割命令，处理可能的编码问题
            try:
                cmd = cmd_input.split()
            except Exception as e:
                print(f"错误: 无法处理输入 ({e})")
                continue
                
            if not cmd:
                continue

            action = cmd[0].lower()
            if action == "quit":
                print("再见!")
                break
            elif action == "add_user" and len(cmd) >= 2:
                uname = " ".join(cmd[1:])
                if lib.add_user(uname):
                    print(maybe_translate(f"User '{uname}' added."))
                else:
                    print(maybe_translate(f"Error: User '{uname}' already exists."))
                continue

            elif action == "login" and len(cmd) >= 2:
                uname = " ".join(cmd[1:])
                if uname in lib.users:
                    current_user = uname
                    print(f"当前用户: {current_user}")
                else:
                    print(f"错误: 用户 '{uname}' 未找到。")
                continue

            elif action == "users":
                if lib.users:
                    print("已注册用户:")
                    for u in lib.users:
                        print(f"- {u}")
                else:
                    print("当前没有已注册用户。")
                continue

            elif action == "history":
                if current_user and current_user in lib.users:
                    user = lib.users[current_user]
                    print(f"{current_user} 的借阅历史:")
                    if user.borrowed_books:
                        for b in user.borrowed_books:
                            print(f"- {b}")
                    else:
                        print("(空)")
                else:
                    print("未登录用户。使用 login <username> 登录或 add_user <username> 创建用户。")
                continue
            elif action == "add":
                # 支持：add title author [category]
                command_line = " ".join(cmd[1:])
                try:
                    parsed_args = shlex.split(command_line)
                except ValueError as e:
                    print(f"错误: 解析命令失败: {e}")
                    continue

                if len(parsed_args) < 2:
                    print("错误: 无效的命令格式。")
                    print("使用方式: add <书名> <作者> [分类]")
                    continue

                title = parsed_args[0]
                author = parsed_args[1]
                category = parsed_args[2] if len(parsed_args) >= 3 else None

                if lib.add_book(title, author, category):
                    if category:
                        print(maybe_translate(f"Added '{title}' by {author} in {category}."))
                    else:
                        print(maybe_translate(f"Added '{title}' by {author}."))
                else:
                    print(f"Error: '{title}' already exists.")

            elif action == "remove" and len(cmd) >= 2:
                title = " ".join(cmd[1:])
                # 调用 remove_book 时启用交互确认
                if lib.remove_book(title, prompt=True):
                    print(f"Removed '{title}'.")
                else:
                    print(f"Error: '{title}' not found or removal cancelled.")

            elif action == "search" and len(cmd) >= 2:
                # 支持：search title [author] [category]
                command_line = " ".join(cmd[1:])
                try:
                    parsed_args = shlex.split(command_line)  # 解析命令行
                except ValueError as e:
                    print(f"错误: 解析命令失败: {e}")
                    continue
                
                title = parsed_args[0]
                author = parsed_args[1] if len(parsed_args) >= 2 else None
                category = parsed_args[2] if len(parsed_args) >= 3 else None

                results = lib.search_book(title, author, category)
                if results:
                    for book in results:
                        status = "Available" if book["available"] else "Borrowed"
                        print(f"- '{book['title']}' by {book['author']} ({status})")
                else:
                    print("No books found.")

            elif action == "borrow" and len(cmd) >= 2:
                title = " ".join(cmd[1:])
                # 使用当前登录用户进行借阅
                msg = lib.borrow_book(current_user, title)
                print(maybe_translate(msg))

            elif action == "return" and len(cmd) >= 2:
                title = " ".join(cmd[1:])
                msg = lib.return_book(current_user, title)
                print(maybe_translate(msg))

            elif action == "list":
                # 如果用户输入了分类，获取分类（支持多字符输入）
                if len(cmd) > 1:
                    category = " ".join(cmd[1:]).strip()  # 获取分类（可能是多字符）
                else:
                    category = None  # 如果没有指定分类，列出所有书籍
                
                # 如果指定了分类，使用 filter_by_category 进行筛选
                if category:
                    filtered_books = lib.filter_by_category(category)
                    if filtered_books:
                        for book in filtered_books:
                            print(f"- '{book['title']}' by {book['author']} in {book['category']}")
                    else:
                        print(f"No available books in the '{category}' category.")
                else:
                    # 如果没有指定分类，列出所有可用书籍
                    available_books = lib.get_available_books()
                    if available_books:
                        for book in available_books:
                            if book.get("category"):
                                print(f"- '{book['title']}' by {book['author']} in {book['category']}")
                            else:
                                print(f"- '{book['title']}' by {book['author']}")
                    else:
                        print("No available books.")
            elif action == "logs":
                # 显示日志文件内容：logs [n] (显示最近 n 行)，n 可为 'all' 显示全部；默认 200 行
                # 日志文件位于本模块同级目录的 logs/library.log
                try:
                    base_dir = os.path.dirname(__file__)
                    log_path = os.path.join(base_dir, "logs", "library.log")
                    if not os.path.exists(log_path):
                        print("日志文件不存在。若尚未产生日志，请先执行一些操作。")
                        continue

                    # 解析参数
                    n = 200
                    if len(cmd) >= 2:
                        if cmd[1].lower() == "all":
                            n = None
                        else:
                            try:
                                n = int(cmd[1])
                            except ValueError:
                                print("参数错误：请输入数字行数或 'all'。示例：logs 100 或 logs all")
                                continue

                    # 读取并显示内容
                    with open(log_path, "r", encoding="utf-8") as f:
                        if n is None:
                            content = f.read()
                            print(content)
                        else:
                            # tail last n lines
                            lines = f.readlines()
                            for line in lines[-n:]:
                                print(line.rstrip())
                except Exception as e:
                    print(f"无法读取日志文件: {e}")
                continue
            else:
                print("Invalid command. Type 'quit' to exit.")
        
        except UnicodeDecodeError as e:
            # 处理Unicode解码错误
            print(f"错误: 字符编码问题 - {e}")
            print("提示: 请确保输入为UTF-8编码的文本")
            continue
        except KeyboardInterrupt:
            # 处理 Ctrl+C
            print("\n再见!")
            break
        except Exception as e:
            # 捕获其他异常
            print(f"错误: 发生未知错误 - {e}")
            continue



if __name__ == "__main__":
    # 仅在直接运行脚本时，尝试设置控制台的编码为 UTF-8（避免在被 pytest/import 时修改全局 IO）
    try:
        import sys
        import io
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        # 忽略在某些环境下无法重新包装标准流的错误
        pass
    main()
