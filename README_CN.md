# 用现代语法写 C

**更多知识在构建期，更少工作在运行时**

**中文** | [English](./README.md)

**正文：** [中文版章节](./cn/) · [English chapters](./en/)

这本书面向已经有一定工程经验的 C 程序员。

它不试图把 C 变成另一门语言，也不把宏、IDL、Graph 或 Lean 当成目的。

全书真正关心的是：

> **当同一个稳定知识开始被多个 C 模块、metadata、HTTP/RPC、Plugin、Mock 或 optimizer 重复维护时，怎样把它提升成有限、显式、可检查的 IR，并在构建阶段尽量消费掉，最终仍然执行普通 C。**

## 三种 IR

全书现在围绕三个不同问题展开：

~~~text
DataBind Contract IR
    程序对外承诺什么

CMeta Native Semantic IR
    C 实现实际上是什么

CFlow Execution IR
    被接受的计算怎样组合、证明和优化
~~~

它们不是三套 runtime。

典型路径是：

~~~text
DataBind Service
        +
CMeta FunctionDesc
        ↓
BindingPlan / exact adapter
        ↓
HTTP / RPC / Plugin / WASM
        ↓
optional CFlow execution
        ↓
ordinary C
~~~

一个核心例子会贯穿后半本：

~~~text
service UserService {
    GetUser: GetUserRequest -> GetUserResponse;
}
~~~

对应普通 C 实现：

~~~c
int get_user(
    UserRepository *repo,
    uint64_t id,
    User *out_user);
~~~

书中会具体展示它怎样被检查、绑定并生成 HTTP、RPC、Plugin、WASM、OpenAPI 和 Mock，而不是分别维护六份 API 描述。

## 四段因果链

### Part I — Native Semantic IR

从真实 C 重复开始：

~~~c
DECLARE_VEC(IntVec, int);
DECLARE_LIST(IntList, int);
~~~

逐步进入：

~~~text
Generic
Struct / Enum
Traits
semantic type identity
FunctionDesc
Callable
~~~

重点是区分：

~~~text
cmeta_function_desc
    = 描述函数是什么

cmeta_callable
    = 一种可执行表示
~~~

Part I 不靠 Lean 才成立。

### Part II — Execution IR

从普通循环：

~~~c
for (...) {
    if (!is_even(x))
        continue;
    total += square(x);
}
~~~

进入：

~~~text
Source<int>
    ↓
Filter(is_even)
    ↓
Map(square)
    ↓
Reduce(sum)
~~~

重点不是链式语法，而是让整个 computation 成为可检查的 program object。

这里才真正需要：

~~~text
observable semantics
Lean law
verified rewrite
normalize / optimize
Plan
Direct / AOT
~~~

最终必须再次展示 lowering 后的普通 C hot path。

### Part III — Contract IR 与 Compiler

这一部分从“同一个 API 为什么被描述很多次”开始。

Plain C：

~~~c
int get_user(UserRepository *, uint64_t, User *);
~~~

然后工程里又出现：

~~~text
HTTP route
RPC method
Plugin export
OpenAPI schema
Mock signature
WASM ABI
~~~

DataBind IDL 把 logical contract 收成一次：

~~~text
message / enum / union
service
channel
component
~~~

再与 CMeta native semantics 编译连接：

~~~text
Contract IR
    +
FunctionDesc
    ↓
BindingPlan
    ↓
projection backends
~~~

HTTP / RPC / PLUGIN / WASM / OPENAPI / MOCK 都是 projection，而不是新的 IDL 语言。

### Part IV — Live Runtime 与工程资格

这里讨论真正活着的 runtime：

~~~text
Reactive / async I/O
Executor / Scheduler
State Machine
Actor
Plugin loader / lease / quiescent unload
CHttp::Server
ABI / Multi-TU / installed consumer
~~~

每个 runtime 都必须说明它消费的是哪一种 IR，以及哪些 metadata 已经在进入 hot path 前被消掉。

## 写法：少讲形容词，多给可检查对象

本书后续重写默认遵守：

~~~text
Plain C baseline
    ↓
具体重复或歧义
    ↓
最小 semantic object
    ↓
C representation
    ↓
compiler/runtime pseudocode
    ↓
flow
    ↓
logic / invariant
    ↓
Lean only if needed
    ↓
lowered ordinary C
    ↓
failure case
    ↓
evidence
~~~

如果一个 abstraction 只能用“更优雅、更灵活、更现代”解释，而不能给出代码、IR、判断规则、失败条件或证据，它还没有写清楚。

## 形式证明的位置

Lean 只用于真正的 semantic obligation，例如：

~~~text
graph rewrite preservation
normalization
state determinism
lifecycle invariant
protocol refinement
~~~

轻量 contract/binding 规则先直接写成逻辑判断：

~~~text
Γ ⊢ field : T
Γ ⊢ param : U
convertible(T, U)
────────────────────
Γ ⊢ bind(field, param) : valid
~~~

ABI、DSO、sanitizer 和性能分别用 compile/link、integration、sanitizer、benchmark 验证，不让一种证据代替另一种。

## 章节写作约束

详细结构见：

- [BOOK_ARCHITECTURE.md](./BOOK_ARCHITECTURE.md)
- [CHAPTER_TEMPLATE.md](./CHAPTER_TEMPLATE.md)
- [SOURCE_SNAPSHOTS.md](./SOURCE_SNAPSHOTS.md)

当前章节文件仍保持 ch-01.md 到 ch-15.md；先修正内容因果关系，再单独处理 publication order / renumbering。

## 出版构建

各章 Markdown 是唯一可编辑正文；出版顺序由 [BOOK_MANIFEST.txt](./BOOK_MANIFEST.txt) 定义。

~~~bash
python3 scripts/validate_book.py
python3 scripts/build_book.py
~~~

Release workflow 从同一份 canonical Markdown 生成 HTML、EPUB3 与 PDF。

## License

本项目采用 [Apache License 2.0](./LICENSE)。
