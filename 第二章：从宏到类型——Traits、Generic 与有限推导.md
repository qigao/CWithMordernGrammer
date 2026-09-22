# 第二章：从宏到类型——Traits、Generic 与有限推导


> **本章路线**
>
> 第一章解决的是“如何只维护一份重复事实”。这一章开始处理更困难的问题：**当事实之间存在类型关系时，怎样让 C 在不拥有完整模板语言和 Runtime reflection 的情况下表达、检查和推导这些关系？**
>
> ~~~text
> Plain C types
>    → Type Descriptor
>    → Traits / Capability
>    → Generic Application
>    → Semantic Identity
>    → Finite Relation
>    → Inference
>    → Lean-checked Semantic Model
>    → Ordinary C Declarations
> ~~~
>
> 本章是 Lean 第一次真正进入全书主线的地方。但 Lean 的目标不是证明“宏很聪明”，而是验证**有限类型宇宙中的关系是否定义良好**。

上一章最后停在一个非常关键的位置。

最开始，我们只是希望：

```text
少写重复代码
```

于是使用宏。

后来，宏不只复用代码，还开始复用：

```text
类型列表
字段列表
枚举列表
函数列表
```

再后来，为了不让不同模块反复实现：

```text
FOR_EACH
NARG
CAT
UNPAREN
```

又开始把宏本身正规化。

走到这里以后，真正限制下一步能力的已经不是：

> 宏能不能生成更多代码？

而是：

> **宏生成代码的时候，能不能知道自己正在处理什么类型？**

如果答案仍然只是：

```text
这是一个叫 INT 的 token
```

那么系统始终只能停留在文本层面。

要继续向前，就必须把：

```text
token
```

变成：

```text
type information
```

---

## 1. 类型信息为什么重要

假设我们有：

```c
int
double
User
```

如果只是为了生成三套函数：

```c
DEFINE(int)
DEFINE(double)
DEFINE(User)
```

知道它们的名字就够了。

但真实库很快会问更多问题。

例如一个 Generic 容器：

```text
Vec<T>
```

需要知道：

```text
T 多大？
T 是否可以直接 memcpy？
T 是否需要 destroy？
```

HashMap 需要知道：

```text
K 是否能 hash？
K 是否能 equal？
```

排序结构需要：

```text
K 是否能 compare？
```

一个 callback 需要知道：

```text
输入 T
输出 U
```

一个 serializer 需要知道：

```text
字段是 integer、float、string 还是 struct？
```

这些都已经不是：

```text
token 拼接
```

能够解决的问题。

因此类型必须逐渐变成一种：

> **可以被程序消费的 metadata。**

---

## 2. 从 type token 到 type descriptor

最自然的第一步，是为每一种类型建立一个 descriptor。

例如概念上：

```c
typedef struct type_desc {
    const char *name;
    size_t size;
    size_t align;
    type_kind kind;
} type_desc;
```

那么：

```text
int
```

不再只是一个 C keyword。

还可以对应：

```text
name  = "int"
size  = sizeof(int)
align = _Alignof(int)
kind  = INTEGER
```

同样：

```text
double
```

可以对应：

```text
name  = "double"
kind  = FLOAT
```

而用户定义的：

```text
User
```

则可能是：

```text
kind = OBJECT
```

这样，类型就第一次从：

```text
compiler 内部知道
```

变成：

```text
程序自己也知道
```

---

## 3. `_Generic` 让 C 类型和 descriptor 可以真正连接起来

C11 的 `_Generic` 提供了一个非常重要的桥梁。

例如：

```c
_Generic((value),
    int:    &type_int,
    double: &type_double)
```

这意味着：

```text
C compiler 的类型系统
        ↓
有限选择
        ↓
我们的 metadata
```

可以连接起来。

所以如果已经有：

```text
TYPE_LIST
```

就可以从同一份事实生成：

```text
descriptor declarations
descriptor registry
_Generic associations
```

于是：

```text
type list
```

不再只是代码生成输入。

它变成了：

> **有限类型宇宙。**

---

## 4. 为什么是“有限类型宇宙”

这里其实出现了一个很重要的设计选择。

我们并没有试图做到：

```text
任意 C 类型
都自动 reflection
```

因为 C11 本身并不提供这种能力。

更合理的模型是：

```text
程序明确注册一组类型
        ↓
这组类型可以被描述
        ↓
可以参与 Generic / Callable / Inference
```

也就是：

```text
Known Types
```

而不是：

```text
All Possible C Types
```

这个限制后来变得非常重要。

因为只要类型集合是有限的：

```text
就可以枚举
可以生成
可以验证
可以推导
```

这也是整个设计后来一直坚持 `finite` 的根本原因之一。

---

## 5. 类型不仅要知道“是什么”，还要知道“能做什么”

一个 descriptor 只有：

```text
name
size
align
kind
```

仍然不够。

例如：

```text
User
```

可能支持：

```text
equal
hash
copy
destroy
```

但另一个类型：

```text
FileHandle
```

可能：

```text
不能 copy
必须 destroy
```

所以真正有用的问题不是：

> 这是哪个类型？

而是：

> **这个类型具有什么能力？**

于是开始引入：

```text
Traits
```

---

## 6. Traits：把行为能力和类型连接起来

例如：

```c
Traits(User,
    (equal, user_equal),
    (hash, user_hash),
    (copy, user_copy),
    (destroy, user_destroy)
);
```

这并不是在模仿 class。

它表达的是：

```text
User supports Equal
User supports Hash
User supports Copy
User supports Destroy
```

于是一个算法可以不再依赖具体类型：

```text
if type == User ...
```

而是依赖能力：

```text
requires HASH + EQUAL
```

这就是一个很大的变化。

---

## 7. 从“具体类型”转向“能力约束”

例如 HashMap。

如果没有 Traits，可能只能写：

```text
HashMapInt
HashMapString
HashMapUser
```

然后每种 key 类型单独处理。

但真正的算法要求其实只有：

```text
Key must support:
    hash
    equal
```

所以 Generic container 需要表达的不是：

```text
我只支持 int / string
```

而是：

```text
只要 K 满足 HASH + EQUAL 就可以
```

同理：

```text
Tree<K>
```

真正要求：

```text
COMPARE
```

而不是：

```text
某几个固定类型
```

这已经开始接近 C++：

```text
type traits
concept
```

所解决的问题。

但实现仍然是普通 C metadata。

---

## 8. Traits 为什么必须和 descriptor 结合

如果 Traits 单独维护：

```text
Type 表一份
Traits 表一份
```

又会回到最开始的问题：

> 同一个知识被维护成两份。

所以更自然的是：

```text
type descriptor
    ↓
traits
```

也就是：

```text
Type
    knows
Capabilities
```

这样任何拿到：

```text
const type_desc *
```

的代码，都可以进一步问：

```text
它能不能 hash？
能不能 compare？
能不能 copy？
```

这让很多运行时协议第一次变得真正通用。

---

## 9. 然后自然出现 Generic

当类型和 Traits 已经存在以后，另一个长期存在的 C 问题会变得非常明显：

> **怎样写 Generic？**

C++ 有：

```cpp
std::vector<int>
std::vector<double>
std::map<int, User>
```

C 没有语言级 template。

传统做法通常有几种：

```text
void *
宏生成
手写 typed wrapper
外部代码生成
```

既然我们已经有：

```text
Type
Traits
Descriptor
```

那么最自然的下一步就是：

> 让一个 Generic kind 根据这些类型信息生成具体 C 类型。

---

## 10. `typed(...)` 的核心并不是语法，而是统一 Generic 路由

例如：

```c
typed(Vec, IntVec, int);
typed(Option, MaybeUser, User);
typed(Pair, Entry, Key, Value);
```

从表面上看，它有一点像：

```cpp
Vec<int>
Option<User>
Pair<Key, Value>
```

但实现思路完全不同。

它不是一个通用 template evaluator。

而只是：

```text
kind
    +
type arguments
    ↓
找到对应 generator
    ↓
生成具体 C 类型
```

也就是：

```text
Vec
    ↓
Vec Generator

Option
    ↓
Option Generator

Pair
    ↓
Pair Generator
```

Generic 是：

```text
registered
finite
explicit
```

的。

---

## 11. Generic 的真正意义是“统一生成模式”

在没有统一入口之前，不同库可能分别提供：

```text
DECLARE_VEC
DECLARE_LIST
DECLARE_MAP
OPTION_DEFINE
PAIR_DEFINE
```

这些宏本身可能都很好用。

但调用方式、metadata 生成方式、descriptor 生成方式都会逐渐不同。

统一成：

```c
typed(kind, name, ...)
```

以后，真正被统一的是：

```text
Generic Instantiation Protocol
```

而不是把所有 Generic 算法塞进一个库。

例如：

```text
Vec algorithm
```

仍然属于容器库。

Meta 层只是知道：

```text
Vec 是一个 Generic constructor
```

以及：

```text
Vec<int>
```

是一个具体 application。

---

## 12. Generic Application 自己也应该有身份

如果：

```text
Vec<int>
```

和：

```text
Vec<double>
```

只是两个字符串名字：

```text
"IntVec"
"DoubleVec"
```

那么 Generic 信息其实丢掉了。

更有意义的表示应该是：

```text
Vec<int>

constructor = Vec
arguments   = [int]
```

而：

```text
Map<int, User>

constructor = Map
arguments   = [int, User]
```

这样类型身份可以是结构化的。

---

## 13. 为什么 descriptor 地址不能作为 type identity

做到 Generic 以后，很快会碰到一个真实工程问题：

如果 descriptor 是 header 中生成的：

```c
static const type_desc ...
```

那么不同 translation unit 中可能各自拥有一份。

例如：

```text
TU A
Vec<int> descriptor @ 0x1000

TU B
Vec<int> descriptor @ 0x9000
```

地址不同。

但类型显然应该相同。

因此：

```text
pointer equality
```

不能继续被当成：

```text
type equality
```

需要引入：

```text
semantic type identity
```

也就是：

```text
Atom:
    int

Generic:
    Vec<int>

Pointer:
    int *
```

通过语义结构比较，而不是通过 descriptor 地址比较。

---

## 14. 这一步让 Multi-TU 和真正的库边界成为可能

这看起来只是一个小细节。

其实它标志着整个系统开始从：

```text
单文件宏实验
```

进入：

```text
真正 library ABI
```

因为真实 C 项目一定有：

```text
多个 .c 文件
多个静态库
动态库
插件
安装头文件
```

如果 type identity 依赖：

```text
某一个 static descriptor 的地址
```

那么跨模块行为很快就会失效。

所以：

> **Semantic identity 是从“宏技巧”走向“工程级类型系统”的关键一步。**

---

## 15. 类型有了以后，下一步自然是 Function Type

数据类型已经能表示：

```text
int
double
User
Vec<int>
```

那么函数类型也可以表示：

```text
int -> double
User -> bool
long × long -> long
```

于是 callback 也不再只是：

```text
function pointer
```

而开始变成：

```text
typed callable
```

例如：

```text
square
    int -> long
```

或者：

```text
enabled
    User -> bool
```

这会为后面的 Lambda、Bind 和 Graph 提供基础。

但在进入函数之前，还会遇到一个更基础的问题：

> **类型之间能不能计算？**

---

## 16. 从“描述类型”走向“推导类型”

例如：

```text
int + int
```

结果应该是：

```text
int
```

而：

```text
int + double
```

结果应该是：

```text
double
```

如果我们已经有：

```text
type token
type descriptor
```

那么完全可以把这种关系写成：

```text
(int, int)       -> int
(int, double)    -> double
(double, int)    -> double
(double, double) -> double
```

这意味着系统开始从：

```text
Describe
```

进入：

```text
Derive
```

---

## 17. 一开始完全可以继续写 specialized macro

例如：

```c
#define COMMON_int_int int
#define COMMON_int_double double
#define COMMON_double_int double
```

这当然能工作。

但很快会发现：

```text
CommonType
TypeRank
Hashable
CallableSignature
OperatorPolicy
```

都在实现：

```text
输入
    ↓
有限映射
    ↓
输出
```

于是又出现了熟悉的问题：

> **同一种推导模式正在重复。**

所以它应该继续正规化。

---

## 18. TypeFunction：把类型关系变成有限函数

可以把：

```text
(A, B) -> C
```

这种规则描述成：

```c
TypeFunction(CommonType,
    (int, int, int),
    (int, double, double),
    (double, int, double),
    (double, double, double)
);
```

然后：

```c
typedef TypeEval(CommonType, int, double) Result;
```

得到：

```text
Result = double
```

这里并没有运行一个 C++ template interpreter。

它只是把：

```text
有限 relation
```

lower 成：

```text
C compiler 可以解析的 declaration
```

---

## 19. ValueFunction 与 Predicate

同样：

```text
Type -> integer
```

可以表示：

```c
ValueFunction(TypeRank,
    (int, 1),
    (double, 2)
);
```

于是：

```c
enum {
    rank = ValueEval(TypeRank, double)
};
```

而：

```text
Type -> bool
```

自然可以变成：

```c
Predicate(Hashable,
    (int, 1),
    (Opaque, 0)
);
```

然后：

```c
Require(Hashable, int);
```

于是第一次可以比较自然地表达：

```text
compile-time property
compile-time requirement
```

---

## 20. 为什么没有 Default

一个非常重要的选择是：

```text
missing mapping
```

不自动选择：

```text
default
```

如果：

```text
CommonType(User, Socket)
```

没有定义，那么最安全的行为不是：

```text
猜一个结果
```

而是：

```text
compile error
```

同样，如果两个规则冲突：

```text
(A,B) -> C
(A,B) -> D
```

应该直接失败。

这使有限推导非常适合 C：

```text
显式
确定
fail-fast
```

---

## 21. 为什么这里仍然坚持 finite

走到推导这一步以后，非常容易产生诱惑：

```text
既然已经有 TypeFunction
是不是继续做递归模板？
```

理论上当然可以继续增强。

但这会快速破坏最开始的目标。

最初所有抽象都是为了：

```text
降低复杂度
```

如果现在为了：

```text
更强的 compile-time computation
```

造出一个复杂到无法理解的宏语言，就本末倒置了。

所以更合理的原则仍然是：

```text
只表示工程中实际存在的有限关系
```

例如：

```text
1~3 个输入
有限 row
显式 mapping
```

而不是：

```text
任意 recursion
任意 template specialization
```

---

## 22. 有限系统带来一个很大的额外收益：可以验证

只要：

```text
Type Universe
Generic Constructors
Callable Signatures
Relations
```

都是有限集合，就可以开始问：

```text
有没有重复？
有没有引用不存在的类型？
关系是否闭合？
某个 operator 是否覆盖了所有允许 signature？
```

这些问题比：

```text
宏展开是否正确
```

更高一层。

它们已经接近：

```text
formal model
```

---

## 23. 也正是在这里，Lean 开始变得有价值

一开始写宏的时候，引入 theorem prover 显然是没有必要的。

但当系统已经有：

```text
Finite Types
Finite Relations
Generic Identity
Function Signature
```

以后，Lean 就开始非常合适。

因为这些东西本身就是：

```text
有限
结构化
数学关系明确
```

的。

例如可以在 Lean 中描述：

```text
Type
Unary Relation
Binary Relation
Generator Relation
```

然后验证：

```text
没有重复
引用类型存在
关系格式正确
```

再把已经验证的 manifest 生成回：

```text
C header
```

---

## 24. 这时我们才真正决定把它作为一个独立系统

走到这个阶段以后，已经不再只是：

```text
一些宏工具
```

而是逐渐拥有：

```text
PP primitives
Schema
Type
Traits
Generic
Identity
Finite Relation
Compile-time Evaluation
```

它们共同解决的是一个越来越清楚的问题：

> **怎样让 C 在保持普通 C 编译和执行模型的情况下，拥有有限的类型化元编程能力。**

这时才有必要把这些机制正式组织成一个独立库。

这个库最终被命名为：

## CMeta

也就是：

```text
C
+
Meta
```

---

## 25. 为什么叫 Meta，而不是 Macro Library

因为它已经不只是：

```text
生成几段代码
```

而开始能够描述：

```text
类型是什么
类型能做什么
Generic 是什么
函数签名是什么
类型之间有什么关系
哪些关系可以在编译期推导
```

换句话说：

```text
Macro
```

只是实现技术的一部分。

真正形成的能力是：

```text
Compile-time Metadata
+
Type Relations
+
Code Generation
```

所以叫 Meta 更准确。

---

## 26. 它和 C++ Template 很像，但目标不同

这时已经能够做一些很像 C++ template/metaprogramming 的事情：

```text
Generic
Traits
Type Selection
Compile-time Function
Predicate
```

但目标并不是复制 C++。

C++ template 的优势是：

```text
强大
通用
语言级
```

这里追求的是：

```text
有限
明确
严格 C11
跨编译器
生成结果简单
```

可以理解成：

> **只取 Meta Programming 中对于 C 工程最有价值的一部分。**

---

## 27. 最终执行仍然应该是普通 C

这一点非常重要。

例如：

```text
typed(Vec, IntVec, int)
```

最终产生的应该是：

```text
真实 C type
+
static inline wrapper
+
metadata
```

容器真正执行：

```text
push_back
reserve
destroy
```

仍然是普通 C 算法。

TypeFunction 最终产生：

```text
typedef / enum / static assertion
```

而不是 runtime evaluator。

Lean 最终生成：

```text
普通 C header
```

普通 build 也不需要 Lean。

所以完整路线始终是：

```text
Meta
    ↓
提前知道更多
    ↓
提前生成更多
    ↓
运行时反而更简单
```

---

## 28. 从这一章开始，系统真正拥有了“类型”

可以把前两章的发展压缩成：

```text
第一阶段

C Code
  ↓
Macro Reuse
  ↓
Shared Facts
  ↓
Schema


第二阶段

Schema
  ↓
Type Metadata
  ↓
Traits
  ↓
Generic
  ↓
Type Identity
  ↓
Finite Relation
  ↓
Inference
  ↓
CMeta
```

而下一步将发生另一次很重要的跨越：

> **既然数据可以拥有类型，那么函数本身能不能也变成有类型、有语义、可以被保存和组合的数据对象？**

这将带来：

```text
Typed Callback
Callable
Lambda
Bind
Generator
Effects
Properties
```

也会成为后面 Graph 和 CFlow 出现的直接基础。

## 29. Semantic Contract：从“类型描述”到“类型关系”

这一章真正增加的不是更多语法，而是一组比第一章更强的 semantic contract。

### 29.1 Known Types，而不是 All C Types

系统只对显式进入类型宇宙的类型做承诺。

~~~text
C language types
      ⊃
Known Types
~~~

这不是缺陷，而是一个关键工程选择。

只有 Known Types 才参与：

~~~text
descriptor
traits
generic identity
type relation
inference
verification
~~~

因此“未知类型”必须保持未知，而不是通过 silent fallback 猜测一个结果。

### 29.2 Type Identity 不等于 Descriptor Address

如果两个 Translation Unit 都描述 Vec<int>，它们可以拥有不同 descriptor object：

~~~text
TU A: descriptor @ A
TU B: descriptor @ B
~~~

但它们必须拥有同一个：

~~~text
semantic type identity
~~~

所以必须明确：

> **representation identity 与 semantic identity 是两个不同概念。**

这条规则以后会直接进入 Multi-TU、ABI、Plugin 和 Serialization。

### 29.3 Generic Identity 是结构，而不是字符串昵称

概念上：

~~~text
Vec<int>
=
constructor: Vec
arguments: [int]
~~~

而不是：

~~~text
"IntVec"
~~~

字符串可以作为名称或诊断信息，但不能替代结构化语义。

### 29.4 TypeFunction 首先是有限 relation

例如：

~~~text
CommonType(int, int)       = int
CommonType(int, double)    = double
CommonType(double, int)    = double
CommonType(double, double) = double
~~~

真正需要的核心性质并不是“宏可以展开”，而是：

1. 同一个 admissible input 不能对应两个冲突 output；
2. relation 中引用的 type 必须存在；
3. 如果某 relation 宣称覆盖一个 domain，那么这个 domain 必须完整；
4. 如果设计本来就是 partial relation，domain 之外必须明确失败。

最后一点尤其重要。

本章已经明确选择：

> **No Default.**

所以不应该把 theorem 写成：

~~~text
forall input, exists output
~~~

除非某一个具体 TypeFunction 明确声明自己是 total。

更准确的语义是：

~~~text
functional on admitted inputs
+
coverage on declared domain
+
explicit failure outside domain
~~~

这就是“有限、显式、按需”第一次真正成为数学约束。

---

## 30. Lean：哪些东西值得真正证明

到这一章，Lean 开始有真实价值，因为问题已经从文本生成升级为有限结构上的数学关系。

可以把 proof obligation 分成四类。

### 30.1 Well-formed type universe

例如：

~~~text
registered semantic identities are unique
generic constructor references exist
generic arguments reference known types
trait references are well formed
~~~

这类 theorem 验证的是：

> 类型世界本身没有自相矛盾。

### 30.2 Functional relation

对于 TypeFunction：

~~~text
if R a b = x
and R a b = y
then x = y
~~~

换句话说，一个 admissible input 不能推导出两个冲突类型。

这比“测试了几个 TypeEval”更强，因为它针对整个有限 relation。

### 30.3 Declared-domain coverage

如果一个 operator 声明：

~~~text
domain = Numeric × Numeric
~~~

那么可以验证：

~~~text
forall input in declared domain,
exactly one output exists
~~~

但对于 intentionally partial relation，则不应该强行证明 totality。

这使“没有 Default”从 API 风格变成清晰 semantic boundary。

### 30.4 Generic semantic identity

我们希望表达类似：

~~~text
same constructor
+
same semantic arguments
→
same semantic generic type
~~~

以及不同 semantic structure 不应该因为 descriptor pointer、symbol location 或 TU 不同而被误判。

这类模型会直接帮助后面的 ABI / Multi-TU 设计。

### 30.5 Lean 不证明什么

Lean 不应该被用来声称：

- 某个 compiler 一定按照特定 ABI layout；
- linker 一定导出某个 symbol；
- dynamic library loader 一定具有某种平台行为；
- hash-based runtime ID 永远不会碰撞，除非模型真的建立并证明了该性质；
- 一个 trait 声明的 PURE 就自动意味着函数在数学上纯。

特别是最后一点：

> **Trait / Property 是 claim；Semantic Law 才可能成为 theorem 的前提或结论。**

这一区分会在 Callable 和 Optimizer 章节反复出现。

---

## 31. C Implementation：证明最终必须落回普通 C

形式模型最终必须连接到真正的 C representation。

概念上，一个 type descriptor 可能包含：

~~~c
typedef struct type_desc {
    const char *name;
    size_t size;
    size_t align;
    type_kind kind;

    /* semantic identity is not object address */
    type_identity identity;
} type_desc;
~~~

这里重要的不是字段名字，而是 ownership contract：

~~~text
descriptor object
    ≠
semantic type itself
~~~

Generic 也应该保留结构信息：

~~~text
constructor
arguments
semantic identity
~~~

而不是只生成一个失去来源信息的别名。

TypeFunction 最终则应 lower 成编译器能够直接消费的事实：

~~~text
typedef
enum
_Generic route
static assertion
generated declaration
~~~

而不是：

~~~text
runtime type interpreter
~~~

所以真正路线是：

~~~text
finite semantic model
        ↓
validate / prove
        ↓
manifest / generated facts
        ↓
ordinary C declarations
        ↓
ordinary compiler
~~~

普通消费者 build 不应该被迫运行 Lean。

Lean 属于可信 control plane，不属于应用 hot path。

---


### 31.1 对照本版 Salts 实现快照：这些抽象已经怎样落成真实 C

为了避免这一节停留在概念伪代码，可以直接看本版 Salts 实现快照中的 CMeta：

~~~text
qigao/salts
snapshot: ad389928b437c0612c1c60844fe53677f3ed27a6
~~~

该快照中的 `cmeta_type_desc` 定义如下：

~~~c
typedef struct cmeta_type_desc {
    const char *name;
    size_t size;
    size_t align;
    cmeta_type_kind kind;
    const struct cmeta_type_desc *pointee;
    const cmeta_type_traits *traits;
    const cmeta_type_identity *identity;
} cmeta_type_desc;
~~~

这里最关键的不是字段数量，而是：

~~~text
descriptor address
    ≠
semantic identity
~~~

identity 被显式放进 descriptor，正是因为跨 Translation Unit 时不能把 object address 当成 type meaning。

更高层的数据描述也继续保持这一边界。该快照中的 `cmeta_data_desc` 包含：

~~~text
struct_size
abi_version
stable_id
display_name
kind
storage_type
shape
versioned operation providers
~~~

这说明 metadata 并不是一个随便增长的匿名 struct，而已经开始承担两个工程责任：

1. semantic identity / stable meaning；
2. ABI-versioned provider boundary。

这两件事会在第十二章继续展开。

#### TypeFunction 也没有 runtime evaluator

该快照中的 TypeFunction 实现仍然遵循本章一直强调的路线：

~~~text
finite relation rows
      ↓
macro expansion
      ↓
ordinary typedef names
      ↓
TypeEval performs token lookup
~~~

例如一元、二元、三元 relation 最终分别生成普通 C typedef。

如果某个输入组合没有 row，就不会有对应 typedef：

~~~text
no relation row
    ↓
no generated type key
    ↓
compile-time failure
~~~

因此 No Default 并不是文档约定，而是 implementation shape 的直接结果。

这正是一个很好的 Modern C 例子：

> **把“推导”提前到 control plane，最终只给 C compiler 留下一组已经决定好的普通声明。**

#### Traits 也是 capability contract，不是动态反射

当前 type descriptor 可以关联 traits；调用方显式要求：

~~~text
EQUAL
HASH
COMPARE
COPY
MOVE
DESTROY
~~~

缺失 capability 会得到明确状态，而不是在 runtime 猜测如何操作一个 object。

这再次说明 CMeta 的目标不是：

~~~text
discover everything dynamically
~~~

而是：

~~~text
declare finite knowledge
validate it early
use it cheaply later
~~~

#### 这一实现快照给本章增加了一个重要要求

从现在开始，书中凡是出现：

~~~text
type descriptor
semantic identity
trait
TypeFunction
~~~

都应该同时回答两层问题：

~~~text
semantic model:
    this concept means what?

C representation:
    this knowledge is stored/generated where?
~~~

如果两层长期分离，书就会重新退回“架构设计文档”。


---

## 32. Evidence：怎样证明类型系统真的跨出了“单文件宏实验”

这一章至少需要四种不同证据。

### 32.1 Compile-time evidence

测试：

~~~text
known type
  → descriptor resolves

supported generic application
  → compiles

unsupported relation
  → compile-time failure

ambiguous/conflicting generated relation
  → generation/proof gate failure
~~~

### 32.2 Multi-TU evidence

最关键的工程测试之一：

~~~text
TU A creates/exports type information
TU B independently references the same semantic type
        ↓
semantic equality succeeds
~~~

同时确认：

~~~text
descriptor pointer equality
~~~

不是 contract。

### 32.3 Installed-consumer evidence

真正的 library boundary 需要：

~~~text
install headers/library
      ↓
external consumer
      ↓
include public API
      ↓
instantiate/reference known generic/type
      ↓
link and run
~~~

只有这样才能证明设计没有依赖 source-tree 偶然状态。

### 32.4 Formal evidence

Lean 或等价 exhaustive checker 应覆盖：

~~~text
universe well formed
relation functional
declared domain covered
references valid
semantic identities consistent
~~~

这和 compile test 是互补关系：

~~~text
compiler evidence
    → C representation/toolchain works

formal evidence
    → semantic relation is well formed
~~~

两者不能互相替代。

---

## 33. What We Learned

第二章真正完成的是一次比“宏技巧”更大的跨越：

~~~text
textual facts
    ↓
typed facts
    ↓
structured identity
    ↓
finite relations
    ↓
checked inference
~~~

并且我们第一次看到 Lean 如何参与设计，而不是参与表演。

Lean 帮助我们把一句模糊的话：

> “这个 TypeFunction 应该是正确的。”

拆成更加准确的问题：

~~~text
Is the universe well formed?
Is the relation functional?
What is its admitted domain?
Is coverage complete on that domain?
What happens outside that domain?
Is identity stable across representation boundaries?
~~~

这反过来让 C API 的边界也变得更清楚。

最重要的是：

> **高级类型知识被放在 control plane 中建立和验证，而执行结果仍然 lower 成普通 C。**

下一章将发生新的跨越：

> **如果数据拥有类型，那么“可执行的东西”本身也应该拥有类型、环境、身份和语义属性。**

下一章将讨论：**如何让 C 中的 callback 从一个裸函数指针，变成真正的类型化可执行对象。**