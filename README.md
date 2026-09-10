# Kairo

Kairo is an experimental local system for asking questions about a supplied
program path and returning answers with inspectable evidence.

It can learn a program through a small reset/step boundary, reuse that learned
model across questions, inspect readable project documentation and Python
structure, and abstain when the available evidence is not enough. The project
is intentionally research-oriented: a successful bounded experiment is not a
claim of general intelligence.

## Architecture comparison

A source-backed comparison of Kairo, typical generative LLMs, and physical
reservoir computing is available here:

[**Kairo vs. LLMs vs. Physical Reservoir Computing**](docs/KAIRO_COMPARISON.md)

![Fact-checked Kairo architecture comparison](docs/kairo-vs-llms-vs-physical-reservoir-computing.svg)

The short version: Kairo shares some useful *methodological* ideas with
reservoir-computing research, especially probing and observing system state,
but it is not currently a reservoir computer. A Kairo + physical-reservoir
implementation would be a new hybrid research branch, not simply a hardware
port of the current software.

## Try it

The interactive entry point accepts a program directory or adapter path once,
then reads one question per line:

```powershell
py -3.12 -m kairo_r24.ask --interactive PROGRAM_PATH
```

Example questions include:

```text
what does this program do?
what does the function convert do?
where is the class Converter defined?
which files mention inventory?
how many states does this program have?
what changes after toggling?
```

Answers include evidence when Kairo can establish it. Static source summaries
are labeled separately from runtime observations.

## Development

The current implementation uses the Python standard library. Run the focused
path/question tests and the preserved regression tests with:

```powershell
py -3.12 -m unittest discover -s . -p "tests_r24_*.py" -q
py -3.12 -m unittest discover -s tests_r23 -q
```

This repository contains the public-facing path/question layer and its tests.
Private evaluation fixtures, historical experiment outputs, archives, and
internal handoff material are intentionally not included.
