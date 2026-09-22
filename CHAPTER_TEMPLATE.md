# Chapter Template

本模板定义下一轮重写的默认约束。

核心原则：

> **Embedded C example first. Prose explains code; prose does not replace code.**

不是每章都必须机械拥有同样标题，但叙事顺序应尽量稳定。

## 1. Show the Plain C problem

先给真实 C。

例如不要先写：

~~~text
“callback ownership 很复杂”
~~~

而是先给：

~~~c
struct request {
    void (*done)(void *);
    void *ctx;
    int state;
    bool cancelled;
};
~~~

让读者直接看到重复、ownership、state 或 composition 问题。

这一节必须回答：

- 当前代码能工作吗？
- 它为什么在小规模时完全合理？
- 当需求增加以后，哪一份 fact 开始重复？
- 哪个 contract 开始由多个地方共同维护？

## 2. Show the duplication / ambiguity in code

最好给一个具体 failure mode：

~~~c
typedef struct User {
    long id;
} User;

static const Field fields[] = {
    {"id", offsetof(User, id), sizeof(int)} /* stale */
};
~~~

或者：

~~~c
if (state == CONNECTING && event == OK) ...
if (state == CONNECTING && event == TIMEOUT) ...
~~~

不要只写“维护困难”。

## 3. Introduce the smallest design

然后才引入 CMeta/CFlow vocabulary。

例如：

~~~c
Struct(User,
    (long, id)
);
~~~

或者：

~~~c
typed(Vec, UserVec, User);
~~~

或者：

~~~text
typed Event
+
transition table
~~~

设计必须说明：

- single source of truth 在哪里；
- ownership 在哪里；
- unsupported case 怎样失败；
- boundedness 在哪里；
- 哪些算法仍然属于 ordinary C。

## 4. Show the after-code

新设计必须落到 C 调用侧：

~~~c
UserVec users = {0};

UserVec_init(&users, 64u);
UserVec_push_back(&users, user);
UserVec_destroy(&users);
~~~

如果有生成层，再给概念性或 exact generated shape。

复杂宏不用逐 token 教学。

只需要回答：

> **最后得到什么 C type/function/data structure？**

## 5. Say what new problem becomes easy

每个 abstraction 必须明确多解决了什么。

例如：

~~~text
Generic
    → 多个 library generic kinds 共享同一个 declaration protocol

Graph
    → 整个 computation 可以被 inspect / rewrite / compile

Plan
    → execution 不再 per-value 查 node/edge

Machine
    → state relation 变成 typed analyzable data

Actor
    → multi-producer admission + single mutable owner
~~~

没有新增能力，就不值得引入 abstraction。

## 6. Semantic Contract — only when semantics matter

当 abstraction 开始：

~~~text
rewrite
optimize
schedule
transition
cancel
commit
~~~

才需要把 observable semantics 单独写清楚。

至少说明：

- 什么结果可观察；
- 什么顺序可观察；
- illegal state 是什么；
- metadata 是 claim 还是 truth；
- fallback 是否允许。

Part I 的 Generic/Struct/Traits 通常不需要先构造复杂 formal model。

## 7. Lean — only after a real proof question appears

Lean 不是每章固定栏目。

只在以下问题出现时进入：

### Rewrite correctness

~~~text
Map(f) ; Map(f)
    ↓
Map(f)
~~~

需要 semantic law。

### Graph normalization

需要 preservation theorem。

### State Machine / Actor

需要 determinism、small-step invariant、lifecycle law。

### Certificate / refinement

需要连接 approved IR 与 execution artifact。

每一个 theorem 都要回答：

> **它授权了 C implementation 做哪一个以前不能安全做的 transformation？**

不要让 Lean 证明：

~~~text
ABI
malloc 一定成功
OS fairness
network liveness
benchmark 更快
~~~

## 8. Show lowering / ordinary-C execution

对于 Graph/CFlow 章节，这是必须项。

至少区分：

~~~text
Graph interpretation
Compiled Plan
Direct/AOT
~~~

最好直接给 C：

~~~c
/* graph-ish */
switch (node->op) { ... }

/* plan */
step->handler(step, frame);

/* direct */
if (is_even(x))
    total += square(x);
~~~

本书的一个核心承诺是：

> **控制面可以复杂，但 hot path 可以重新简单。**

## 9. Evidence

根据主张选择证据。

### C / compiler

- compile-pass；
- compile-fail；
- generated surface；
- Multi-TU；
- installed consumer。

### Runtime

- unit/integration；
- deterministic scheduler；
- bounded failure；
- sanitizer；
- race/stress。

### Formal

- theorem；
- invariant；
- preservation；
- refinement。

### Performance

只有声明 cost/performance 时才给 benchmark。

至少记录：

~~~text
commit
compiler
flags
platform
workload
limitations
~~~

## 10. What We Learned

最后只回答三件事：

1. 哪个原始 C problem 被消掉了？
2. 这个设计让哪个以前困难的任务变简单了？
3. 下一章为什么自然出现？

---

# Canonical examples

## Part I — duplicated contract

持续使用：

~~~c
User
IntVec / UserVec
Option<User>
Pair<int,double>
Traits(User, ...)
~~~

让读者看到同一个 type fact 怎样逐步被复用。

## Part II — LINQ-like computation

持续使用：

~~~c
long sum_even_squares(const int *xs, size_t n);
~~~

以及：

~~~text
Source<int>
    ↓
Filter(is_even)
    ↓
Map(square)
    ↓
Reduce(sum)
~~~

逐步展示：

~~~text
Callable
Graph
Stream
Lean law
Optimizer
Plan
Direct/AOT
benchmark
~~~

## Part III — connection/service example

Stateful/concurrent chapters复用：

~~~text
DISCONNECTED
CONNECTING
CONNECTED
CLOSING
~~~

和：

~~~text
CONNECT
CONNECT_OK
TIMEOUT
CLOSE
~~~

再扩展到：

~~~text
async I/O
Machine
Actor
RPC/service lifecycle
~~~

这样全书的代码会真正形成连续工程，而不是 15 组独立 demo。
