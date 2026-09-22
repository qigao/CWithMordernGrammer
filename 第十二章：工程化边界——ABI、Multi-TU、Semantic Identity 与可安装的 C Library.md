# 第十二章：工程化边界——ABI、Multi-TU、Semantic Identity 与可安装的 C Library


> **本章路线**
>
> 前十一章已经回答“怎样设计”和“怎样证明”。这一章回答更现实的问题：
>
> **这些能力离开源码树以后还成立吗？**
>
> ~~~text
> One-TU prototype
>      ↓
> Multi-TU
>      ↓
> Static / Shared Library
>      ↓
> Install / Export
>      ↓
> External Consumer
>      ↓
> Cross-Compiler / Cross-Platform
>      ↓
> Stable semantic + ABI contract
> ~~~
>
> 本章不把 ABI 问题形式化成它不是的东西。Lean 可以帮助定义 semantic identity；真正的 linker、symbol visibility、package export、SOVERSION、installed-header 和 external-consumer 行为仍然必须通过真实工具链证据验证。

前面的章节已经把体系推进到了一个很完整的状态：

```text
Macro
 ↓
Type
 ↓
Traits
 ↓
Generic
 ↓
Callable
 ↓
Graph
 ↓
Stream / Reactive
 ↓
Executor
 ↓
Machine / Actor
 ↓
Optimization
 ↓
Lean Proof
```

如果只停留在这些抽象上，整个系统已经很有意思。

但对于一个真正的 C 基础库来说，还有一个完全不同层面的考验：

> **这些设计能不能离开单文件 Demo，进入真实工程？**

真实 C 工程意味着：

```text
几十甚至几百个 .c 文件
多个静态库 / 动态库
独立安装的 public headers
GCC / Clang / MSVC
Linux / Windows / macOS
Debug / Release
不同编译单元独立编译
```

这时很多在单文件里看起来完全成立的设计，会突然暴露问题。

例如：

```text
Type Descriptor 的地址能不能当作类型身份？

header 中生成的对象在不同 TU 中是不是同一个？

Generic 类型的名字是否稳定？

metadata 应该放 header 还是 .c？

generated header 谁负责生成？

Lean 是否进入普通用户构建？

不同 module 谁真正拥有某个 abstraction？
```

这些问题决定的不是：

```text
CMeta 功能强不强
```

而是：

> **它能不能真正成为一个 Library。**

---

# 1. 单 Translation Unit 会掩盖很多问题

假设所有代码都写在：

```text
main.c
```

里面。

那么：

```c
static const cmeta_type_desc user_type = { ... };
```

无论在哪里引用：

```text
&user_type
```

地址都相同。

于是很容易自然地写：

```c
if (a == b) {
    /* same type */
}
```

在单 TU 中：

```text
descriptor pointer equality
```

似乎完全可以作为：

```text
type equality
```

但是当代码拆成：

```text
a.c
b.c
```

以后，事情就不同了。

假设某个 header 中定义：

```c
static const cmeta_type_desc int_vec_type = { ... };
```

那么：

```text
a.c
```

拥有一份：

```text
int_vec_type @ 0x1000
```

而：

```text
b.c
```

又拥有另一份：

```text
int_vec_type @ 0x9000
```

它们描述的是：

```text
同一个 Vec<int>
```

但：

```text
0x1000 != 0x9000
```

如果：

```text
pointer equality
=
type equality
```

整个类型系统在跨 Translation Unit 后立即失效。

---

# 2. 地址只是实现位置，不是语义身份

这暴露了一个非常基本的事实：

> **内存地址不是类型的语义身份。**

这不仅适用于 CMeta。

很多系统都会遇到类似问题。

例如：

```text
同一个字符串
```

可能在两个模块中有两个不同地址。

```text
同一个 schema
```

可能被两个 shared library 各自实例化一次。

所以类型真正应该回答的是：

```text
“你是什么？”
```

而不是：

```text
“你现在放在哪里？”
```

于是：

```text
Type Descriptor
```

和：

```text
Type Identity
```

必须分开。

---

# 3. Semantic Type Identity

对于普通原子类型，可以有：

```text
Atom(int)
Atom(double)
Atom(User)
```

对于 Pointer：

```text
Pointer(int)
Pointer(User)
```

对于 Generic：

```text
Generic(
    constructor = Vec,
    args = [int]
)
```

以及：

```text
Generic(
    constructor = Map,
    args = [String, User]
)
```

于是：

```text
Vec<int>
```

的身份不是：

```text
descriptor address
```

而是：

```text
constructor = Vec
argument[0] = int
```

这样即使：

```text
TU A
```

和：

```text
TU B
```

各自产生了一份 descriptor，

只要它们的：

```text
semantic identity
```

相同，就应该判断为：

```text
same type
```

---

# 4. Semantic Identity 对 Generic 尤其重要

普通：

```text
int
```

还可以通过：

```text
enum type id
```

比较容易处理。

真正复杂的是：

```text
Vec<int>
Vec<double>
Map<int, User>
Option<Vec<int>>
```

这种组合类型。

如果每个 application 都手工注册一个全局整数：

```text
TYPE_VEC_INT = 1001
TYPE_VEC_DOUBLE = 1002
...
```

很快就会重新产生：

```text
registration explosion
```

更自然的是让 identity 本身就是：

```text
结构化描述
```

例如：

```text
Option<Vec<int>>
```

可以表示成：

```text
Generic Option
    ↓
Generic Vec
    ↓
Atom int
```

也就是：

```text
Type Identity Tree
```

---

# 5. Identity 与 Descriptor 的职责不同

可以把两者明确分开：

```text
Descriptor

name
size
alignment
traits
runtime metadata
```

而：

```text
Identity

semantic equality
generic structure
stable relation
```

也就是说：

```text
Descriptor
    主要服务“怎么操作这个类型”

Identity
    主要服务“它到底是不是那个类型”
```

一个 descriptor 可以指向：

```text
identity
```

但 identity 不能简单退化成：

```text
descriptor address
```

---

# 6. 这一步也是 ABI 设计的一部分

很多人把 ABI 理解成：

```text
function calling convention
struct layout
symbol name
```

这些当然都重要。

但对于一个具有 runtime metadata 的 library 来说，还存在：

```text
Semantic ABI
```

例如两个 module 是否对：

```text
Vec<int>
```

理解一致。

是否对：

```text
Callable<int,long>
```

理解一致。

是否对：

```text
Trait HASH
```

使用相同 bit。

如果这些语义结构不稳定，即使 linker 完全正常：

```text
library 仍然无法真正互操作
```

所以 ABI 不只是：

```text
binary layout
```

还包括：

```text
semantic contract
```

---

# 7. Header 和 Source 的边界必须重新考虑

宏系统很容易倾向于：

```text
everything in header
```

因为：

```text
宏必须在调用点展开
```

这本身没有问题。

但不代表：

```text
所有 runtime object
所有 function body
所有 registry
```

也必须在 header。

例如：

```text
Struct(...)
Enum(...)
typed(...)
```

这类声明可能必须在 header 暴露。

但真正的：

```text
registry storage
complex helper implementation
runtime lookup
large tables
```

完全可以放在：

```text
.c
```

中。

这可以减少：

```text
duplicate code
compile time
object file bloat
```

---

# 8. 一个重要原则：需要调用点信息的留 Header，其余尽量普通 C

例如：

```text
_Generic
macro dispatch
type capture
__FILE__
__LINE__
compile-time assertion
```

这些必须在调用点工作。

那么应该留在：

```text
header
```

但：

```text
registry traversal
descriptor validation
runtime lookup
executor implementation
plan compiler
graph normalization
```

并没有这个要求。

所以更健康的结构是：

```text
Header

DSL
macro façade
inline adapters
public structs
compile-time selection

Source

runtime implementation
registry
algorithms
heavy logic
```

这样可以避免把：

```text
Meta
```

误解成：

```text
Header-only Everything
```

---

# 9. Public Declaration 与 Implementation Generation 也应分开

Generic 代码尤其容易产生这个问题。

例如：

```text
typed(Vec, IntVec, int)
```

到底生成：

```text
declaration
```

还是：

```text
definition
```

如果用户在多个 header 中都写：

```text
definition
```

很容易产生：

```text
duplicate symbols
```

或者：

```text
static copy per TU
```

所以 Generic infrastructure 应该明确：

```text
declare
```

和：

```text
instantiate / define
```

的边界。

类似：

```text
Header
    declare typed API

One .c
    instantiate implementation
```

这样才更接近真实 library 使用方式。

---

# 10. Generated Code 也必须有 Ownership

当项目开始有：

```text
generated manifest
generated operator policy
generated type relation
```

以后，会出现一个很现实的问题：

> **这些文件到底属于谁？**

例如：

```text
builtin_signature_manifest.h
```

如果同时：

```text
CMeta
CFlow
Lean scripts
build system
```

都认为自己可以修改它，就会很混乱。

所以应该明确：

```text
CMeta owns:
    global signature manifest

CFlow owns:
    operator admission policy

Lean owns:
    authoritative formal source / generator

Generated Header:
    build artifact checked into defined location
```

这其实和：

```text
module ownership
```

完全一样。

---

# 11. Generated Header 不应该成为第二份手写 Source of Truth

最危险的情况是：

```text
Lean file
```

维护一套 relation。

同时开发者又直接修改：

```text
generated.h
```

那么很快：

```text
generated result
```

就不再真正是：

```text
generated
```

而变成：

```text
半生成、半手写
```

最终无法判断：

```text
哪个才是真的？
```

所以 generated file 应该有明确规则：

```text
Do not edit manually.
```

真正修改必须回到：

```text
authoritative schema / Lean definition
```

然后重新生成。

这仍然是整个体系贯穿始终的：

```text
Single Source of Truth
```

原则。

---

# 12. 普通消费者构建不应该依赖 Generator

如果安装一个 C library 后，用户只是：

```c
#include <cmeta/cmeta.h>
```

那么最理想状态是：

```text
gcc
clang
msvc
```

即可完成普通构建。

不应该要求：

```text
Python
Lean
custom generator
special preprocessing step
```

全部同时存在。

因此可以把构建分成两类：

```text
Library Development Build
```

和：

```text
Consumer Build
```

开发阶段：

```text
Lean
Generators
Verification
CI
```

可以很丰富。

发布结果应该是：

```text
headers
sources / libraries
generated checked artifacts
```

消费者只依赖：

```text
C toolchain
```

---

# 13. 这也是“简单 C”承诺的一部分

如果最终使用 CMeta 的成本是：

```text
必须安装大型 meta compiler
必须运行 theorem prover
必须使用特殊 build wrapper
```

那么即使 runtime 很简单：

```text
工程体验已经不是普通 C
```

所以整个系统的高级能力应该：

```text
mostly disappear before distribution
```

例如：

```text
Lean proof
    → generated header

Schema
    → ordinary declaration

Graph
    → Plan / Direct execution
```

最终用户看到的仍然应尽量是：

```text
normal .h
normal .c
normal .a / .lib / .so
```

---

# 14. Multi-TU 还会暴露 Callable Identity 问题

类型有 identity。

函数同样会遇到类似问题。

假设：

```text
static int square(int x)
```

分别存在于多个 TU 中。

或者一个 callable 被：

```text
wrapper
adapter
generated thunk
```

包了一层。

那么：

```text
raw function address
```

不一定总能代表：

```text
semantic callable identity
```

尤其当 optimizer 想判断：

```text
Map(f)
Map(f)
```

是否真的是：

```text
same f
```

时，需要非常小心。

这说明：

```text
function pointer equality
```

和：

```text
semantic callable equality
```

也可能不是完全相同的问题。

---

# 15. 但不能为了 Identity 把系统做得过重

最容易出现的反应是：

```text
给每一个 callable 分配 UUID
```

甚至：

```text
全局注册表
动态名字
runtime symbol database
```

这可能比问题本身更复杂。

更合理的策略仍然是：

```text
只在真正需要 semantic equality 的地方
引入足够稳定的 identity
```

例如 built-in / named callable 可以：

```text
有稳定 symbol identity
```

capture callable 则可能：

```text
identity = callable kind + function + capture semantics
```

而很多执行场景根本不需要：

```text
semantic equality
```

只需要：

```text
invoke
```

所以 Identity 也应该：

```text
按需进入协议
```

而不是成为所有对象的沉重基础。

---

# 16. ABI Stability 要求 Public Struct 非常谨慎

如果 public header 暴露：

```c
typedef struct cmeta_callable {
    ...
} cmeta_callable;
```

那么以后增加字段：

```text
ABI
```

可能发生变化。

所以必须考虑：

```text
哪些 struct 真正应该 public by value
哪些应该 opaque
哪些允许 static embedding
```

C 的 ABI 设计通常需要在：

```text
透明
```

和：

```text
稳定
```

之间选择。

例如：

```text
small value protocol
```

适合 by-value public struct。

而：

```text
复杂 runtime object
```

可能更适合 opaque handle。

---

# 17. 为什么小 Interface 特别适合保持 ABI 边界

例如：

```c
struct interface {
    void *self;
    const vtable *vtable;
};
```

这种形态有一个优势：

```text
Interface value 很小
Provider implementation 可以 opaque
```

用户只依赖：

```text
vtable contract
```

而不依赖具体对象内部布局。

所以：

```text
Executor
Scheduler
Publisher
Subscriber
Collector
```

这类 provider boundary 很适合 Interface。

而：

```text
Vec
Machine IR
Plan
```

是否 opaque，则可以按需求决定。

---

# 18. Interface VTable 自己也是 ABI

如果：

```text
vtable
```

顺序发生变化：

```text
ABI 会直接破坏
```

因此 Interface 一旦成为 public contract，就必须像普通 C ABI 一样认真管理：

```text
method ordering
method signature
versioning
reserved slots
capabilities
```

不能因为它由宏生成，就认为：

```text
它只是 compile-time implementation detail
```

只要跨 library boundary 使用，它就是：

```text
真正 ABI
```

---

# 19. Capability 可以帮助减轻 VTable 演进压力

假设 Scheduler 新增：

```text
MANUAL_CLOCK
```

不是所有实现都支持。

如果直接要求所有 provider：

```text
马上实现新 method
```

ABI 和兼容性都可能很麻烦。

Capability 提供另一种方式：

```text
Provider declares:
    DELAYED
    CONCURRENT
    MANUAL_CLOCK
```

上层先检查：

```text
required capability
```

再使用对应功能。

这比：

```text
根据 concrete implementation name 猜能力
```

更稳健。

---

# 20. Status Code 同样是 ABI Contract

例如：

```text
ACCEPTED
FULL
CLOSED
INVALID
STALE
```

这些并不是普通内部 enum。

如果 public API 返回它们：

```text
数字值
语义
兼容规则
```

都成为 API/ABI 的组成部分。

因此：

```text
status enum
```

应该保持：

```text
明确
有限
可扩展
```

而不是不断复用一个：

```text
bool
```

导致所有错误语义都丢失。

---

# 21. Fail-fast 是最重要的工程化策略之一

复杂 Meta 系统最大的危险之一，是：

```text
遇到未知情况自动猜
```

例如：

```text
未知 Type
    → 当 void *

未知 Trait
    → 默认 memcpy

未知 Signature
    → generic invoke

缺少 Executor Capability
    → fallback

Plan stale
    → 继续运行

Mailbox full
    → 自动 drop
```

这些行为短期看起来：

```text
更方便
```

但长期会让：

```text
错误边界越来越模糊
```

所以整个系统更适合坚持：

```text
Fail Early
Fail Explicitly
```

---

# 22. Compile-time 能失败，就不要 Runtime 猜

例如：

```text
typed callback signature 不存在
```

最好：

```text
compile error
```

而不是生成：

```text
unknown callable
```

运行时再报错。

Generic relation 缺失也类似：

```text
TypeEval(...)
```

如果没有定义：

```text
直接失败
```

而不是：

```text
fallback to void
```

这样错误位置距离：

```text
用户真正写错的位置
```

更近。

---

# 23. Build-time 能失败，就不要 Execution-time 猜

例如 Graph：

```text
String
 ↓
Map<int,double>
```

应该在：

```text
Graph Build / Validation
```

就失败。

State Machine：

```text
Unknown Target State
```

也应该在：

```text
Machine Build
```

拒绝。

这样 execution plane 可以建立在更强 invariant 上：

```text
只执行已经合法的 artifact
```

而不是每一步都防御：

```text
Graph 可能坏
Machine 可能坏
Type 可能不匹配
```

---

# 24. Admission-time 能失败，就不要偷偷做另一件事

例如：

```text
executor queue full
```

返回：

```text
FULL
```

而不是：

```text
自动转同步执行
```

Actor mailbox full：

```text
FULL
```

而不是：

```text
自动 drop
```

Parallel Plan 不支持：

```text
UNSUPPORTED
```

而不是：

```text
静默变 Sequential
```

这使系统行为更加：

```text
Predictable
```

---

# 25. Predictability 是 C 工程非常重要的价值

很多时候：

```text
最高性能
```

并不是系统软件唯一目标。

同样重要的是：

```text
知道它会做什么
```

例如：

```text
是否 allocate？
是否 block？
是否 spawn thread？
是否 retry？
是否 drop？
```

如果一个 API 隐藏这些行为，调试 production problem 会很困难。

所以 CMeta/CFlow 更适合在 API contract 中直接表达：

```text
bounded
non-blocking
borrowed
move ownership
serial
concurrent
```

而不是依赖：

```text
framework magic
```

---

# 26. Naming 也是工程边界的一部分

宏系统很容易产生大量内部名字：

```text
meta_xxx
cmeta_xxx
salts_xxx
internal_xxx
generated_xxx
```

随着项目演进，如果不整理，很容易把：

```text
历史实现细节
```

暴露成：

```text
永久 public API
```

所以 public naming 应该遵循一个重要原则：

> **对用户有语义的名字进入 public surface；仅仅为了宏实现存在的名字保持 internal。**

例如用户真正应该看到：

```text
Struct
Enum
Traits
typed
interface
```

而不是：

```text
CMETA_PP_EXPAND_A_17
```

---

# 27. 这也是为什么不能强制所有东西都加 `meta_` 前缀

如果用户定义：

```text
Struct(User, ...)
```

它描述的是：

```text
User
```

而不是：

```text
MetaUser
```

同样：

```text
Enum(State, ...)
```

最终生成的应该是：

```text
State
```

如果所有生成对象都被迫：

```text
meta_state
meta_user
```

就会让 Meta implementation 泄漏进业务模型。

前缀更适合：

```text
Library infrastructure symbol
```

而不是：

```text
用户声明出来的语义对象
```

---

# 28. Module Ownership 必须明确

随着体系扩大，最危险的问题之一是：

```text
CMeta 也实现一点
CFlow 也实现一点
Container 又实现一点
```

最后谁都知道对方内部细节。

更合理的 ownership 应该是：

```text
CMeta
    Type / Traits / Generic / Callable / Interface

CFlow
    Graph / Operator / Subscription / Executor / Machine / Actor

Container Library
    Vec / Map / Tree algorithms

Serialization
    Serializer / Parser / Binding

Lean
    Formal model / generated verified manifests
```

然后通过：

```text
Protocol
```

连接。

---

# 29. CMeta 不应该拥有 Container Algorithm

例如：

```text
Vec
```

需要知道：

```text
T
Traits
```

这并不意味着：

```text
Vec implementation
```

应该搬进 CMeta。

正确关系是：

```text
CMeta
    提供 Type / Traits / Generic metadata

Container
    使用这些信息实现算法
```

也就是：

```text
Meta describes.
Container executes.
```

否则 CMeta 会迅速膨胀成：

```text
Everything Library
```

---

# 30. CFlow 也不应该拥有具体业务 Scheduler Policy

CFlow 可以定义：

```text
Scheduler Protocol
```

但：

```text
高优先级任务如何调度
CPU affinity 怎么做
fairness policy
real-time priority
```

这些不应该全部进入 CFlow core。

CFlow 应该提供：

```text
mechanism + capabilities
```

具体策略可以由：

```text
provider
application
```

实现。

这让：

```text
embedded
desktop
server
```

都可以使用同一 execution model，而不被迫使用同一个 scheduler。

---

# 31. 同样，CMeta 不应该成为 Runtime Reflection VM

Type Descriptor 很有价值。

但如果继续无限增加：

```text
method lookup by string
dynamic invocation by name
runtime AST
object factory
property database
```

很容易逐渐变成：

```text
Reflection Runtime
```

这不是最初目标。

Metadata 应该主要服务：

```text
type relation
traits
protocol binding
serialization
validation
optimization
```

而不是：

```text
把所有 C 程序变成动态对象系统
```

---

# 32. “它不做什么”是架构稳定的重要部分

一个成熟基础库不仅需要：

```text
Capability List
```

还需要：

```text
Non-goals
```

例如可以明确：

```text
CMeta 不做：

完整 C++ template replacement
无限 compile-time evaluator
GC
runtime class system
container algorithm
scheduler implementation policy
C compiler replacement
```

CFlow 不做：

```text
强制线程模型
无限 queue
业务 retry policy
所有框架的一站式 replacement
```

Lean 不做：

```text
production runtime
普通 C 用户构建依赖
所有 implementation line-by-line verification
```

这些边界会让项目更容易长期保持简单。

---

# 33. Cross-Compiler 是另一个真正的压力测试

复杂 C preprocessor code 很容易出现：

```text
GCC works
Clang works
MSVC fails
```

或者：

```text
MSVC works
GCC pedantic fails
```

因此从一开始坚持：

```text
Strict C11
```

和：

```text
有限宏模式
```

价值很大。

因为：

```text
越依赖 compiler extension
```

Meta 系统越难真正成为 portable library。

---

# 34. Extension 可以存在，但不能成为语义基础

例如 GCC/Clang 可能支持：

```text
typeof
statement expression
```

这些功能可以让某些 API 更漂亮。

但如果核心类型系统依赖：

```text
GNU-only extension
```

那么：

```text
MSVC
```

就变成二等公民。

更好的方式是：

```text
Core Semantics
    strict C11

Optional Convenience
    compiler-specific extension
```

这样 extension 可以提升 ergonomics。

但不改变：

```text
semantic model
```

---

# 35. 这也解释了为什么有限 `_Generic` 很重要

`_Generic` 是：

```text
C11 standard
```

虽然能力比：

```text
C++ template
```

弱很多。

但它提供了一个非常重要的：

```text
portable type dispatch primitive
```

结合：

```text
有限 known type list
```

就足以构造：

```text
typed routing
callable signature selection
descriptor lookup
```

而不必依赖：

```text
compiler AST plugin
```

这使整个系统的能力虽然有限，却更容易：

```text
GCC / Clang / MSVC
```

统一。

---

# 36. CI 必须验证 Fresh Build，而不是只验证 Incremental Build

Generated code、CMake、header install 这些问题很容易被：

```text
开发机已有文件
```

掩盖。

所以真正可靠的 CI 应该经常做：

```text
fresh checkout
fresh configure
fresh build
test
```

而不是只：

```text
在已经生成过文件的 workspace
重新编译
```

特别是：

```text
generated manifest
installed header
cross-module include
```

问题往往只会在 fresh environment 中出现。

---

# 37. Installed Headers 是一个很重要的最终测试

在 repository 内构建成功，并不代表 library 真正可用。

真正更严格的测试是：

```text
install library
```

然后建立一个：

```text
external consumer project
```

只使用：

```text
installed include/
installed lib/
```

再：

```text
#include <cmeta/cmeta.h>
```

构建。

这可以立刻发现：

```text
偷偷依赖 repo-relative header
generated file 没安装
public header include internal path
symbol 没导出
```

等问题。

只有通过这种测试，才能真正说：

```text
public API
```

已经独立于：

```text
repository layout
```

---

# 38. Multi-TU Test 同样必须是正式测试

Type identity、Generic、Callable 等问题，单元测试如果全部：

```text
one test .c
```

是看不出来的。

所以应该专门设计：

```text
producer.c
consumer.c
main.c
```

例如：

```text
producer.c
    创建 TYPE<Vec<int>>

consumer.c
    比较 TYPE<Vec<int>>

main.c
    验证 semantic equality
```

这种测试看似简单，却能暴露：

```text
header-static descriptor
pointer equality
registry duplication
```

等非常真实的问题。

---

# 39. ABI Test 也应该进入 CI

如果 library 目标是长期稳定，可以进一步测试：

```text
sizeof public struct
enum values
exported symbols
public header compile
```

甚至保存：

```text
ABI snapshot
```

避免无意中：

```text
改了 public struct layout
```

这对于：

```text
shared library
plugin
```

场景尤其重要。

---

# 40. Error Surface 也是 Public API 的一部分

一个复杂 library 如果内部有：

```text
50 种错误
```

但 public API 最终都返回：

```c
bool
```

那么大量诊断信息丢失。

反过来，如果每个内部细节都暴露：

```text
几百个 error codes
```

用户也无法使用。

所以 Error Surface 应该围绕：

```text
用户能够采取不同动作的错误
```

来设计。

例如：

```text
FULL
```

和：

```text
CLOSED
```

必须不同，因为：

```text
FULL
    可以 retry / backpressure

CLOSED
    retry 没意义
```

这是一种：

```text
semantic error design
```

而不是简单：

```text
error number accumulation
```

---

# 41. 工程化以后，“简单”有了新的含义

最开始说：

```text
C 应该简单
```

很容易理解成：

```text
代码行数少
抽象少
```

但实际工程里真正的简单更接近：

```text
每个模块职责清楚
每个 ownership 明确
错误显式
runtime 行为可预测
ABI 稳定
构建依赖少
```

有时为了得到这些特性，需要增加：

```text
Descriptor
Identity
Status
Certificate
```

一些结构。

但这些结构的目标是：

```text
让复杂性显式
```

而不是：

```text
把复杂性隐藏起来
```

---

# 42. CMeta 最终应该像一个“编译期/控制面基础层”

走到这里，可以重新给 CMeta 定位。

它不应该是：

```text
万能宏集合
```

也不应该是：

```text
Runtime Object Framework
```

更接近：

> **为现代 C library 提供类型化声明、有限推导、协议和语义 metadata 的基础层。**

它可以服务：

```text
Container
Flow
Serialization
Binding
Plugin
RPC
```

但不拥有这些领域本身。

---

# 43. CFlow 则是对这套基础层的复杂工程验证

CFlow 证明：

```text
Type
Callable
Interface
Effects
Properties
```

这些 Meta 能力不是：

```text
为了写漂亮 Demo
```

而是可以真正组合成：

```text
Graph
Stream
Reactive
Executor
Machine
Actor
Optimizer
```

这种复杂系统。

同时 CFlow 不断暴露：

```text
ABI
Ownership
Type Identity
Runtime Boundary
```

问题，迫使 CMeta 继续成熟。

因此：

```text
CFlow
```

既是应用层，也是：

```text
integration stress test
```

---

# 44. 一个真正成熟的 Meta Layer 应该逐渐“消失”

这是本章最后一个很重要的观点。

最成功的 Meta infrastructure 不应该让用户每天都在思考：

```text
我正在使用 Meta
```

而应该让最终代码看起来仍然很自然。

例如：

```c
Struct(User, ...);

typed(Vec, UserVec, User);

stream
    ->filter(...)
    ->map(...);
```

真正执行时更应该只剩：

```text
ordinary C objects
ordinary C calls
ordinary C ABI
```

换句话说：

> **Meta 最终的成功，不是到处都能看到 Meta，而是大量重复和错误边界已经消失，而 C 本身仍然看起来像 C。**

---

# 45. 到这里，工程边界已经可以总结成几条明确原则

整个工程化设计可以压缩成：

```text
Semantic Identity
    不依赖地址

Header / Source Boundary
    宏留调用点，runtime 留普通 C

Generated Ownership
    单一事实源

Consumer Build
    不依赖 Lean / generator

ABI
    显式、稳定、谨慎

Module Ownership
    各层只拥有自己的语义

Fail-fast
    不猜、不静默 fallback

Bounded Resources
    不隐藏无限增长

Cross-Compiler
    Core 保持 Strict C11

Fresh CI / Install Test / Multi-TU Test
    验证真实 library 场景
```

这些原则听起来不像：

```text
Meta Programming
```

却恰恰决定：

> **Meta Programming 能不能从一个技巧，真正变成工程基础。**

---

# 小结：真正困难的不是“做出 Meta”，而是让它在普通 C 工程中成立

单文件里实现：

```text
Enum
Struct
Generic
Lambda
```

并不是最难的事情。

真正困难的是：

```text
不同 Translation Unit 是否认同同一种类型？

不同 library 能否共享同一个协议？

descriptor 是否具有稳定身份？

generated artifact 是否有唯一事实源？

普通用户是否只需要 C compiler？

ABI 是否可以稳定？

错误是否在正确阶段暴露？

内部 abstraction 是否不会泄漏到 public surface？
```

这些问题决定了：

```text
一个宏实验
```

和：

```text
一个真正的基础 library
```

之间的差别。

也正是在解决这些问题以后，CMeta 的定位开始真正清晰：

```text
它不是为了把 C 变成 C++。

也不是为了创造一个新的 Runtime 世界。

而是给仍然必须保持 C 的系统
补上一层有限、类型化、可生成、可验证的知识。
```

CFlow 则继续证明：

```text
这些知识确实可以支撑复杂的软件模型。
```

而 Lean 提供：

```text
最关键关系的可信边界。
```

下一章可以把前面的所有内容进一步收束成一个更大的问题：

> **当 Type、Traits、Callable、Graph、Executor、Machine 这些基础能力已经存在以后，它们还可以服务哪些现代 C 系统？**

下一章将讨论 **CMeta / CFlow 作为 Modern C 基础设施的进一步应用方向**：包括 Serialization / Data Binding、RPC、Plugin ABI、Event Bus、Workflow、ECS、Query Pipeline 等，以及为什么这些并不意味着继续制造更多大型 Framework，而是继续复用同一组有限 primitive。

---


# 46. Case Study：为什么 Descriptor Address 不能成为 Type Identity

单 Translation Unit 中，最诱人的实现是：

~~~c
if (a_type == b_type) {
    /* same type */
}
~~~

如果所有 descriptor 都来自同一个全局 object，这甚至会长期“看起来正确”。

但一旦进入：

~~~text
header-local generated descriptors
static archive embedded into multiple DSOs
plugin/shared-library boundary
independent translation units
~~~

同一个 semantic type 完全可能存在：

~~~text
descriptor object A
descriptor object B
~~~

地址不同，但 meaning 相同。

所以：

~~~text
pointer equality
    ≠
semantic type equality
~~~

这不是抽象洁癖，而是 Multi-TU/DSO correctness。

## 46.1 当前 CMeta 已经把 Identity 从 Descriptor 中显式分离

当前 type descriptor 包含：

~~~text
name
size
align
kind
pointee
traits
identity
~~~

而 cmeta_type_identity 可以表达：

~~~text
ATOM(stable id)
POINTER(base identity)
CONST(base identity)
APPLY(generic constructor, arguments...)
~~~

Generic constructor自身还有：

~~~text
stable_id
display_name
min/max arity
category
~~~

因此：

~~~text
Pair<int, long>
~~~

的 semantic identity 是结构：

~~~text
APPLY(
    constructor = "cmeta.Pair",
    args = ["cmeta.int", "cmeta.long"]
)
~~~

而不是：

~~~text
address of one Pair descriptor
~~~

## 46.2 Structural identity 已经有真实 Multi-TU test

当前测试不是在同一个源文件里复制两个指针做比较。

它专门从 peer Translation Unit 返回 independently constructed identity：

~~~text
local Pair<A,B>
peer  Pair<A,B>
~~~

并验证：

~~~text
local identity address != peer identity address
local constructor address != peer constructor address

but

cmeta_type_identity_equal(local, peer) == true
~~~

这就是第十二章需要的证据类型：

> **不是证明“理论上支持 Multi-TU”，而是让两个真正独立编译单元产生不同 representation，再验证 semantic equality。**

## 46.3 Custom Trait Descriptor 也要跨 TU 保持语义一致

当前 CMeta tests 还覆盖：

~~~text
custom owned_int descriptor in TU A
peer descriptor in TU B
~~~

目标同样不是：

~~~text
descriptor pointer equality
~~~

而是：

~~~text
same type semantics
same trait contract
cross-TU behavior remains valid
~~~

这样 Traits 才不是“只有 header demo 能用”的机制。

---

# 47. Callable Identity：函数地址也不是一个足够统一的答案

Callable 比 Type 更复杂，因为它可能有：

~~~text
canonical raw target
adapter
generator
capture
effects
properties
signature
~~~

所以 Callable identity 必须先问：

> “哪一种 dispatch 表示是 authoritative？”

当前实现已经区分：

~~~text
CANONICAL_RAW
ADAPTER
~~~

并明确：

~~~text
canonical-raw identity
    uses authoritative raw target across translation units

adapter identity
    uses adapter/generator pointers + capture bytes
~~~

## 47.1 为什么 canonical raw 可以跨 TU

如果两个 Translation Unit 各自产生 wrapper/adapter：

~~~text
wrapper A address != wrapper B address
~~~

但它们最终解析到同一个：

~~~text
authoritative raw C function
~~~

那么 semantic callable identity 不应该因为 wrapper 地址不同而失败。

当前测试已经覆盖：

~~~text
canonical callable identity across translation units by raw target
~~~

这会直接被：

~~~text
Graph structural equality
Optimizer duplicate detection
AOT Graph/Stage matching
Certificate checking
~~~

消费。

所以 callable identity 不是一个局部 helper。

它已经成为 compiler/control-plane correctness 的基础。

## 47.2 Capturing Callable 则必须把 Capture 纳入 identity

对于：

~~~text
bind(multiply, 10)
bind(multiply, 20)
~~~

raw/adapter code 可能相同，但 capture 不同。

因此它们不能被当成 same callable。

这说明 identity 的正确原则不是：

~~~text
always compare pointer
~~~

也不是：

~~~text
never compare pointer
~~~

而是：

> **根据 representation 的 semantic authority 定义 equality。**

---

# 48. Static Library / Shared Library：Duplicate Globals 不能成为语义事故

当前 CMeta CMake 有一个非常值得写进书里的工程决定。

对于 static CMeta archive：

~~~text
C_VISIBILITY_PRESET hidden
~~~

原因不是单纯“减少导出符号”。

注释明确指出：

~~~text
a static CMeta archive may be embedded by Core
and multiple bridge DSOs

keep each image's immutable descriptors/helpers local

type compatibility is semantic,
not address-based
~~~

这是一条非常成熟的 ABI 思路。

如果 semantic correctness依赖：

~~~text
process-wide unique descriptor address
~~~

那么同一个 static archive 被链接进两个 DSO 时，设计天然脆弱。

而当前方向是：

~~~text
duplicate representation objects may exist
      ↓
semantic identity still agrees
~~~

所以 symbol visibility 变成优化/封装问题，而不是 type semantics 的事实源。

---

# 49. Public Struct：Visible 不等于 Mutable，也不等于 Stable Bytes

C library 很容易出现一个误区：

~~~text
struct 在 public header
    ↓
所有 field 都属于 caller contract
~~~

这并不成立。

第十章已经看到 Graph 为了 introspection 保持 concrete IR；

Subscription / Actor 等 live execution owner 则使用 opaque handle。

第十二章应该进一步把 public field分成三类。

## 49.1 Stable contract fields

例如：

~~~text
configuration rows
status/result structs
documented method pointers
semantic enum values
~~~

caller 可以按照文档初始化/读取。

## 49.2 Read-only introspection

例如：

~~~text
Graph
Node
Edge
Subgraph
Plan input/output type
stats
~~~

可见是为了：

~~~text
diagnostics
verification
advanced tooling
~~~

不代表 caller 可以绕过 builder mutation。

## 49.3 Internal carrier

例如：

~~~text
void *impl
~~~

即使它在 public struct 中可见，也没有额外 semantic meaning。

不能：

~~~text
dereference
serialize
compare as identity
copy a live owner
use sizeof/offsetof as persistence protocol
~~~

这一点应该明确写进 ABI philosophy：

> **C visibility is not semantic ownership.**

---

# 50. Versioned Provider ABI：扩展 Struct 时必须保留 Admission Boundary

对于可扩展 provider/vtable，最危险的做法是：

~~~text
直接假设 caller 和 library 的 struct layout 完全同步
~~~

当前 CMeta data descriptor/provider 已经采用：

~~~text
struct_size
abi_version
~~~

这样的字段。

这使 checked facade 可以先验证：

~~~text
provider ABI version
minimum struct prefix size
storage type identity
ownership/layout contract
required operations
~~~

再使用 optional appended fields。

这种模式适合：

~~~text
descriptor
provider ops
plugin ABI
extension interface
~~~

但必须遵守：

1. 旧 prefix meaning 不能静默改变；
2. 新 field append 后要有 version/size admission；
3. optional capability 与 required capability 分开；
4. caller不能因为 field 当前存在就推断 future ABI；
5. enum/status numeric values若公开，也属于 ABI。

---

# 51. CFlow 的 SOVERSION：ABI Version 应该成为真实 Library Artifact

当前 CFlow library snapshot：

~~~text
library version = 4.1.0
SOVERSION = 4
~~~

Windows shared build还会把 ABI major写进输出名。

这一点很重要。

如果一个 library 对外暴露：

~~~text
public structs
enum values
function signatures
calling conventions
symbol names
ownership contracts
~~~

那么 ABI break 不能只藏在 Git history 里。

至少要有：

~~~text
library ABI major
package version
release compatibility policy
~~~

当然：

> **SOVERSION 本身不会自动让 ABI 稳定。**

它只是把 incompatible boundary 变得可表达。

真正 stability 仍然依赖 public API discipline 和 qualification。

---

# 52. Compile-time Configuration 也是 ABI 的一部分

CMeta 的 finite signature universe 和 CFlow 的 configured limits 都可能进入 public compilation surface。

例如 CFlow 当前把若干 Machine/Statechart limits作为 PUBLIC compile definitions导出：

~~~text
CFLOW_MACHINE_MAX_STATES
CFLOW_MACHINE_MAX_EVENTS
CFLOW_MACHINE_MAX_GUARDS
CFLOW_MACHINE_MAX_ACTIONS
CFLOW_MACHINE_MAX_TRANSITIONS
...
~~~

这意味着 consumer 编译看到的 public header configuration 必须与 library contract 一致。

同样，CMeta user relation/type lists属于 shared compile-time configuration。

文档明确要求：

> affected translation units 必须看到一致的 callable ABI/configuration。

所以 Multi-TU correctness 不只包括：

~~~text
same struct declaration
~~~

还包括：

~~~text
same finite signature universe
same compile-time configuration
same public feature/limit contract
~~~

如果不同 TU 使用不同 relation universe，却共同交换 callable/descriptor object，行为可能从 semantic bug 变成 ABI bug。

---

# 53. Header / Source Boundary：哪些 Meta 必须留在调用点

Modern C meta library不应该走向：

~~~text
everything header-only
~~~

也不应该走向：

~~~text
everything hidden in .c
~~~

正确边界取决于信息在哪里存在。

## 53.1 必须在 Header / Call Site 的内容

典型包括：

~~~text
_Generic selection
compile-time type assertion
finite macro specialization
typed wrapper generation
call-site C type inspection
~~~

因为 C compiler 只在调用点知道：

~~~text
actual static C type
~~~

## 53.2 应该放进 compiled C library 的内容

包括：

~~~text
container algorithms
Graph mutation/validation
Subscription runtime
Executor
Machine/Actor runtime
type identity comparison
optimizer
plan compiler
certificate checker
~~~

这些没有理由因为“Meta”而被复制到每个 Translation Unit。

因此：

> **header-only typed façade 不等于 header-only implementation。**

这也是控制代码膨胀、ABI、compile time 和 debug experience 的关键。

---

# 54. Generated Artifact Ownership：一个事实不能既由 Lean 又由人维护

第十一章已经看到：

~~~text
builtin_signature_manifest.h
builtin_operator_policy.h
machine_schema.h
~~~

这些 C header 由 formal source/generator 产生。

工程规则必须非常严格：

~~~text
formal model
    = authoritative source

generated header
    = checked-in build artifact

manual edit generated header
    = forbidden
~~~

普通 consumer build：

~~~text
does not require Lean
~~~

CI / semantic development：

~~~text
generator --check
~~~

验证 artifact 没有 drift。

这同时解决：

~~~text
reproducible package
ordinary C consumer
single source of truth
reviewable generated diff
~~~

四个问题。

---

# 55. Install / Export：源码树里能 link 远远不够

当前 Salts 已经使用标准 CMake package/export boundary：

~~~text
SaltsConfig.cmake
SaltsConfigVersion.cmake
SaltsTargets.cmake
namespace Salts::
~~~

CMeta / CFlow 分别 export 为：

~~~text
Salts::CMeta
Salts::CFlow
~~~

并安装：

~~~text
public headers
library/archive/runtime artifact
package config
target export
~~~

consumer 的目标形态是：

~~~cmake
find_package(Salts CONFIG REQUIRED)

target_link_libraries(app PRIVATE
    Salts::CMeta
    Salts::CFlow)
~~~

这比：

~~~text
add_subdirectory(path/to/salts)
include_directories(source/tree)
link random .a file
~~~

重要得多。

因为 install boundary 会立刻暴露：

~~~text
missing public dependency
wrong include interface
private header leak
missing transitive target
wrong compile definition export
bad symbol visibility
source-tree-only path
~~~

## 55.1 CFlow 的 public dependency 必须通过 target contract 导出

当前 CFlow link contract包含：

~~~text
PUBLIC
    Salts::CMeta
    Salts::NativeIO
    Salts::Platform

PRIVATE
    Salts::Concurrency
~~~

这不是 CMake aesthetics。

它表达：

> external consumer 使用 CFlow public headers / symbols 时，哪些 dependency 是 exported contract，哪些只是 implementation detail。

如果 PRIVATE dependency 的 symbol 出现在 public ABI，却没有被 export，source-tree build 可能绿，而 installed consumer link 会失败。

## 55.2 Public header install 也必须排除 private headers

当前 CFlow install：

~~~text
install include/cflow/*.h
~~~

同时显式排除：

~~~text
plan_internal.h
relation_exec.h
~~~

这条边界很重要：

> **一个 header 放在仓库里，不代表它属于 SDK。**

如果 public header 偷偷 include private header，installed build 会最快把问题暴露出来。

---

# 56. Installed Consumer Qualification：最接近真实用户的 Gate

本书建议把 installed-consumer test 当成正式 gate，而不是 release 前手工冒烟。

推荐流程：

~~~text
clean source checkout
    ↓
configure/build/test Salts
    ↓
install into empty prefix
    ↓
new independent consumer source tree
    ↓
find_package(Salts CONFIG REQUIRED)
    ↓
link only exported Salts::* targets
    ↓
include only installed headers
    ↓
build
    ↓
run
~~~

consumer 至少覆盖：

~~~text
CMeta type/traits/callable
CFlow Graph/Stream
Multi-TU use
static build
shared build where supported
C and C++ header compatibility
~~~

关键规则：

~~~text
no source-tree include path
no build-tree target
no undeclared private library
no generated source file copied manually
~~~

只有这样，才能证明：

> **“可安装 library”不是文档里的愿望，而是用户真正能拿到的 SDK contract。**

---

# 57. Multi-TU Qualification 应该故意制造 Representation 不同

一个弱 Multi-TU test 只是：

~~~text
foo.c calls bar.c
~~~

这不足以验证 Meta identity。

真正有效的 test 要故意让两个 TU 各自拥有独立 representation。

## 57.1 Type Identity Test

~~~text
TU A:
    independently constructs Pair<A,B> identity

TU B:
    independently constructs Pair<A,B> identity

assert:
    addresses differ
    constructors may differ
    semantic equality true
~~~

当前 CMeta 已经有这种 peer test。

## 57.2 Callable Identity Test

~~~text
TU A:
    canonical callable wrapper A

TU B:
    canonical callable wrapper B

assert:
    wrapper representation can differ
    authoritative raw target identity agrees
~~~

当前 tests 同样覆盖这一点。

## 57.3 Generated Configuration Test

还应覆盖：

~~~text
shared configuration header
    included consistently in TU A/TU B

callable signature ABI
    agrees across both
~~~

并增加 negative compile/link test：

~~~text
intentionally inconsistent configuration
    → fail fast
~~~

如果工具链无法可靠诊断，则至少让这种状态成为明确 unsupported contract，而不是 runtime 猜测。

---

# 58. Cross-Compiler：Core Semantics 不能建立在偶然扩展上

CMeta 可以使用：

~~~text
C11 _Generic
preprocessor
_Static_assert
standard alignment/type rules
~~~

并针对 MSVC 的 conforming preprocessor mode做必要 compiler option。

但书里需要保持一条原则：

> **Compiler extension 可以优化 implementation，但不能成为 semantic model 唯一基础。**

例如：

~~~text
GNU statement expression
typeof extension
compiler-specific section trick
~~~

可以做 optional fast path；

核心 type relation / callable semantics / ABI contract 应该仍能用支持目标 compiler 的正式机制表达。

Cross-compiler CI 的意义不是：

~~~text
“语法都能编译”
~~~

而是验证：

~~~text
same declared semantics
same ownership/error contract
same installed API shape
~~~

在目标 compiler family 中保持成立。

---

# 59. ABI Qualification：不要只比较 sizeof(struct)

ABI test 的层次至少有四类。

## 59.1 Compile ABI

~~~text
public headers compile as C11
public headers compile from supported C++ mode
macros do not depend on include accident
generated headers self-consistent
~~~

当前 CFlow 已有 public/header C++ compile tests，这类 gate应持续扩展。

## 59.2 Link ABI

~~~text
public symbol exists
calling convention matches
transitive dependency exported
static/shared consumer links
~~~

这是 installed consumer才能真正验证的部分。

## 59.3 Semantic ABI

即使 function signature没变，如果：

~~~text
FULL suddenly starts dropping
CLOSED becomes retryable
Actor stale ref becomes INVALID_ARGUMENT
Graph mutation stops changing version
~~~

也属于 breaking behavior。

所以：

> **Status meaning、ownership、lifecycle、ordering、fallback 都属于 semantic ABI。**

## 59.4 Data ABI

对于真正承诺跨 binary boundary 的 struct：

~~~text
prefix fields
version
struct_size
enum values
alignment
ownership of pointed data
~~~

才需要被正式版本化。

而 opaque owner：

~~~text
void *impl
~~~

就是为了避免把内部 layout变成 ABI。

---

# 60. Fail-fast Across Boundaries：错误越晚越昂贵

全书反复出现的 fail-fast，在工程边界可以排列成：

~~~text
compile-time
    ↓
build-time
    ↓
install/package-time
    ↓
link-time
    ↓
admission-time
    ↓
execution-time
~~~

原则是：

> **能在更早层发现，就不要把同一个错误留到更晚层。**

例如：

~~~text
unsupported TypeFunction row
    → compile-time

invalid Machine schema
    → build-time

generated manifest drift
    → CI/generator check

missing public link dependency
    → installed consumer link

wrong Event payload
    → admission

I/O failure
    → execution
~~~

把所有错误都变成：

~~~text
runtime error string
~~~

不叫“API 简单”。

那只是把诊断成本推给用户。

---

# 61. What We Learned

第十二章把前面所有“高级”能力重新压回普通 C 工程现实。

一个 Modern C abstraction 真正成熟，需要同时成立：

~~~text
semantic identity
    does not depend on representation address

Multi-TU
    sees compatible finite configuration

public ABI
    separates stable/read-only/internal fields

generated artifacts
    have one authority

ordinary build
    does not require Lean

static/shared libraries
    do not rely on duplicate-global coincidence

install/export
    publishes real dependency contracts

external consumer
    builds only from installed SDK

cross-compiler
    preserves core semantics

status/ownership/lifecycle
    are treated as semantic ABI
~~~

当前 Salts 已经有很多真实工程基础：

~~~text
structural type identity
cross-TU identity tests
cross-TU callable tests
CMake install/export
Salts::* imported targets
CFlow SOVERSION
public/private install headers
generated-header CI checks
public-header compile checks
~~~

而成熟 qualification还应该持续把：

~~~text
independent installed consumer
static/shared matrix
negative ABI/config tests
platform/toolchain matrix
release compatibility
~~~

当成正式 gate。

Lean 在这一章的位置也变得非常清楚。

它可以帮助定义：

~~~text
semantic identity
finite schema
generated manifest
protocol invariants
~~~

但：

~~~text
linker
loader
symbol visibility
CMake package export
compiler ABI
shared-library resolution
~~~

必须用真实工具链验证。

这不是形式化能力不足。

而是：

> **正确的问题应该由正确的证据回答。**

到这里，Part IV 的两章形成完整可信边界：

~~~text
Chapter 11:
    semantic/proof trusted boundary

Chapter 12:
    binary/toolchain/package trusted boundary
~~~

接下来最后一部分不再继续增加基础机制。

我们开始回答：

> **已经拥有 Type、Callable、Graph、Reactive、Machine、Actor、Lean proof 与稳定 library boundary 后，这些 primitive 怎样组合出 Serialization、RPC、Workflow 等真正的高级应用？**


