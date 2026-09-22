# 第十四章：有限、显式、按需——什么时候应该停止 Meta 化


> **本章路线**
>
> 前十三章一直在展示“什么时候抽象有价值”。这一章反过来专门研究“什么时候抽象会失败”。
>
> 我们不再只列原则，而是用具体 counterexample 验证：
>
> ~~~text
> Too-Early Meta
> Infinite Inference
> Pointer Identity
> Hidden Allocation
> Unbounded Queue
> Silent Fallback
> Everything-is-Virtual
> Raw Token as Business Data
> Formal Proof at the Wrong Layer
> Module Ownership Leakage
> ~~~
>
> 每个反例都回答三件事：
>
> **它为什么一开始看起来很合理？真正坏在哪里？最小修正是什么？**
>
> 目标不是让读者害怕抽象，而是建立一个更专业的判断能力：
>
> > **不是“能不能 Meta 化”，而是“这份知识是否已经稳定到值得进入 Meta”。**

做到上一章以后，已经可以看到一个很容易让项目走向另一个极端的问题。

我们已经证明：

```text
Type
Traits
Generic
Callable
Graph
Executor
Machine
```

这些基础能力能够组合出很多东西。

甚至可以进一步支撑：

```text
Serialization
RPC
Plugin
Workflow
ECS
Query
Protocol
```

这时最危险的诱惑反而不是：

> C 能力不够。

而是：

> **既然 Meta 可以解决这么多问题，是不是所有问题都应该继续 Meta 化？**

答案应该非常明确：

## 不是。

如果继续沿着：

```text
“这个也能用宏实现”
“这个也能做 DSL”
“这个也能在编译期推导”
```

无限向前扩展，那么最终很可能重新回到第一章的问题：

```text
本来为了减少复杂度
        ↓
创造了一套更复杂的系统
```

因此，CMeta 真正成熟以后，最重要的能力之一反而应该是：

> **知道什么时候不应该增加新的 Meta 能力。**

---

## 1. Meta 不是目的

整个系统最开始不是为了：

```text
实现元编程
```

而是为了：

```text
少维护重复代码
```

后来增加 Schema，不是因为：

```text
Schema 很高级
```

而是因为：

```text
同一组事实被多次使用
```

增加 Type，不是因为：

```text
想给 C 做 Reflection
```

而是因为：

```text
宏没有类型
导致同一份类型知识重复维护
```

增加 Generic，不是因为：

```text
想复制 C++ Template
```

而是因为：

```text
相同算法不断针对不同类型重复实例化
```

增加 Graph，也不是因为：

```text
Graph 是一个漂亮的抽象
```

而是因为：

```text
需要验证 Type + Callable
能否描述一个真正复杂的计算对象
```

所以判断一个 abstraction 是否应该存在，最重要的问题始终不是：

> 能不能做？

而应该是：

> **它消除了什么已经真实存在的复杂度？**

---

## 2. Ordinary C 永远应该是第一选择

如果一个问题用：

```c
for (...) {
    ...
}
```

写出来：

```text
简单
清楚
只出现一次
```

那么完全没有理由为了：

```text
“统一”
```

强行改成：

```text
Stream
Graph
Meta DSL
```

同样，如果一个模块只有：

```c
struct Config {
    int port;
    int workers;
};
```

而且它：

```text
不需要 serialization
不需要 field iteration
不需要 binding
```

就没有必要马上：

```text
Struct(Config, ...)
```

Meta abstraction 不是默认语法。

它应该只在：

```text
普通 C 已经产生稳定重复模式
```

之后出现。

---

## 3. 一个非常重要的原则：先写普通 C，再抽象

更健康的发展顺序应该是：

```text
Problem
   ↓
Ordinary C Implementation
   ↓
第二个类似实现
   ↓
第三个类似实现
   ↓
观察真正重复的部分
   ↓
抽象
```

而不是：

```text
设计一个 Universal Meta Abstraction
        ↓
然后寻找问题来使用它
```

可以简单概括成：

## Code First, Meta Later

因为只有真实代码出现以后，才能知道：

```text
什么真的重复
什么只是看起来相似
哪些差异是偶然的
哪些差异是语义性的
```

---

## 4. 过早抽象最大的危险，是把偶然相似变成永久约束

假设现在有两个模块：

```text
A
B
```

都写了：

```text
init
run
stop
```

看起来非常相似。

如果立刻抽成：

```text
Lifecycle<T>
```

以后却发现：

```text
A:
    stop 可以恢复

B:
    stop 永远 terminal
```

那么最初的抽象实际上把两个：

```text
不同语义
```

强行压进：

```text
同一接口
```

最后只能增加：

```text
flags
optional methods
special cases
```

抽象反而更复杂。

所以：

> **重复的形状，不一定意味着重复的语义。**

CMeta 应该抽的是：

```text
stable semantic repetition
```

而不是：

```text
syntactic similarity
```

---

## 5. Finite 是第一条核心纪律

整个体系中最重要的限制之一，就是：

## Finite

例如：

```text
Finite Type Universe
Finite Signature Universe
Finite Generic Kinds
Finite Relations
Finite Operator Policies
Finite Rewrite Rules
```

这并不是：

```text
因为技术能力不够
```

而是主动设计。

因为 finite 会带来一个非常重要的链条：

```text
Finite
   ↓
Enumerable
   ↓
Inspectable
   ↓
Validatable
   ↓
Generatable
   ↓
Provable
```

如果一个系统允许：

```text
任意类型
任意 token recursion
任意 template computation
```

那么很多：

```text
完整检查
manifest
proof
```

都会困难很多。

---

## 6. Finite 也让编译行为更可预测

复杂 template/meta 系统一个常见问题是：

```text
编译器到底会实例化多少东西？
```

如果规则可以递归扩展：

```text
A<T>
    ↓
B<A<T>>
    ↓
C<B<A<T>>>
    ↓
...
```

生成规模可能迅速失控。

而有限模型可以明确：

```text
最多多少 Type
最多多少 Signature
最多多少 Operator Relation
```

因此：

```text
compile time
generated code size
error surface
```

更容易预测。

对于一个底层 C library，这种可预测性本身就是价值。

---

## 7. 第二条核心纪律：Explicit

C 之所以长期适合系统编程，一个重要原因就是：

```text
很多成本是显式的
```

例如：

```text
malloc
free
mutex
thread
```

用户通常知道：

```text
什么时候 allocation
什么时候 synchronization
```

CMeta/CFlow 不应该为了高级 abstraction 破坏这一点。

所以应该尽量明确：

```text
谁拥有对象
谁 borrow
谁 move
哪里 allocate
哪里可能 block
queue capacity 是多少
```

而避免：

```text
hidden allocation
hidden retry
hidden thread
hidden fallback
```

---

## 8. Explicit Ownership 比自动“聪明”更重要

例如：

```text
Subscription
```

成功接管 Publisher 时：

```text
Publisher ownership moves to Subscription
```

这比：

```text
“framework 会自己决定什么时候释放”
```

更容易理解。

Actor：

```text
Owner
```

负责 lifecycle，

Producer Reference：

```text
只能 send
```

同样如此。

这种设计看起来比：

```text
shared smart object
```

更手工。

但它给出了：

```text
非常明确的 lifetime boundary
```

对 C 来说，这往往比自动化更重要。

---

## 9. 第三条核心纪律：Bounded

所有可能积累资源的地方，都应该优先考虑：

```text
上限是什么？
```

例如：

```text
Executor Queue
Mailbox
Capture Storage
Machine Declaration
Graph Nodes
Pending Tasks
```

无限增长通常意味着：

```text
问题只是被推迟
```

例如：

```text
Producer
    100k/s

Consumer
    10k/s
```

如果 queue unbounded：

```text
系统暂时没有失败
```

但最终只是：

```text
Memory Exhaustion
```

所以更好的协议是：

```text
capacity
FULL
```

把系统的真实限制暴露出来。

---

## 10. Bounded 也让系统更容易证明

形式化系统最怕：

```text
状态空间无限扩张
```

如果：

```text
Mailbox
Executor Queue
Type Relation
```

都存在明确边界，

很多性质就更容易表达。

例如：

```text
pending <= capacity
```

可以成为明确 invariant。

这再次说明：

```text
Engineering Constraint
```

和：

```text
Formal Verifiability
```

往往不是矛盾的。

有限资源边界反而让二者更统一。

---

## 11. 第四条核心纪律：Fail-fast

整个体系应该尽量避免：

```text
猜
```

例如：

```text
Type 不知道
    → 猜成 void *

Trait 缺失
    → 猜成 memcpy

Signature 不匹配
    → runtime generic call

Parallel 不支持
    → 自动变 sequential
```

这些“友好”行为很容易隐藏真正问题。

所以更合适的是：

```text
Unknown Type
    → Reject

Missing Trait
    → Reject

Invalid Signature
    → Reject

Unsupported Execution Mode
    → Reject
```

---

## 12. Fail-fast 的真正价值，是缩短错误距离

假设用户写：

```text
Filter(user_name)
```

但：

```text
user_name : User -> String
```

而 Filter 要求：

```text
User -> bool
```

最好的错误位置是：

```text
Graph Build
```

甚至：

```text
compile-time
```

而不是：

```text
程序跑了一小时
某个 User 到来以后
在 adapter 里发现输出大小不对
```

也就是说：

```text
Error Detection
```

应该尽量靠近：

```text
Error Introduction
```

这是 Fail-fast 最重要的价值。

---

## 13. 第五条核心纪律：No Silent Fallback

Fail-fast 之外，还需要更严格的一条：

## 不静默改变语义

例如调用方要求：

```text
Parallel Reduce
```

系统不能因为条件不满足：

```text
偷偷执行 Sequential Reduce
```

结果可能仍然一样。

但调用方真正请求的是：

```text
一个 execution contract
```

如果没有满足，就应该明确：

```text
Unsupported
```

而不是：

```text
“我帮你做了一个差不多的”
```

---

## 14. Fallback 什么时候才合理

这并不是说所有 fallback 都错误。

关键在于：

```text
fallback 是否属于显式 contract
```

例如用户明确写：

```text
try_direct
else_plan
```

那么：

```text
Direct 不可用
    ↓
Plan
```

完全合理。

因为 policy 是：

```text
用户明确允许的
```

问题是：

```text
framework 自己悄悄决定
```

所以仍然回到：

```text
Mechanism
≠
Policy
```

---

## 15. 第六条核心纪律：Static When Possible, Dynamic When Necessary

CMeta 已经提供：

```text
Runtime Type Descriptor
Interface
Dynamic Callable Adapter
```

但这并不意味着：

```text
所有代码都应该动态化
```

相反，更理想的策略是：

```text
Static Interior
Dynamic Boundary
```

例如：

```text
Plugin / Publisher
    runtime provider
```

可以通过：

```text
Interface
```

进入系统。

但：

```text
已经确定的 Map / Filter
```

应尽量：

```text
direct call
```

而不是每个 value 继续动态 dispatch。

---

## 16. Runtime Reflection 应该只服务真正动态的问题

例如：

```text
Deserializer
```

在 runtime 才知道：

```text
目标 Field
```

使用 descriptor 很合理。

但如果：

```text
Vec<int>
```

已经在编译期确定，

就不应该每次 push 都：

```text
find_type("int")
```

再去决定：

```text
sizeof(int)
```

这种使用方式相当于：

```text
主动丢掉编译器已经知道的信息
```

这显然不是目标。

---

## 17. 第七条核心纪律：No Hidden Runtime

如果用户写：

```text
lambda(...)
```

不应该默认：

```text
heap allocate closure
```

如果写：

```text
actor_create(...)
```

不应该自动：

```text
spawn thread
```

如果写：

```text
stream.map(...)
```

不应该自动：

```text
创建一堆 heap stage object
```

除非 API contract 明确说明。

更好的设计是：

```text
Inline Capture
Bounded Queue
Borrowed Scheduler
Explicit Executor
```

让 runtime resource model 能从 API 表面看出来。

---

## 18. 高级语法不能隐藏低级成本

假设未来增加更漂亮的 DSL：

```text
users
    |> filter(enabled)
    |> map(name)
```

这当然很好。

但前提是用户仍然能够知道：

```text
是否 materialize？
是否 allocate？
是否 parallel？
```

高级语法的价值应该是：

```text
减少表达噪声
```

而不是：

```text
隐藏成本模型
```

这也是 Modern C 和很多高级语言 abstraction 可以保持不同的地方。

---

## 19. 第八条核心纪律：Cross-Compiler Semantics First

如果某种 abstraction 只有：

```text
GNU C
```

可以正确实现，

但核心 library 声称支持：

```text
C11
```

那么它不应该进入：

```text
核心 semantic model
```

可以提供：

```text
GNU convenience syntax
```

但底层必须仍然存在：

```text
strict C11 equivalent
```

因此：

```text
Compiler Extension
```

应该是：

```text
Ergonomic Layer
```

而不是：

```text
Semantic Foundation
```

---

## 20. 第九条核心纪律：Meta Layer 不应该泄漏进所有名字

如果用户定义：

```text
User
```

最终使用时应该仍然是：

```c
User user;
```

而不是：

```c
cmeta_generated_struct_User user;
```

Meta 只是一种：

```text
定义方式
```

不应该改变：

```text
领域模型本身
```

同样：

```text
State
Order
Event
```

仍然应该使用自然领域名字。

否则 Library implementation 会侵入整个 application vocabulary。

---

## 21. 第十条核心纪律：Module Owns Meaning

如果：

```text
CMeta
```

负责 Type，

那么其他模块不要重新定义：

```text
另一套 Type System
```

如果：

```text
CFlow
```

负责 Graph operator semantics，

CMeta 不应该反过来知道：

```text
Filter / Map
```

是什么。

如果：

```text
Container
```

负责：

```text
Vec algorithm
```

CMeta 不应该实现：

```text
Vec reserve
```

这是非常重要的：

## Ownership of Meaning

每个 module 应该拥有：

```text
自己的语义
```

而不是只按：

```text
文件目录
```

分层。

---

## 22. 什么不属于 CMeta

做到现在，可以比较明确地给 CMeta 列出 Non-goals。

CMeta 不应该负责：

```text
Container Algorithms
```

例如：

```text
Vec growth
BTree balancing
HashMap probing
```

---

不应该负责：

```text
Scheduling Policy
```

例如：

```text
worker priority
CPU affinity
fair scheduling
```

---

不应该负责：

```text
Business Retry Policy
```

---

不应该成为：

```text
Runtime Reflection VM
```

---

不应该成为：

```text
GC Object System
```

---

不应该成为：

```text
C++ Template Clone
```

---

也不应该成为：

```text
C Compiler Replacement
```

---

## 23. 什么不属于 CFlow

CFlow 同样需要 Non-goals。

CFlow 不应该：

```text
强制所有数据处理使用 Graph
```

简单 loop 仍然是简单 loop。

---

不应该：

```text
拥有所有容器
```

它只消费：

```text
Range / Collector
```

协议。

---

不应该：

```text
强制所有应用使用同一个 Thread Pool
```

---

不应该：

```text
自动决定所有 retry/drop policy
```

---

也不应该发展成：

```text
Stream + RPC + UI + Workflow + Database
全部放进同一个 core
```

它更应该保持：

```text
Execution Substrate
```

而不是：

```text
Application Framework Universe
```

---

## 24. 什么不属于 Lean

Lean 的边界也非常重要。

Lean 不应该：

```text
成为普通 C build 的必需依赖
```

---

不应该：

```text
运行生产 callback
```

---

不应该：

```text
承担所有 integration testing
```

---

不应该：

```text
为了“证明率”而形式化每一行普通 C
```

它应该优先覆盖：

```text
高复用
高风险
语义稳定
有限
```

的核心规则。

例如：

```text
Type Relations
Signature Manifest
Rewrite Law
WAIT / Demand invariants
Machine Semantics
```

---

前面 1–24 节已经把核心纪律与 non-goals 说明清楚。早期草稿随后又用二十多节重复总结“如何判断是否抽象、为什么要克制、为什么仍然是 C”。出版稿不再重复这些结论，而是直接进入反例实验：让每条纪律对应一个真实的失败模式。

---

## 25. Counterexample Lab：十种“看起来高级，实际上更差”的设计

下面这些反例都不是为了制造稻草人。

它们都很常见，而且在早期通常看起来“更统一、更智能、更自动”。

真正的问题只有在系统变大以后才会暴露。

---

## 25.1 Counterexample 1：只有一次重复，也立刻造 Meta DSL

假设只有：

~~~c
int user_age(const User *u) {
    return u->age;
}

int order_count(const Order *o) {
    return o->count;
}
~~~

看到形状相似，就立刻设计：

~~~text
FieldGetter(Type, Field, ReturnType)
GenerateAccessor(...)
Reflect(...)
GenericInvoke(...)
~~~

表面收益：

~~~text
少写两行函数
~~~

实际成本：

~~~text
新的 macro vocabulary
新的错误信息
新的 naming convention
新的 compile-time dependency
新的 debugging path
~~~

而且：

~~~text
User.age
Order.count
~~~

可能只是偶然相似。

### 为什么错

你抽象的不是：

~~~text
稳定知识
~~~

而是：

~~~text
当前代码形状
~~~

这违反：

> **Code First, Meta Later.**

### 最小修正

继续写普通 C。

直到出现：

~~~text
大量稳定字段 schema
多个消费者都重复读取同一字段事实
serializer / binder / UI / query 都需要同一信息
~~~

再把：

~~~text
Field Metadata
~~~

抽成真正共享事实。

---

## 25.2 Counterexample 2：为了“像 Template”追求无限类型推导

假设最初只需要：

~~~text
CommonType(int, long) = long
CommonType(int, double) = double
~~~

但很快产生诱惑：

~~~text
既然叫 TypeFunction
为什么不能支持任意嵌套任意递归任意偏特化？
~~~

于是开始模拟：

~~~text
template partial specialization
SFINAE
recursive pattern matching
higher-kinded generic
~~~

用 preprocessor 实现。

### 为什么一开始看起来合理

因为：

~~~text
C++ Template 很强
~~~

所以容易把目标变成：

~~~text
“C 也应该一样强”
~~~

### 真正问题

C preprocessor 并不是为开放递归类型计算设计的。

结果往往是：

~~~text
错误爆炸
compile time 不可预测
compiler divergence
debugging 极差
规则边界没人说得清
formal model 反而更困难
~~~

### 最小修正

把问题重新写成：

~~~text
finite admitted universe
+
finite relation rows
+
explicit unsupported case
~~~

也就是：

~~~text
TypeFunction
    = finite relation
~~~

不是：

~~~text
TypeFunction
    = secret general-purpose compiler
~~~

这正是为什么 No Default 很重要。

未知输入就失败。

---

## 25.3 Counterexample 3：Descriptor Pointer 当 Type Identity

最简单的实现：

~~~c
if (a == b) {
    /* same type */
}
~~~

单 TU 完美工作。

甚至 test 也可能全绿。

直到：

~~~text
TU A
TU B
shared library A
shared library B
static archive duplicated into multiple DSOs
~~~

出现。

同一个：

~~~text
Pair<int, long>
~~~

可能拥有多个 descriptor object。

于是：

~~~text
pointer differs
    ↓
“type mismatch”
~~~

### 为什么错

地址回答：

~~~text
representation object 在哪里
~~~

不是：

~~~text
semantic type 是什么
~~~

### 最小修正

使用：

~~~text
stable atom id
generic constructor identity
structural arguments
pointer/const/application form
~~~

建立 semantic identity。

如果两个 descriptor：

~~~text
地址不同
结构/meaning 相同
~~~

应该相等。

这不是 abstraction bonus。

这是 Multi-TU correctness。

---

## 25.4 Counterexample 4：Lambda Capture 超过 Inline Bound 就偷偷 malloc

设计一个 C lambda：

~~~text
callable
+
inline capture[32]
~~~

很好。

然后遇到 80-byte capture。

最“方便”的做法：

~~~text
if too large:
    malloc(...)
    hide pointer inside callable
~~~

用户 API 完全不变。

### 为什么看起来合理

因为用户获得：

~~~text
“任何 capture 都能用”
~~~

### 真正问题

API 原本暗示：

~~~text
bounded value object
copy by value
no hidden allocation
predictable lifetime
~~~

现在却悄悄变成：

~~~text
some callables allocate
copy may fail
destroy becomes mandatory
thread/lifetime semantics changed
ABI shape meaning changed
~~~

而调用点不知道。

### 最小修正

三种合法选择：

~~~text
A. compile/admission failure
B. explicit heap-backed callable type
C. caller-owned external context
~~~

但必须 explicit。

> **Hidden convenience that changes ownership is not convenience. It is semantic drift.**

---

## 25.5 Counterexample 5：Actor / Executor Queue 自动无限增长

需求：

~~~text
send should almost never fail
~~~

于是实现：

~~~text
queue full
    ↓
realloc bigger
    ↓
keep accepting
~~~

甚至：

~~~text
linked-list unbounded queue
~~~

### 为什么看起来合理

上层不用处理 FULL。

demo 非常顺滑。

### 生产环境会发生什么

当 consumer变慢：

~~~text
producer rate > consumer rate
~~~

系统不会 backpressure。

只会：

~~~text
memory rises
latency rises
cache locality collapses
event becomes stale
eventually OOM
~~~

问题从：

~~~text
明确 FULL
~~~

被变成：

~~~text
很晚才发生的全局 failure
~~~

### 最小修正

固定 capacity。

返回：

~~~text
FULL
~~~

让上层选择：

~~~text
retry later
drop by explicit policy
backpressure upstream
fail operation
shed load
~~~

> **Boundedness turns resource pressure into information.**

---

## 25.6 Counterexample 6：Parallel Plan 不可用时 Silent Sequential Fallback

用户显式请求：

~~~text
parallel reduce
~~~

当前输入太小、Executor 满、reducer contract 不满足、plan 不支持。

框架觉得：

~~~text
“没关系，我帮你顺序执行，结果一样。”
~~~

### 为什么看起来合理

功能似乎“更鲁棒”。

### 为什么实际上危险

虽然结果可能相同，但：

~~~text
latency
CPU topology
resource usage
deadline behavior
load shedding
SLA
benchmark
~~~

都变了。

更糟的是：

~~~text
一个本应暴露的 admission bug
~~~

被隐藏。

### 最小修正

返回明确：

~~~text
UNSUPPORTED
FULL
INVALID_OPTIONS
INELIGIBLE
~~~

如果 application 真想 fallback：

~~~text
if parallel failed:
    explicitly choose sequential
~~~

由它自己决定。

> **Semantic equivalence does not imply operational equivalence.**

---

## 25.7 Counterexample 7：Everything Is Virtual

为了“统一”，把所有东西都变成：

~~~text
{ self, vtable }
~~~

包括：

~~~text
Map
Filter
type operations
small value transform
inner-loop compare
Graph node execution
~~~

每个 value：

~~~text
vtable lookup
indirect call
metadata check
dynamic dispatch
~~~

### 为什么一开始看起来漂亮

统一：

~~~text
one interface to rule them all
~~~

增加新类型不改调用者。

### 真正问题

你把：

~~~text
真正需要动态性的 boundary
~~~

和：

~~~text
编译/构造时已经知道的 interior
~~~

混在一起。

结果：

~~~text
optimizer knowledge无法消除
hot path始终保留动态层
debugging堆栈膨胀
cache/inlining opportunities减少
~~~

### 最小修正

保持：

~~~text
Dynamic Boundary
    Publisher / Scheduler / plugin provider

Static Interior
    known Graph stage / Plan instruction / direct target
~~~

动态性只留在真正动态的边界。

> **Interface is a boundary tool, not a universal object model.**

---

## 25.8 Counterexample 8：把 Raw Parser Token 当 Business Stream

有 JSON parser 输出：

~~~text
OBJECT_BEGIN
KEY
STRING
ARRAY_BEGIN
...
~~~

又已经有 CFlow Stream。

于是自然想到：

~~~text
Stream<Token>
    .filter(...)
    .map(...)
~~~

### 为什么看起来合理

都是“流”。

### 真正问题

token sequence不是独立 business values。

它是：

~~~text
grammar-preserving structural protocol
~~~

如果业务 filter 掉：

~~~text
ARRAY_END
~~~

整个语法失效。

而且：

~~~text
field name
number
container boundary
~~~

仍未形成 semantic object。

### 最小修正

正确边界：

~~~text
parser syntax
    ↓
canonical grammar
    ↓
binding / validation
    ↓
complete semantic/native value
    ↓
business CFlow
~~~

> **Same shape “stream of items” does not mean same semantics.**

---

## 25.9 Counterexample 9：为了“形式化”让 Lean 证明 ABI / Benchmark

团队有了 Lean 后，很容易产生新的形式主义：

~~~text
能不能证明 struct ABI stable？
能不能证明这个版本快 2x？
能不能证明 Linux scheduler 不饿死？
~~~

### 为什么错

这些问题依赖：

~~~text
compiler ABI
linker/loader
platform
CPU
OS
allocator
benchmark workload
external environment
~~~

如果 formal model没有精确包含这些现实事实，证明的只是：

~~~text
一个抽象模型
~~~

不是实际工具链。

### 最小修正

Lean 证明：

~~~text
semantic identity
rewrite preservation
state-machine invariant
bounded protocol relation
refinement
~~~

Toolchain evidence验证：

~~~text
ABI
link
install
compiler compatibility
~~~

Benchmark验证：

~~~text
actual performance
~~~

Stress/Sanitizer验证：

~~~text
memory/race bugs
~~~

> **Using proof at the wrong layer is another form of hidden assumption.**

---

## 25.10 Counterexample 10：因为“上层需要”就把 Domain Semantics 塞进 Core

例如 RPC 需要：

~~~text
retry
deadline
service discovery
~~~

于是把：

~~~text
retry policy
~~~

塞进 Executor。

Workflow 需要：

~~~text
compensation
~~~

于是把 compensation 塞进 Machine core。

JSON 需要：

~~~text
field names
~~~

于是把 JSON syntax 塞进 CMeta。

### 为什么错

Core 开始失去：

~~~text
single semantic ownership
~~~

一个 primitive 同时服务太多 domain，最后只能拥有：

~~~text
模糊的“万能”参数
~~~

### 最小修正

问：

~~~text
这是不是该 domain 独有的 meaning？
是否在至少多个独立领域稳定重复？
没有它 core 是否仍完整？
~~~

如果答案是 domain-specific：

~~~text
留在上层
~~~

> **Reuse does not require ownership transfer.**

---

## 26. “普通 C 更好”不是失败，而是设计成功

一本讲 Modern C 的书如果最后让读者觉得：

~~~text
每个问题都应该用 CMeta/CFlow
~~~

那就是错误结论。

有大量场景普通 C 明显更好。

## 26.1 一个固定 pipeline

如果只有：

~~~c
for (...) {
    if (...) {
        ...
    }
}
~~~

不会动态组合、不需要复用 Graph、不需要分析/优化：

> 直接写 loop。

## 26.2 一个小状态机

只有：

~~~text
3 states
4 events
one file
no dynamic binding
no concurrency
~~~

一个 switch 可能比 Machine IR 更好。

## 26.3 一个 callback

不需要：

~~~text
capture
signature registry
Graph
semantic optimization
~~~

就直接：

~~~c
void (*fn)(void *);
~~~

## 26.4 一个固定 struct 的 parser

只有一个 format、一个 object、不需要通用 binding：

> 手写 parser 到 struct。

## 26.5 一个简单同步程序

不需要：

~~~text
WAIT
Demand
Scheduler
Executor
~~~

就不要为了“现代”增加异步模型。

### 判断标准

如果 abstraction 没有删除：

~~~text
真实重复知识
真实错误边界
真实 runtime decision duplication
~~~

它就可能只是新增一层。

---

## 27. Decision Tree：一个新能力是否值得进入 Meta / Core

可以使用下面的顺序判断。

~~~text
Q1. Plain C 是否已经清楚、短、稳定？
    YES → 保持 Plain C
    NO  ↓

Q2. 重复的是“知识”还是只是代码形状？
    code shape only → 暂不抽象
    stable knowledge ↓

Q3. 是否至少有多个独立消费者需要同一事实？
    NO → 留在模块内部
    YES ↓

Q4. 这份知识是否有限、可显式描述？
    NO → 可能是 runtime/domain feature
    YES ↓

Q5. Ownership / failure / capacity 是否能写清？
    NO → 不进入 Core
    YES ↓

Q6. 它属于已有哪个 semantic owner？
    已有 owner → 扩展/复用 owner
    没有 ↓

Q7. 是否在多个 domain 中稳定重复？
    NO → 上层 feature
    YES ↓

Q8. 能否在执行前消费掉大部分复杂度？
    NO → 明确它是 Runtime Feature
    YES ↓

Q9. 是否有正确的 evidence strategy？
    NO → 设计未完成
    YES ↓

Q10. 加入后系统整体更容易理解吗？
    NO → 删除 abstraction
    YES → 才考虑进入 Core
~~~

最后一个问题最重要。

---

## 28. Anti-Meta Budget：Core 每增加一个 Primitive 都应该付出成本

可以把 Core feature 视为有“长期维护预算”。

一个新 primitive 一旦进入：

~~~text
CMeta
CFlow kernel
public ABI
formal model
generated manifest
~~~

以后就需要长期承担：

~~~text
documentation
compiler compatibility
ABI
Multi-TU
tests
formal maintenance
debugging
migration
downstream compatibility
~~~

所以判断标准不能只是：

~~~text
实现它是否容易
~~~

而应该是：

> **它值得我们未来 5 年继续解释、测试、兼容吗？**

这会自然降低 Core feature 增长速度。

而这正是好事。

---

## 29. Counterexample Review Checklist

代码审查一个新的 Meta/Runtime abstraction 时，可以直接问：

~~~text
[ ] 有没有 Plain C baseline？
[ ] 重复的知识是什么？
[ ] 为什么不是 module-local helper？
[ ] 为什么必须进入 Core？
[ ] type identity 是否跨 TU？
[ ] ownership 是否显式？
[ ] 是否有 hidden allocation？
[ ] resource 是否 bounded？
[ ] FULL/CLOSED/STALE 是否被保留为信息？
[ ] 是否有 silent fallback？
[ ] dynamic dispatch 是否进入不必要的 hot path？
[ ] failure 是否尽可能提前？
[ ] theorem 证明的是正确层次的问题吗？
[ ] ABI/toolchain claim 是否有真实 consumer test？
[ ] 性能 claim 是否有 fresh measurement？
[ ] abstraction 最终能否在 hot path 消失？
~~~

如果很多项答不上来：

> 不应该继续“完善 abstraction”，而应该先缩小 abstraction。

---

## 30. What We Learned

第十四章真正建立的是：

> **克制本身也是一种系统能力。**

前面的十条纪律现在有了具体失败模式：

~~~text
Finite
    防止把 preprocessor 变成无限语言

Explicit
    防止 ownership/policy 偷偷变化

Bounded
    防止 backpressure 变成 OOM

Fail-fast
    防止错误距离不断拉长

No Silent Fallback
    防止 operational semantics 被偷偷改变

Static When Possible
    防止已知 interior 保留动态成本

No Hidden Runtime
    防止 API 看起来简单、ownership 变复杂

Cross-Compiler Semantics First
    防止 core 绑定偶然 compiler trick

Semantic Identity
    防止地址偶然成为 meaning

Module Owns Meaning
    防止 Core 变成 domain feature landfill
~~~

但最重要的一条仍然是：

~~~text
Ordinary C First
~~~

不是因为普通 C 更“纯”。

而是：

> **抽象的价值必须被真实复杂度证明。**

所以一个成熟的 Modern C 系统最终应该同时拥有两种能力：

~~~text
知道什么时候应该构造 Typed / Verified abstraction

以及

知道什么时候应该只写一个普通 C function
~~~

下一章作为全文最终总结，不再列 Feature。

我们只保留一套可重复使用的方法：

~~~text
Understand
→ Model
→ Formalize
→ Verify
→ Implement
→ Lower
→ Measure
~~~

并用它回答：

> **什么才是这本书所说的 Modern C？**


