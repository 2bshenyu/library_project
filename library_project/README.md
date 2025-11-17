# 简单图书馆管理系统: 一个用于演示软件测试级别的 python 项目

## 项目意义
本项目是一个极简的 Python 图书馆管理系统, 它通过一个直观、可视化的示例, 帮助理解和区分软件测试的三个关键级别: 
- **单元测试(Unit Testing)**: 针对单个方法进行隔离测试, 验证基本功能正确性。
- **构件测试(Component Testing)**: 测试构件内部方法间的交互, 确保数据流和逻辑连贯。
- **系统测试(System Testing)**: 端到端测试整个集成系统, 包括用户界面交互, 模拟真实使用场景。

## 项目内容
项目模拟一个小型图书馆, 支持书籍添加、移除、搜索、借阅和归还。核心逻辑封装在 `Library` 类中, 使用字典列表存储书籍(每个书籍包含标题、作者和可用状态)。

### 文件结构
```
library_project/
├── library.py          # 核心 Library 类: 书籍管理方法(add_book, remove_book 等)
├── main.py             # 系统入口: 控制台 UI, 支持命令行交互(add, borrow 等)
├── test_unit.py        # 单元测试: 隔离测试单个方法, 使用 fixtures 简化设置
├── test_component.py   # 构件测试: 测试方法间交互(如 add -> search -> borrow)
├── test_system.py      # 系统测试: 模拟用户输入, 端到端验证 UI 输出
├── test_edge_cases.py  # 边界测试: 测试特殊输入和边界情况的处理
├── requirements.txt    # 依赖: pip install -r requirements.txt
└── README.md           # 本文档: 项目说明和任务指南
```

### 核心功能示例
- **添加书籍**: `lib.add_book("Python 基础", "爱丽丝")` → 返回 True(成功)或 False(重复标题)。
- **搜索书籍**: `lib.search_book("Python")` → 返回匹配列表(部分匹配, 不区分大小写)。
- **借阅/归还**: 更新可用状态, 返回成功/错误消息。
- **控制台 UI**(main.py): 输入如 `add Python 基础 爱丽丝` 或 `borrow Python 基础`, 实时反馈。


### 输入格式说明
为保持项目简单, `main.py` 的命令解析基于空格分割(`split()`), 因此有特定限制: 
- **作者名称**: 必须是**单个单词**(无空格)。例如, `add Python 基础 Alice`(作者 "Alice")。如果作者名含空格(如 "John Doe"), 解析会出错: 部分姓名会误入标题(标题变为 "Python 基础 John", 作者仅 "Doe")。
- **标题**: 支持**多个单词(含空格)**, 但需注意作者是最后一个单词。例如: 
  - 正确: `add Test Book Author` → 标题="Test Book", 作者="Author"。
  - 错误(多单词作者名): `add Test Book John Doe` → 标题="Test Book John", 作者="Doe"(数据错误)。
- **其他命令**(remove、search、borrow、return): 标题/查询支持多单词, 直接用空格连接, 如 `borrow Test Book`。
- **列表命令**: `list`(无参数), 显示可用书籍。
- **退出**: `quit`。

## 测试方法
使用 pytest 框架(自动发现 `test_` 开头的函数, 无需手动执行)。

### 环境设置
1. 安装依赖: `pip install -r requirements.txt`。
2. 运行完整系统: `python main.py`(交互模式, 输入命令测试 UI)。注意输入格式！

### 运行测试
- **单元测试**(test_unit.py): `pytest test_unit.py -v`
  示例输出(可视化): 绿色 PASS 表示单个方法正确; 失败显示具体断言错误。
  
- **构件测试**(test_component.py): `pytest test_component.py -v`
  示例: 测试“添加 → 搜索 → 借阅”链路。

- **系统测试**(test_system.py): `pytest test_system.py -v`
  示例: 模拟输入序列(如添加 → 借阅 → 列表), 捕获打印输出验证。

- **全部测试**: `pytest -v --tb=short`

### 测试可视化与调试
- **选项**: 
  - `-v`: 详细输出(函数名 + PASSED/FAILED)。
  - `--tb=short`: 简洁错误追踪。
  - `pytest-cov`(可选扩展): `pip install pytest-cov`, 运行 `pytest --cov=library` 查看覆盖率报告。

### 测试文件说明
项目包含四个测试文件, 每个关注不同的测试层面: 

1. **test_unit.py**: 单元测试
   - 专注于单个方法的基本功能测试
   - 使用简单的测试夹具(fixtures)
   - 验证基本功能的正确性

2. **test_component.py**: 构件测试
   - 测试多个方法之间的交互
   - 验证数据流的正确性
   - 测试典型的使用场景

3. **test_system.py**: 系统测试
   - 模拟用户界面交互
   - 测试完整的命令处理流程
   - 验证系统的端到端行为

4. **test_edge_cases.py**: 边界测试
   - 测试空输入和空格处理
   - 验证特殊字符的处理
   - 测试长输入和边界条件
   - 验证大小写敏感性
   - 测试完整的操作序列
   - 验证搜索功能的各种情况


- **常见问题**: 
  - 输入解析: main.py 使用 `split()` 处理空格标题; 多个单词的图书标题无需引号(如 `add Test Book Author`), 但作者限单个单词。
  - 失败调试: 检查输出中的实际打印(如标题引号不匹配)。


## 课后任务: 

### 基础任务
1. 输入验证增强 (容易)
   - 为书名和作者名添加长度限制(如最大 200 字符)
   - 实现对多单词作者名称的支持(提示: 使用 shlex 进行命令解析)

2. 功能扩展 (中等)
   - 为图书馆系统新增书籍分类功能，使每本书在添加时可指定分类，并能在列表和搜索中显示与筛选分类
   - 添加用户系统, 记录每个用户的借阅历史

3. 系统健壮性 (中等)
   - 添加日志记录系统, 记录所有操作和错误
   - 实现命令确认机制(如删除前确认)

4. 数据持久化 (偏难)
   - 使用 SQLite 数据库存储图书信息
   - 实现数据导入导出功能(支持 CSV/JSON 格式)

5. 性能优化 (偏难)
   - 优化大量图书数据的处理效率(提示: 如使用二分查找替代线性搜索等)
   - 添加批量操作功能(提示: 如支持 CSV 文件批量导入图书)

6. 代码重构 (困难)
   - 将 Library 类按功能拆分为多个类(如 BookManager, LoanManager)
   - 实现命令模式处理用户输入 (https://www.runoob.com/design-pattern/command-pattern.html)

### 挑战任务
7. 高级功能实现
   - 添加图书推荐系统(基于用户借阅历史)
   - 实现图书预约功能
   - 添加图书评分和评论功能
   - 实现模糊搜索(使用 Levenshtein 距离算法)

8. 用户体验优化
   - 实现命令行自动补全功能
   - 添加交互式菜单界面
   - 实现命令历史记录和回溯
   - 添加统计报表功能(如借阅趋势分析)

### 完成要求: 
1. 在 `test_edge_cases.py` 中，以添加注释的形式标注出每个函数分别属于单元测试还是构件测试
2. 从“基础任务”中选择并实现至少一个改进功能;
3. 为改进功能编写对应的测试用例;
4. 提交以下内容: 
   - 修改后的源代码（如 library.py / main.py）
   - 新增或修改的测试文件（test_*.py）
   - `pytest -v --tb=short` 运行截图（通过结果）
   - README 中更新的功能说明（简述实现与测试）
5. 所有功能修改须保持原系统的其他功能正常运行。

### 建议的实现步骤: 
1. 先完成基础任务中的一项
2. 编写相应的测试用例
3. 运行所有测试确保未破坏现有功能
4. 更新文档说明新功能的使用方法


### 已经实现的功能（截至 2025-11-17）

- **核心书籍管理**: 实现 `Library` 的基本方法，包括 `add_book`, `remove_book`, `search_book`, `get_available_books` 和 `filter_by_category`，用于添加、移除、搜索和列出书籍。
- **书籍分类支持**: 每本书包含 `category` 字段，`list`/`search` 输出会显示分类，支持按分类筛选。
- **多词标题/作者与命令解析改进**: `main.py` 使用 `shlex.split` 来解析命令行输入，支持通过引号传递包含空格的标题或作者（例如: `add "The Test Book" "John Doe" 科技`）。
- **用户系统**: 实现用户注册/登录功能（`add_user` / `login`），在 `Library.users` 中记录用户，并为每位用户维护借阅历史（`history` 命令可以查看）。
- **按用户借阅/归还**: `borrow_book(username, title)` 与 `return_book(username, title)` 接口，借阅/归还会更新图书可用状态并写入该用户借阅记录。
- **TTY 友好中文提示**: 提供 `maybe_translate` 机制，仅在交互终端（TTY）下将部分英文提示翻译为中文，保证自动化测试仍然接收英文原文，不被本地化破坏。
- **安全的 I/O 处理**: 将对 `sys.stdout`/`sys.stderr` 的重绑定限制在 `if __name__ == "__main__"` 下，避免影响 pytest 的捕获行为，修复了导入时因 I/O 重绑定导致的测试异常。
- **测试覆盖与新增用例**: 增加并更新了若干测试用例，覆盖用户借阅历史、多用户并发借阅以及系统交互流程（新增系统测试覆盖删除确认等场景）。在当前工作区上已运行全部测试，结果为: **44 passed**。

- **日志记录系统**: 使用 Python `logging` 在 `library_project/logs/library.log` 写入操作与错误日志（默认 INFO 级别）。记录项包括添加/删除/搜索/借阅/归还/用户管理及查看历史等操作，日志包含时间戳与级别，便于审计。

- **CLI 日志查看命令**: 在 `main.py` 中新增 `logs [n|all]` 命令，用于查看 `logs/library.log`：
   - `logs` 显示最近 200 行（默认）；
   - `logs 100` 显示最近 100 行；
   - `logs all` 显示全部日志内容。

- **删除确认机制**: 删除操作现在支持交互确认：`remove <title>` 在 CLI 中会触发确认提示 `Confirm remove '<title>'? [Y/N]: `，仅当用户输入 `Y`/`yes`（不区分大小写）时才实际删除。库层的 `remove_book(title, prompt=False)` 保持可选的非交互调用，方便脚本/测试使用。

### 当前命令（CLI）

在交互式 `python main.py` 中支持以下命令（含新增的 `logs` 与删除确认说明）：

- `add <title> <author> [category]` : 添加一本书。支持用引号包含含空格的 `title` 或 `author`，`category` 可选。
- `remove <title>` : 交互式删除（会要求确认）。
- `search <query>` : 按标题/作者模糊搜索。
- `borrow <title>` : 当前已登录用户借阅指定书籍。
- `return <title>` : 当前已登录用户归还指定书籍。
- `list [category]` : 列出所有可借图书（含分类信息），可选按分类筛选。
- `add_user <username>` : 注册新用户。
- `login <username>` : 切换/登录为指定用户（后续 borrow/return 使用该用户）。
- `users` : 列出已注册用户。
- `history` : 查看当前登录用户的借阅历史。
- `logs [n|all]` : 查看日志文件（默认最近 200 行，或 `all` 显示全部）。
- `quit` : 退出程序。

### 当前命令（CLI）

在交互式 `python main.py` 中支持以下命令：

- `add <title> <author> [category]` : 添加一本书。支持用引号包含含空格的 `title` 或 `author`，`category` 可选。
- `remove <title>` : 移除一本书（按标题匹配）。
- `search <query>` : 按标题/作者模糊搜索。
- `borrow <title>` : 当前已登录用户借阅指定书籍。
- `return <title>` : 当前已登录用户归还指定书籍。
- `list` : 列出所有可借图书（含分类信息）。
- `add_user <username>` : 注册新用户。
- `login <username>` : 切换/登录为指定用户（后续 borrow/return 使用该用户）。
- `users` : 列出已注册用户。
- `history <username?>` : 查看某用户的借阅历史；若不带参数则查看当前登录用户历史。
- `quit` : 退出程序。

示例：

```bash
python main.py
> add "深入理解计算机系统" "John Doe" 计算机
> add_user alice
> login alice
> borrow "深入理解计算机系统"
> history
> list
> return "深入理解计算机系统"
> quit
```

### 运行与测试

- 运行交互式程序: `python main.py`
- 运行全部测试: `pytest -v --tb=short`

当前测试状态（本地）：`44 passed`。

