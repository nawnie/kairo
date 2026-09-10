# Kairo Gauntlet Run 1

Date: 2026-09-10

This is the first executable run of the gauntlet against the currently
implemented lanes. It is a boundary-finding report, not a claim that every
protocol gate has been implemented.

## Scorecard

| Lane | Status | Evidence |
|---|---|---|
| Current R24/path tests | PASS | 32 tests passed |
| Current R23 regression tests | PASS | 12 tests passed |
| R40 new schemas/values/bindings | PASS task/artifact gate | 12/12 artifacts verified; 0/12 exact models |
| Historical R23 clean reproduction | INTEGRITY BLOCK | Receipt source hashes mismatch in `kairo_r11/learn.py`, `kairo_r23/challenges.py`, `kairo_r23/client.py`, and `tests_r23/test_challenges.py` before the audit could run |
| Noise and transient-failure gate | NOT IMPLEMENTED | No noise adapter exists yet |
| Hidden late-state gate | NOT IMPLEMENTED | No dedicated late-state adapter exists yet |
| Cross-domain transfer gate | NOT IMPLEMENTED | No isolated cross-domain runner exists yet |

## R40 result

R40 changed table and column schemas, row counts, values, and operation
bindings while keeping the SQLite transaction family. Cold, retained,
random-challenge, and plan-challenge policies each completed 3/3 tasks and
passed 3/3 independent artifact checks. Each policy produced 0/3 exact finite
models. Query totals were 1,116 cold, 1,172 retained, 1,215 random, and 1,215
planned. Retention therefore did not beat cold on this held-out presentation.

## Interpretation

Kairo currently handles unfamiliar data and operation permutations well enough
to produce correct checked artifacts, but its learned model does not transfer
exactly. The historical receipt mismatch is a reproducibility/integrity issue,
not evidence of a capability failure; it must be resolved or explicitly
re-baselined before using the old clean-reproduction result as a fresh pass.

The next executable gate should be a hidden late-state adapter, followed by a
noise/failure adapter and then a genuinely cross-domain transfer run.

## First adversarial probes

The hidden late-state probe passed: a flip/read adapter changed from `early` to
`late` after repeated flips, and Kairo answered the eight-flip question
correctly. Its learning status remained provisional after 128 bounded probes.

The conflicting-documentation probe failed as expected. A directory README
claimed that a program encrypted files, while the Python source called
`Path.unlink()` and deleted a file. Kairo answered with the README's encryption
claim, did not report the deletion operation, and mislabeled the function name
`run` as an operation. This is a false-supported source-summary result and is
the first concrete gauntlet failure requiring repair before broader claims.

## Repair checkpoint

The source summarizer was repaired after that failure. Python AST analysis now
detects method-based effects including `unlink`, `remove`, `rmdir`, file writes,
directory creation, and path moves. Function names are no longer counted as
operations. When documentation is not corroborated by detected source
operations, the answer leads with code-derived behavior and labels the
documentation as an unverified claim.

Regression verification: 34 R24/path tests passed and 12 R23 tests passed. The
same adversarial program now reports `unlink (deletes paths)` first and marks
the encryption README as not independently corroborated.

## Capability false-positive checkpoint

A second adversarial probe put the word `Socket` only in a README while the
Python program performed no network operation. The old capability scanner
reported `yes` from the prose. Python capability detection is now AST-based;
documentation and comments are excluded, while real imports and calls remain
evidence. The repaired probe reports `no` with zero matches.

Regression verification: 37 R24/path tests passed and 12 R23 tests passed.

## Unsupported-predicate checkpoint

A third adversarial probe asked whether a trivial program was secure while the
only matching evidence was a README phrase saying it was “secure-looking.” The
old open-ended fallback returned an `answered` result based on that word, which
was not a security analysis. The fallback now abstains on unsupported yes/no,
causal, and modal predicates while preserving the ranked evidence for a later
semantic analyzer. Explicit capability handlers remain available for questions
they can actually ground, such as whether source imports a network library.

Regression verification: pending after this repair.

The summary path was also tightened so a README claim is labeled as
uncorroborated whenever source files are present, even if the source exposes no
recognized operation. This prevents documentation-only descriptions from being
silently promoted to source-backed behavior.

A cross-language probe then found the same false-positive pattern in the
JavaScript/TypeScript capability path: a string literal containing “socket” was
reported as network use. Non-Python capability scanning now requires
syntax-shaped evidence such as an import, `require`/`from`, or a call/member
access, and regression coverage confirms both the string-literal negative and a
real network import positive.

The follow-up positive caught a missed `require("node:net")` case; the scanner
now preserves module specifiers for explicit `require(...)` evidence while
continuing to ignore ordinary string literals.

An additional adversarial string containing the literal text
`require("socket")` exposed a second false positive. The scanner now requires
the `require(` token to survive string removal before accepting the module
specifier. The negative string case and the real `require("node:net")` case both
pass.

The dependency summary then failed a JavaScript probe by extracting package names
from comments and string literals. Its import/require path is now guarded by
comment removal and outside-string token checks; regression coverage confirms
that fake text is ignored while real `import` and `require` dependencies are
retained.

The Python operation probe then found that a user-defined bare `connect()` was
being mislabeled as a database operation. Bare-name inference is now limited
to built-in `open`; database, process, and network operations require imported
or qualified source evidence. Function-level operation names follow the same
rule.

The cross-language scanner then received a quote-aware comment masker. The old
regex could treat `//` inside a URL string as a comment or treat inline-comment
text as code. Regression coverage now preserves real imports after URL strings
and ignores fake `require("socket")` text in inline comments.

The routing audit found one remaining lexical mismatch: template literals were
recognized by comment masking but not by later string removal. Template text
containing fake `require(...)` evidence is now excluded from both capability and
dependency scans.

Hard-variant coverage then found that dynamic JavaScript imports
(`import("...")`) were missed entirely. Both capability and dependency paths
now detect guarded dynamic imports, and a quoted fake dynamic-import string is
still ignored.

The Python side-effect probe found that arbitrary custom methods such as
`Cache().unlink()` were being labeled as path deletion. Method-based path
operations are now constrained to recognizable `Path`/`PurePath` constructors;
real `Path(...).unlink()` evidence remains covered.

The next lexical probe found that JavaScript regex literals could contain fake
`require(...)` or `import(...)` text and still be reported. Regex literals are
now masked after comments and quoted strings, with regression coverage for both
capability and dependency scans.
