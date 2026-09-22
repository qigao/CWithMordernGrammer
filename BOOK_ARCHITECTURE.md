# Book Architecture — 从 Plain C 到 Typed and Verified Computation

本文件定义全书下一阶段的结构与编辑约束。

这本书不是 CMeta/CFlow 的 API 手册，也不是一本单独讲 Lean 的形式化教材。它的主题是：

> **如何从最基础的 C 语言出发，逐步构造类型化、可组合、可验证的高级程序，同时让最终执行仍然保持普通 C 的 ABI、性能和可预测性。**

全书的方法可以浓缩成：

~~~text
Understand
    ↓
Model
    ↓
Formalize
    ↓
Verify
    ↓
Implement
    ↓
Lower
    ↓
Measure
~~~

以及：

~~~text
Modern C
=
Plain C Execution
+
Typed Control Plane
+
Verified Semantics
~~~

## 1. 全书的三条主线

### Design

回答“为什么这样设计”。

重点是从普通 C 的真实问题出发，识别最小必要抽象，并明确 ownership、lifetime、admission、failure、fallback、boundedness 以及模块责任边界。

### Semantics / Lean

回答“哪些性质是真的”。

Lean 的职责不是替代 C，而是：

- 把隐含假设变成明确语义；
- 区分 metadata claim 与 semantic law；
- 暴露设计缺失的前置条件；
- 证明合法 rewrite / normalization；
- 建立 small-step semantics、refinement 或 certificate；
- 为优化和状态转换建立可信边界。

不是每章都必须包含大量 Lean 代码，但每章都要明确 observable semantics、值得证明的 invariant/law，以及哪些问题本来就不属于形式化证明。

### Real C Implementation / Evidence

回答“最终怎样落回真实 C”。

逐步补齐：

- public C API；
- struct / descriptor / vtable / generated symbol；
- ownership / lifetime；
- status / error model；
- ABI / Multi-TU；
- runtime layout；
- hot path；
- tests / sanitizer / installed consumer；
- benchmark 与手写 Plain C baseline。

## 2. 每章统一结构

默认骨架：

~~~text
Problem
   ↓
Plain C Baseline
   ↓
Design
   ↓
Semantic Contract
   ↓
Lean / Proof Obligation
   ↓
C Implementation
   ↓
Evidence
~~~

详细要求见 [CHAPTER_TEMPLATE.md](./CHAPTER_TEMPLATE.md)。

核心不是形式整齐，而是让读者始终知道：

> **问题是什么 → 为什么需要抽象 → 抽象承诺什么 → 为什么可信 → 在 C 里怎样实现 → 成本是多少。**

# Part I — 从普通 C 到类型化计算

## Chapter 1 — Macro Reuse

核心问题：普通 C 的重复什么时候从“代码重复”变成“知识重复”？

重点：

- Plain C baseline；
- 最小宏复用；
- preprocessor 边界；
- 为什么宏没有类型；
- _Generic 为什么改变问题性质。

Lean 在本章不是主角。Evidence 侧重 preprocessing、compile diagnostics、cross-compiler behavior 与 generated code。

## Chapter 2 — Type / Traits / Generic / Finite Inference

核心跨越：从生成代码进入描述类型、描述能力、有限推导。

需要加强：

- descriptor 的真实表示；
- semantic identity；
- finite type universe；
- TypeFunction / Predicate；
- Multi-TU implications；
- 可验证性为何来自 finite / explicit。

Lean 目标：

- 有限映射的 totality / uniqueness；
- admissible inference；
- identity 与 representation 的区分。

## Chapter 3 — Callable / Lambda / Bind

核心问题：如何把函数地址提升为带类型、环境和语义属性的可执行对象？

需要闭环：

- function pointer baseline；
- signature normalization；
- capture representation；
- adapter / lambda / bind / generator；
- effects vs properties；
- callable identity；
- inline storage 与 ABI。

Lean 目标：

- signature compatibility；
- composition laws；
- property admission 与 semantic law 的边界。

# Part II — 从 Callable 到可组合执行

## Chapter 4 — Graph as Typed IR

核心跨越：让 computation itself become data。

从这一章开始建立贯穿后续章节的 canonical example：

~~~text
Source<int>
    ↓
Filter<int>
    ↓
Map<int,int>
    ↓
Reduce<int,int>
~~~

本章建立 typed node / edge、validate、type propagation、immutable graph snapshot、surface graph vs normalized graph，并解释为什么 Graph 不直接等于 Runtime。

Lean / semantics：graph well-formedness 与 observable semantics 的最小定义。

Implementation：实际 node/edge representation、builder、failure point 与 ownership。

## Chapter 5 — Stream as a Graph Front-end

核心观点：Stream 是构造 Graph 的高级 façade，而不是另一套 Runtime。

使用 canonical example 从 surface API 一路展开到 typed graph。

Lean / semantics：

- map/filter/reduce operator laws；
- 哪些 fusion 可以证明；
- 哪些仅凭 property bit 不允许做。

Evidence：

- usability；
- generated graph；
- hand-written loop baseline。

## Chapter 6 — Reactive: Time, WAIT, Demand

核心跨越：数据关系保持不变，但执行模型开始拥有时间。

明确：

- WAIT != blocking；
- wake protocol；
- demand；
- subscription；
- bounded resource；
- terminal / cancel；
- lost wakeup。

Lean 目标：

- wake/demand invariant；
- terminal safety；
- selected liveness/safety properties。

Implementation：state representation、atomic/concurrency boundary、manual clock 与 deterministic tests。

## Chapter 7 — Executor

核心原则：Executor 决定怎样执行，不决定执行什么。

加强：

- Manual / Serial / Concurrent；
- bounded queue；
- FULL；
- shutdown；
- Scheduler orthogonality；
- thread/coro/readiness/native async I/O 的位置。

Evidence：deterministic tests、queue saturation、throughput/latency、thread ownership。

# Part III — 有状态、并发与 Lowering

## Chapter 8 — State Machine

核心问题：如何把控制状态也变成 typed, analyzable data？

完整模型：

~~~text
Event Admission
      ↓
Transition Selection
      ↓
Guard
      ↓
Action
      ↓
State Commit
      ↓
Observation
~~~

Lean 是本章的重要设计工具：

- determinism；
- ambiguity；
- terminal properties；
- transition preservation；
- small-step semantics。

Implementation：immutable machine、mutable instance、event representation、serial execution boundary。

## Chapter 9 — Actor

核心观点：Actor 不是一个线程，而是 identity + bounded mailbox + serialized ownership + lifecycle。

Lean / semantics：

- single mutable owner；
- lifecycle admission；
- stale identity；
- ordering assumptions。

Evidence：

- multi-producer；
- bounded mailbox；
- lifecycle race；
- no silent drop。

## Chapter 10 — Rich Control Plane, Simple Execution Plane

这是全书架构核心之一。

~~~text
Surface Graph
    ↓
Normalize
    ↓
Verify / Optimize
    ↓
Compile Plan
    ↓
Direct / Planned Execution
    ↓
Plain C Hot Path
~~~

必须给出完整 end-to-end case：

1. surface API；
2. graph；
3. semantic metadata；
4. normalized IR；
5. Lean-backed rewrite；
6. optimized plan；
7. lowered C execution；
8. benchmark。

这是全书从“设计书”走向“Modern C engineering book”的关键章。

# Part IV — 可信边界与工程边界

## Chapter 11 — Lean and the Trusted Boundary

本章成为全书 proof methodology。

核心链：

~~~text
Graph Pattern
      +
Metadata Admission
      +
Semantic Law
      ↓
Preservation Theorem
      ↓
Manifest / Certificate
      ↓
C Implementation
~~~

区分 claim、invariant、semantic law、theorem、generated fact、certificate、runtime validation。

至少选择 2–3 个前文真实 rewrite / state law 做完整 Lean derivation。

## Chapter 12 — ABI / Multi-TU / Semantic Identity

回答：一个在单 TU demo 中成立的设计，怎样成为真正可安装、可链接、可演进的 C library？

加强真实 engineering evidence：

- installed consumer；
- shared/static；
- symbol ownership；
- descriptor identity；
- ABI surface；
- public struct policy；
- generated code ownership；
- cross-TU tests。

Lean 在这里角色有限但明确：不要把 linker/ABI/toolchain 问题误写成形式化问题。

# Part V — 高级应用、克制与方法论

## Chapter 13 — Serialization / RPC / Plugin / Workflow

从“能力枚举”升级为“组合证明”。

每个高级系统都回答：

~~~text
Which primitives?
Which semantic contracts?
Which runtime pieces?
Which ABI boundary?
Which evidence?
~~~

建议深入两个案例：Serialization / Binding，以及 Workflow / RPC 之一；其他应用作为扩展图谱。

## Chapter 14 — Where Meta Should Stop

这是 anti-overengineering 章节。

用前文案例验证十条纪律：

- finite；
- explicit；
- bounded；
- fail-fast；
- no silent fallback；
- static when possible；
- no hidden runtime；
- cross-compiler semantics first；
- naming does not define ownership；
- module owns meaning。

加入失败设计或 counterexample。

## Chapter 15 — From Macro Reuse to Typed Computation

最终不总结 API，而总结方法论：

~~~text
Plain C
  +
Finite Typed Knowledge
  +
Explicit Semantic Laws
  +
Verified Transformations
  +
Simple Lowered Execution
=
Modern C
~~~

最后重新走一遍：

~~~text
Understand
 → Model
 → Formalize
 → Verify
 → Implement
 → Lower
 → Measure
~~~

并说明什么时候最好的选择仍然是普通 C。

## 3. Lean 在全书中的定位

正确关系：

~~~text
C problem
   ↓
C design
   ↓
semantic question
   ↘
     Lean
   ↙
stronger C design
   ↓
implementation
~~~

不追求 theorem 数量。更重要的是：

- proof 是否改变设计；
- proof obligation 是否暴露缺失前置条件；
- theorem 是否授权真实 optimizer rewrite；
- formal model 是否对应 C runtime observable semantics；
- implementation 是否能通过 refinement / certificate / test 与 formal model 连接。

## 4. Evidence 标准

### Compile-time

- expected compile success/failure；
- static assertion；
- cross-compiler behavior；
- generated symbols/types。

### Runtime

- deterministic unit test；
- state transition test；
- bounded/failure test；
- concurrency stress；
- sanitizer。

### Formal

- Lean theorem；
- finite exhaustive check；
- model invariant；
- preservation proof。

### Performance

只有声明 zero-cost / direct / faster / cheaper 时才必须给 benchmark。

建议至少比较：

~~~text
hand-written C
direct lowered path
compiled plan
graph/interpreted path
~~~

并记录 workload、compiler、optimization level 和 measurement limitations。

## 5. Editorial rules

1. **Plain C first.** 没有 baseline，就不引入抽象。
2. **Code first, meta later.** 先看重复是否真的是稳定知识。
3. **Finite by default.**
4. **Explicit ownership.**
5. **No silent semantic change.**
6. **Lean proves semantics, not marketing claims.**
7. **Metadata is not proof.**
8. **High-level syntax must expose its lowering story.**
9. **Every abstraction must identify its runtime cost center.**
10. **The best endpoint may be ordinary C again.**

## 6. Completion definition

逐章重构完成时，读者应该能走完：

~~~text
repetition
→ reusable fact
→ type knowledge
→ semantic model
→ composable computation
→ stateful/concurrent application
→ Lean-assisted verification
→ optimized/lowered C
→ tests and measurements
~~~

最终获得的不是一套必须采用的 framework，而是一种设计 Modern C 系统的方法。
