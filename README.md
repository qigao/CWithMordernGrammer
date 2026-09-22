# C with Modern Grammar

A book about evolving Modern C from macro reuse toward typed computation: CMeta, callable objects, graphs, streams, reactive execution, state machines, actors, verification boundaries, ABI/Multi-TU engineering, and CFlow.

This repository was extracted from `qigao/salts/book`.

- Source repository: `qigao/salts`
- Source branch: `master`
- Source snapshot: `a90053416f1af748f8a356baf2e3f957be6105a4`
- Initial extraction: 15 Markdown chapters, preserved from the source manuscript

## Chapters

1. [第一章：CMeta 的起点——从写 C 宏的痛苦开始](./%E7%AC%AC%E4%B8%80%E7%AB%A0%EF%BC%9ACMeta%20%E7%9A%84%E8%B5%B7%E7%82%B9%E2%80%94%E2%80%94%E4%BB%8E%E5%86%99%20C%20%E5%AE%8F%E7%9A%84%E7%97%9B%E8%8B%A6%E5%BC%80%E5%A7%8B.md)
2. [第二章：从宏到类型——Traits、Generic 与有限推导](./%E7%AC%AC%E4%BA%8C%E7%AB%A0%EF%BC%9A%E4%BB%8E%E5%AE%8F%E5%88%B0%E7%B1%BB%E5%9E%8B%E2%80%94%E2%80%94Traits%E3%80%81Generic%20%E4%B8%8E%E6%9C%89%E9%99%90%E6%8E%A8%E5%AF%BC.md)
3. [第三章：从函数指针到可执行对象——Callback、Lambda 与 Bind](./%E7%AC%AC%E4%B8%89%E7%AB%A0%EF%BC%9A%E4%BB%8E%E5%87%BD%E6%95%B0%E6%8C%87%E9%92%88%E5%88%B0%E5%8F%AF%E6%89%A7%E8%A1%8C%E5%AF%B9%E8%B1%A1%E2%80%94%E2%80%94Callback%E3%80%81Lambda%20%E4%B8%8E%20Bind.md)
4. [第四章：从 Callable 到 Graph——把计算本身变成数据](./%E7%AC%AC%E5%9B%9B%E7%AB%A0%EF%BC%9A%E4%BB%8E%20Callable%20%E5%88%B0%20Graph%E2%80%94%E2%80%94%E6%8A%8A%E8%AE%A1%E7%AE%97%E6%9C%AC%E8%BA%AB%E5%8F%98%E6%88%90%E6%95%B0%E6%8D%AE.md)
5. [第五章：从 Graph 到 Stream——用高级接口解决数据转换问题](./%E7%AC%AC%E4%BA%94%E7%AB%A0%EF%BC%9A%E4%BB%8E%20Graph%20%E5%88%B0%20Stream%E2%80%94%E2%80%94%E7%94%A8%E9%AB%98%E7%BA%A7%E6%8E%A5%E5%8F%A3%E8%A7%A3%E5%86%B3%E6%95%B0%E6%8D%AE%E8%BD%AC%E6%8D%A2%E9%97%AE%E9%A2%98.md)
6. [第六章：从 Stream 到 Reactive——WAIT、Wake、Demand 与 Backpressure](./%E7%AC%AC%E5%85%AD%E7%AB%A0%EF%BC%9A%E4%BB%8E%20Stream%20%E5%88%B0%20Reactive%E2%80%94%E2%80%94WAIT%E3%80%81Wake%E3%80%81Demand%20%E4%B8%8E%20Backpressure.md)
7. [第七章：Executor——把执行策略从计算语义中拆出来](./%E7%AC%AC%E4%B8%83%E7%AB%A0%EF%BC%9AExecutor%E2%80%94%E2%80%94%E6%8A%8A%E6%89%A7%E8%A1%8C%E7%AD%96%E7%95%A5%E4%BB%8E%E8%AE%A1%E7%AE%97%E8%AF%AD%E4%B9%89%E4%B8%AD%E6%8B%86%E5%87%BA%E6%9D%A5.md)
8. [第八章：从 Event 到 State Machine——把状态变化变成可验证的执行模型](./%E7%AC%AC%E5%85%AB%E7%AB%A0%EF%BC%9A%E4%BB%8E%20Event%20%E5%88%B0%20State%20Machine%E2%80%94%E2%80%94%E6%8A%8A%E7%8A%B6%E6%80%81%E5%8F%98%E5%8C%96%E5%8F%98%E6%88%90%E5%8F%AF%E9%AA%8C%E8%AF%81%E7%9A%84%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B.md)
9. [第九章：从 State Machine 到 Actor——用 Mailbox、串行执行与生命周期组合并发对象](./%E7%AC%AC%E4%B9%9D%E7%AB%A0%EF%BC%9A%E4%BB%8E%20State%20Machine%20%E5%88%B0%20Actor%E2%80%94%E2%80%94%E7%94%A8%20Mailbox%E3%80%81%E4%B8%B2%E8%A1%8C%E6%89%A7%E8%A1%8C%E4%B8%8E%E7%94%9F%E5%91%BD%E5%91%A8%E6%9C%9F%E7%BB%84%E5%90%88%E5%B9%B6%E5%8F%91%E5%AF%B9%E8%B1%A1.md)
10. [第十章：Rich Control Plane，Simple Execution Plane——把复杂性提前，把 Hot Path 重新变回普通 C](./%E7%AC%AC%E5%8D%81%E7%AB%A0%EF%BC%9ARich%20Control%20Plane%EF%BC%8CSimple%20Execution%20Plane%E2%80%94%E2%80%94%E6%8A%8A%E5%A4%8D%E6%9D%82%E6%80%A7%E6%8F%90%E5%89%8D%EF%BC%8C%E6%8A%8A%20Hot%20Path%20%E9%87%8D%E6%96%B0%E5%8F%98%E5%9B%9E%E6%99%AE%E9%80%9A%20C.md)
11. [第十一章：Lean 与可信边界——从 Semantic Law 到 Verified Rewrite、Manifest 与 Certificate](./%E7%AC%AC%E5%8D%81%E4%B8%80%E7%AB%A0%EF%BC%9ALean%20%E4%B8%8E%E5%8F%AF%E4%BF%A1%E8%BE%B9%E7%95%8C%E2%80%94%E2%80%94%E4%BB%8E%20Semantic%20Law%20%E5%88%B0%20Verified%20Rewrite%E3%80%81Manifest%20%E4%B8%8E%20Certificate.md)
12. [第十二章：工程化边界——ABI、Multi-TU、Semantic Identity 与可安装的 C Library](./%E7%AC%AC%E5%8D%81%E4%BA%8C%E7%AB%A0%EF%BC%9A%E5%B7%A5%E7%A8%8B%E5%8C%96%E8%BE%B9%E7%95%8C%E2%80%94%E2%80%94ABI%E3%80%81Multi-TU%E3%80%81Semantic%20Identity%20%E4%B8%8E%E5%8F%AF%E5%AE%89%E8%A3%85%E7%9A%84%20C%20Library.md)
13. [第十三章：从基础能力到 Modern C——Serialization、RPC、Plugin、Workflow 与更多应用](./%E7%AC%AC%E5%8D%81%E4%B8%89%E7%AB%A0%EF%BC%9A%E4%BB%8E%E5%9F%BA%E7%A1%80%E8%83%BD%E5%8A%9B%E5%88%B0%20Modern%20C%E2%80%94%E2%80%94Serialization%E3%80%81RPC%E3%80%81Plugin%E3%80%81Workflow%20%E4%B8%8E%E6%9B%B4%E5%A4%9A%E5%BA%94%E7%94%A8.md)
14. [第十四章：有限、显式、按需——什么时候应该停止 Meta 化](./%E7%AC%AC%E5%8D%81%E5%9B%9B%E7%AB%A0%EF%BC%9A%E6%9C%89%E9%99%90%E3%80%81%E6%98%BE%E5%BC%8F%E3%80%81%E6%8C%89%E9%9C%80%E2%80%94%E2%80%94%E4%BB%80%E4%B9%88%E6%97%B6%E5%80%99%E5%BA%94%E8%AF%A5%E5%81%9C%E6%AD%A2%20Meta%20%E5%8C%96.md)
15. [第十五章：从 Macro Reuse 到 Typed Computation——CMeta - CFlow 对 Modern C 的真正意义](./%E7%AC%AC%E5%8D%81%E4%BA%94%E7%AB%A0%EF%BC%9A%E4%BB%8E%20Macro%20Reuse%20%E5%88%B0%20Typed%20Computation%E2%80%94%E2%80%94CMeta%20-%20CFlow%20%E5%AF%B9%20Modern%20C%20%E7%9A%84%E7%9C%9F%E6%AD%A3%E6%84%8F%E4%B9%89.md)
