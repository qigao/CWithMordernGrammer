# Chapter Template

本模板用于约束下一轮章节重写。

核心规则：

> **Code / pseudocode / flow / logic first. Prose only connects artifacts.**

不是每章都必须机械使用相同标题，但重要 claim 必须有可检查对象。

---

# 1. Artifact rule

每个主要小节至少包含下面一种 artifact：

- C code；
- generated/lowered C；
- pseudocode；
- state/flow diagram；
- type/logic judgment；
- Lean theorem/proof sketch；
- test/ABI/benchmark evidence。

默认不要连续写超过两段纯解释 prose。

如果一段文字只是说“更优雅 / 更现代 / 更灵活 / 更容易扩展 / 能力更强”，下一段必须回答至少一个具体问题：删掉了哪段重复代码？新增了哪一个数据结构？哪个错误提前了？哪个 runtime branch 消失了？哪个 theorem 授权了哪个 transformation？哪个 benchmark 测到了什么？

## Text fence rule

`~~~text` 不是强调框，也不是“看起来更技术”的排版手段。

只有当**等宽布局本身承载语义**时才使用 fenced text，例如：

- pipeline / dataflow；
- state machine；
- race/interleaving timeline；
- inference rule / proof judgment；
- pseudocode；
- 需要对齐的 IR / memory layout。

简单说明不要放进 fenced text。以下内容优先使用普通 Markdown：

- 一个术语或一句结论 → 正文或行内代码；
- 两三个定义对比 → 表格；
- 一组无顺序的项目 → bullet list；
- 简单等式 → 行内公式/单独一行普通文本；
- “A 不是 B” → 直接写成一句话。

判断规则：

> **如果去掉等宽字体和对齐后，信息完全不变，就不应该使用 `~~~text`。**

---

# 2. Start with executable Plain C

先给能工作的普通 C。

例如：

~~~c
int get_user_http(
    void *ctx,
    const chttp_server_request_view *req,
    chttp_server_response *res)
{
    const char *id = chttp_server_request_param(req, "id");
    ...
}
~~~

不要先写：

~~~text
“HTTP binding 存在重复契约问题。”
~~~

先让读者看到重复在哪里。

这一节必须回答：

- baseline 是否正确？
- 为什么小系统这样写完全合理？
- 哪个事实开始重复？
- 哪个 ownership/lifetime 已经隐含在约定里？

---

# 3. Show the duplicate fact, not just duplicate code

例如：

~~~c
int get_user(UserRepository *, uint64_t, User *);
~~~

同时还有 HTTP route、RPC method、Plugin export、OpenAPI parameter 和 Mock signature。

真正重复的是 **logical operation contract**。

不是几行相似代码。

必须把“重复代码”和“重复知识”区分开。

---

# 4. Introduce the smallest semantic object

新增设计必须能写成一个具体对象。

例如：CMeta TypeDesc、CMeta FunctionDesc、DataBind Service Operation、CFlow Graph Node、BindingPlan、Machine Transition 或 Plugin lease。

必须明确 identity、owner、lifetime、capacity、failure、mutable/immutable，以及 semantic truth 与 representation 的区别。

不要只画一个“Layer A -> Layer B”的图。

---

# 5. Show the representation

每个 abstraction 都要回答：

> **它最后是什么 C data/function？**

例如 FunctionDesc：

~~~c
typedef struct cmeta_param_desc {
    const char *name;
    const cmeta_type_desc *type;
    uint32_t flags;
} cmeta_param_desc;
~~~

例如 plan：

~~~c
typedef struct http_method_plan {
    chttp_method method;
    const char *route;
    const databind_ingress_plan *ingress;
    const service_exact_adapter *invoke;
    const databind_egress_plan *egress;
} http_method_plan;
~~~

概念性 layout 可以不是最终 ABI，但必须足够具体，让读者知道 runtime 拿到什么。

---

# 6. Show the compiler/control-plane algorithm

如果章节存在 build/admission phase，就给 pseudocode。

例如：

~~~text
compile_service(op, function):
    require compatible(op.request, function.inputs)
    require compatible(function.outputs, op.response)

    ingress = compile_ingress(op, function)
    invoke  = generate_exact_adapter(function)
    egress  = compile_egress(function, op)

    return BindingPlan(ingress, invoke, egress)
~~~

不要用“系统自动完成绑定”代替算法。

---

# 7. Use a flow diagram only after code/pseudocode

流程图总结 ownership 或阶段。

例如：

~~~text
Service IR
    +
FunctionDesc
    ↓
validate
    ↓
BindingPlan
    ↓
exact adapter
    ↓
ordinary C call
~~~

图不能代替 baseline code。

---

# 8. Write semantic judgments when there is a rule

不一定每次都用 Lean。

可以先用简单 logic。

例如字段绑定：

~~~text
Γ ⊢ field : T
Γ ⊢ param : U
convertible(T, U)
────────────────────
Γ ⊢ bind(field, param) : valid
~~~

例如 transactional commit：

~~~text
bind(input) = error
──────────────────────
observable(output) = unchanged
~~~

例如 state transition：

~~~text
(state, event) -> (state', effects)
~~~

写清 judgment 后再决定需不需要 machine-check。

---

# 9. Lean only for a real semantic obligation

适合：

~~~text
rewrite preservation
normalization
state determinism
terminal/lifecycle invariants
protocol refinement
certificate relation
~~~

每个 theorem 后必须紧跟：

> **这个 theorem 授权 C implementation 做什么？**

例如：

~~~text
theorem map_fusion_preserves_eval
    ↓
optimizer may replace two admitted Map nodes with one fused Map
~~~

不适合用 Lean 替代：

~~~text
ABI link test
DSO loading
sanitizer
malloc failure test
benchmark
OS/network liveness
~~~

---

# 10. Always separate descriptive and executable objects

特别是下面几组必须明确区分：

| 描述/语义对象 | 不能混同为 |
|---|---|
| FunctionDesc | Callable |
| Service Contract | HTTP MethodPlan |
| Component | Plugin DLL |
| InterfaceDesc | live `{self,vtable}` |
| Graph | Compiled Plan |
| metadata property | semantic proof |

如果章节把“描述”与“执行”混成一个对象，需要重写。

---

# 11. Show lowering / hot path

高级 abstraction 必须说明 runtime 是否仍然查询它。

例如：

~~~text
build:
IDL + FunctionDesc -> HTTP MethodPlan

runtime:
request -> MethodPlan -> exact adapter -> response
~~~

然后给普通 C endpoint：

~~~c
return plan->invoke(plan->ctx, request, response);
~~~

如果 Graph eligible for Direct/AOT：

~~~c
for (...) {
    if (!is_even(x))
        continue;
    total += square(x);
}
~~~

全书的目标是：

> **Know more before execution; do less during execution.**

---

# 12. Include one explicit failure case

每章至少给一个失败例。

例如：

~~~text
IDL says:
    GetUserRequest.id : uint64

native function says:
    const char *id

no explicit conversion
        ↓
generation fails
~~~

或者：

~~~text
Plugin unload
    while interface lease > 0
        ↓
BUSY
~~~

或者：

~~~text
Graph rewrite
    lacks required semantic law
        ↓
optimizer does not rewrite
~~~

Fail-fast 行为比“happy path architecture”更能说明边界。

---

# 13. Evidence must match the claim

| Claim | Evidence |
|---|---|
| generated type/function compiles | compile-pass/fail |
| same identity across TU | Multi-TU |
| installed ABI works | independent installed consumer |
| DSO lifecycle safe | integration + sanitizer/stress |
| semantic rewrite valid | theorem + differential test |
| request binding atomic | failure-path integration test |
| docs match HTTP runtime | shared projection IR + contract test |
| faster | benchmark |

不要用 unit test 代替 universal semantic proof，不要用 Lean theorem 代替 ABI/link qualification，也不要用 benchmark 代替 correctness evidence。

---

# 14. Canonical chapter flow

推荐：

~~~text
1. Plain C baseline
2. Concrete duplicated/implicit knowledge
3. Minimal semantic object
4. Representation in C
5. Compiler/control-plane pseudocode
6. Flow diagram
7. Semantic judgment / invariant
8. Lean only if necessary
9. Generated/lowered ordinary C
10. Failure case
11. Evidence
12. What changed / what did not change
~~~

---

# 15. Canonical examples

## Typed data

~~~c
typedef struct User {
    uint64_t id;
    const char *name;
} User;
~~~

用于 Generic / Struct / Traits / DataBind / ABI。

## Typed computation

~~~c
long sum_even_squares(const int *xs, size_t n);
~~~

用于 Callable / Graph / Stream / Lean / Optimize / Direct。

## Service contract

~~~text
service UserService {
    GetUser: GetUserRequest -> GetUserResponse;
}
~~~

Native：

~~~c
int get_user(
    UserRepository *repo,
    uint64_t id,
    User *out_user);
~~~

用于 FunctionDesc / DataBind binding / HTTP / RPC / Plugin / WASM / OpenAPI / Mock。

## Connection runtime

~~~text
DISCONNECTED
CONNECTING
CONNECTED
CLOSING
~~~

用于 Reactive / Executor / Machine / Actor / lifecycle proof。

---

# 16. Final editing check

删除或改写一个段落，如果它不能回答至少一个问题：

~~~text
What is the C representation?
What fact became single-source?
Who owns it?
When can it fail?
What exact algorithm consumes it?
What is observable?
What theorem/invariant applies?
What leaves the hot path?
What evidence supports the claim?
~~~

如果一个 abstraction 只能用形容词解释，而不能用代码、IR、logic 或 evidence 表示，它还没有写清楚。

提交前可以运行：

~~~bash
python scripts/audit_text_fences.py --edition cn
python scripts/audit_text_fences.py --edition en
~~~

这个脚本只报告疑似“说明性 text fence”，作为编辑提示，不作为硬性 publication gate。
