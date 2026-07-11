# Research Summary — Biome FM

## Decision: Python + PySide6/Qt

### Alternatives Evaluated (40+ agents, 3 sessions)

| Framework | Verdict | Key Reason |
|-----------|---------|------------|
| **PySide6/Qt** | **CHOSEN** | Ecosystem, D&D, 100k+ files, AI native, 35 years maturity |
| Textual | Rejected | CSS O(n) bottleneck, no D&D, GC pauses, Textualize dissolved |
| wxPython | Runner-up | Truly native, 7MB, but bus factor=2, no animations |
| Flet | Rejected | No TreeView, no headless tests, pre-1.0 |
| Kivy | Rejected | OpenGL-only, mobile-centric, never native |
| Dear PyGui | Rejected | No native look, weak testing |
| Toga | Rejected | Beta, missing critical FM features |
| pywebview/NiceGUI | Rejected | No virtual scroll, basic D&D |
| Kotlin/Compose | Rejected | No Python AI ecosystem, everything from scratch |

### Key Architecture Decisions

1. **MVP Pattern** — Views passive (signals), Presenters hold logic (testable w/o Qt)
2. **VFS via fsspec** — local/SSH/S3/archive, 20+ backends
3. **Command Pattern** — every mutation = Command with execute()+undo()
4. **Plugins via pluggy** + entry_points discovery
5. **Config: TOML** (stdlib tomllib) + dataclass validation
6. **AI: Provider abstraction** — Claude/Ollama/NoOp, graceful degradation
7. **Hot paths in Rust** — scandir-rs, xxhash, watchfiles, blake3
8. **Testing: 80% unit (no Qt)** + 15% integration (offscreen) + 5% property (Hypothesis)

### Reference Architectures

- **Nimble Commander** — VFS host chaining, PanelData/View split, Job queue
- **fman** — plugin-as-core, convention-over-configuration commands
- **F2 Commander** — fsspec VFS, Textual dual-pane
- **Double Commander** — WCX/WFX/WDX plugin API design
- **Sunflower** — ABC plugin system + importlib discovery

### Performance Stack

| Task | Tool | Speed |
|------|------|-------|
| Dir traversal 100k+ | scandir-rs (Rust) | 5-70x os.walk |
| File hashing | xxhash | 14 GB/s |
| File watching | watchfiles (Rust) | ~0% CPU, 10ms latency |
| File copy | shutil.copy2 | kernel zero-copy (fcopyfile) |
| Crypto hash | blake3 | 3.7 GB/s |
| APFS clone | ctypes clonefile | instant (CoW) |
