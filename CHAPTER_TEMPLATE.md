# Chapter Template

本模板定义逐章重构时的默认结构。它是编辑约束，不要求机械套用标题。

## 1. Problem

从真实的普通 C 问题开始，不提前引入 CMeta/CFlow。

明确：

- 最初简单版本是什么；
- 复杂性从哪里出现；
- 哪些部分只是代码重复；
- 哪些部分已经变成知识重复。

## 2. Plain C Baseline

给出直接 C 实现。

回答：

- 完全不用抽象时代码是什么样；
- 它为什么并不“错误”；
- 什么时候出现组合、状态、维护或安全成本；
- baseline 的性能、ABI、ownership 特征。

> 新抽象必须明确比 baseline 多解决了什么，否则不要引入。

## 3. Design

一步一步引入最小抽象。

必须交代：

- data model；
- API；
- ownership；
- lifetime；
- failure；
- boundedness；
- static/dynamic boundary；
- 哪些事情明确不属于本层。

避免从“我们需要一个 Framework”开始。

## 4. Semantic Contract

用与实现无关的方式说明该层承诺什么。

至少回答：

- observable behavior 是什么；
- invariant 是什么；
- 哪些顺序可观察；
- 哪些状态非法；
- 哪些 metadata 只是 claim；
- 哪些关系是真正 semantic law。

这一节是 C implementation 与 Lean 之间的接口。

## 5. Lean / Proof Obligation

按需要选择：

### A. Full proof

适用于 rewrite correctness、state invariants、finite inference。

### B. Model + key theorem

只建立足以影响设计的 formal model。

### C. Explicit non-proof boundary

明确某问题属于 ABI、allocator、OS scheduling、performance、toolchain 或 empirical concurrency，因此 Lean 不应该假装证明它。

每次引入 theorem，都要回答：

> 这个 theorem 允许 C 实现安全地做什么以前不能做的事情？

## 6. C Implementation

把设计落回真实 C。

尽量包括：

- public declarations；
- private representation；
- generated declarations/definitions；
- actual data layout；
- status/error path；
- cross-TU ownership；
- hot path；
- lowering result。

复杂宏同时给 expansion 或等价 plain-C representation。

## 7. Evidence

按主张选择证据：

- compile-pass / compile-fail；
- unit / integration tests；
- deterministic scheduler tests；
- stress / sanitizer；
- Lean proof；
- exhaustive finite check；
- benchmark；
- generated C / disassembly；
- installed consumer / ABI test。

不能用测试替代 semantic proof，也不能用 theorem 替代 runtime/ABI/performance evidence。

## 8. What We Learned

明确：

- 哪个设计原则被确认；
- 哪个原始假设被推翻；
- Lean 是否改变了设计；
- control-plane knowledge 是否让 runtime 更简单；
- 下一章为什么自然出现。

# Canonical worked examples

从 Chapter 4 开始复用同一个 data-flow example：

~~~text
Source<int>
    ↓
Filter<int>
    ↓
Map<int,int>
    ↓
Reduce<int,int>
~~~

逐章展示 Graph、Stream、Reactive、Executor、Lean rewrite、Optimizer、Lowering 和 benchmark。

State Machine / Actor 使用第二个贯穿案例：

~~~text
Event
 → Admission
 → Transition
 → Guard
 → Action
 → Commit
 → Observation
~~~

这样全书不会退化成 15 组互不相关的设计说明。
