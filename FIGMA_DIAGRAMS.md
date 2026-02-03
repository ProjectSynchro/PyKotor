# PyKotor FigJam Architectural Diagrams

This document contains links to all architectural diagrams created for the PyKotor workspace using Figma's diagram generation tools.

## Overview Diagrams

### 1. [PyKotor Workspace Architecture](https://www.figma.com/online-whiteboard/create-diagram/89237efa-33c5-4da2-9dcb-ae7f1fbc1b97)
High-level architecture showing the relationship between PyKotor libraries and tools.
- **ID**: `89237efa-33c5-4da2-9dcb-ae7f1fbc1b97`
- **Components**: PyKotor Core Library, HolocronToolset, HoloPatcher, KotorDiff, BatchPatcher, HoloPazaak

### 2. [PyKotor Resource Type System](https://www.figma.com/online-whiteboard/create-diagram/471f886b-413a-4b76-8e2e-15b07834a891)
Comprehensive resource type system supported by PyKotor.
- **ID**: `471f886b-413a-4b76-8e2e-15b07834a891`
- **Types**: GFF, 2DA, TLK, DLG, ERF/MOD/SAV, RIM, BIF, NSS/NCS, MDL/MDX, TGA/TPC, WAV, LYT, VIS, PTH

### 3. [PyKotor Installation System](https://www.figma.com/online-whiteboard/create-diagram/4030cc70-8fec-41bd-b7a5-11db9f55c87e)
Installation detection and resource management system.
- **ID**: `4030cc70-8fec-41bd-b7a5-11db9f55c87e`
- **Features**: Registry detection, Steam/GOG support, Resource paths, Archive management

## Tool-Specific Diagrams

### 4. [HolocronToolset Editor Architecture](https://www.figma.com/online-whiteboard/create-diagram/f0bebb71-9245-45e6-93ea-7f3970f5d985)
Complete editor suite showing all resource type editors.
- **ID**: `f0bebb71-9245-45e6-93ea-7f3970f5d985`
- **Editors**: DLG, UTC, UTI, UTP, UTE, UTD, UTT, UTS, UTW, GFF, 2DA, TLK, NSS

### 5. [HoloPatcher Mod Installation Flow](https://www.figma.com/online-whiteboard/create-diagram/c8ef83a4-32b0-4977-a707-551702f971b5)
Sequence diagram for mod installation process.
- **ID**: `c8ef83a4-32b0-4977-a707-551702f971b5`
- **Flow**: Config reading → Backup → Patch application → File copying

### 6. [KotorDiff Comparison Workflow](https://www.figma.com/online-whiteboard/create-diagram/cf166a06-056f-446e-9908-5d2d32d5eb32)
Comparison workflow for different resource types.
- **ID**: `cf166a06-056f-446e-9908-5d2d32d5eb32`
- **Types**: GFF, 2DA, TLK, Binary comparison

### 7. [BatchPatcher Processing Pipeline](https://www.figma.com/online-whiteboard/create-diagram/8dedee25-ee96-429b-a08e-00838d8d17d7)
Batch processing pipeline for resource transformations.
- **ID**: `8dedee25-ee96-429b-a08e-00838d8d17d7`
- **Stages**: Load → Validate → Transform → Merge → Backup → Output → Report

### 8. [HoloPazaak Game State Machine](https://www.figma.com/online-whiteboard/create-diagram/15e614cb-0959-48af-a143-f406efd47aed)
State machine for HoloPazaak game flow.
- **ID**: `15e614cb-0959-48af-a143-f406efd47aed`
- **States**: MainMenu, OpponentSelect, DeckBuilder, PlayerTurn, AITurn, GameOver

## Core System Diagrams

### 9. [PyKotor GFF Read/Write Flow](https://www.figma.com/online-whiteboard/create-diagram/28004fa3-1205-4b1e-ad59-83518cf61913)
Sequence diagram for GFF binary read/write operations.
- **ID**: `28004fa3-1205-4b1e-ad59-83518cf61913`
- **Components**: GFF Class, BinaryReader, BinaryWriter, File System

### 10. [Resource Loading Priority System](https://www.figma.com/online-whiteboard/create-diagram/c0d19a3c-a369-4d3d-8759-e7dd52131be3)
Priority system for loading resources from different locations.
- **ID**: `c0d19a3c-a369-4d3d-8759-e7dd52131be3`
- **Priority**: Override → Modules → chitin.key/BIF → Texture Packs

### 11. [Script Compilation Pipeline](https://www.figma.com/online-whiteboard/create-diagram/6ac14a1d-ec15-4203-9802-ff6bfb7a4aed)
NSS script compilation from source to bytecode.
- **ID**: `6ac14a1d-ec15-4203-9802-ff6bfb7a4aed`
- **Stages**: Tokenize → Parse → Type Check → Generate Bytecode

### 12. [TSLPatcher Configuration Structure](https://www.figma.com/online-whiteboard/create-diagram/ee6230bc-c950-4bc0-8ef1-b462a292264a)
Complete TSLPatcher configuration structure.
- **ID**: `ee6230bc-c950-4bc0-8ef1-b462a292264a`
- **Operations**: 2DA, GFF, TLK, Script compilation, File operations

## UI and Editor Diagrams

### 13. [DLG Editor Node Management](https://www.figma.com/online-whiteboard/create-diagram/e53d6e87-5d53-4135-9782-9a6d1428b5f8)
Dialog editor node management workflow.
- **ID**: `e53d6e87-5d53-4135-9782-9a6d1428b5f8`
- **Features**: Tree view, Entry/Reply nodes, Properties, Links, Scripts

### 14. [Module Editor Workflow](https://www.figma.com/online-whiteboard/create-diagram/c5f584fe-059e-4c7a-a129-7e71ef18a6eb)
Module editing workflow with 2D/3D views.
- **ID**: `c5f584fe-059e-4c7a-a129-7e71ef18a6eb`
- **Content**: IFO, ARE, GIT, instances, 2D/3D editing

### 15. [UI Component Hierarchy](https://www.figma.com/online-whiteboard/create-diagram/25df65c2-ddf9-46e0-8563-4d24c85d99fd)
Custom Qt widget hierarchy.
- **ID**: `25df65c2-ddf9-46e0-8563-4d24c85d99fd`
- **Widgets**: LongSpinBox, ComboBox2DA, ColorEdit, LocStringEdit, Dialogs, Editors

## Development Diagrams

### 16. [Build System Architecture](https://www.figma.com/online-whiteboard/create-diagram/daef0147-6437-407c-b08d-39bbdcb59d22)
Build system with packaging and distribution.
- **ID**: `daef0147-6437-407c-b08d-39bbdcb59d22`
- **Tools**: UV, PyInstaller, Nuitka, PyPI, GitHub Releases

### 17. [Testing Architecture](https://www.figma.com/online-whiteboard/create-diagram/472807f1-ffa0-4fca-82a5-ac242bd16b2c)
Comprehensive testing architecture.
- **ID**: `472807f1-ffa0-4fca-82a5-ac242bd16b2c`
- **Coverage**: Resource tests, TSLPatcher tests, Tool tests, Test infrastructure

### 18. [PyKotor Development Roadmap](https://www.figma.com/online-whiteboard/create-diagram/a07016c5-5ce3-4de0-80fe-d181e5c4710d)
Gantt chart showing development roadmap.
- **ID**: `a07016c5-5ce3-4de0-80fe-d181e5c4710d`
- **Timeline**: Q1-Q2 2026 feature development

### 19. [Resource Opening Sequence](https://www.figma.com/online-whiteboard/create-diagram/07559462-7ccd-4aed-b6b4-024bc57bb165)
Sequence diagram for opening resources in HolocronToolset.
- **ID**: `07559462-7ccd-4aed-b6b4-024bc57bb165`
- **Flow**: User → FileDialog → Installation → Cache → Editor

### 20. [Editor State Machine](https://www.figma.com/online-whiteboard/create-diagram/03524ce3-a850-4441-ad08-8fc99bb6d1fd)
Generic editor state machine.
- **ID**: `03524ce3-a850-4441-ad08-8fc99bb6d1fd`
- **States**: Uninitialized, Loading, Loaded, Editing, Validating, Saving, Error

### 21. [Installation Detection Flow](https://www.figma.com/online-whiteboard/create-diagram/7d9a8fa5-f65b-4e32-a26f-109c07672170)
Comprehensive installation detection workflow.
- **ID**: `7d9a8fa5-f65b-4e32-a26f-109c07672170`
- **Methods**: Registry, Steam, GOG, Common paths, Manual selection

### 22. [Project Configuration Structure](https://www.figma.com/online-whiteboard/create-diagram/a9ac16da-9795-4c10-9790-537670ab471c)
pyproject.toml workspace configuration.
- **ID**: `a9ac16da-9795-4c10-9790-537670ab471c`
- **Shows**: Workspace members, dev tools, dependencies

### 23. [PyKotor Documentation Map](https://www.figma.com/online-whiteboard/create-diagram/5f6fc88c-9d82-4fa3-b9ac-08f8166d2a14)
Comprehensive documentation navigation map.
- **ID**: `5f6fc88c-9d82-4fa3-b9ac-08f8166d2a14`
- **Shows**: All documentation files and their relationships

---

## Diagram Statistics

- **Total Diagrams**: 23
- **Categories**: 
  - Overview & Architecture: 7
  - Tool-Specific: 5
  - Core Systems: 4
  - UI & Editors: 3
  - Development: 4
- **Types**:
  - Flowcharts: 8
  - Sequence Diagrams: 4
  - State Machines: 2
  - Graphs: 8
  - Gantt Chart: 1

## Accessing the Diagrams

All diagrams are created in FigJam and can be:
1. **Viewed**: Click the links above to open in your browser
2. **Edited**: Claim the diagram to make edits (requires Figma account)
3. **Exported**: Export as PNG, PDF, or SVG from FigJam
4. **Shared**: Share links with team members for collaboration

## Usage in Documentation

These diagrams can be referenced in:
- Technical documentation
- Onboarding materials
- Architecture decision records (ADRs)
- Development guides
- Presentation materials
- Wiki pages

## Maintenance

When updating the codebase architecture:
1. Update the corresponding FigJam diagram
2. Note the change in this document
3. Communicate diagram updates to the team
