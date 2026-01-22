# AI Coding Agent Instructions (PyKotor)

Concise, actionable guidance to get an AI productive fast. Prefer small, surgical changes that respect existing architecture.

## Core idea 🔧
- Core vs Tools: Libraries under `Libraries/` (PyKotor, PyKotorGL, PyKotorFont); Tools under `Tools/` (HolocronToolset, HoloPatcher, KotorDiff, BatchPatcher).
- Tools sit atop the core library. Keep library APIs stable; UI/tool code depends on them.
- Priorities: engine fidelity, type-safety, reproducible builds. See essentials below.

**Workspace Layout**
- Libraries: `Libraries/PyKotor/src`, `Libraries/PyKotorGL/src`, `Libraries/PyKotorFont/src`.
- Tools: `Tools/HolocronToolset`, `Tools/HoloPatcher`, `Tools/KotorDiff`, `Tools/BatchPatcher`.
- Scripts & docs: `compile/` (build helpers), `docs/` (setup, tests), `wiki/` (format references).

**Setup & Run (Windows)**
- Preferred: `uv sync`, then activate `.venv\Scripts\activate`.
- Install editable packages selectively: `uv pip install -e Libraries/PyKotor [-e Tools/HolocronToolset ...]`.
- Quick runs without install: `uvx holocrontoolset`, `uvx holopatcher`, `uvx kotordiff`.

**Builds & Packaging**
- Use VS Code tasks / `compile/` scripts; don’t reinvent pipelines.
- PyInstaller one-file builds: tasks like “Build KotorDiff”, “Build K-BatchPatcher”, “Build GUI Creator”, “Build Model ASCII Compiler”, “Build Toolset - PyInstaller”.
- Respect excludes (numpy, PyQt5, PIL, matplotlib, multiprocessing, PyOpenGL, PyGLM, dl_translate, torch) as defined in tasks.

**Testing & Linting**
- Tests: `pytest` or `uv run pytest`. TSLPatcher comprehensive suite lives under `tests/test_tslpatcher/` (see docs/QUICK_START.md for targeted commands).
- Static checks: `ruff` (style), `mypy` (types), `pylint` (analysis). Prefer targeted runs on changed modules.

**Conventions & Patterns**
- Qt UI: use `qtpy` for backend-agnostic bindings. New widgets live under `Libraries/PyKotor/src/utility/ui_libraries/qt/...`.
- Resource types: use `pykotor.resource.type.ResourceType` with format helpers; avoid ad-hoc parsers.
- Error strategy: raise typed exceptions from `pykotor` modules; present user-facing messages in Tools.
- Dependencies: keep `pyproject.toml` and `requirements.txt` mirrored; don’t drift.

**Engine Fidelity (REVA Essentials)**
- Treat K1 (swkotor.exe) and TSL (swkotor2.exe) as a unified engine with conditional divergences; all functions exist in both.
- Mandatory workflow for engine-related changes:
	1. Confirm/open both executables in REVA MCP: `open-project <full path to .gpr>` (e.g., `%USERPROFILE%\Odyssey.gpr`).
	2. Locate and decompile the relevant function in K1; note address and key logic.
	3. Locate the corresponding function in TSL; note address and key logic.
	4. Compare side-by-side; identify differences in logic/flow.
	5. Use unified naming for functions/features.
	6. Format addresses exactly per rules below.
	7. Write a single unified description/docstring with inline notes on differences.
	8. If an address is unknown, mark `TODO` and continue searching.
- Address formatting:
	- `FunctionName @ (K1: 0xADDRESS, TSL: 0xADDRESS)`; if unknown, `TODO: <task>` for the missing one.
	- Reference comment: `# Reference: K1 swkotor.exe:0xADDRESS, TSL swkotor2.exe:0xADDRESS`.
- Prohibited: single-game-only analysis, single-game headings, or addresses for only one game without noting the other.
- At the end of any response involving engine-related changes, add exactly one:
	- `REVA status: Completed - Analyzed both K1 and TSL :)`
	- `REVA status: Partially completed - Missing TSL address for <function>, TODO find it :(`
	- `REVA status: Skipped - <exact reason> :(`

**Git Commit Discipline**
- Never use `git add .` / `git add -A` or any wildcard-all-files adds.
- Always add and commit one file at a time (or a tightly related small group).

**Toolset Integration Notes**
- Holocron Toolset is modular; see `Tools/HolocronToolset/CONVENTIONS.md` for Spyder plugin patterns.
- Avoid creating `ToolWindow` in plugin contexts; prefer Spyder-compatible widgets and signals.

**Useful Commands (Examples)**
```powershell
# Setup (Windows)
uv sync
. .venv\Scripts\activate
uv pip install -e Libraries/PyKotor -e Tools/HolocronToolset

# Run tools quickly
uvx holocrontoolset
uvx holopatcher --help

# Tests (TSLPatcher comprehensive suite)
python tests/test_tslpatcher/test_diff_comprehensive.py -v

# Build via VS Code tasks (PyInstaller)
# Use provided tasks; don’t add custom flags unless necessary.
```

**Quick Dev Runs (src/__main__.py)**
```powershell
# Run tools from source during development
python Tools\KotorDiff\src\__main__.py
python Tools\BatchPatcher\src\__main__.py
python Tools\MDLDecompile\src\__main__.py
# Pattern (others): python Tools\<ToolName>\src\__main__.py

# Example: Holocron Toolset (if needed)
uvx holocrontoolset  # preferred; faster than local run
```

**Preferred Smoke Tests**
```powershell
# Fast, targeted tests
python tests/test_tslpatcher/test_diff_comprehensive.py Test2DAMemoryComprehensive.test_addrow_stores_row_index -v
python tests/test_tslpatcher/test_diff_comprehensive.py Test2DAMemoryComprehensive.test_2damemory_cross_reference_chain -v

# Quick suite loops
python tests/test_tslpatcher/test_diff_comprehensive.py TestGFFComprehensive -v
python tests/test_tslpatcher/test_diff_comprehensive.py TestIntegrationComprehensive -v
```

**VS Code Build Tasks (labels)**
- Build KotorDiff — one-file console binary via PyInstaller.
- Build K-BatchPatcher — one-file console binary via PyInstaller.
- Build GUI Creator — one-file console binary via PyInstaller.
- Build Model ASCII Compiler — one-file console binary via PyInstaller.
- Build Toolset - PyInstaller — bundled GUI build.

**REVA Project Path**
- Default `.gpr`: `%USERPROFILE%\Odyssey.gpr` (Windows).
- Use: `open-project %USERPROFILE%\Odyssey.gpr` before engine analyses.

**Read First**
- README.md – overview, features, quick install.
- docs/SETUP.md – dev environment, dependency managers, testing.
- docs/QUICK_START.md – targeted test commands for TSLPatcher.
- Tools/HolocronToolset/CONVENTIONS.md – dual-mode UI integration.
- .cursorrules – engine fidelity + commit discipline (mirrored above).
