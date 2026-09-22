# C with Modern Grammar

**Finite CMeta, advanced programs, ordinary C execution**

[中文](./README_CN.md) | **English**

This book is written for C programmers who already know the language and want to build more capable systems without replacing C with C++ templates, a VM, or a new source language.

Its thesis is not “macros are powerful” and not “formal proofs are interesting”.

The thesis is:

> **A small, finite meta layer can remove repeated C contracts, make computation structurally visible, and enable advanced designs that are otherwise difficult to express and optimize in C.**

The recurring method is:

~~~text
real C code
    ↓
repeated fact / repeated contract
    ↓
finite CMeta design
    ↓
typed ordinary-C surface
    ↓
Graph / CFlow when computation itself must become data
    ↓
Lean only when semantic proof or optimization needs it
    ↓
ordinary C implementation, toolchain evidence, and measurement
~~~

Macro expansion back into C is a mechanism, not the subject of the book.

What matters is what the design lets us build.

## Audience

The reader is expected to be comfortable with structs, macros, function pointers, containers, callbacks, memory ownership, libraries, and normal systems-programming constraints.

The book aims to connect design and production engineering:

- why a Generic protocol is better than many unrelated macro families;
- how CMeta makes type/trait/callable identity reusable across libraries;
- how a LINQ-like typed graph makes whole computations first-class in C;
- how Lean can authorize graph rewrites and state-machine laws after semantics exist;
- how Plan/Direct lowering replaces repeated graph lookup with pre-resolved indices, handlers, and normal C calls;
- how the same foundation makes Reactive, async I/O, State Machines, Actors, CSTL, testing, serialization, and RPC easier to design.

## Three parts

### Part I — Remove repeated definitions and contracts with finite CMeta

Start with ordinary C and repeated contracts.

Generic is the answer to proliferating macro families; Struct/Traits/typed/finite relations turn duplicated facts into one source of truth. Lean is not needed to justify this layer.

The current core material is Chapters 1–3.

### Part II — Build, prove, and optimize LINQ-style graph computation

This is the technical center of the book.

A pipeline such as:

~~~text
Source<int>
    ↓
Filter(is_even)
    ↓
Map(square)
    ↓
Reduce(sum)
~~~

is valuable not because it resembles another language, but because C/C++ do not natively make the whole computation a typed, inspectable, transformable program object.

This Part shows Graph, Stream surface syntax, semantic laws, Lean-backed rewrite preservation, optimizer passes, compiled Plan execution, and Direct/AOT lowering back to ordinary C.

The core Part II sequence is now Chapters 4–7: Graph → Stream → verified semantics → Optimize/Plan/Direct.

### Part III — Build advanced applications from CMeta/CFlow

The foundation is then reused for:

- Reactive execution and async file/network I/O;
- Executors and schedulers;
- State Machines and Actors;
- CSTL typed containers;
- testing/mocking infrastructure;
- serialization and data binding;
- HTTP/RPC and other systems patterns;
- ABI, Multi-TU, and installed-consumer qualification.

The goal is not to multiply frameworks. It is to show that a small set of well-defined primitives can support increasingly sophisticated C software.

## Editorial method: code before explanation

Major ideas should normally be demonstrated as:

~~~text
1. embedded Plain C example
2. concrete repeated/error-prone contract
3. minimal CMeta/CFlow design
4. resulting C API/generated/lowered shape
5. capability that becomes easy
6. Lean only for a real semantic question
7. tests/ABI/sanitizer/benchmark evidence
~~~

Implementation and theorem references remain pinned in [SOURCE_SNAPSHOTS.md](./SOURCE_SNAPSHOTS.md). The detailed editorial design is in [BOOK_ARCHITECTURE.md](./BOOK_ARCHITECTURE.md), with [CHAPTER_TEMPLATE.md](./CHAPTER_TEMPLATE.md) as the chapter-level constraint.

## Publication build

The chapter files remain the authoritative editable sources. Their publication order is defined once in [BOOK_MANIFEST.txt](./BOOK_MANIFEST.txt).

Run the zero-dependency QA gate and build the canonical single-file Markdown manuscript with:

```bash
python3 scripts/validate_book.py
python3 scripts/build_book.py
```

The generated manuscript is written to `dist/C-with-Modern-Grammar.md` and is intentionally not committed. The `Publication` GitHub Actions workflow runs the same validation/build on pull requests and `master`, then uploads the combined manuscript as a workflow artifact.

Release rendering is intentionally separate from ordinary manuscript QA. The `Release Formats` workflow runs manually or for `v*` tags, consumes only that canonical Markdown artifact, renders Mermaid diagrams to SVG, and produces standalone HTML, EPUB3, and PDF from the same validated source. Renderer versions are pinned in the workflow; release artifacts also include `SOURCE_SNAPSHOTS.md`, renderer-version metadata, and SHA-256 checksums. A tag run publishes the same files to a GitHub Release.

PDF/EPUB rendering is intentionally a separate layer so ordinary writing and review do not require Pandoc, LaTeX, Node, or Lean.

## Repository history

The manuscript originally lived in the `qigao/salts` repository and was later extracted into this standalone book repository.

- Original repository: `qigao/salts`
- Original branch: `master`
- Source snapshot: `a90053416f1af748f8a356baf2e3f957be6105a4`
- Initial migration commit here: `5133429d2c7cc24f5b9b633b1fd1d1a059b40987`
- Initial manuscript: 15 Markdown chapters

The initial migration preserved the chapter contents byte-for-byte.

## License

Licensed under the [Apache License 2.0](./LICENSE).
