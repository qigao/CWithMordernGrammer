# 用现代语法写 C

**从普通 C 到类型化与可验证计算**

**中文** | [English](./README.md)

**C with Modern Grammar** 讨论的是一个很具体的问题：在不把 C 变成另一门语言的前提下，我们究竟可以把现代 C 推进到什么程度？

全书从一个非常现实的痛点开始：**重复代码很多，而宏复用越来越难维护**。随后逐层构建一套面向现代 C 的“类型化计算”思路：CMeta、Callable、Graph、Stream、Reactive、Executor、State Machine、Actor、形式化验证边界、ABI / Multi-TU 工程约束，以及最终的 CFlow。

全书的核心思想可以概括为：

> **让执行平面尽量保持普通 C，把类型、组合、结构和验证能力前移到显式的控制平面。**

## 为什么写这本书

C 的优势一直非常明确：

- 运行时模型直接；
- ABI 清晰；
- 性能行为容易理解；
- 与操作系统和硬件距离很近；
- 可移植性强；
- 很适合基础设施、系统软件和高性能库。

但当 C 工程逐渐变大，同样的问题也会反复出现：

- 不同类型之间存在大量重复代码；
- 宏展开容易失去类型和语义边界；
- 可复用“计算”很难成为一等抽象；
- Callback、生命周期和所有权逐渐复杂；
- 异步、状态和事件逻辑难以组合；
- 编译期结构与运行时执行容易混杂；
- ABI 与 Multi-TU 会限制很多元编程技巧；
- 优化和重写缺少可以验证的语义依据。

本书尝试给出一种答案：**不依赖 C++ Template，不引入 VM，也不创造一门新的源码语言，而是在 C 内部建立有限、显式、可工程化的抽象层。**

## 全书演进路线

这些章节不是彼此独立的功能集合，而是一条逐步演进的主线：

```text
宏复用
  ↓
类型化宏 / Traits / Generic
  ↓
Callable
  ↓
Graph
  ↓
Stream
  ↓
Reactive
  ↓
Executor
  ↓
State Machine
  ↓
Actor
  ↓
Rich Control Plane / Simple Execution Plane
  ↓
可验证的语义重写
  ↓
ABI + Multi-TU 工程边界
  ↓
Modern C 应用
  ↓
CMeta / CFlow：类型化计算
```

目标并不是“让 C 看起来像 C++”。

真正关心的是：

- 哪些能力应该在编译期表达；
- 哪些结构应该在运行前构造；
- 哪些信息应该进入类型或 descriptor；
- 哪些抽象可以在执行阶段被消掉；
- 如何让最终 Hot Path 重新接近普通 C；
- 如何让这些抽象能够跨 ABI、跨 Translation Unit，并且接受验证。

## 适合哪些读者

如果你关心下面这些主题，这本书会比较适合：

- 系统编程与基础库设计；
- C 元编程；
- 类型化 C API；
- Callback / Lambda / Bind；
- Graph / Stream / Reactive；
- Executor 与异步执行；
- State Machine / Actor；
- 编译期与运行期边界；
- ABI 稳定性与 Multi-TU；
- Lean / 形式化语义；
- 在保留普通 C 执行模型的同时构建更现代的基础设施。

## 全书结构

15 章已经按照统一方法完成结构化重构：

**Problem → Plain C → Design → Semantic Contract → Lean / Proof Obligation → C Implementation → Evidence**

全书分为五个 Part。详细编辑架构见 [BOOK_ARCHITECTURE.md](./BOOK_ARCHITECTURE.md)，逐章重构模板见 [CHAPTER_TEMPLATE.md](./CHAPTER_TEMPLATE.md)。

### Part I — 从普通 C 到类型化计算

1. [第一章：CMeta 的起点——从写 C 宏的痛苦开始](./%E7%AC%AC%E4%B8%80%E7%AB%A0%EF%BC%9ACMeta%20%E7%9A%84%E8%B5%B7%E7%82%B9%E2%80%94%E2%80%94%E4%BB%8E%E5%86%99%20C%20%E5%AE%8F%E7%9A%84%E7%97%9B%E8%8B%A6%E5%BC%80%E5%A7%8B.md)
2. [第二章：从宏到类型——Traits、Generic 与有限推导](./%E7%AC%AC%E4%BA%8C%E7%AB%A0%EF%BC%9A%E4%BB%8E%E5%AE%8F%E5%88%B0%E7%B1%BB%E5%9E%8B%E2%80%94%E2%80%94Traits%E3%80%81Generic%20%E4%B8%8E%E6%9C%89%E9%99%90%E6%8E%A8%E5%AF%BC.md)
3. [第三章：从函数指针到可执行对象——Callback、Lambda 与 Bind](./%E7%AC%AC%E4%B8%89%E7%AB%A0%EF%BC%9A%E4%BB%8E%E5%87%BD%E6%95%B0%E6%8C%87%E9%92%88%E5%88%B0%E5%8F%AF%E6%89%A7%E8%A1%8C%E5%AF%B9%E8%B1%A1%E2%80%94%E2%80%94Callback%E3%80%81Lambda%20%E4%B8%8E%20Bind.md)

### Part II — 从 Callable 到可组合执行

4. [第四章：从 Callable 到 Graph——把计算本身变成数据](./%E7%AC%AC%E5%9B%9B%E7%AB%A0%EF%BC%9A%E4%BB%8E%20Callable%20%E5%88%B0%20Graph%E2%80%94%E2%80%94%E6%8A%8A%E8%AE%A1%E7%AE%97%E6%9C%AC%E8%BA%AB%E5%8F%98%E6%88%90%E6%95%B0%E6%8D%AE.md)
5. [第五章：从 Graph 到 Stream——用高级接口解决数据转换问题](./%E7%AC%AC%E4%BA%94%E7%AB%A0%EF%BC%9A%E4%BB%8E%20Graph%20%E5%88%B0%20Stream%E2%80%94%E2%80%94%E7%94%A8%E9%AB%98%E7%BA%A7%E6%8E%A5%E5%8F%A3%E8%A7%A3%E5%86%B3%E6%95%B0%E6%8D%AE%E8%BD%AC%E6%8D%A2%E9%97%AE%E9%A2%98.md)
6. [第六章：从 Stream 到 Reactive——WAIT、Wake、Demand 与 Backpressure](./%E7%AC%AC%E5%85%AD%E7%AB%A0%EF%BC%9A%E4%BB%8E%20Stream%20%E5%88%B0%20Reactive%E2%80%94%E2%80%94WAIT%E3%80%81Wake%E3%80%81Demand%20%E4%B8%8E%20Backpressure.md)
7. [第七章：Executor——把执行策略从计算语义中拆出来](./%E7%AC%AC%E4%B8%83%E7%AB%A0%EF%BC%9AExecutor%E2%80%94%E2%80%94%E6%8A%8A%E6%89%A7%E8%A1%8C%E7%AD%96%E7%95%A5%E4%BB%8E%E8%AE%A1%E7%AE%97%E8%AF%AD%E4%B9%89%E4%B8%AD%E6%8B%86%E5%87%BA%E6%9D%A5.md)

### Part III — 有状态、并发与 Lowering

8. [第八章：从 Event 到 State Machine——把状态变化变成可验证的执行模型](./%E7%AC%AC%E5%85%AB%E7%AB%A0%EF%BC%9A%E4%BB%8E%20Event%20%E5%88%B0%20State%20Machine%E2%80%94%E2%80%94%E6%8A%8A%E7%8A%B6%E6%80%81%E5%8F%98%E5%8C%96%E5%8F%98%E6%88%90%E5%8F%AF%E9%AA%8C%E8%AF%81%E7%9A%84%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B.md)
9. [第九章：从 State Machine 到 Actor——用 Mailbox、串行执行与生命周期组合并发对象](./%E7%AC%AC%E4%B9%9D%E7%AB%A0%EF%BC%9A%E4%BB%8E%20State%20Machine%20%E5%88%B0%20Actor%E2%80%94%E2%80%94%E7%94%A8%20Mailbox%E3%80%81%E4%B8%B2%E8%A1%8C%E6%89%A7%E8%A1%8C%E4%B8%8E%E7%94%9F%E5%91%BD%E5%91%A8%E6%9C%9F%E7%BB%84%E5%90%88%E5%B9%B6%E5%8F%91%E5%AF%B9%E8%B1%A1.md)
10. [第十章：Rich Control Plane，Simple Execution Plane——把复杂性提前，把 Hot Path 重新变回普通 C](./%E7%AC%AC%E5%8D%81%E7%AB%A0%EF%BC%9ARich%20Control%20Plane%EF%BC%8CSimple%20Execution%20Plane%E2%80%94%E2%80%94%E6%8A%8A%E5%A4%8D%E6%9D%82%E6%80%A7%E6%8F%90%E5%89%8D%EF%BC%8C%E6%8A%8A%20Hot%20Path%20%E9%87%8D%E6%96%B0%E5%8F%98%E5%9B%9E%E6%99%AE%E9%80%9A%20C.md)

### Part IV — 可信边界与工程边界

11. [第十一章：Lean 与可信边界——从 Semantic Law 到 Verified Rewrite、Manifest 与 Certificate](./%E7%AC%AC%E5%8D%81%E4%B8%80%E7%AB%A0%EF%BC%9ALean%20%E4%B8%8E%E5%8F%AF%E4%BF%A1%E8%BE%B9%E7%95%8C%E2%80%94%E2%80%94%E4%BB%8E%20Semantic%20Law%20%E5%88%B0%20Verified%20Rewrite%E3%80%81Manifest%20%E4%B8%8E%20Certificate.md)
12. [第十二章：工程化边界——ABI、Multi-TU、Semantic Identity 与可安装的 C Library](./%E7%AC%AC%E5%8D%81%E4%BA%8C%E7%AB%A0%EF%BC%9A%E5%B7%A5%E7%A8%8B%E5%8C%96%E8%BE%B9%E7%95%8C%E2%80%94%E2%80%94ABI%E3%80%81Multi-TU%E3%80%81Semantic%20Identity%20%E4%B8%8E%E5%8F%AF%E5%AE%89%E8%A3%85%E7%9A%84%20C%20Library.md)

### Part V — 高级应用、克制与方法论

13. [第十三章：从基础能力到 Modern C——Serialization、RPC、Plugin、Workflow 与更多应用](./%E7%AC%AC%E5%8D%81%E4%B8%89%E7%AB%A0%EF%BC%9A%E4%BB%8E%E5%9F%BA%E7%A1%80%E8%83%BD%E5%8A%9B%E5%88%B0%20Modern%20C%E2%80%94%E2%80%94Serialization%E3%80%81RPC%E3%80%81Plugin%E3%80%81Workflow%20%E4%B8%8E%E6%9B%B4%E5%A4%9A%E5%BA%94%E7%94%A8.md)
14. [第十四章：有限、显式、按需——什么时候应该停止 Meta 化](./%E7%AC%AC%E5%8D%81%E5%9B%9B%E7%AB%A0%EF%BC%9A%E6%9C%89%E9%99%90%E3%80%81%E6%98%BE%E5%BC%8F%E3%80%81%E6%8C%89%E9%9C%80%E2%80%94%E2%80%94%E4%BB%80%E4%B9%88%E6%97%B6%E5%80%99%E5%BA%94%E8%AF%A5%E5%81%9C%E6%AD%A2%20Meta%20%E5%8C%96.md)
15. [第十五章：从 Macro Reuse 到 Typed Computation——CMeta - CFlow 对 Modern C 的真正意义](./%E7%AC%AC%E5%8D%81%E4%BA%94%E7%AB%A0%EF%BC%9A%E4%BB%8E%20Macro%20Reuse%20%E5%88%B0%20Typed%20Computation%E2%80%94%E2%80%94CMeta%20-%20CFlow%20%E5%AF%B9%20Modern%20C%20%E7%9A%84%E7%9C%9F%E6%AD%A3%E6%84%8F%E4%B9%89.md)

## 关于 CMeta 与 CFlow

**CMeta** 不是“把 C 变成模板语言”。

它更关注：

- 类型描述；
- 有限推导；
- Traits；
- 类型化宏；
- descriptor；
- 单一定义；
- 编译期结构复用。

**CFlow** 则建立在这些基础能力之上，把“计算本身”逐步变成可以组合、分析和执行的对象：

```text
Callable
   ↓
Graph
   ↓
Stream / Reactive
   ↓
Executor
   ↓
State Machine / Actor
```

最终追求的并不是更多运行时框架，而是：

> **控制平面可以丰富，执行平面应该简单。**

## 仓库历史

这套书稿最初位于 `qigao/salts/book`，之后独立迁移到当前仓库。

- 原仓库：`qigao/salts`
- 原分支：`master`
- 迁移源快照：`a90053416f1af748f8a356baf2e3f957be6105a4`
- 本仓库初始迁移提交：`5133429d2c7cc24f5b9b633b1fd1d1a059b40987`
- 初始书稿：15 个 Markdown 章节

首次迁移时，15 个章节内容保持了与原始文件完全一致的 Git blob。

## License

本项目采用 [Apache License 2.0](./LICENSE)。
