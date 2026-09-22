# 第十三章：从基础能力到 Modern C——Serialization、RPC、Plugin、Workflow 与更多应用

> **本章不是 Feature List，而是四个真实工程案例。**
>
> 前面的 CMeta / CFlow primitive 是否真的有价值，最终要看它们能不能减少真实 C library 里的重复契约，而不是看抽象名字有多少。
>
> 本章选择 edition snapshot 中已经存在的四类实现：
>
> ~~~text
> CSTL
>     finite Generic → typed containers
>     algorithms remain compiled C
>
> CSerde + CBind
>     one native semantic shape
>     multiple serialization formats
>
> CRPC + CHTTP + CNet + NativeIO
>     protocol layers reuse existing ownership/runtime boundaries
>
> TinyTest + TinyMock
>     finite typed assertions/mocks
>     runtime remains a small static C library
> ~~~
>
> 四个案例都用同一把尺子检查：
>
> **Plain C 原来哪里重复？Meta 只抽走了什么事实？最终普通 C 还剩什么？资源和 ownership 在哪里？有没有为了“统一”偷偷创造第二套 runtime？**
## 1. 很多现代 C Library 面临的是同一类问题

表面上：

```text
Serialization
RPC
Plugin
Event Bus
Workflow
ECS
Query Engine
```

看起来属于完全不同领域。

但深入以后，会发现它们反复需要：

```text
Type
Field Metadata
Function Signature
Capability
Schema
Runtime Binding
Lifecycle
Dispatch
```

例如 Serialization 需要知道：

```text
这个对象是什么类型？
有哪些字段？
字段是什么类型？
怎样构造？
怎样销毁？
```

RPC 需要知道：

```text
方法是什么？
参数是什么类型？
返回什么类型？
是否可能失败？
```

Plugin 需要知道：

```text
Provider 实现了什么 Interface？
ABI 是否匹配？
具有什么 Capability？
```

Event Bus 需要知道：

```text
Event Type
Payload Type
Handler Signature
```

Workflow 需要：

```text
Node
Edge
State
Transition
Executor
Retry / Error Policy
```

这些问题中，有相当一部分已经在前面的体系中被解决过。

---

在早期草稿中，这里曾按 Serialization、RPC、Plugin、Event Bus、Workflow、ECS、Query、Protocol、UI 等方向逐项展开。那种写法能展示广度，但会重复前面已经建立的 Type / Callable / Graph / Machine / ownership 原则，也容易让这一章变成 Feature Catalog。

出版稿改用四个真实案例作为主干：

~~~text
CSTL
    → 检验 Generic 是否真的能统一 typed surface，而不复制容器算法

Serialization / Data Binding
    → 检验 semantic truth、format boundary、native lifecycle

RPC
    → 检验 typed semantics、protocol layering、bounded runtime、cancellation

TinyTest / TinyMock
    → 检验 finite meta 是否也能服务 testing，而不制造测试 VM
~~~

其他方向保留在后面的 Extension Map，只说明复用哪些 primitive 以及哪些 domain semantics 不应进入 Core。

---

## 2. Deep Case A：CSTL——Generic 统一 typed surface，但算法仍然是普通 C

Part I 讲 Generic 时最容易留下一个误解：

> `typed(...)` 是不是意味着每个容器算法都被宏重新生成一份？

CSTL 正好用真实实现回答这个问题。

### Plain C baseline：真正重复的是 type binding，不是 vector growth

如果只支持一种类型，下面的 C 完全合理：

~~~c
typedef struct IntVec {
    int *data;
    size_t size;
    size_t capacity;
} IntVec;

int IntVec_init(IntVec *v, size_t capacity);
int IntVec_push_back(IntVec *v, int value);
void IntVec_destroy(IntVec *v);
~~~

问题出现在 `double`、`User`、`Pair`、Map、BTree 等 family 都需要同样的 type binding 时。

edition snapshot 的 CSTL 只把这一层交给 CMeta Generic：

~~~c
#include <cstl/typed.h>

typed(Vec, IntVec, int);
typed(List, IntList, int);
typed(HashMap, IntLongHashMap, int, long);

IntVec values = {0};

IntVec_init(&values, 16u);
IntVec_push_back(&values, 10);
IntVec_push_back(&values, 20);

IntVec_destroy(&values);
~~~

用户得到的是 concrete `IntVec_*` typed ABI，而不是 `void *` + size + 手写 cast。

## 2.1 最重要的边界：typed façade 可以 header-only，container algorithm 不应该 header-only

snapshot 的设计刻意分成两层：

~~~text
generated typed layer
    wrapper type
    Type_method forwarding functions
    descriptor / Range / collector metadata

compiled CSTL core
    vector growth
    list allocation/linking
    hash probing
    heap operations
    B-tree/B+tree balancing
~~~

也就是说：

> **Meta 生成的是 type contract，不是重新实现算法。**

这正是有限模板设计比“每个类型复制一个 container implementation”更工程化的地方。

## 2.2 同一份 typed container 可以继续进入 CFlow，而不复制 Filter/Map 算法

CSTL 的 optional CFlow bridge 继续复用同一个 Range / Graph contract。

snapshot README 中的实际形态是：

~~~c
typed(filter, value, bool, keep_even, (int value)) {
    return value % 2 == 0;
}

cflow_stream pipeline = {0};

stream(&values, &pipeline)
    ->filter(&pipeline, keep_even)
    ->distinct(&pipeline, 64u)
    ->sorted(&pipeline, 64u)
    ->skip(&pipeline, 1u)
    ->take(&pipeline, 10u);
~~~

关键不是 fluent syntax。

关键是：

~~~text
Vec / List / Set
    do not each implement their own filter/map

CSTL
    owns storage / Range / collector

CFlow
    owns Graph operator semantics

CMeta callable
    owns predicate signature/contract
~~~

一个 `keep_even` predicate 可以进入不同容器的 Range，而无需产生 `VecFilter`、`ListFilter`、`SetFilter` 三套逻辑。

## 2.3 这个案例解决了什么

CSTL 展示的是本书最基本的成功标准：

~~~text
before:
    many container macro families
    repeated type binding
    repeated adapter declarations

after:
    one finite Generic entry
    one typed ABI per instantiated type
    one compiled algorithm implementation
    shared Range / Collector / CFlow composition
~~~

这不是把 C 变成 C++ STL。

它只是让 C 中原本重复而稳定的 type contract 被收成一次定义，同时保留 C 对 ownership、allocation 和 algorithm implementation 的直接控制。

---
## 3. Deep Case B：Serialization / Data Binding

Serialization 很适合检验一套 Meta System 是否真的拥有清楚的边界。

最容易做错的方式是：

~~~text
JSON parser
    owns JSON syntax
    +
    owns native struct reflection
    +
    owns allocation policy
    +
    owns container binding
    +
    owns validation
    +
    owns application conversion
~~~

然后再为：

~~~text
YAML
XML
CSV
binary protocol
database row
IPC message
~~~

分别复制一套类似机制。

这会重新产生：

~~~text
Knowledge Duplication
~~~

正确问题应该是：

> **格式语法、canonical data events、native semantic shape、native storage lifecycle，分别由谁拥有？**

本版 Salts 快照 已经形成一个很清楚的分层。

---

## 3.1 Plain C Baseline：手写 parser → struct 并没有错

假设我们有：

~~~c
typedef struct User {
    int id;
    char name[64];
} User;
~~~

一个固定格式、固定字段的小程序完全可以：

~~~text
parse "id"
    ↓
atoi
    ↓
user.id

parse "name"
    ↓
copy with bound
    ↓
user.name
~~~

如果：

~~~text
只有一种格式
只有一个 struct
schema 很稳定
没有通用 binding 需求
~~~

这就是最好的方案。

Data binding abstraction 只在重复开始稳定出现时才值得：

~~~text
多个格式都需要同一个 User semantic shape
多个 native type 都重复写字段映射
ownership / rollback / limits 反复出现
parser 与 native layout 被紧耦合
~~~

---

## 3.2 第一层：Concrete Parser 只拥有 Syntax

具体 parser 应该回答：

~~~text
这里是 object begin
这里是 field name
这里是 signed integer
这里是 string slice
这里是 array end
~~~

而不应该回答：

~~~text
这个字段要写到 User.name offset
这个字符串要分配 tstr
这个 enum 是否属于业务 domain
~~~

因此具体 JSON/YAML/XML parser 的输出可以先投影到：

~~~text
CSerde canonical token protocol
~~~

而不是直接写 native object。

这使：

~~~text
syntax
~~~

与：

~~~text
semantic/native binding
~~~

第一次解耦。

---

## 3.3 第二层：CSerde 只拥有 Format-Neutral Token Truth

本版 Salts 快照 architecture 将 CSerde 定位为：

~~~text
canonical token
reader/writer contract
view lifetime semantics
~~~

它不依赖：

~~~text
CMeta
CFlow
concrete parser
~~~

这很重要。

因为 CSerde 本身不应该知道：

~~~text
User
Vec<User>
Actor
Graph
JSON
YAML
~~~

它只定义：

~~~text
canonical value/event grammar
single-pass reader
writer protocol
slice stability/lifetime
status
~~~

这让 concrete parser 可以变化，而 downstream binding kernel 不变。

反方向 write 同样成立：

~~~text
Native C Value
    ↓
semantic writer/binding
    ↓
CSerde canonical events
    ↓
concrete serializer
    ↓
JSON/YAML/...
~~~

---

## 3.4 第三层：CMeta 提供 Native Semantic Shape

CBind 不应该重新发明第二套 native type system。

它消费：

~~~text
cmeta_data_desc
~~~

这类 semantic shape。

一个 descriptor 可以告诉 binding layer：

~~~text
kind
storage type
struct shape
enum shape
variant shape
buffer provider
fixed/native operations
stable identity
ABI/version information
~~~

于是：

~~~text
native type meaning
~~~

仍然只有一个权威来源。

这和第十二章的原则一致：

> **Data Binding 不应该因为“需要 schema”就建立另一个 type identity universe。**

---

## 3.5 第四层：CBind 是 Format-Neutral Decode Kernel

当前 CBind 的 public定位非常明确：

~~~text
CSerde Reader
    +
CMeta-described native storage
    ↓
CBind
    ↓
native C value
~~~

并且 production target 只依赖：

~~~text
Salts::CMeta
Salts::CSerde
~~~

它不依赖：

~~~text
CFlow
CSTL
SaltsUtils concrete parsers
application runtime
~~~

这是一个非常好的 module ownership 例子。

### STRING / BYTES

CBind 不知道具体：

~~~text
tstr
vstr
application buffer class
~~~

它只通过 CMeta buffer adapter 处理：

~~~text
owned
borrowed
custom
~~~

并遵守：

~~~text
STRING only accepts STRING token
BYTES only accepts BYTES token
owned adapter copies
borrowed adapter only accepts stable view
max_buffer_bytes is hard bound
~~~

### ENUM

Enum 必须经过完整 enum provider contract：

~~~text
declared text/symbol/integer
    → admitted

undeclared value / float coercion
    → rejected
~~~

不是“尽量转换”。

### VARIANT

Variant 使用明确 canonical representation：

~~~text
ARRAY_BEGIN
tag
payload
ARRAY_END
~~~

select/restore_zero 负责 active payload lifecycle。

Malformed provider不能留下 half-active union。

---

## 3.6 Failure Atomicity：绑定失败后 Native Graph 回到 Semantic Zero

这是这个案例最专业的部分之一。

Decode 过程中可能失败于：

~~~text
bad token
wrong field type
buffer bound
container bound
provider allocation/copy
enum value
variant case
depth
item count
~~~

如果 failure 后留下：

~~~text
一半字段已写
一半 owned buffer 已分配
variant 已 engaged 但 payload incomplete
~~~

C caller 很难安全 destroy/retry。

因此 CBind contract要求：

~~~text
destination starts in semantic zero
      ↓
decode
      ↓
success:
    complete semantic object

failure:
    restore complete root semantic graph to zero
~~~

并且：

~~~text
reader is not rewound
~~~

这很重要。

因为：

> **Rollback belongs to target object ownership, not to pretending the input stream never advanced.**

这是一种非常 C 风格的事务边界。

---

## 3.7 Boundedness：Serialization 也不能偷偷无限增长

Context明确携带：

~~~text
scratch size
max depth
max container items
max buffer bytes
~~~

所以：

~~~text
deep malicious input
huge string
unbounded array
~~~

不会因为“serializer 一般都会动态分配”而获得例外。

这继续遵守：

~~~text
Bounded resource
    is semantic contract
~~~

而不是 performance hint。

---

## 3.8 Binding 后才进入 CFlow

一个非常重要的 anti-pattern 是：

~~~text
Stream<cserde_token>
    → arbitrary business filter/map
~~~

为什么不推荐？

因为 token 是：

~~~text
structural transport grammar
~~~

不是：

~~~text
business semantic value
~~~

如果业务层直接任意过滤 token：

~~~text
OBJECT_BEGIN
FIELD
ARRAY_END
~~~

很容易破坏 grammar。

更正确的 boundary：

~~~text
format syntax
    ↓
CSerde token grammar
    ↓
CBind + CMeta
    ↓
complete native semantic value
    ↓
optional CFlow Stream<T> / Graph / Machine
~~~

所以 CFlow composition 从：

~~~text
完整 semantic/native value
~~~

开始，而不是从 raw parser token 开始。

---

## 3.9 Evidence：这个案例怎样证明自己不是“漂亮架构图”

当前 CBind tests 已经覆盖多个关键维度：

~~~text
buffer root/struct decode
embedded NUL
borrowed lifetime rejection
hard limits
target failure
rollback

enum exact input
undeclared rejection
rollback

variant preflight
tag/payload lifecycle
nested payload
resource limit
rollback
~~~

进一步的完整 application qualification 应包含：

~~~text
same native type
    decoded from multiple concrete format adapters
        ↓
same semantic value

native value
    → CSerde writer
    → serializer
    → parser
    → CBind
        ↓
round-trip semantic equality
~~~

注意这里的 equality 应使用：

~~~text
type-specific semantic equality
~~~

而不是简单 memcmp 任意 padding/object bytes。

---

## 4. Deep Case C：RPC 不是“再造一个网络 Runtime”

RPC 是第二个非常好的组合案例。

表面上它需要：

~~~text
method schema
serialization
HTTP
connection
TLS
deadline
async execution
cancellation
server registry
errors
batch
~~~

如果每个 RPC framework 都重新拥有这些能力，很快就会出现：

~~~text
second type system
second serializer
second event loop
second socket pool
second retry policy
second lifecycle model
~~~

当前 CHTTP/CRPC 的边界提供了一个更好的例子。

当前 snapshot：

~~~text
qigao/salts
    ad389928b437c0612c1c60844fe53677f3ed27a6

qigao/chttp
    5e9f388c2009836d024e0fcd5a3ff8f7c2d49e39
~~~

---

## 4.1 RPC Stack 先按 Ownership 分层

当前 CRPC 文档直接把链写成：

~~~text
CMeta method semantics
+
CSerde params/result
      ↓
JSON-RPC envelope + deadline
      ↓
CHTTP POST + HTTP limits
      ↓
CNet connection
      ↓
NativeIO terminal completion
~~~

每一层都只拥有自己的 meaning。

### CMeta

可选描述：

~~~text
local callable signature
effects
properties
~~~

### CSerde

描述：

~~~text
params/result canonical data events
~~~

### CRPC

拥有：

~~~text
JSON-RPC 2.0 envelope
method/id
remote error
notification/batch semantics
RPC deadline
local request handle
~~~

### CHTTP

拥有：

~~~text
HTTP request/response
headers/body limits
H1/H2
connection pool integration
server routing/middleware
~~~

### CNet

拥有：

~~~text
connection/session/TLS transport progress
~~~

### NativeIO

拥有：

~~~text
native operation progress/completion
~~~

RPC 不需要成为：

~~~text
socket runtime
~~~

这就是 Module Owns Meaning 的高级应用。

---

## 4.2 Method Identity 与 Callable Metadata 也必须分开

一个 RPC method在 wire 上由：

~~~text
service/name
or
wire method name
~~~

决定。

本地可以额外绑定：

~~~text
cmeta_callable
~~~

描述：

~~~text
signature
effects
properties
~~~

但必须保持：

> **Local callable semantics 不等于 wire schema。**

当前 CRPC 在 admission/register 时：

~~~text
copy/bind callable metadata
~~~

response/request view消费的是稳定 snapshot。

CRPC 不：

~~~text
用 CMeta 猜 JSON wire schema
在 runtime 自动 invoke 这个 callable
~~~

这条边界非常重要。

否则：

~~~text
CMeta metadata
~~~

会从 semantic description 滑向隐式 RPC code execution framework。

---

## 4.3 Params/Result 复用 CSerde，而不是专用 JSON AST API

RPC params encoder写入：

~~~text
exactly one Array or Map root
~~~

through：

~~~text
cserde_writer
~~~

result/error data通过：

~~~text
single-pass cserde_reader
~~~

读取。

这样 RPC protocol 关心：

~~~text
JSON-RPC envelope shape
~~~

而 params/result semantic payload继续使用 canonical value protocol。

这让未来：

~~~text
local test provider
non-JSON internal binding
schema validator
native binder
~~~

可以共享同一 data semantics，而不必强绑一个 JSON DOM。

---

## 4.4 Blocking API 与 Async API 共享协议，但 Ownership 不同

普通业务路径：

~~~text
crpc_client_init
    ↓
crpc_request_reply
    ↓
owning crpc_response
    ↓
crpc_response_destroy
~~~

caller 不需要：

~~~text
poller
executor
worker thread
~~~

高级 caller-driven path：

~~~text
crpc_async_client_init
    ↓
submit
    ↓
generation-checked request handle
    ↓
poll / cancel
    ↓
exactly-once terminal callback
    ↓
stop
    ↓
destroy
~~~

两种 API 不是两个 RPC semantic system。

它们只是两种 progress ownership。

---

## 4.5 JSON-RPC ID 与 Local Request Handle 是两个 Identity

这是一个很好的 identity 案例。

~~~text
request_id
    = JSON-RPC wire identity

crpc_request {slot, generation}
    = local cancellation/lifetime capability
~~~

两者不能混用。

为什么需要 generation？

因为：

~~~text
slot reused
    ↓
old handle must not cancel new request
~~~

所以：

~~~text
slot + generation
~~~

表达的是 local stale-handle protection。

这和 Actor STALE、Graph version/certificate 都是同一个模式：

> **Representation slot 可以复用，但 semantic lifetime identity 必须能区分 generation。**

---

## 4.6 Deadline 不是“超时就 free”

RPC deadline 到期后：

~~~text
request cancellation
~~~

只是向下层发出 control request。

在：

~~~text
CHTTP
CNet
NativeIO
~~~

真正给出 terminal completion 前：

~~~text
payload
parser
callback state
request handle
TLS/profile dependency
~~~

仍然可能需要存活。

所以：

~~~text
deadline reached
    ≠
all underlying work already quiescent
~~~

这和前面 Reactive cancel / Actor destroy 的原则完全一致：

> **Cancellation is a protocol, not an immediate memory reclamation event.**

---

## 4.7 No Automatic Retry：RPC 特别不能偷偷 replay

当前 CRPC 明确：

~~~text
accepted send之后发生断线
    → original error path
    → no automatic replay
~~~

为什么？

因为 method 可能有副作用：

~~~text
charge card
create order
send message
modify state
~~~

底层根本不知道：

~~~text
request 是否已经被服务器执行
~~~

因此 transport retry 不是：

~~~text
“提高可靠性的小优化”
~~~

而是 application semantic policy。

只有更高层明确知道：

~~~text
idempotency key
deduplication
transaction semantics
retry budget
~~~

时，才有资格做 retry。

这正是 No Silent Fallback / Module Owns Meaning 的实际例子。

---

## 4.8 Server Registry 也必须 Bounded / Pre-start Admission

当前 server：

~~~text
init
    ↓
bounded method registry
    ↓
register target + wire method
    ↓
start
~~~

start 后 register返回：

~~~text
BUSY
~~~

duplicate key：

~~~text
ALREADY
~~~

registry full：

~~~text
ENOBUFS
~~~

这说明 method table 不是：

~~~text
runtime unordered_map that grows forever
~~~

而是 control-plane bounded artifact。

同样：

~~~text
JSON depth
batch items
method bytes
HTTP headers/body
network resources
~~~

都有 hard bounds。

---

## 4.9 Exactly-Once Completion：RPC 的另一条核心 invariant

Async client：

~~~text
submit accepted
    ↓
eventually exactly one terminal callback
~~~

immediate admission failure：

~~~text
no callback
~~~

server handler：

~~~text
normal call
    ↓
exactly one response_result or response_error
~~~

第二次 completion：

~~~text
EALREADY
~~~

notification：

~~~text
handler runs
but response bytes suppressed
~~~

这些都属于 protocol semantics，而不是 implementation convenience。

一个 RPC toolkit如果连“completion 到底几次”都没有明确 contract，就很难安全组合 Actor/Executor/Workflow。

---

## 4.10 Error Surface 必须区分 Domain Failure 与 Transport Failure

合法 JSON-RPC error object：

~~~text
REMOTE_ERROR
~~~

不是：

~~~text
socket failure
HTTP parse failure
deadline
decode failure
invalid envelope
~~~

当前 error context区分：

~~~text
Salts status
native status
HTTP status
stable stage
~~~

这延续第十二章的 semantic error design：

> **只有 caller 会采取不同动作的错误，才值得拥有不同 public category。**

---

## 4.11 Evidence：RPC 需要协议、网络、生命周期三层测试

当前 CRPC verification 已覆盖：

~~~text
bounded codec
UTF-8
integer boundaries
malformed envelope
remote error
real HTTP round trip
h2c
TLS H1/H2
multi-endpoint request/reply
owning response
CMeta callable metadata
deadline
duplicate id
manual cancel
callback reentrancy
server lifecycle
middleware/session
notification suppression
ordered batch
protocol error mapping
~~~

这正好展示复杂应用的 evidence 不可能只有：

~~~text
Lean theorem
~~~

这里需要：

~~~text
protocol tests
real transport round-trip
bounded-resource tests
lifecycle tests
TLS/H1/H2 matrix
header/package tests
sanitizer
performance/load tests
~~~

形式化如果介入，应优先选择：

~~~text
request lifecycle
exactly-once completion
batch ordering
retry/admission law
typed method/schema relation
~~~

这些稳定 semantic core，而不是尝试证明 TCP 实现。

---

## 5. Deep Case D：TinyTest / TinyMock——finite meta 也可以改善测试工具，而不制造测试 VM

测试代码同样会积累重复契约。

最简单的 Plain C assertion 往往长这样：

~~~c
if (actual != expected) {
    fprintf(stderr, "expected %d, got %d\n", expected, actual);
    abort();
}
~~~

当类型增加以后，很容易继续复制：

~~~text
assert_int_equal
assert_u64_equal
assert_double_equal
assert_string_equal
assert_pointer_equal
...
~~~

TinyTest 使用 strict C11 generic assertions，把这一组稳定的 type dispatch 收成一个入口：

~~~c
#include "tinytest.h"

spec("math") {
    it("keeps type-aware assertions") {
        int actual = 1 + 2;
        check_equal(actual, 3);
        check_greater(actual, 0);
    }
}
~~~

这里的 `check_equal(actual, expected)` 会根据有限 builtin type family 选择正确比较逻辑；未注册的复杂结构在 compile time 被拒绝，而不是运行时猜测。

## 5.1 Mock 也是同一个问题：函数签名、参数比较、返回值脚本不要每次手写

edition snapshot 中 TinyMock 可以直接生成一个有限 C wrapper：

~~~c
#include "tinymock.h"

TINYMOCk_MOCK(int, add, int, int)

spec("calculator") {
    it("uses the expected dependency call") {
        mock_add_reset();
        mock_add_expect(
            TINYMOCk_ARG(2),
            TINYMOCk_ARG(3),
            TINYMOCk_RETURN(5));

        check_equal(add(2, 3), 5);
        mock_add_verify();
    }
}
~~~

真实 runtime state 仍然是普通、固定上限的 C struct；snapshot 明确限制：

~~~text
max args          = 6
max expectations  = 32
max calls         = 32
max scripts       = 32
~~~

这意味着 mock framework 不需要一个动态对象系统或解释器来表达最常见的 expectation/return script。

## 5.2 更重要的设计：TinyTest 不强迫依赖 CMeta runtime

TinyTest 的 runtime 是只依赖 libc 的 static library。

C11 test translation unit 里只保留必须在调用点展开的 generic assertion / generated mock wrapper；runner、formatting、script state、verification 都在 compiled C library 中。

这和 CSTL 的边界非常相似：

~~~text
call-site type knowledge
    stays in a thin header layer

runtime algorithm/state
    stays in ordinary compiled C
~~~

因此 TinyTest 是一个很好的反例：

> **“采用有限 Meta 的设计方法”不等于“所有模块都必须依赖 CMeta”。**

真正应该复用的是设计原则：有限 vocabulary、compile-time rejection、bounded runtime state、清楚 ownership，而不是强迫模块共享不需要的 dependency。

---
## 6. 四个 Deep Case 的共同结构

Serialization/Binding 与 RPC 看起来相差很远。

但把细节拿掉以后，它们共享同一个方法：

~~~text
1. 找到已有 Plain C problem
2. 分离不同 semantic owners
3. 让稳定知识拥有单一事实源
4. 在 boundary 上做 typed admission
5. resource capacity 显式 bounded
6. ownership / lifetime 显式
7. dynamic behavior 只留在必要边界
8. failure 不 silent fallback
9. formalize reusable semantic laws
10. 用真实 runtime/toolchain tests补齐 proof 外的证据
~~~

也就是说：

> **高级应用不是“Core 又多了一个 Feature”，而是 primitive architecture 是否真的具有组合力的测试。**

---

## 7. Extension Map：其他领域应该怎样复用，而不是进入 Core

下面的方向仍然值得研究，但默认应先作为上层组合存在。

## 7.1 Plugin

可复用：

~~~text
Semantic Type Identity
Interface
Capability
ABI version
Admission
Explicit Lifecycle
~~~

Plugin core真正需要的新 primitive只有在：

~~~text
多个不同 plugin domain
重复出现同一个稳定 contract
~~~

以后才考虑下沉。

## 7.2 Event Bus / Command Bus

可复用：

~~~text
Typed Event
Bounded Mailbox
Publisher/Subscriber
Executor
Actor refs
~~~

Bus-specific routing、fanout、retention、delivery guarantee属于 domain policy。

## 7.3 Workflow

可组合：

~~~text
Graph
Machine/Statechart
Actor
Timer
Executor
Persistence adapter
~~~

Retry / compensation / durability / lease仍然必须显式。

Workflow 不应该因此获得：

~~~text
its own hidden thread runtime
its own type universe
~~~

## 7.4 ECS / Query

可复用：

~~~text
Type identity
Traits
Range
Predicate
Typed Graph
Plan/Direct lowering
~~~

component storage/layout/query planning属于 ECS/domain implementation。

## 7.5 Parser / Protocol

Parser拥有 syntax/protocol grammar。

如果输出需要进入业务 dataflow：

~~~text
parser
    ↓
complete semantic event/value
    ↓
CFlow
~~~

不要为了“统一”强迫：

~~~text
raw lexer token
~~~

成为业务 Stream item。

## 7.6 Device / UI / Service Runtime

可复用：

~~~text
Typed Event
Machine/Statechart
Actor
Executor
Scheduler
Reactive
~~~

但设备驱动、UI rendering、service discovery等 domain meaning不应下沉到 CFlow kernel。

---

## 8. Application Admission Checklist

未来增加一个“高级应用”以前，可以先回答十个问题。

~~~text
1. Plain C version是什么？
2. 哪些知识真的重复？
3. 已有哪个 primitive 已经拥有这份 semantics？
4. 是否正在创建第二套 Type/Identity system？
5. 是否正在创建第二套 Scheduler/Executor/Runtime？
6. ownership/capacity/cancel/terminal 是否显式？
7. 哪些 error 会让 caller 采取不同动作？
8. 哪些 law 值得 Lean 证明？
9. 哪些事实只能靠 toolchain/runtime test？
10. 这个 feature 能否保持在上层，而不是进入 Core？
~~~

如果第 10 个问题答案是：

~~~text
可以
~~~

那通常应该：

> **先留在上层。**

Core 的稳定来自：

~~~text
少
慢变化
高复用
明确边界
~~~

而不是 feature 数量。

---

## 9. What We Learned

第十三章真正证明的不是：

~~~text
CMeta/CFlow 什么都能做
~~~

而是：

> **一组边界清楚的 primitive 可以让高级应用少重复很多基础知识。**

Deep Case A 展示：

~~~text
Concrete Format
    ↓
CSerde
    ↓
CBind + CMeta
    ↓
Native Value
    ↓
CFlow when needed
~~~

其中：

~~~text
syntax
token grammar
semantic shape
native lifecycle
execution
~~~

各自只有一个 owner。

Deep Case C（RPC）展示：

~~~text
CMeta/CSerde
    ↓
CRPC
    ↓
CHTTP
    ↓
CNet
    ↓
NativeIO
~~~

其中 RPC没有重新发明：

~~~text
type system
serializer
socket runtime
connection pool
retry policy
scheduler
~~~

而是在正确 boundary 上组合现有能力。

Deep Case D（TinyTest / TinyMock）则展示：

~~~text
finite C11 type dispatch
    ↓
typed assertion / generated mock wrapper
    ↓
bounded compiled C runtime
~~~

而且它刻意不要求 CMeta runtime dependency，说明“有限 Meta”首先是一种设计纪律，而不是依赖扩张策略。

这就是 Modern C infrastructure 真正成熟的表现：

~~~text
higher-level behavior increases

but

core primitives do not multiply at the same rate
~~~

下一章必须反过来回答：

> **什么时候这种组合仍然是不值得的？什么时候普通 C、一个 switch、一个 for loop、一个 function pointer 就已经是更好的答案？**

这就是“什么时候停止 Meta 化”。


