# Kairo R38: source-aware program-purpose questions

R38 adds a source-evidence path to the existing path-only question session.
When asked `what does this program do?`, Kairo scans the supplied file or
directory, reads README/description text, parses Python structure, and returns
a concise purpose summary with file/line evidence.

It also answers `what does the function NAME do?` for an unambiguous Python
function, reporting its documentation, direct named calls, and return
expressions with source evidence.

Text-evidence questions such as `which files mention inventory?` return
matching file/line records and abstain when no match exists.

The answer is explicitly scoped as a source summary. Kairo does not claim that
documentation or function names prove runtime behavior; execution-backed
questions continue to use the R37 reset/step learner and fresh-trace check.

Verification:

- R24 path/question/source tests: 19/19 passed.
- Preserved R23 regression tests: 12/12 passed.
- Source and question modules compile under Python 3.12.

Example:

```text
py -3.12 -m kairo_r24.ask --interactive PROGRAM_DIRECTORY
what does this program do?
```
