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

## 1. 单 Translation Unit 会掩盖很多问题

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

## 2. 地址只是实现位置，不是语义身份

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

## 3. Semantic Type Identity

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

## 4. Semantic Identity 对 Generic 尤其重要

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

## 5. Identity 与 Descriptor 的职责不同

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

## 6. 这一步也是 ABI 设计的一部分

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

## 7. Header 和 Source 的边界必须重新考虑

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

## 8. 从工程原则进入资格验证

前七节已经给出本章的根问题：单 Translation Unit 会掩盖 identity 与 ABI 问题；地址不是语义身份；descriptor、generic relation 与 public representation 必须有明确的 semantic authority；而 header/source 边界不能因为使用宏就退化成 header-only everything。

后半部分因此不再逐项重复 naming、module ownership、fail-fast、cross-compiler、installed header 等一般原则，而是把这些原则放进真实工程资格验证：structural type identity、callable identity、static/shared image、versioned provider ABI、compile-time configuration、generated artifact ownership、CMake install/export、independent consumer、Multi-TU、cross-compiler 与 ABI gate。

凡是当前 snapshot 已有真实测试或 package contract 的地方，本章明确指出证据；尚未完成的 release/platform qualification 只写成应建立的 gate，而不写成已经成立的保证。

---

## 9. Case Study：为什么 Descriptor Address 不能成为 Type Identity

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

## 9.1 本版 CMeta 实现 已经把 Identity 从 Descriptor 中显式分离

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

## 9.2 Structural identity 已经有真实 Multi-TU test

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

## 9.3 Custom Trait Descriptor 也要跨 TU 保持语义一致

本版 CMeta 实现 tests 还覆盖：

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

## 10. Callable Identity：函数地址也不是一个足够统一的答案

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

## 10.1 为什么 canonical raw 可以跨 TU

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

## 10.2 Capturing Callable 则必须把 Capture 纳入 identity

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

## 11. Static Library / Shared Library：Duplicate Globals 不能成为语义事故

本版 CMeta 实现 CMake 有一个非常值得写进书里的工程决定。

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

## 12. Public Struct：Visible 不等于 Mutable，也不等于 Stable Bytes

C library 很容易出现一个误区：

~~~text
struct 在 public header
    ↓
所有 field 都属于 caller contract
~~~

这并不成立。

第七章已经看到 Graph 为了 introspection 保持 concrete IR；

Subscription / Actor 等 live execution owner 则使用 opaque handle。

第十二章应该进一步把 public field分成三类。

## 12.1 Stable contract fields

例如：

~~~text
configuration rows
status/result structs
documented method pointers
semantic enum values
~~~

caller 可以按照文档初始化/读取。

## 12.2 Read-only introspection

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

## 12.3 Internal carrier

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

## 13. Versioned Provider ABI：扩展 Struct 时必须保留 Admission Boundary

对于可扩展 provider/vtable，最危险的做法是：

~~~text
直接假设 caller 和 library 的 struct layout 完全同步
~~~

本版 CMeta 实现 data descriptor/provider 已经采用：

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

## 14. CFlow 的 SOVERSION：ABI Version 应该成为真实 Library Artifact

本版 CFlow 实现 library snapshot：

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

## 15. Compile-time Configuration 也是 ABI 的一部分

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

## 16. Header / Source Boundary：哪些 Meta 必须留在调用点

Modern C meta library不应该走向：

~~~text
everything header-only
~~~

也不应该走向：

~~~text
everything hidden in .c
~~~

正确边界取决于信息在哪里存在。

## 16.1 必须在 Header / Call Site 的内容

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

## 16.2 应该放进 compiled C library 的内容

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

## 17. Generated Artifact Ownership：一个事实不能既由 Lean 又由人维护

第六章已经看到：

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

## 18. Install / Export：源码树里能 link 远远不够

本版 Salts 快照 已经使用标准 CMake package/export boundary：

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

## 18.1 CFlow 的 public dependency 必须通过 target contract 导出

本版 CFlow 实现 link contract包含：

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

## 18.2 Public header install 也必须排除 private headers

本版 CFlow 实现 install：

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

## 19. Installed Consumer Qualification：最接近真实用户的 Gate

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

## 20. Multi-TU Qualification 应该故意制造 Representation 不同

一个弱 Multi-TU test 只是：

~~~text
foo.c calls bar.c
~~~

这不足以验证 Meta identity。

真正有效的 test 要故意让两个 TU 各自拥有独立 representation。

## 20.1 Type Identity Test

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

本版 CMeta 实现 已经有这种 peer test。

## 20.2 Callable Identity Test

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

## 20.3 Generated Configuration Test

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

## 21. Cross-Compiler：Core Semantics 不能建立在偶然扩展上

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

## 22. ABI Qualification：不要只比较 sizeof(struct)

ABI test 的层次至少有四类。

## 22.1 Compile ABI

~~~text
public headers compile as C11
public headers compile from supported C++ mode
macros do not depend on include accident
generated headers self-consistent
~~~

本版 CFlow 实现 已有 public/header C++ compile tests，这类 gate应持续扩展。

## 22.2 Link ABI

~~~text
public symbol exists
calling convention matches
transitive dependency exported
static/shared consumer links
~~~

这是 installed consumer才能真正验证的部分。

## 22.3 Semantic ABI

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

## 22.4 Data ABI

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

## 23. Fail-fast Across Boundaries：错误越晚越昂贵

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

## 24. What We Learned

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

本版 Salts 快照 已经有很多真实工程基础：

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


