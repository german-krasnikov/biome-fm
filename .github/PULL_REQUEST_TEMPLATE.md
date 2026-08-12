## What

<!-- One sentence: what changed? -->

## Why

<!-- Why is this change needed? Link issues: Fixes #123 -->

## Test Evidence

- [ ] Unit tests pass — `uv run pytest tests/unit/ -x -q`
- [ ] Integration tests pass — `QT_QPA_PLATFORM=offscreen uv run pytest tests/integration/ -x -q`
- [ ] Coverage still above 80% — `uv run pytest --cov=biome_fm --cov-fail-under=80 -q`
- [ ] Lint clean — `ruff check src/ && mypy src/`
- [ ] Manual smoke test in the running app — describe below if UI changed

**Manual verification** (fill in if UI, theme, or keybinding changed):

```
Platform tested: macOS / Windows / Linux
Scenario tested:
Result:
```

## Checklist

- [ ] No file exceeds 300 lines (utility/static-only classes exempt)
- [ ] View is passive — no business logic in `*View` classes
- [ ] Every new file mutation is a `Command` subclass with `execute()` + `undo()`
- [ ] VFS writes guarded with `isinstance(vfs, WritableVFS)` check
- [ ] No hardcoded colours — theme tokens via `views/theme.py` + TOML
- [ ] No `os.path` string joins — `pathlib.Path` only
- [ ] No new dependencies without justification in PR body
- [ ] CHANGELOG.md updated (if user-facing change)
- [ ] No secrets, credentials, or `.env` files included
