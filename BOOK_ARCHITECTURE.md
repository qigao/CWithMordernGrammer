# Book Architecture — 有限 CMeta 如何让 C 获得高级设计能力

本文件定义下一阶段的全书重构方向。

这本书不是 CMeta API reference，也不是 Lean 教材，更不是“如何用宏模拟 C++”。

它要回答的是：

> **当普通 C 因为重复定义、重复契约、计算结构不可见而越来越难维护时，怎样用很小、有限、可解释的 Meta 设计，把复杂问题重新变成简单 C；又怎样在这个基础上构造 C 原本很难表达的高级计算与应用模型。**

目标读者是已经有一定工程经验的 C 程序员。

## 1. 全书唯一主线

全书默认沿着一条因果链推进：

~~~text
真实 C 问题
    ↓
embedded C baseline
    ↓
发现重复 fact / contract / state relation
    ↓
最小有限设计
    ↓
CMeta / CFlow surface
    ↓
更高级的能力变得容易
    ↓
如果出现 semantic rewrite / optimization / state law
    才引入 Lean
    ↓
ordinary C implementation / lowering
    ↓
toolchain / tests / ABI / measurement
~~~

有三条编辑纪律。

第一，**Code first**。

不要先写：

~~~text
“C 缺少反射”
“我们需要 Graph”
“Lean 可以证明……”
~~~

先给一段真实 C，让读者看到为什么原来的写法在规模扩大以后开始痛苦。

第二，**Lean after semantics**。

没有明确 observable semantics 时，不引入 theorem。

Generic、Struct、Traits、typed container 这类问题首先是 C 的重复契约问题，与 Lean 无关。

Lean 真正有价值的地方是：

~~~text
rewrite
normalization
optimizer legality
state transition
refinement
certificate
~~~

第三，**show the ordinary C endpoint**。

每一个高级 abstraction 都要回答：

~~~text
最终是什么 C type？
调用哪个 C function？
ownership 在哪里？
hot path 还查不查 Graph？
是否可以预解析成 index / handler？
是否可以完全 lower 掉？
~~~

---

# Part I — 用有限 CMeta 消除重复定义与重复契约

Part I 不需要 Lean 来成立。

它只回答：

> **C 工程中为什么同一个事实会被写很多次，以及有限 Generic/Meta 怎样把它收成一次定义。**

## Chapter 1 — 从重复代码到重复知识

从最普通的 C 宏开始。

主要使用 embedded C 展示：

~~~c
typedef struct IntVec { ... } IntVec;
typedef struct DoubleVec { ... } DoubleVec;
~~~

以及：

~~~c
#define DECLARE_VEC(Name, T) ...
~~~

让读者看到问题如何从：

~~~text
code duplication
~~~

升级成：

~~~text
macro-family duplication
contract duplication
~~~

结论不是“宏不好”。

结论是：

> **宏应该生成稳定事实，但不能让每个模块创造自己的小语言。**

## Chapter 2 — Generic：统一有限类型契约

Chapter 2 是 Part I 的核心。

必须围绕真实 C before/after 展开：

~~~c
DECLARE_LIST(IntList, int);
DECLARE_VEC(IntVec, int);
DECLARE_OPTION(MaybeInt, int);
~~~

变成：

~~~c
typed(List, IntList, int);
typed(Vec, IntVec, int);
typed(Option, MaybeInt, int);
~~~

然后继续解决：

~~~text
struct fields repeated in metadata
trait flags repeated with function slots
compile-time relation repeated with runtime relation
descriptor address confused with semantic identity
~~~

关键 CMeta vocabulary：

~~~text
Struct
Enum
Traits
typed
CMETA_TYPEOF
TypeFunction
ValueFunction
Predicate
semantic type identity
~~~

本章不出现“因为 finite，所以需要 Lean”的叙事。

Finite 的工程价值首先是：

~~~text
bounded vocabulary
fail-fast unsupported cases
stable generated surface
predictable ABI
no hidden fallback
~~~

## Chapter 3 — Callable：把行为契约也收成一次定义

普通 callback 的问题要通过代码展示：

~~~c
void (*fn)(void *);
void *ctx;
enum signature;
unsigned effects;
unsigned properties;
~~~

同一个行为 fact 再次散落。

然后引入：

~~~text
signature
capture
dispatch authority
effects
properties
typed callable
~~~

这里仍然主要是 CMeta engineering。

这一章的结束点是：

> **数据和行为都已经成为 typed value；下一步可以保存它们之间的计算关系。**

---

# Part II — 用 CMeta / CFlow 构造、证明和优化 LINQ-like Graph

这是全书最重要的技术 Part。

它回答：

> **C 已经可以写任何 for-loop，为什么还需要 Graph？**

答案不是语法糖。

答案是：

> **普通 C/C++ 的 for-loop 执行完就消失了；Graph 把整个计算关系保存成一个 typed program object，因此它可以被检查、推导、证明、重写、优化和编译。**

## Canonical example

Part II 只使用少量持续演化的 C example。

Plain C：

~~~c
long sum_even_squares(const int *xs, size_t n)
{
    long total = 0;

    for (size_t i = 0; i < n; ++i) {
        int x = xs[i];

        if ((x & 1) != 0)
            continue;

        total += (long)x * x;
    }

    return total;
}
~~~

逐步变成：

~~~text
Source<int>
    ↓
Filter(is_even)
    ↓
Map(square)
    ↓
Reduce(sum)
~~~

每个阶段都必须同时展示：

~~~text
surface C
internal Graph
semantic contract
lowered/compiled C shape
~~~

## Graph — computation becomes data

Graph 章节重点不再是解释“Node/Edge 是什么”。

应该用 C 对比说明：

~~~text
hand-written loop
    看不到完整 program structure

typed Graph
    可以 inspect / validate / normalize / rewrite / compile
~~~

Graph 必须至少拥有：

~~~text
typed node
typed edge
operator semantics
callable
snapshot/version
observable semantics
~~~

## Stream / LINQ-like surface

Stream 是 Graph 的 surface，不是另一套 runtime。

读者应该能看到类似：

~~~c
/* illustrative surface */
stream_from(int, input, n)
    .filter(is_even)
    .map(square)
    .reduce(sum);
~~~

如何形成 canonical Graph。

重点不是语法像 LINQ。

重点是：

> **C 第一次拥有“高级查询/数据流语法 + 完整可分析 IR”这一组合。**

## Lean 在这里第一次成为核心工具

当 optimizer 想做：

~~~text
Map(f)
Map(f)
    ↓
Map(f)
~~~

metadata 中的 IDEMPOTENT 只是一条 claim。

真正允许 rewrite 的是：

~~~text
f(f(x)) = f(x)
~~~

Lean 应该出现在这里，而不是 Chapter 2。

Part II 至少完整展示：

~~~text
Graph pattern
+
metadata admission
+
semantic law
+
Lean preservation theorem
+
concrete C rewrite
~~~

## Optimization / lowering

这是 Part II 的第二个核心。

Graph 不能成为每个 value 都查询的 runtime object。

需要展示：

~~~text
Surface Graph
    ↓
Normalize
    ↓
Optimize
    ↓
Compile Plan
    ↓
pre-resolved step index / handler / callable
    ↓
execute values
~~~

读者必须看到“前后 C 代码”的差异。

解释器式 hot path：

~~~c
node = graph_node(graph, node_id);

switch (node->op) {
case CFLOW_MAP:
    ...
}
~~~

Plan path 的目标：

~~~c
for (size_t i = 0; i < plan->step_count; ++i) {
    const cflow_step *step = &plan->steps[i];
    step->handler(step, frame);
}
~~~

再进一步，Direct/AOT eligibility 满足时：

~~~c
for (...) {
    if (!is_even(x))
        continue;

    total += square(x);
}
~~~

Graph 可以完全退出 hot path。

这就是：

> **Rich Control Plane, Simple Execution Plane。**

## Part II 需要的 evidence

至少比较：

~~~text
hand-written C
Graph/interpreted path
compiled Plan
Direct/AOT path
~~~

并给：

~~~text
compiler
flags
platform
workload
measurement limitations
~~~

不要把 Lean theorem 当 benchmark。

---

# Part III — 在 CMeta / CFlow 上构造高级应用

Part III 的主题不是继续增加语言 feature。

它回答：

> **当 Type、Generic、Callable、Graph、Plan、Executor、Semantic Law 已经存在以后，原本在 C 中非常难写清楚的系统可以怎样组合出来？**

每一个 application 都必须从 C example 开始。

## Reactive / async I/O

从一个普通 blocking/readiness loop 开始：

~~~c
ssize_t n = read(fd, buffer, sizeof(buffer));

if (n < 0 && errno == EAGAIN) {
    ...
}
~~~

逐步展示：

~~~text
WAIT
arm
wake
demand
subscription
terminal
cancel
~~~

然后连接真实 async file/network driver。

目标是让读者看到：

> **Reactive 不是 framework magic，而是 Graph execution 多了时间和 demand。**

## Executor / Scheduler

用任务队列 C code 展示：

~~~c
if (queue_full(exec))
    return FULL;
~~~

再说明：

~~~text
Executor = how
Scheduler = when
Graph/Machine = what
~~~

高级层不应该自己重新发明线程系统。

## State Machine

State Machine 必须用一个完整 C case 贯穿：

~~~text
DISCONNECTED
CONNECTING
CONNECTED
CLOSING
~~~

Plain C baseline：

~~~c
switch (state) {
case CONNECTING:
    if (event == CONNECT_OK) {
        ...
    }
    break;
}
~~~

再变成 typed transition data。

重点是：

~~~text
Event Admission
Transition Selection
Guard
Action
Commit
Observation
~~~

Lean 在这里证明：

~~~text
determinism
terminal law
state typing
small-step properties
~~~

而不是证明线程调度。

## Actor

从：

~~~text
mutex + shared object + many producers
~~~

转成：

~~~text
identity
bounded mailbox
single mutable owner
lifecycle
stale ref
~~~

强调：

> **Actor 不是一条线程。**

## CSTL

把 Part I 的 Generic 放到真正容器工程里：

~~~c
typed(Vec, UserVec, User);
typed(HashMap, UsersById, int, User);
~~~

说明 typed wrapper 与共享 ordinary-C algorithm 怎样配合。

## Test / Mock

展示有限 Meta 怎样减少：

~~~text
test registration
fixture declaration
mock function signatures
expectation boilerplate
~~~

并与 deterministic executor/manual clock 组合。

## Serialization / Data Binding

从：

~~~c
if (strcmp(field, "id") == 0)
    user->id = atoi(value);
~~~

进入：

~~~text
format syntax
→ canonical data events
→ CMeta semantic shape
→ CBind
→ native C value
~~~

不要让 serializer 发明第二套 type system。

## HTTP / RPC / Network

展示：

~~~text
CMeta method facts
CSerde payload
RPC envelope
HTTP
CNet
NativeIO
~~~

每层只拥有自己的 meaning。

重点仍然是组合，而不是“做一个更大的 framework”。

## Engineering closure

ABI / Multi-TU / installed consumer 放在 Part III 作为所有高级应用的共同 qualification。

说明：

~~~text
semantic identity != pointer address
header-generated metadata may differ across TUs
public ABI must be intentional
installed consumer is a real gate
~~~

## Restraint

最终必须保留“什么时候不需要 Meta”这一章。

好的终点可能仍然只是：

~~~c
for (...)
    ...

switch (...)
    ...

fn(arg);
~~~

有限设计的目标不是让所有 C 代码 Meta 化。

目标是：

> **只把稳定、重复、值得共享的知识提升出来，让剩下的程序重新简单。**

---

# Editorial Rule — Embedded C is the primary explanation

每个主要概念至少应该包含一个 before/after pair。

推荐结构：

~~~text
Problem shown in C
    ↓
why the code becomes duplicated/opaque
    ↓
new design shown in C
    ↓
what gets generated/stored
    ↓
what advanced task becomes easy
    ↓
semantic proof only if needed
    ↓
engineering evidence
~~~

禁止只用：

~~~text
概念列表
架构口号
抽象图
~~~

代替真实代码。

Diagram 用来总结代码，不用来替代代码。

---

# Migration map

当前仓库文件仍保留历史 15 章编号，避免本次架构重构同时制造大规模 rename/link noise。

新的三 Part 主题映射暂时是：

~~~text
Part I
    Ch 1
    Ch 2
    Ch 3

Part II core
    Ch 4
    Ch 5
    Ch 10
    Ch 11

Part III
    Ch 6
    Ch 7
    Ch 8
    Ch 9
    Ch 12
    Ch 13
    Ch 14
    Ch 15
~~~

后续单独 PR 再处理 publication order / chapter renumbering。

这样可以先确保内容因果关系正确，再处理文件名和目录机械变化。

---

# Completion definition

重构完成后，一个有经验的 C 程序员应该能回答：

1. 为什么多个宏 family 最终仍然是重复？
2. Generic 为什么是统一契约，而不只是语法糖？
3. 为什么有限 Meta 比 unrestricted template 更适合这里的 C 工程目标？
4. Graph 比 for-loop 多提供了什么真正的新能力？
5. 为什么 LINQ-like surface 有价值的部分是 typed IR，而不是链式语法？
6. Lean 到底证明了什么，为什么 Chapter 2 不需要它而 optimizer/state machine 需要它？
7. 为什么 compiled Plan 可以避免 per-value graph lookup？
8. 什么条件下 Graph 可以被 Direct/AOT 完全 lower 回普通 C？
9. 为什么相同 primitive 可以组合出 Reactive、State Machine、Actor、Serialization、RPC？
10. 怎样把这些设计作为真实 library 安装、链接、测试和测量？

如果读者只能记住 API 名字，而不能回答这些问题，书就还没有完成。
