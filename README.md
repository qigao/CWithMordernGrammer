# C with Modern Grammar

[中文](./README_CN.md) | **English**

**C with Modern Grammar** explores how far modern C can be pushed without turning it into another language.

The book starts from a very practical problem: repetitive C code and increasingly difficult macro reuse. From there it develops a layered approach to **typed computation in C**—CMeta, callable objects, graph-based computation, streams, reactive execution, executors, state machines, actors, formal verification boundaries, ABI/Multi-TU engineering, and finally CFlow.

The central idea is simple:

> Keep the execution plane close to ordinary C, while moving richer structure, typing, composition, and verification into explicit control-plane abstractions.

## Why this book

C remains attractive because its runtime model is direct, portable, efficient, and easy to map to the machine. But large C systems repeatedly encounter the same problems:

- boilerplate across types and data structures;
- unsafe or opaque macro expansion;
- limited ways to express reusable computation;
- callback and ownership complexity;
- difficulty composing asynchronous or stateful behavior;
- weak boundaries between metaprogramming and runtime code;
- ABI and multi-translation-unit constraints;
- lack of explicit semantic contracts for optimization and verification.

This book develops one possible answer without requiring C++ templates, a VM, or a new source language.

## The progression

The chapters intentionally build one layer at a time:

```text
Macro reuse
    ↓
Typed macros / traits / generic operations
    ↓
Callable objects
    ↓
Graph
    ↓
Stream
    ↓
Reactive execution
    ↓
Executor
    ↓
State Machine
    ↓
Actor
    ↓
Rich control plane / simple execution plane
    ↓
Verified semantic rewrites
    ↓
ABI + Multi-TU engineering
    ↓
Modern C applications
    ↓
CMeta / CFlow as typed computation
```

The goal is not to make C look like C++. It is to keep the useful properties of C while adding stronger vocabulary for reusable computation.

## Who this is for

This book is intended for developers interested in:

- systems programming and library design;
- advanced C metaprogramming;
- type-oriented APIs in C;
- stream/reactive systems;
- callback, executor, state-machine, and actor design;
- compile-time/runtime separation;
- ABI-stable libraries and Multi-TU design;
- formal reasoning and verified transformations;
- building modern infrastructure while keeping a plain-C execution model.

## Book architecture

The next editorial phase follows a unified **Problem → Plain C → Design → Semantics → Lean → Implementation → Evidence** method. See [BOOK_ARCHITECTURE.md](./BOOK_ARCHITECTURE.md) and the reusable [chapter template](./CHAPTER_TEMPLATE.md).

## Chapters

1. [CMeta's Starting Point — From the Pain of Writing C Macros](./%E7%AC%AC%E4%B8%80%E7%AB%A0%EF%BC%9ACMeta%20%E7%9A%84%E8%B5%B7%E7%82%B9%E2%80%94%E2%80%94%E4%BB%8E%E5%86%99%20C%20%E5%AE%8F%E7%9A%84%E7%97%9B%E8%8B%A6%E5%BC%80%E5%A7%8B.md)
2. [From Macros to Types — Traits, Generic Programming, and Bounded Inference](./%E7%AC%AC%E4%BA%8C%E7%AB%A0%EF%BC%9A%E4%BB%8E%E5%AE%8F%E5%88%B0%E7%B1%BB%E5%9E%8B%E2%80%94%E2%80%94Traits%E3%80%81Generic%20%E4%B8%8E%E6%9C%89%E9%99%90%E6%8E%A8%E5%AF%BC.md)
3. [From Function Pointers to Executable Objects — Callback, Lambda, and Bind](./%E7%AC%AC%E4%B8%89%E7%AB%A0%EF%BC%9A%E4%BB%8E%E5%87%BD%E6%95%B0%E6%8C%87%E9%92%88%E5%88%B0%E5%8F%AF%E6%89%A7%E8%A1%8C%E5%AF%B9%E8%B1%A1%E2%80%94%E2%80%94Callback%E3%80%81Lambda%20%E4%B8%8E%20Bind.md)
4. [From Callable to Graph — Turning Computation Itself into Data](./%E7%AC%AC%E5%9B%9B%E7%AB%A0%EF%BC%9A%E4%BB%8E%20Callable%20%E5%88%B0%20Graph%E2%80%94%E2%80%94%E6%8A%8A%E8%AE%A1%E7%AE%97%E6%9C%AC%E8%BA%AB%E5%8F%98%E6%88%90%E6%95%B0%E6%8D%AE.md)
5. [From Graph to Stream — Solving Data Transformation with Higher-Level Interfaces](./%E7%AC%AC%E4%BA%94%E7%AB%A0%EF%BC%9A%E4%BB%8E%20Graph%20%E5%88%B0%20Stream%E2%80%94%E2%80%94%E7%94%A8%E9%AB%98%E7%BA%A7%E6%8E%A5%E5%8F%A3%E8%A7%A3%E5%86%B3%E6%95%B0%E6%8D%AE%E8%BD%AC%E6%8D%A2%E9%97%AE%E9%A2%98.md)
6. [From Stream to Reactive — WAIT, Wake, Demand, and Backpressure](./%E7%AC%AC%E5%85%AD%E7%AB%A0%EF%BC%9A%E4%BB%8E%20Stream%20%E5%88%B0%20Reactive%E2%80%94%E2%80%94WAIT%E3%80%81Wake%E3%80%81Demand%20%E4%B8%8E%20Backpressure.md)
7. [Executor — Separating Execution Policy from Computational Semantics](./%E7%AC%AC%E4%B8%83%E7%AB%A0%EF%BC%9AExecutor%E2%80%94%E2%80%94%E6%8A%8A%E6%89%A7%E8%A1%8C%E7%AD%96%E7%95%A5%E4%BB%8E%E8%AE%A1%E7%AE%97%E8%AF%AD%E4%B9%89%E4%B8%AD%E6%8B%86%E5%87%BA%E6%9D%A5.md)
8. [From Event to State Machine — Making State Changes a Verifiable Execution Model](./%E7%AC%AC%E5%85%AB%E7%AB%A0%EF%BC%9A%E4%BB%8E%20Event%20%E5%88%B0%20State%20Machine%E2%80%94%E2%80%94%E6%8A%8A%E7%8A%B6%E6%80%81%E5%8F%98%E5%8C%96%E5%8F%98%E6%88%90%E5%8F%AF%E9%AA%8C%E8%AF%81%E7%9A%84%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B.md)
9. [From State Machine to Actor — Mailbox, Serialized Execution, and Lifecycle Composition](./%E7%AC%AC%E4%B9%9D%E7%AB%A0%EF%BC%9A%E4%BB%8E%20State%20Machine%20%E5%88%B0%20Actor%E2%80%94%E2%80%94%E7%94%A8%20Mailbox%E3%80%81%E4%B8%B2%E8%A1%8C%E6%89%A7%E8%A1%8C%E4%B8%8E%E7%94%9F%E5%91%BD%E5%91%A8%E6%9C%9F%E7%BB%84%E5%90%88%E5%B9%B6%E5%8F%91%E5%AF%B9%E8%B1%A1.md)
10. [Rich Control Plane, Simple Execution Plane — Move Complexity Upfront and Make the Hot Path Plain C Again](./%E7%AC%AC%E5%8D%81%E7%AB%A0%EF%BC%9ARich%20Control%20Plane%EF%BC%8CSimple%20Execution%20Plane%E2%80%94%E2%80%94%E6%8A%8A%E5%A4%8D%E6%9D%82%E6%80%A7%E6%8F%90%E5%89%8D%EF%BC%8C%E6%8A%8A%20Hot%20Path%20%E9%87%8D%E6%96%B0%E5%8F%98%E5%9B%9E%E6%99%AE%E9%80%9A%20C.md)
11. [Lean and the Trusted Boundary — From Semantic Laws to Verified Rewrite, Manifest, and Certificate](./%E7%AC%AC%E5%8D%81%E4%B8%80%E7%AB%A0%EF%BC%9ALean%20%E4%B8%8E%E5%8F%AF%E4%BF%A1%E8%BE%B9%E7%95%8C%E2%80%94%E2%80%94%E4%BB%8E%20Semantic%20Law%20%E5%88%B0%20Verified%20Rewrite%E3%80%81Manifest%20%E4%B8%8E%20Certificate.md)
12. [Engineering Boundaries — ABI, Multi-TU, Semantic Identity, and an Installable C Library](./%E7%AC%AC%E5%8D%81%E4%BA%8C%E7%AB%A0%EF%BC%9A%E5%B7%A5%E7%A8%8B%E5%8C%96%E8%BE%B9%E7%95%8C%E2%80%94%E2%80%94ABI%E3%80%81Multi-TU%E3%80%81Semantic%20Identity%20%E4%B8%8E%E5%8F%AF%E5%AE%89%E8%A3%85%E7%9A%84%20C%20Library.md)
13. [From Foundations to Modern C — Serialization, RPC, Plugin, Workflow, and More](./%E7%AC%AC%E5%8D%81%E4%B8%89%E7%AB%A0%EF%BC%9A%E4%BB%8E%E5%9F%BA%E7%A1%80%E8%83%BD%E5%8A%9B%E5%88%B0%20Modern%20C%E2%80%94%E2%80%94Serialization%E3%80%81RPC%E3%80%81Plugin%E3%80%81Workflow%20%E4%B8%8E%E6%9B%B4%E5%A4%9A%E5%BA%94%E7%94%A8.md)
14. [Finite, Explicit, On Demand — When Meta-Programming Should Stop](./%E7%AC%AC%E5%8D%81%E5%9B%9B%E7%AB%A0%EF%BC%9A%E6%9C%89%E9%99%90%E3%80%81%E6%98%BE%E5%BC%8F%E3%80%81%E6%8C%89%E9%9C%80%E2%80%94%E2%80%94%E4%BB%80%E4%B9%88%E6%97%B6%E5%80%99%E5%BA%94%E8%AF%A5%E5%81%9C%E6%AD%A2%20Meta%20%E5%8C%96.md)
15. [From Macro Reuse to Typed Computation — What CMeta / CFlow Really Mean for Modern C](./%E7%AC%AC%E5%8D%81%E4%BA%94%E7%AB%A0%EF%BC%9A%E4%BB%8E%20Macro%20Reuse%20%E5%88%B0%20Typed%20Computation%E2%80%94%E2%80%94CMeta%20-%20CFlow%20%E5%AF%B9%20Modern%20C%20%E7%9A%84%E7%9C%9F%E6%AD%A3%E6%84%8F%E4%B9%89.md)

## Repository history

The manuscript originally lived under `qigao/salts/book` and was extracted into this standalone repository.

- Original repository: `qigao/salts`
- Original branch: `master`
- Source snapshot: `a90053416f1af748f8a356baf2e3f957be6105a4`
- Initial migration commit here: `5133429d2c7cc24f5b9b633b1fd1d1a059b40987`
- Initial manuscript: 15 Markdown chapters

The initial migration preserved the chapter contents byte-for-byte.

## License

Licensed under the [Apache License 2.0](./LICENSE).
