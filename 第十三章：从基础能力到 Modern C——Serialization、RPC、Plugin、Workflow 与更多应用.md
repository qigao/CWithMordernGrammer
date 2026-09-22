# 第十三章：从基础能力到 Modern C——Serialization、RPC、Plugin、Workflow 与更多应用


> **本章路线**
>
> 这一章不再把 Serialization、RPC、Plugin、Workflow、ECS、Query 当成一串“还能做什么”的 Feature List。
>
> 我们选择两个已经有真实实现边界的深案例：
>
> ~~~text
> Case A
> Concrete Format
>      ↓
> CSerde Canonical Tokens
>      ↓
> CBind + CMeta Semantic Shape
>      ↓
> Native C Value
>      ↓
> optional CFlow composition
>
> Case B
> CMeta Method Semantics + CSerde Params/Result
>      ↓
> JSON-RPC Envelope
>      ↓
> CHTTP
>      ↓
> CNet
>      ↓
> NativeIO
> ~~~
>
> 两个案例都回答同一组问题：
>
> **复用了哪些 primitive？谁拥有 semantic truth？谁拥有 runtime？资源在哪里 bounded？错误在哪里 fail-fast？证据是什么？**
>
> Plugin、Event Bus、Workflow、ECS、Query、Parser、Protocol 继续保留，但作为 extension map，而不是继续制造新的 core framework。

做到上一章以后，CMeta 和 CFlow 的边界已经比较清楚。

CMeta 提供的是：

```text
Type
Traits
Generic
Callable
Interface
Schema
Finite Relation
Semantic Identity
```

CFlow 则进一步提供：

```text
Graph
Operator
Executor
Scheduler
Subscription
Event
Machine
Actor
```

如果继续按照传统 Framework 的思路，很容易开始问：

```text
还可以再做什么？

CStream？
CRx？
CActor？
CWorkflow？
CRPC？
```

然后不断增加新的大型模块。

但前面几章真正得到的经验恰恰相反。

我们越来越发现：

> **真正有价值的不是不断增加 Framework，而是确认已经形成的 primitive 能否继续组合解决其他问题。**

因此这一章并不是要制定一张：

```text
未来 Feature List
```

而是重新观察：

> 当 C 已经拥有一套有限的 Type、Callable、Graph 和 Execution substrate 后，哪些原本需要大量约定和重复代码的问题，可以自然建立在这些基础上？

---

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

出版稿改用两个深案例作为主干：

~~~text
Serialization / Data Binding
    → 检验 semantic truth、format boundary、native lifecycle

RPC
    → 检验 typed semantics、protocol layering、bounded runtime、cancellation
~~~

其他方向保留在后面的 Extension Map，只说明复用哪些 primitive 以及哪些 domain semantics 不应进入 Core。

---

## 2. Deep Case A：Serialization / Data Binding

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

## 2.1 Plain C Baseline：手写 parser → struct 并没有错

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

## 2.2 第一层：Concrete Parser 只拥有 Syntax

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

## 2.3 第二层：CSerde 只拥有 Format-Neutral Token Truth

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

## 2.4 第三层：CMeta 提供 Native Semantic Shape

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

## 2.5 第四层：CBind 是 Format-Neutral Decode Kernel

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

## 2.6 Failure Atomicity：绑定失败后 Native Graph 回到 Semantic Zero

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

## 2.7 Boundedness：Serialization 也不能偷偷无限增长

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

## 2.8 Binding 后才进入 CFlow

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

## 2.9 Evidence：这个案例怎样证明自己不是“漂亮架构图”

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

## 3. Deep Case B：RPC 不是“再造一个网络 Runtime”

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

## 3.1 RPC Stack 先按 Ownership 分层

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

## 3.2 Method Identity 与 Callable Metadata 也必须分开

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

## 3.3 Params/Result 复用 CSerde，而不是专用 JSON AST API

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

## 3.4 Blocking API 与 Async API 共享协议，但 Ownership 不同

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

## 3.5 JSON-RPC ID 与 Local Request Handle 是两个 Identity

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

## 3.6 Deadline 不是“超时就 free”

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

## 3.7 No Automatic Retry：RPC 特别不能偷偷 replay

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

## 3.8 Server Registry 也必须 Bounded / Pre-start Admission

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

## 3.9 Exactly-Once Completion：RPC 的另一条核心 invariant

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

## 3.10 Error Surface 必须区分 Domain Failure 与 Transport Failure

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

## 3.11 Evidence：RPC 需要协议、网络、生命周期三层测试

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

## 4. Engineering Cases C–E：Async I/O、CSTL 与 Testing

前两个 Deep Case 证明了 CMeta/CFlow 可以支撑跨层业务能力。

下面三个更短的工程案例回答另一个问题：

> **这些设计是否也能进入普通基础库，而不是只适合“大 framework”？**

### 4.1 Async file/network：Reactive 定义等待语义，Executor 只负责交付

第八、九章已经建立了一条很重要的边界：

~~~text
I/O request / readiness
    owns completion truth
        ↓
WAIT / wake
    transports readiness
        ↓
Subscription / Executor
    owns resumption and execution admission
~~~

本版 Salts 快照中的 Reactive source outcome 是有限五态：

~~~text
CFLOW_STEP_VALUE
CFLOW_STEP_VALUE_AND_DONE
CFLOW_STEP_WAIT
CFLOW_STEP_DONE
CFLOW_STEP_ERROR
~~~

外部 file/socket driver 不需要知道 Graph，也不应该直接修改 Graph execution state。

它只需要在 completion/readiness 发生时调用已经定义好的 wake boundary；
`cflow_subscription_wake()` 再把执行重新交回 Subscription / Scheduler。

这让异步文件和网络接入不需要再发明一套：

~~~text
async operator system
async type system
async graph
async thread ownership model
~~~

同样的 typed Graph 只是 source 开始拥有时间。

这一点在 RPC stack 中继续向下组合：

~~~text
CRPC
  ↓
CHTTP
  ↓
CNet
  ↓
NativeIO terminal completion
~~~

因此“异步能力”不是 Core 多一个 framework，而是 WAIT/Wake、Executor、ownership 与 completion contract 被复用。

### 4.2 CSTL：Generic 只生成 typed contract，算法仍然是普通 C

容器是 Part I 的 Generic 设计最直接的工程验证。

如果每个容器 family 都拥有自己的宏入口，用户很快会面对：

~~~c
DECLARE_VEC(IntVec, int);
DECLARE_LIST(IntList, int);
DECLARE_HASHMAP(IntLongHashMap, int, long);
~~~

问题不是这些宏不能工作，而是每个 family 都在重新定义“怎样声明一个 typed application”。

本版 Salts 快照的 CSTL 使用同一个 CMeta Generic 入口：

~~~c
#include <cstl/typed.h>

typed(Vec, IntVec, int);
typed(List, IntList, int);
typed(HashMap, IntLongHashMap, int, long);
typed(Map, IntLongMap, int, long);
typed(BTree, IntTree, int, long);
~~~

生成后的使用仍然是普通 C：

~~~c
IntList values = {0};
IntLongMap index = {0};

IntList_init(&values, 100u);
IntList_push_back(&values, 10);
IntList_push_back(&values, 20);

IntLongMap_init(&index, 100u);
IntLongMap_put(&index, 7, 70L);

IntLongMap_destroy(&index);
IntList_destroy(&values);
~~~

这里最值得注意的不是语法缩短，而是实现边界。

edition snapshot 明确把：

~~~text
typed wrapper / descriptor / Range traits
    留在薄的 generated/static-inline surface

vector growth / hashing / tree balancing / allocation
    留在 compiled CSTL C implementation
~~~

所以：

> **finite Meta 负责统一契约，不负责把容器算法变成宏。**

这正是本书最核心的方法：Meta 越成熟，真正 runtime C 反而越普通。

CSTL 还能直接进入前面的 Graph/Stream 世界，而不需要第二套 collection pipeline。

### 4.3 TinyTest / TinyMock：测试框架也可以复用有限 typed design

测试框架常见的重复同样不是算法，而是类型分派：

~~~text
check_int_equal
check_long_equal
check_double_equal
check_string_equal
check_pointer_equal
...
~~~

edition snapshot 的 TinyTest 把它收敛成 strict-C11 generic assertions：

~~~c
#include "tinytest.h"

spec("strncmp") {
    it("should return 0 when strings are equal") {
        check(strncmp("foo", "foo", 12) == 0);
    }
}

check_equal(actual, expected);
check_not_equal(actual, expected);
check_greater(actual, expected);
check_within(actual, expected, margin);
~~~

更有意思的是，自定义 C value 可以只注册它需要的 equality fact：

~~~c
typedef struct Point {
    int x, y;
} Point;

static bool point_equal(const Point *actual, const Point *expected)
{
    return actual->x == expected->x && actual->y == expected->y;
}

#define TTEST_USER_EQUAL_TRAIT_LIST , (POINT, Point, point_equal)
#include "tinytest.h"

check_equal((Point){1, 2}, (Point){1, 2});
~~~

这里甚至刻意不要求 production code 依赖 CMeta。

TinyTest 复用的是同一种**有限 trait-map 设计**：

~~~text
known value kinds
    ↓
_Generic admission
    ↓
typed comparator
    ↓
compiled test runtime
~~~

这说明真正可复用的不是某个宏名字，而是设计方法。

TinyMock 进一步使用同一 strict-C11 trait map；snapshot 中 runtime state、comparison、formatting、scripting 与 verification 都在 compiled TinyTest library 中，header 只保留必须在调用点生成的 mock wrapper。

它还明确把资源做成有限上界，例如：

~~~c
#define TINYMOCk_MAX_ARGS 6
#define TINYMOCk_MAX_EXPECTATIONS 32
#define TINYMOCk_MAX_CALLS 32
#define TINYMOCk_MAX_SCRIPTS 32
~~~

这再次出现全书同一个原则：

> **有限、显式、调用点需要的留 header，其余逻辑回到普通 compiled C。**

CSTL 与 TinyTest 还可以直接组合。snapshot 提供 `<cstl/tinytest.h>`：

~~~c
#include <cstl/typed.h>

typed(Vec, IntVec, int);

#include <cstl/tinytest.h>

CSTL_TINYTEST_DEFINE_SEQUENCE_EQUAL(IntVec, int)

check_cstl_equal(IntVec, actual, expected);
~~~

这里 comparator bridge 借用 container，不复制 storage-owning handle。

所以 testing 并不是脱离 CMeta/CSTL 的独立故事；它说明同一份 typed identity / trait contract 可以跨 library boundary 被安全消费。

---
## 5. 五个案例的共同结构

Serialization/Binding、RPC、Async I/O、CSTL 与 Testing 看起来相差很远。

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

## 6. Extension Map：其他领域应该怎样复用，而不是进入 Core

下面的方向仍然值得研究，但默认应先作为上层组合存在。

## 6.1 Plugin

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

## 6.2 Event Bus / Command Bus

可复用：

~~~text
Typed Event
Bounded Mailbox
Publisher/Subscriber
Executor
Actor refs
~~~

Bus-specific routing、fanout、retention、delivery guarantee属于 domain policy。

## 6.3 Workflow

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

## 6.4 ECS / Query

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

## 6.5 Parser / Protocol

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

## 6.6 Device / UI / Service Runtime

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

## 7. Application Admission Checklist

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

## 8. What We Learned

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

Deep Case B 展示：

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

Engineering Cases C–E 进一步说明：

~~~text
Async I/O
    复用 WAIT/Wake + Executor + completion ownership

CSTL
    复用 typed(...) / Traits，但算法仍是 compiled C

TinyTest/TinyMock
    复用 finite trait-map / _Generic admission，runtime 仍是 compiled C
~~~

它们共同证明：

> **有限 Meta 的价值不在“把所有库统一成一个 framework”，而在让不同库共享同一类契约设计，同时保留各自正确的 runtime owner。**

这就是 Modern C infrastructure 真正成熟的表现：

~~~text
higher-level behavior increases

but

core primitives do not multiply at the same rate
~~~

下一章必须反过来回答：

> **什么时候这种组合仍然是不值得的？什么时候普通 C、一个 switch、一个 for loop、一个 function pointer 就已经是更好的答案？**

这就是“什么时候停止 Meta 化”。


