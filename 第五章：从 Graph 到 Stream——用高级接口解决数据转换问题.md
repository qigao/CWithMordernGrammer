# 第五章：从 Graph 到 Stream——用高级接口解决数据转换问题


> **本章路线**
>
> 第四章已经把 canonical pipeline 保存成 Typed Graph。本章不再设计新的执行语义，而只解决一个 API 问题：
>
> ~~~text
> Typed Graph
>     ↓
> Stream façade
>     ↓
> same Graph
>     ↓
> fresh execution state per evaluation
> ~~~
>
> 贯穿示例保持不变：
>
> ~~~text
> Source<int>
>     ↓
> Filter(is_even)
>     ↓
> Map(square)
>     ↓
> Reduce(sum)
> ~~~
>
> 本章需要证明的不是“链式调用很漂亮”，而是 **Stream surface syntax 不改变 Graph semantics，也不引入隐藏 runtime ownership**。

上一章完成了一个重要转变：

```text
Callable
    ↓
Graph
```

函数不再只是独立执行，而是可以连接成一个完整的、有类型的计算结构。

有了 Graph 以后，我们首先想到的并不是：

> 还要再设计一种新的运行时。

真正出现的第一个非常自然的应用，是：

> **数据转换。**

因为大量业务代码，本质上都在重复做几类相同的事情：

```text
过滤
转换
展开
跳过
截断
聚合
收集
```

也就是：

```text
Filter
Map
FlatMap
Skip
Limit
Reduce
Collect
```

这些操作非常适合 Graph。

而当这些操作开始组成一条线性计算链时，我们很快发现：

> **它和 Java Stream 所解决的问题非常接近。**

所以 Stream 并不是 Graph 的原因。

恰恰相反。

是 Graph 做出来以后，我们才发现：

> **可以在 Graph 上提供一个类似 Java Stream 的高级接口，让 C 的数据转换也可以写得更接近问题本身。**

---

## 1. 大量 C 代码其实都在做数据转换

例如有一个：

```c
User users[1000];
```

现在希望：

1. 找到所有 enabled user；
2. 取出他们的名字；
3. 只保留前 100 个；
4. 收集到一个新的容器。

普通 C 完全可以写：

```c
size_t out_count = 0;

for (size_t i = 0; i < user_count; ++i) {
    if (!user_enabled(&users[i]))
        continue;

    names[out_count++] = user_name(&users[i]);

    if (out_count == 100)
        break;
}
```

这段代码没有任何问题。

甚至对于一个局部、简单、一次性的处理过程，它通常就是最好的代码。

问题出现在这种模式大量重复以后。

例如项目中不断出现：

```text
遍历
if
continue
临时变量
输出下标
容量检查
提前停止
错误处理
```

真正的业务逻辑反而被夹在这些执行细节之间。

用户真正想表达的其实只有：

```text
Filter(user_enabled)
Map(user_name)
Limit(100)
Collect(names)
```

所以问题并不是：

> C 的 `for` 不够好。

而是：

> **能不能把“数据怎样变化”从“循环怎样执行”中抽出来？**

---

## 2. Graph 已经能够表达这种关系

上一章中的 Graph 已经拥有：

```text
Node
Edge
Type
Callable
```

所以可以自然表达：

```mermaid
flowchart LR
    A["Input<User>"]
    B["Filter<br/>User → bool"]
    C["Map<br/>User → String"]
    D["Limit<br/>100"]
    E["Collect<br/>List<String>"]

    A --> B --> C --> D --> E
```

这里每一步都有非常明确的语义。

例如：

```text
Filter
```

并不是：

```text
调用一个 bool callback
```

那么简单。

它表达的是：

```text
输入类型 = T
Predicate = T -> bool
输出流类型仍然 = T
Cardinality = 0..1
```

而：

```text
Map
```

表达：

```text
输入 = T
Callable = T -> U
输出 = U
Cardinality = 1
```

`FlatMap` 则是：

```text
输入 = T
Generator = T -> 0..N U
输出 = U
```

一旦这些语义进入 Graph，数据转换第一次变成可以被统一处理的结构。

---

## 3. 但是 Graph API 对普通数据处理来说太底层

Graph 的优势是通用。

它可以表达：

```text
Node
Edge
Subgraph
Relation
Branch
Join
```

但如果用户只是想：

```text
filter
map
reduce
```

直接写：

```text
create_node
connect
set_exit
```

显然过于繁琐。

这就像编译器 IR 很强，但用户不会直接写 SSA。

所以需要一个更高层的 façade。

对于线性数据转换，一个很自然的 façade 就是：

# Stream

---

## 4. Stream 的作用是“更方便地构造 Graph”

这一点必须非常明确。

Stream 不应该拥有第二套：

```text
Type System
Operator System
Runtime
Optimizer
```

它应该只是：

```text
Graph Builder
```

例如用户写：

```text
stream
    .filter(enabled)
    .map(name)
    .limit(100)
    .collect(...)
```

内部做的仍然是：

```text
Graph
    + Filter Node
    + Map Node
    + Limit Node
    + Collect Node
```

可以表示成：

```mermaid
flowchart TD
    A["Stream API"]

    B["Filter(...)"]
    C["Map(...)"]
    D["Limit(...)"]
    E["Collect(...)"]

    G["Typed Graph"]

    A --> B --> G
    A --> C --> G
    A --> D --> G
    A --> E --> G
```

所以：

> **Stream 是用户体验；Graph 是语义事实。**

---

## 5. 为什么这比“直接实现一个 Stream Runtime”更重要

如果一开始就设计：

```text
Stream Runtime
```

很容易让每个 operator 都变成一个 runtime object：

```text
FilterStage
MapStage
LimitStage
ReduceStage
```

然后每个 value 流经：

```text
Stage
 ↓
virtual dispatch
 ↓
Stage
 ↓
virtual dispatch
```

这当然能工作。

但这样高级 API 会天然绑定一种执行实现。

而如果 Stream 只是构造 Graph：

```text
Stream
    ↓
Graph
```

那么执行方式可以以后再决定。

同一张 Graph 可以：

```text
直接解释
```

也可以：

```text
编译成 Plan
```

还可以：

```text
静态 lowering 成普通 C
```

甚至以后：

```text
Reactive execution
```

所以：

```text
High-level API
```

和：

```text
Execution Strategy
```

真正分离了。

---

## 6. Java Stream 给出的启发主要是“表达方式”

Java Stream 很成功的一点，是它把很多数据处理问题表达成：

```java
source.stream()
    .filter(...)
    .map(...)
    .limit(...)
    .collect(...);
```

用户读代码时看到的是：

```text
数据变化
```

而不是：

```text
迭代控制
```

这种表达方式对 C 同样有价值。

例如：

```text
users
  -> filter(enabled)
  -> map(name)
  -> collect(names)
```

比一个大型循环更容易直接看出：

```text
输入是什么
发生了哪些转换
最终得到什么
```

所以希望获得的是：

> **Java Stream 的高层表达能力。**

但没有必要复制：

> Java Stream 的全部语言、对象和 runtime 实现。

---

## 7. C 版本最大的机会：我们可以让类型链更明确

因为底层已经拥有类型系统，所以：

```text
Input<User>
```

接一个：

```text
Filter<User>
```

再接：

```text
Map<User, String>
```

可以在 Graph 构造时明确形成：

```text
User
 ↓
User
 ↓
String
```

例如：

```mermaid
flowchart LR
    A["Input<User>"]
    B["Filter<br/>User → bool"]
    C["Map<br/>User → String"]
    D["Output<String>"]

    A -->|"User"| B
    B -->|"User"| C
    C -->|"String"| D
```

如果后面接了一个：

```text
Map<int, double>
```

那么在执行之前就应该失败：

```text
String != int
```

而不是把错误留给运行时的 `void *`。

---

## 8. Filter、Map、Reduce 的类型规则可以正规化

Stream operator 并不只是 API 名字。

它们各自拥有明确的类型规则。

例如：

### Filter

```text
Input Flow Type = T

Predicate:
    T -> bool

Output Flow Type:
    T
```

---

### Map

```text
Input Flow Type = T

Mapper:
    T -> U

Output Flow Type:
    U
```

---

### FlatMap

```text
Input Flow Type = T

Generator:
    T -> 0..N U

Output Flow Type:
    U
```

---

### Reduce

```text
Input Flow Type = T

Reducer:
    T × T -> T

Output:
    T
```

---

### Collect

```text
Input Flow Type = T

Collector:
    T* -> Container<T>

Output:
    Container<T>
```

这些规则本身都可以建立在前面已经存在的：

```text
Signature
Finite Relation
Type Inference
```

之上。

---

## 9. Stream API 因此可以在“调用时”进行类型约束

例如用户有：

```text
enabled : User -> bool
name    : User -> String
```

那么：

```text
stream<User>
    .filter(enabled)
    .map(name)
```

是合法的。

而：

```text
stream<User>
    .filter(name)
```

应该失败。

因为：

```text
Filter<User>
```

要求：

```text
User -> bool
```

而 `name` 是：

```text
User -> String
```

这也是为什么前一章专门把 Callable 类型化非常重要。

如果 callback 仍然只是：

```text
void *
```

Stream 就无法成为真正的 typed API。

---

## 10. Stream 不应该拥有数据

另一个很重要的设计边界是：

> Stream 应该描述数据处理，而不是成为新的容器。

例如：

```text
Vec<User>
```

数据仍然属于 Vec。

```text
Range<User>
```

只提供 traversal。

Stream 只是描述：

```text
如何处理 Range 中的值
```

因此结构应该更接近：

```mermaid
flowchart LR
    A["Container"]
    B["Range"]
    C["Stream / Graph"]
    D["Collector"]
    E["Output Container"]

    A --> B --> C --> D --> E
```

这样：

```text
Container
```

和：

```text
Computation
```

不会混在一起。

---

## 11. Range 是 Stream 的自然输入协议

前面 CMeta 已经可以提供：

```text
Range
```

用于统一：

```text
Vec
List
Set
Map
```

等不同数据结构的读取方式。

一个 Range 可以描述：

```text
value type
size
iteration
capabilities
```

例如：

```text
SIZED
ORDERED
SORTED
UNIQUE
CONTIGUOUS
RANDOM_ACCESS
```

因此 Stream 不需要分别实现：

```text
VecStream
ListStream
SetStream
```

而只需要：

```text
Range<T>
```

作为一种统一输入。

---

## 12. Collector 则成为 Stream 的自然输出协议

另一端：

```text
Collect
```

也不应该写死：

```text
Vec_push_back
```

否则每增加一种 output container 都需要增加 Stream 特殊逻辑。

所以更自然的是：

```text
Collector
```

统一：

```text
begin
accept
finish
abort
```

于是：

```text
Stream<T>
```

最终可以收集到：

```text
Vec<T>
List<T>
Set<T>
其他 destination
```

只要目标提供：

```text
Collector<T>
```

即可。

---

## 13. Range + Graph + Collector 形成完整数据转换模型

这一组合非常重要：

```text
Range
    ↓
Graph
    ↓
Collector
```

分别回答：

```text
Range
    数据从哪里读？

Graph
    数据怎样变？

Collector
    数据写到哪里？
```

可以表示成：

```mermaid
flowchart LR
    A["Range<T>"]
    B["Typed Graph<br/>T → U"]
    C["Collector<U>"]
    D["Output"]

    A --> B --> C --> D
```

这样数据转换系统就不再绑定：

```text
某种输入容器
```

或：

```text
某种输出容器
```

---

## 14. 这使很多常见的数据处理问题可以统一表达

例如：

### 过滤

```text
Users
 ↓
Filter(enabled)
 ↓
EnabledUsers
```

### 投影

```text
User
 ↓
Map(name)
 ↓
String
```

### 一对多转换

```text
Sentence
 ↓
FlatMap(words)
 ↓
Word
```

### 聚合

```text
Numbers
 ↓
Reduce(sum)
 ↓
Number
```

### 收集

```text
Value Stream
 ↓
Collect
 ↓
Vec / List / Set
```

这些模式不再需要每一个业务模块自己实现完整遍历逻辑。

---

## 15. 但真正有意思的是：Graph 允许优化整条数据转换链

例如：

```text
Map(f)
 ↓
Map(g)
```

如果条件允许，可以转成：

```text
Map(g ∘ f)
```

这样中间的：

```text
B
```

甚至不需要成为一个 materialized object。

例如原来：

```text
A
 ↓ f
B
 ↓ g
C
```

可以执行成：

```c
C c = g(f(a));
```

而不是：

```c
B b = f(a);
C c = g(b);
```

虽然编译器有时也能优化掉局部变量，但 Graph 层能看到更高层的语义。

---

## 16. Filter 和 Map 也可能进一步合并到同一个 loop

例如 Graph：

```text
Filter(enabled)
 ↓
Map(name)
 ↓
Limit(100)
```

如果走 Direct path，最终完全可能变成：

```c
size_t out = 0;

for (size_t i = 0; i < count && out < 100; ++i) {
    if (!enabled(users[i]))
        continue;

    names[out++] = name(users[i]);
}
```

也就是说：

```text
高级 Stream API
```

不必对应：

```text
三个 runtime stage objects
```

反而可以对应：

```text
一个普通 C loop
```

这就是整个设计中非常重要的性能方向。

---

## 17. “高级接口”与“低成本执行”并不冲突

很多 C 开发者对类似：

```text
Stream
Graph
Lambda
```

的抽象天然警惕。

因为它们经常意味着：

```text
allocation
virtual dispatch
temporary objects
runtime type erasure
```

但如果系统拥有足够多的编译期和 control-plane 信息，就可以走完全不同的路线：

```text
高级表达
    ↓
Graph
    ↓
Validate
    ↓
Optimize
    ↓
Lower
    ↓
普通 C
```

也就是说：

> **高级接口负责让人写得简单，Graph 负责让系统看懂，Lowering 负责让机器执行得简单。**

---

## 18. Stream 因此可以只是 façade，而不是成本中心

理想情况下：

```text
stream.filter(...).map(...)
```

主要承担：

```text
Graph Construction Cost
```

而不是：

```text
Per-item Runtime Cost
```

这两者的差别非常大。

如果一个 Graph 构建一次，处理：

```text
1,000,000 个 value
```

那么在构建阶段多做一点：

```text
类型检查
signature lookup
optimization
```

完全可能是划算的。

因为这些成本只付一次。

---

## 19. Build Once, Execute Many

这里开始形成一个很重要的执行哲学：

```text
Build Once
Execute Many
```

例如：

```text
构造 Stream / Graph
       ↓
Validate
       ↓
Optimize
       ↓
Compile Plan
       ↓
重复执行 N 次
```

Graph 的复杂度被摊销。

而数据 hot path 可以保持很小。

---

## 20. Stream 也可以解决中间容器泛滥的问题

传统代码很容易这样写：

```text
Input
 ↓
Filter
 ↓
Temporary Vec A
 ↓
Map
 ↓
Temporary Vec B
 ↓
Limit
 ↓
Output
```

每一步都 materialize 一个 container。

但如果这些转换以 Graph 形式存在：

```text
Filter
Map
Limit
```

系统知道：

```text
它们其实是一条连续 pipeline
```

于是很多场景可以直接 streaming execution：

```text
value
 ↓ filter
 ↓ map
 ↓ limit
 ↓ sink
```

而不创建：

```text
Temporary A
Temporary B
```

这会减少：

```text
allocation
copy
cache miss
memory footprint
```

---

## 21. Generic 和 Traits 在 Stream 中第一次真正组合起来

例如：

```text
Stream<User>
    ↓
Map<User, String>
    ↓
Collect<Vec<String>>
```

这里已经同时涉及：

```text
User
String
Vec<String>
Callable<User,String>
Collector<Vec<String>>
```

如果 `String` 不是 trivial type，还需要：

```text
copy / move / destroy
```

Traits。

也就是说，一个看起来很简单的：

```text
map + collect
```

实际上正在同时使用：

```text
Type
Generic
Traits
Callable
Collector
```

这正是为什么 Stream 是验证整个类型化 Meta 基础是否真正可组合的一个很好用例。

---

## 22. Collect 也让容器算法和数据转换真正解耦

如果 Stream 自己直接调用：

```text
Vec_push_back
```

那么它就知道太多 CSTL 细节。

更好的结构是：

```text
Stream
 ↓
Collector Protocol
 ↓
Vec Collector
```

或者：

```text
Stream
 ↓
Collector Protocol
 ↓
List Collector
```

于是：

```text
Stream
```

只依赖：

```text
Collector
```

而不知道：

```text
具体容器内部如何扩容
如何分配 node
如何保持顺序
```

这也是模块边界逐渐成熟的表现。

### 22.1 当前 CSTL 如何落地这条边界

当前仓库中，CSTL 是 CMeta finite generic 的容器提供者。一次：

```c
typed(List, IntList, int);
```

会生成具体 wrapper、类型与容器描述、borrowed Range 和 transactional Collector；但 list storage、节点分配、插入和销毁算法仍归 CSTL 所有。CFlow 只读取 Range，并通过 Collector terminal 写入 caller-owned zero-state 输出。

下面是当前 `Salts::CSTLStream` 接口的一条完整最小路径：

```c
#include <stdbool.h>
#include <cstl/stream.h>

typed(List, IntList, int);
typed(List, LongList, long);

typed(filter, value, bool, keep_even, (int value)) {
    return value % 2 == 0;
}

typed(map, value, long, square, (int value)) {
    return (long)value * (long)value;
}

int main(void) {
    IntList input = {0};
    LongList output = {0};
    cstl_stream_t pipeline = {0};
    cstl_collect_result result = {0};
    int exit_code = 1;

    if (IntList_init(&input, 4u) != STL_OK) goto cleanup;
    for (int value = 1; value <= 4; ++value) {
        if (IntList_push_back(&input, value) != STL_OK) goto cleanup;
    }
    if (stream(&input, &pipeline) == NULL) goto cleanup;
    if (pipeline.filter(&pipeline, keep_even) == NULL) goto cleanup;
    if (pipeline.map(&pipeline, square) == NULL) goto cleanup;

    result = to_list_typed(&pipeline, LongList, &output, 2u);
    if (result.ok && result.count == 2u) exit_code = 0;

cleanup:
    LongList_destroy(&output);
    cstl_stream_destroy(&pipeline);
    IntList_destroy(&input);
    return exit_code;
}
```

这里的 `2u` 是 hard item limit，不是截断提示。若 pipeline 产生第三个值，Collector 返回容量错误并 abort，`output` 恢复为约定的 zero state。`input` 与它导出的 Range 则在整个求值期间保持 borrowed，不能在中途 append、erase、resize 或 destroy。

---

## 23. Stream 之后才发现：Publisher 不一定来自 Container

做到这里，最初的假设通常还是：

```text
数据已经存在
```

例如：

```text
Array
Vec
Range
```

执行时：

```text
next
next
next
```

总能立即回答：

```text
VALUE
```

或者：

```text
DONE
```

但 Graph 本身其实并没有要求：

> Publisher 必须来自一个同步 Container。

于是一个新的问题自然出现：

> **如果 Publisher 来自 socket、timer、message queue，它现在没有 value 怎么办？**

这就是从 Stream 走向下一阶段的地方。

---

## 24. 一个非常重要的发现：Operator 其实不关心 Publisher 是否同步

例如：

```text
Map(f)
Filter(g)
Reduce(r)
```

它们真正关心的是：

```text
输入 Value
```

而不是：

```text
Value 是从 Array 来的
还是 Socket 来的
```

所以：

```text
Map
Filter
Reduce
```

这些 Graph operator 可以继续复用。

真正需要改变的只是：

```text
Publisher 如何推进
```

这意味着：

```text
Stream
```

和：

```text
Reactive
```

之间可能并没有想象中那么大的距离。

---

## 25. 如果 Publisher 可以说“现在还没有”，就出现 WAIT

同步 Publisher 通常只有：

```text
VALUE
DONE
ERROR
```

但异步 Publisher 还需要：

```text
WAIT
```

也就是说：

```text
resume()
```

可以返回：

```text
现在没有 value
但我也没有结束
稍后再来
```

一旦有：

```text
WAIT
```

再配合：

```text
Wake
Scheduler
```

同一个 Graph 就可以从：

```text
同步数据处理
```

进一步扩展为：

```text
异步数据流
```

---

## 26. 所以 Reactive 并不是重新设计一套 Operator

这是整个演化过程中很重要的发现。

最初完全可以想象：

```text
Stream API
```

和：

```text
Reactive API
```

是两套系统。

但 Graph 让我们看到：

```text
Map
Filter
Reduce
```

的语义可以完全共享。

区别主要只是：

```text
Stream:
    Input 可立即读取

Reactive:
    Publisher 可能 WAIT
```

于是：

```text
Same Graph
+
Different Publisher / Execution Model
```

就有可能同时支撑两者。

---

## 27. 这也是 Graph 比 Stream 更重要的原因

如果底层一开始就是：

```text
Stream Runtime
```

那么扩展 Reactive 时可能不得不：

```text
重新设计
```

而因为底层是：

```text
Graph
```

Stream 只是：

```text
Facade
```

所以后面可以继续添加：

```text
Reactive Backend
```

而不用改变原有 operator semantics。

可以表示成：

```mermaid
flowchart TD
    G["Typed Graph"]

    S["Stream façade"]
    R["Reactive Runtime"]

    S --> G
    G --> R
```

更准确一点：

```text
Stream
    负责方便构造 Graph

Reactive
    负责以异步方式推进 Graph
```

它们其实不处于同一层。

---

## 28. 这一阶段真正得到的不是一个 Java Stream Clone

如果最后只是：

```text
把 Java Stream API 翻译成 C
```

价值其实有限。

更重要的结果是：

```text
Graph
+
Range
+
Collector
+
Callable
+
Type
```

形成了一套通用数据转换模型。

Java Stream 风格 API 只是这个模型的：

```text
一个很自然的人机界面
```

所以目标不是：

> 做一个 Java API 的复制品。

而是：

> **让 C 拥有类似的高级数据转换表达能力，同时保留自己的类型模型、资源管理和执行方式。**

---

## 29. 从这一章开始，可以看到 CFlow 的应用方向逐渐打开

有了 Graph 和数据转换以后：

```text
同步 Container
    ↓
Stream
```

只是第一个应用。

接下来还可以是：

```text
Async Publisher
    ↓
Reactive
```

再往后：

```text
Typed Event
    ↓
Event Processing
```

再进一步：

```text
Event + State
    ↓
State Machine
```

然后：

```text
State Machine
+
Mailbox
+
Executor
    ↓
Actor
```

整个路线并不是预先规划出来的一张 feature list。

而是 Graph 和 Executor 的能力不断组合以后自然出现的。

---

## 30. 完整发展链再次向前延伸

目前的路线已经变成：

```text
Macro
 ↓
Type
 ↓
Traits
 ↓
Generic
 ↓
Inference
 ↓
CMeta
 ↓
Callable
 ↓
Lambda / Bind
 ↓
Graph
 ↓
Data Transformation
 ↓
Stream
```

下一步则是：

```text
Stream
 ↓
Publisher may WAIT
 ↓
Reactive
```

也就是说，Graph 做出来以后，我们第一次发现：

> **同一套有类型的数据转换关系，不仅可以处理已经存在的数据，还可以处理未来才会到来的数据。**

这将把执行问题从：

```text
iteration
```

推进到：

```text
scheduling
waiting
waking
demand
backpressure
```

也会真正引出：

```text
Executor
Scheduler
Subscription
```

这些模型。

---


## 31. Canonical Example：同一张 Graph，换一个更适合用户的入口

第四章已经有了：

~~~text
Input<int>
    ↓
Filter(is_even)
    ↓
Map(square)
    ↓
Reduce(sum)
~~~

如果用户每次都直接调用低层 Graph builder，API 会显得很机械。

Stream 的价值是让构造过程更接近数据转换本身：

~~~c
cflow_stream s = {0};

cflow_stream_init(&s, &cmeta_type_int);

s.filter(&s, is_even)
 ->map(&s, square)
 ->reduce(&s, sum);
~~~

这里最重要的不是 fluent syntax。

真正重要的是：

> **这三次调用最终仍然只是在构造同一套 Graph IR。**

Stream 没有重新拥有一套：

~~~text
StreamNode
StreamExecutor
StreamOptimizer
StreamTypeSystem
~~~

而只是：

~~~text
user-friendly construction surface
        ↓
same typed Graph
~~~

这就是“高级接口不等于新 Runtime”。

---

## 32. Semantic Contract：Stream façade 不能偷偷改变什么

### 32.1 Operator semantics 必须与 Graph 一致

如果 Graph 中：

~~~text
FILTER
    output type = input type
    cardinality = 0..1

MAP
    output type = callable return
    cardinality = 1

REDUCE
    homogeneous fold
    cardinality = N..1
~~~

那么 Stream 不能因为 surface API 不同而重新定义这些规则。

因此 Stream method 本质上应该是：

~~~text
typed Graph builder wrapper
~~~

而不是：

~~~text
second semantic authority
~~~

### 32.2 Stream owns the description, not the source data

Stream 可以拥有：

~~~text
Graph description
copied Range view
evaluation options
builder/admission state
~~~

但输入 object/container 的真实数据仍然由原 owner 管理。

所以需要明确：

~~~text
Stream lifetime
    ≠
container lifetime
~~~

如果绑定的是 borrowed Range，那么 evaluation 期间原 owner 必须继续存活并满足 Range contract。

### 32.3 Evaluation state 必须与 reusable Graph 分离

一个很关键的 contract 是：

> 同一条 Stream/Graph description 可以在条件允许时多次执行，但每次执行拥有新的 cursor/operator state。

不能把：

~~~text
reduce accumulator
skip counter
take counter
publisher cursor
~~~

这些 live execution fact 写回 Graph 本身。

否则：

~~~text
Build Once, Execute Many
~~~

会立刻失效。

### 32.4 “可链式”不等于“延迟执行对象无限增长”

Stream 只负责 construction。

当用户真正执行时，可以选择：

~~~text
direct synchronous evaluation
normalized Graph
compiled Plan
Reactive Subscription
~~~

因此链式 API 不是成本模型。

真正成本取决于：

> **最终选中的 execution backend。**

---

## 33. Lean / Proof Obligation：Stream 这一层应该证明什么

Stream façade 本身不需要拥有一套新的复杂 formal semantics。

更自然的证明目标是：

### 33.1 Surface-to-Graph construction correctness

如果一串 Stream method：

~~~text
filter f
map g
reduce h
~~~

构造出的 Graph 是：

~~~text
FILTER(f)
MAP(g)
REDUCE(h)
~~~

那么 Stream 的 observable meaning 应直接继承 Graph。

也就是说可以把证明问题写成：

~~~text
BuildStream(ops) = g
→
StreamSemantics(ops, input)
=
GraphSemantics(g, input)
~~~

如果 Stream 只是 deterministic builder，这个 theorem 应该非常薄。

这正是好事。

> **Façade 越薄，需要独立证明的语义就越少。**

### 33.2 Type-chain preservation

对于：

~~~text
T
  --filter--> T
  --map f--> U
  --reduce--> U
~~~

需要确保 surface method 不可能偷偷绕过 Graph admission。

例如：

~~~text
map : T -> U
next filter expects V
U != V
~~~

应该在 Graph construction/admission 阶段失败。

### 33.3 Reusable description / fresh execution separation

形式模型中最好明确区分：

~~~text
Program Description
~~~

与：

~~~text
Execution State
~~~

这会在下一章 Reactive 变得更加重要。

如果 formal model 一开始就把 cursor/demand/cancel state 塞进 Graph，就会把 control plane 与 execution plane 混在一起。

---

## 34. Current C Implementation：Stream 真的就是 Graph façade

对照当前 Salts：

~~~text
qigao/salts
master: ad389928b437c0612c1c60844fe53677f3ed27a6
~~~

当前 cflow_stream 的核心形态非常直接：

~~~c
struct cflow_stream {
    cflow_graph graph;

    cmeta_range input_range;
    bool has_input_range;

    cflow_eval_options eval_options;
    bool failed;

    /* generated explicit-self operator methods */
    ...
};
~~~

这段 representation 本身就回答了很多问题。

### 34.1 Graph 是 Stream 的核心 owned description

Stream 不是指向一个隐藏 Stream runtime。

它直接拥有：

~~~text
cflow_graph graph
~~~

operator method 的主要工作就是继续构造它。

因此：

~~~text
Stream
    ↓
Graph
~~~

不是架构图上的理想关系，而是实际 data layout。

### 34.2 Range 是输入协议，不是 Graph 的一部分

input_range 与 has_input_range 表示：

~~~text
这个 Stream 当前绑定了哪一种输入 view
~~~

但它不改变 Graph 的 operator semantics。

这让：

~~~text
array
container Range
channel-like publisher
other source
~~~

可以逐步共享后面的计算描述。

### 34.3 Method fields 是显式 self 的 ISO C11 façade

当前 Stream methods 不是 C++ member function。

它们仍然只是 C function pointer fields：

~~~text
stream.filter(&stream, ...)
stream.map(&stream, ...)
~~~

这样的设计有两个价值：

1. 保持 ISO C11；
2. surface syntax 更接近 fluent API，但没有引入 object runtime。

### 34.4 Public Graph view 是 read-only introspection

当前 API 已经明确：

~~~text
cflow_stream_graph()
    → borrowed read-only Graph view
~~~

普通用户不应该：

~~~text
stream.graph.nodes[...] = ...
~~~

来绕过 builder contract。

这延续了第四章的原则：

> **public visibility 不等于 arbitrary mutability。**

---

## 35. Evidence：canonical pipeline 已经存在于真实测试里

当前 CFlow 的 certificate tests 已经使用几乎和本书完全一致的 pipeline：

~~~text
filter even
    ↓
map square
    ↓
reduce add
~~~

测试会继续执行：

~~~text
Stream
    ↓
Surface Graph
    ↓
Normalize
    ↓
Optimize
    ↓
Compile Plan
    ↓
Build Certificate
    ↓
Check Certificate
~~~

这说明 canonical example 不是为了书临时发明的 toy example。

它已经是实际 trusted execution path 的测试对象。

### 35.1 Surface/API evidence

需要验证：

~~~text
filter/map/reduce method
    ↓
Graph rows appear with expected operators/types
~~~

### 35.2 Reuse evidence

同一 Stream description 在合法 Range contract 下多次 evaluation，应拥有独立 execution state。

特别要检查：

~~~text
reduce accumulator
take/skip counters
temporary value storage
~~~

不能泄漏回 Graph description。

### 35.3 Ownership evidence

测试要区分：

~~~text
Stream destroys its Graph

but

Stream does not destroy borrowed container/Range owner
~~~

### 35.4 Certificate / verification evidence

当 Stream 构造完成以后，所有 trusted transformation 都应该针对：

~~~text
Graph / Plan / Certificate
~~~

而不是针对 surface syntax。

这再次证明：

> **Stream 不是 semantic center；Graph 才是。**

---

## 36. Performance：不要 benchmark “链式语法”，要 benchmark execution path

Stream API 本身大多发生在 construction/control plane。

因此性能问题不能简单问：

~~~text
stream.map() 比普通 C 慢多少？
~~~

更有意义的问题是：

~~~text
同一条 pipeline 最终如何执行？
~~~

比较：

~~~text
hand-written C loop
surface Graph interpreter
normalized/optimized Graph
compiled Plan
direct/AOT path
~~~

如果最后 lowering 成与手写 loop 等价的执行形式，那么 Stream 的高级表达能力和 hot-path cost 可以被分离。

这就是本书最重要的观点之一：

> **高级 API 的成本不应该自动等于每个 value 的执行成本。**

---

## 37. What We Learned

第五章真正完成的不是“给 C 加链式 API”。

而是证明一个更重要的架构关系：

~~~text
Friendly Surface Syntax
        ↓
Typed Graph IR
        ↓
Independent Execution Backends
~~~

因此我们得到：

1. **Stream is a façade, not a second runtime.**
2. **Operator semantics belong to Graph/operator schema.**
3. **Input Range ownership remains explicit.**
4. **Program description and execution state are separate.**
5. **A reusable Stream can create fresh execution state each time.**
6. **Formal reasoning should target Graph meaning, not surface syntax.**
7. **Performance evidence must compare execution backends, not API aesthetics.**

到这里，同一条 canonical pipeline 已经拥有两个视角：

~~~text
user view:
    filter → map → reduce

compiler/control-plane view:
    typed Graph
~~~

下一章真正改变的不是 operator。

改变的是：

> **数据不一定已经在那里。**

当 source 可以回答：

~~~text
WAIT
~~~

以后，Graph semantics 开始进入时间、Wake、Demand 与 Backpressure。

这就是 Reactive。

---

# 小结：Stream 是 Graph 的第一个高级应用，而不是它的底层

本章最重要的关系可以总结成：

```text
Graph
    描述计算

Stream
    提供方便的数据转换接口

Range
    提供输入

Collector
    提供输出

Executor
    以后决定如何执行
```

也就是：

```mermaid
flowchart LR
    A["Range"]
    B["Stream façade"]
    C["Typed Graph"]
    D["Executor"]
    E["Collector"]

    A --> B
    B --> C
    C --> D
    D --> E
```

这种分层带来的最大好处是：

> **高级接口和底层执行不再绑定。**

用户可以获得：

```text
类似 Java Stream 的声明式数据转换
```

而系统仍然可以把它降低为：

```text
普通 C loop
预编译 Plan
其他执行形式
```

所以 Stream 的价值并不是让 C 变得像 Java。

而是证明：

> **当 C 已经拥有 Type、Callable 和 Graph 后，也可以用很高级的方式表达数据转换，而这种表达能力并不要求牺牲 C 原本简单、高效的执行模型。**

下一章将继续沿着这一发现前进：

> **如果 Graph 的 Publisher 不一定马上有数据，会发生什么？**

答案就是从同步 Stream 走向 **Reactive、WAIT、Wake、Demand 与 Backpressure**。
