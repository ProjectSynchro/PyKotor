# AI Coding Agent Instructions (PyKotor)

Concise, actionable guidance to get an AI productive fast. Prefer small, surgical changes that respect existing architecture.

## Core idea 🔧
- Core vs Tools: Libraries under `Libraries/` (PyKotor, PyKotorGL, PyKotorFont); Tools under `Tools/` (HolocronToolset, HoloPatcher, KotorDiff, BatchPatcher).
- Tools sit atop the core library. Keep library APIs stable; UI/tool code depends on them.
- Priorities: game game engine fidelity, type-safety, reproducible builds. See essentials below.

## Purpose
Give AI agents just the essentials: where code lives, how to run/build/test safely, project-specific conventions (REVA engine rules, git discipline), and where to find deeper docs.

## Big picture
- **Core vs Tools**: Core libraries live in `Libraries/` and tools are in `Tools/`. Libraries are stable APIs; tools depend on them.
- **Build helpers**: Use `compile/` scripts and VS Code tasks for canonical packaging (look for task labels like **Build KotorDiff**).

## Quick start (Windows)
- Setup: `uv sync` → `. .venv\Scripts\activate`
- Optional: `uv pip install -e Libraries/PyKotor -e Tools/HolocronToolset`
- Run from source: `python Tools\KotorDiff\src\__main__.py` or `uvx holocrontoolset`

## Build & packaging notes
- Use VS Code tasks and `compile/` scripts as canonical build flows. See the **Build KotorDiff** task for example PyInstaller flags and `--path` entries.
- PyInstaller tasks intentionally exclude heavy GUI/compute libs (numpy, PyQt5, PIL, PyOpenGL, torch). Avoid adding or removing excludes without checking maintainers.

## Tests & static checks
- Unit/integration tests: `pytest` (TSLPatcher suites live in `tests/test_tslpatcher/`). Run targeted test paths for fast feedback.
- Linters: `ruff` (style), `mypy` (types), `pylint` (analysis). Prefer running checks only on modified modules.

## Conventions & patterns
- UI: use `qtpy` (see `Libraries/PyKotor/src/utility/ui_libraries/qt/`).
- Resources: use `pykotor.resource.type.ResourceType` helpers; avoid ad-hoc parsing.
- Errors: libraries raise typed exceptions; tools convert to user-facing messages.

## REVA engine workflow (MANDATORY)
- Treat K1 (swkotor.exe) and TSL (swkotor2.exe) as a unified game engine with conditional divergences; all functions exist in both.
- MANDATORY workflow (short):
  1. `open-project <full path to .gpr>` in REVA MCP (default: `%USERPROFILE%\Odyssey.gpr`).
  2. Decompile/analyze function in K1 and in TSL; compare side-by-side.
  3. Use unified naming and one docstring to note differences.
  4. If an address is unknown, mark `TODO` and continue searching.
  5. End engine reports with exactly one REVA status line (see below).

- Address formatting:
  - Use `FunctionName @ (K1: 0xADDRESS, TSL: 0xADDRESS)`. If an address is unknown, mark `TODO: <task>`.
  - Add a reference comment: `# Reference: K1 swkotor.exe:0xADDRESS, TSL swkotor2.exe:0xADDRESS`.

- Prohibited: single-game-only analysis, single-game headings, or addresses for only one game without noting the other.

- End engine-related responses with **exactly one** of the following three lines:
  - `REVA status: Completed - Analyzed both K1 and TSL :)`
  - `REVA status: Partially completed - Missing TSL address for <function>, TODO find it :(`
  - `REVA status: Skipped - <exact reason> :(`


## Git discipline (MANDATORY)
- Never use `git add .` or `git add -A`.
- Add & commit one file (or a small logical group) at a time. Windows example:
  `git add path\to\file; git commit -m "fix(module): short message"`
- After edits, include a **Proposed Git Commands** block in your message and finish with: `Git commits: Issued per rules ✅`.

## Where to look
- **Read first**: `README.md`, `docs/SETUP.md`, `docs/QUICK_START.md`, and `.cursorrules` (MANDATORY reading).
- **Tool conventions**: `Tools/HolocronToolset/CONVENTIONS.md` for plugin/Spyder integration patterns.
- **Packaging & tasks**: `compile/` and workspace `tasks.json` (see task **Build KotorDiff** for example flags).
- **Quick runs**: `uvx holocrontoolset`, or `python Tools\KotorDiff\src\__main__.py`.

---
If you want I can add a short REVA report template and a pre-PR checklist for engine changes.
