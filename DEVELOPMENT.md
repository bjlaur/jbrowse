# DEVELOPMENT.md

Development checklist and conventions for the jbrowse project.

---

## Every Few Commits (Habit Checks)

Run these regularly — don't wait until release time.

### Documentation
- [ ] `AGENTS.md` — "Current Playback / IPC Status" section reflects what's actually done
- [ ] `TODO.md` — completed items checked off, "Next" pointer updated
- [ ] `CHANGELOG.md` — recent changes have entries with testing summaries
- [ ] `README.md` — version number, features list, controls reference, config example are current
- [ ] `jbrowse.conf.example` — any new config sections added

### Tests & Screenshots
- [ ] `python -m py_compile jbrowse.py` — no syntax errors
- [ ] `python -m py_compile tools/svg_screenshot_poc.py` — no syntax errors
- [ ] `python tools/svg_screenshot_poc.py --item otter` — all SVG captures pass
- [ ] **Every new UI page/overlay/prompt has a corresponding capture in the harness** with expected text checks
- [ ] Use `--view <name>` for fast single-capture iteration during development

### Code Quality
- [ ] `backspace` key works to go back/close on every overlay that uses `q`
- [ ] IPC failures are graceful — fall back to existing behavior, never crash
- [ ] `PlaybackManager` owns all IPC state; `BrowseApp` calls public methods only
- [ ] No new Python packages needed (all stdlib: `socket`, `json`, `tempfile`)

### Commit Discipline
- [ ] Commit message is short (~8 words), imperative mood
- [ ] Every commit updates `AGENTS.md`, `TODO.md`, and `CHANGELOG.md`
- [ ] Ask user before pushing to remote

---

## Release (Every Release)

See [AGENTS.md § Release Checklist](AGENTS.md) for the full per-release checklist.

Key steps:
1. Run all "Every Few Commits" checks above
2. Full screenshot harness: `python tools/svg_screenshot_poc.py --item otter`
3. IPC smoke test: `python tools/svg_screenshot_poc.py --ipc-only --real --play-duration 5`
4. Manual release check (see CHANGELOG.md section for current version)
5. Update version number in `README.md` and `jbrowse.py` (`CLIENT_VERSION`)
6. Final `git diff --stat` review
7. Ask user before committing/pushing

---

## Major Release (Infrequent)

Everything in "Release" above, plus:

- [ ] Full theme gallery: `python tools/svg_screenshot_poc.py --item otter --all-themes`
- [ ] Verify all themes render without errors in `docs/themes/`
- [ ] Spot-check 3–4 theme SVGs visually for correct colors
- [ ] Copy updated screenshots from `tools/screenshot/` to `docs/screenshots/` for README use
- [ ] Review and update `README.md` from scratch if needed
- [ ] Update `CHANGELOG.md` with full release notes and testing summary
- [ ] Ask user before pushing to remote

---

## Screenshot Harness Quick Reference

```bash
# Full harness (all captures)
python tools/svg_screenshot_poc.py --item otter

# Single capture (fast iteration)
python tools/svg_screenshot_poc.py --view now-playing
python tools/svg_screenshot_poc.py --view replace-prompt
python tools/svg_screenshot_poc.py --view web-url
python tools/svg_screenshot_poc.py --view playback-control

# IPC smoke test (quick regression)
python tools/svg_screenshot_poc.py --ipc-only --real --play-duration 0.5

# IPC smoke test (full release)
python tools/svg_screenshot_poc.py --ipc-only --real --play-duration 5

# Full theme gallery (major releases only)
python tools/svg_screenshot_poc.py --item otter --all-themes

# Browse fixture data interactively
./jbrowse.py --fake
```

### Adding a New Capture

1. Add a new entry to the `captures` list in `tools/svg_screenshot_poc.py`:
   ```python
   ("my-new-screen.svg", "my-new-view", ["expected", "text", "on", "screen"]),
   ```
2. Add a view handler in `export_view()` if needed
3. Run `python tools/svg_screenshot_poc.py --view my-new-view` to verify
4. Run full harness to make sure nothing broke
