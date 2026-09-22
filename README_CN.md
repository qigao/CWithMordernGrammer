# 用现代语法写 C

**有限 CMeta，复杂能力，最终仍然是 C**

**中文** | [English](./README.md)

**正文：** [中文版章节](./cn/) · [English chapters](./en/)

这本书面向已经有一定工程经验的 C 程序员。

它不从“如何设计一门更强的语言”开始，也不把宏、Generic 或 Lean 当成目的。全书真正关心的是：

> **怎样用很小、有限、可解释的 CMeta 设计，解决 C 里反复出现的重复定义、重复契约和难以组合的高级程序结构。**

书里的基本方法是：

~~~text
先写真实 C
    ↓
看到重复事实 / 重复契约
    ↓
用有限 CMeta 收成一个定义
    ↓
得到更简单的 typed C API
    ↓
当计算关系变复杂时，引入 Graph / CFlow
    ↓
当 rewrite / optimization / state semantics 需要可信边界时，再引入 Lean
    ↓
最终仍然落回普通 C implementation、toolchain、tests 和 measurements
~~~

“宏最后生成 C”只是基本操作，不是本书的中心。

真正重要的是：

- 一个简单设计为什么可以替代大量重复 C；
- Generic 怎样把不同宏 family 收成统一契约；
- CMeta 怎样让类型、traits、callable、identity 成为高级设计的共同基础；
- Graph 怎样让类似 LINQ 的计算在 C 中第一次成为可分析、可优化的程序数据；
- Lean 怎样证明 graph rewrite、normalization、state transition 等关键语义；
- Plan / Direct lowering 怎样把控制面的复杂度提前，把执行时的 graph lookup 变成预解析的 index / handler / 普通 C 调用；
- 在这个基础上，Reactive、异步 I/O、Executor、State Machine、Actor、CSTL、测试框架、Serialization、RPC 等高级应用为什么会明显变得容易。

## 目标读者

读者默认已经熟悉：

- C struct / enum / pointer / function pointer；
- 宏与预处理器；
- 基本容器与内存管理；
- callback、线程、I/O；
- CMake / library / ABI 的基本工程概念。

本书不是 C 入门书。

目标是让已经会写 C 的读者看到：

> **C 并不是只能停留在“手写 switch + callback + void *”的层次。**

如果有限的类型知识、计算结构和语义契约被正确建模，C 同样可以承载现代、高级而且可工程化的软件设计。

## 三部分

### Part I — 用有限 CMeta 消除重复定义与重复契约

从最普通的 C 重复开始。

重点不是 Lean，而是 C 本身：

- 宏为什么会从“减少代码重复”演化成“宏 family 自己也重复”；
- Generic 怎样把 List / Vec / Option / Pair / Result 等声明收成统一 typed(...) protocol；
- Struct / Traits 怎样让 field/capability 事实只维护一次；
- finite type universe / type identity / callable 怎样形成共享契约；
- 生成层只负责 typed surface / metadata，真实算法继续是 ordinary compiled C。

核心章节目前对应 Chapter 1–3。ABI / Multi-TU 的工程收口在后面统一讨论。

### Part II — 用 CMeta / CFlow 构造、证明和优化 LINQ-like Graph

这里是全书技术核心。

从：

~~~c
for (...) {
    if (!is_even(x))
        continue;
    total += square(x);
}
~~~

逐步进入：

~~~text
Source<int>
    ↓
Filter(is_even)
    ↓
Map(square)
    ↓
Reduce(sum)
~~~

重点不是“模仿 Java/C# 语法”，而是 C/C++ 本身缺少这样一种能力：

> **把完整计算关系变成一个 typed、可检查、可转换、可证明、可编译的 program object。**

本 Part 依次回答：

- Callable 怎样成为 Graph node；
- Stream 怎样成为 LINQ-like surface；
- Graph 怎样拥有 observable semantics；
- Lean 怎样证明 rewrite / normalize preservation；
- optimizer 怎样安全做 fusion / elimination；
- Plan 怎样把 graph topology 预解析成 index / handler；
- Direct/AOT 怎样在满足条件时把 Graph 从 hot path 中完全删除；
- hand-written C / Graph / Plan / Direct 怎样做真实对比。

Part II 现在按 Chapter 4–7 连续展开：Graph → Stream → 可信语义 → Optimize / Plan / Direct。

### Part III — 在 CMeta / CFlow 上构造高级应用

前两部分得到的是少量 primitive：

~~~text
Type / Traits / Generic
Callable
Graph / Plan
Executor / Scheduler
Typed Event
Semantic Identity
Lean-backed laws
~~~

第三部分不再发明新的“语言”。

它展示这些 primitive 怎样组合成传统 C 中很难写得清楚的高级系统：

- Reactive / WAIT / Wake / Demand；
- 异步文件与网络 I/O；
- Executor / Scheduler；
- State Machine / Statechart；
- Actor；
- CSTL typed containers；
- test / mock / deterministic test infrastructure；
- Serialization / Data Binding；
- HTTP / RPC；
- Plugin / Workflow / Event Bus 等工程模式；
- ABI / Multi-TU / installed consumer qualification。

这里的重点始终是：

> **复杂能力增加，但 core primitive 不按相同比例增加。**

## 章节写法：代码先于解释

后续章节默认按这个顺序推进：

~~~text
1. 先给出真实 Plain C
2. 用代码暴露重复 / ownership / state / composition 问题
3. 给出最小 CMeta/CFlow 设计
4. 给出设计后的 C API / generated shape / lowering
5. 明确它让什么高级任务变得简单
6. 只有出现真正 semantic question 时才引入 Lean
7. 最后用 tests / ABI / sanitizer / benchmark 说明工程边界
~~~

优先使用完整的小 C 示例，而不是用大段 prose 解释“可能有什么问题”。

具体实现与定理引用仍固定到 [SOURCE_SNAPSHOTS.md](./SOURCE_SNAPSHOTS.md) 的 edition snapshots。详细重构约束见 [BOOK_ARCHITECTURE.md](./BOOK_ARCHITECTURE.md) 与 [CHAPTER_TEMPLATE.md](./CHAPTER_TEMPLATE.md)。

## 出版构建

各章 Markdown 仍然是唯一可编辑正文；出版顺序由 [BOOK_MANIFEST.txt](./BOOK_MANIFEST.txt) 统一定义。

本地可以只用 Python 标准库完成整书 QA，并生成确定性的单文件 Markdown 书稿：

```bash
python3 scripts/validate_book.py
python3 scripts/build_book.py
```

生成结果位于 `dist/C-with-Modern-Grammar.md`，不会提交到仓库。GitHub Actions 的 `Publication` workflow 会在 Pull Request 与 `master` 上执行同样的校验/构建，并把合并后的书稿上传为 workflow artifact。

HTML / EPUB / PDF 渲染与普通书稿 QA 保持分离。`Release Formats` workflow 可手动触发，也会在 `v*` tag 上运行；它只消费上述 canonical Markdown，先把 Mermaid 统一渲染为 SVG，再从同一份已验证输入生成 standalone HTML、EPUB3 与 PDF。渲染器版本在 workflow 中固定；发布产物同时包含 `SOURCE_SNAPSHOTS.md`、渲染器版本记录和 SHA-256 校验和。tag 运行会把同一组文件发布到 GitHub Release。

PDF / EPUB 排版刻意保持为下一层能力，这样日常写作和 review 不需要安装 Pandoc、LaTeX、Node 或 Lean。

## 仓库历史

这套书稿最初位于 `qigao/salts` 仓库中，之后独立迁移为当前书稿仓库。

- 原仓库：`qigao/salts`
- 原分支：`master`
- 迁移源快照：`a90053416f1af748f8a356baf2e3f957be6105a4`
- 本仓库初始迁移提交：`5133429d2c7cc24f5b9b633b1fd1d1a059b40987`
- 初始书稿：15 个 Markdown 章节

首次迁移时，15 个章节内容保持了与原始文件完全一致的 Git blob。

## License

本项目采用 [Apache License 2.0](./LICENSE)。
