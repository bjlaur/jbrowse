# Screenshot Analysis — Ranking All Harness Captures

## Methodology

Each screenshot is ranked on a 1-10 scale across multiple dimensions:

- **Beautifulness**: Visual appeal, layout quality, use of space
- **Significance**: How important the feature is to the app's core functionality
- **Interestingness**: How visually interesting or unique the screenshot is
- **Documentation Value**: How useful this screenshot is for showing users what the app does
- **Technical Complexity**: How much engineering is visible in the screenshot

## All 31 Screenshots Ranked

| # | Screenshot | Beautiful | Significant | Interesting | Doc Value | Tech Complex | **TOTAL** | Notes |
|---|-----------|:---------:|:-----------:|:-----------:|:---------:|:------------:|:---------:|-------|
| 1 | **now-playing.svg** | 9 | 10 | 9 | 10 | 9 | **47** | Progress bar with █░ blocks, track info, state display. The flagship feature. |
| 2 | **info.svg** | 8 | 10 | 8 | 10 | 7 | **43** | Media details, episode navigation, subtitle info. Core browsing experience. |
| 3 | **playback-control.svg** | 8 | 9 | 8 | 9 | 8 | **42** | Ctrl+P overlay, shows all playback controls in one place. |
| 4 | **jump-to-time.svg** | 8 | 8 | 9 | 8 | 8 | **41** | New feature, timeline bar, time input. Visually distinctive. |
| 5 | **replace-prompt.svg** | 7 | 9 | 7 | 9 | 7 | **39** | Shows current vs new item, action buttons. Important UX flow. |
| 6 | **help.svg** | 7 | 8 | 6 | 10 | 5 | **36** | All hotkeys listed. Essential documentation. Largest file (57KB). |
| 7 | **browser.svg** | 7 | 10 | 5 | 9 | 5 | **36** | Main view, but plain list. High significance, low visual interest. |
| 8 | **now-playing-quality.svg** | 7 | 7 | 8 | 7 | 7 | **36** | Quality flash message visible. Shows Ctrl+B feedback. |
| 9 | **subtitles.svg** | 7 | 8 | 6 | 8 | 6 | **35** | Subtitle picker overlay. Important for accessibility. |
| 10 | **mpv-log.svg** | 6 | 7 | 7 | 7 | 7 | **34** | mpv output, command display. Important for debugging. |
| 11 | **info-playing.svg** | 7 | 7 | 7 | 7 | 7 | **35** | Live IPC progress on info page. Shows integration working. |
| 12 | **ctrl-b-bitrate.svg** | 7 | 7 | 7 | 7 | 7 | **35** | Quality label updates. Shows bitrate cycling. |
| 13 | **search.svg** | 6 | 8 | 5 | 7 | 4 | **30** | Search functionality. Important but visually plain. |
| 14 | **playback-control-menu.svg** | 7 | 7 | 6 | 7 | 6 | **33** | Same as playback-control but from menu context. |
| 15 | **ctrl-p-from-browser.svg** | 7 | 7 | 6 | 7 | 6 | **33** | Ctrl+P from browser context. Verifies fix works. |
| 16 | **after-ctrl-x.svg** | 6 | 6 | 6 | 6 | 4 | **28** | Theme cycle. Shows theming but visually similar to browser. |
| 17 | **refreshing.svg** | 5 | 6 | 4 | 6 | 4 | **25** | Refresh state. Important but visually minimal. |
| 18 | **mpv-log-scrolled.svg** | 5 | 5 | 5 | 5 | 5 | **25** | Scrolled mpv log with line numbers. |
| 19 | **web-url.svg** | 5 | 6 | 4 | 6 | 4 | **25** | Web URL overlay. Niche but useful feature. |
| 20 | **web-url-info-overlay.svg** | 5 | 5 | 4 | 5 | 4 | **23** | Same overlay from info page context. |
| 21 | **web-url-now-playing-overlay.svg** | 5 | 5 | 4 | 5 | 4 | **23** | Same overlay from Now Playing context. |
| 22 | **now-playing-backspace-to-info.svg** | 5 | 5 | 4 | 5 | 4 | **23** | Navigation verification. Important for testing, not for docs. |
| 23 | **info-backspace-to-browser.svg** | 5 | 5 | 4 | 5 | 4 | **23** | Navigation verification. |
| 24 | **ctrl-n-now-playing.svg** | 5 | 5 | 4 | 5 | 4 | **23** | Ctrl+N navigation to Now Playing. |
| 25 | **space-pause.svg** | 5 | 5 | 4 | 5 | 4 | **23** | Pause state verification. |
| 26 | **seek-comma-period.svg** | 5 | 5 | 4 | 5 | 4 | **23** | Seek state verification. |
| 27 | **ctrl-k-stop.svg** | 5 | 5 | 4 | 5 | 4 | **23** | Stop state verification. |
| 28 | **bottom-bar-format.svg** | 4 | 4 | 3 | 4 | 3 | **18** | Bottom bar format check. Testing artifact. |
| 29 | **bottom-bar-long-name.svg** | 4 | 4 | 3 | 4 | 3 | **18** | Truncation test. Testing artifact. |
| 30 | **replace-n-to-info.svg** | 4 | 4 | 3 | 4 | 3 | **18** | Navigation verification. Testing artifact. |
| 31 | **info-progress-auto-update.svg** | 4 | 4 | 3 | 4 | 3 | **18** | Timer poll verification. Testing artifact. |

## Top 10 Recommended for README

Based on the analysis, these are the 10 screenshots that should be in `docs/screenshots/`:

| Rank | Screenshot | Why |
|------|-----------|-----|
| 1 | **now-playing.svg** | Flagship feature, beautiful progress bar, shows off IPC integration |
| 2 | **info.svg** | Core browsing experience, media details |
| 3 | **playback-control.svg** | Shows all playback controls, demonstrates Ctrl+P |
| 4 | **jump-to-time.svg** | New feature, visually distinctive timeline bar |
| 5 | **replace-prompt.svg** | Important UX flow, shows item comparison |
| 6 | **help.svg** | Essential documentation reference |
| 7 | **browser.svg** | Main view (keep existing) |
| 8 | **subtitles.svg** | Accessibility feature, important for users |
| 9 | **search.svg** | Core functionality (keep existing) |
| 10 | **after-ctrl-x.svg** | Shows theming (keep existing) |

## Comparison with Current 8

**Current**: browser, after-ctrl-x, help, info, mpv-log, refreshing, search, subtitles

**Recommended**: browser, after-ctrl-x, help, info, search, subtitles, now-playing, playback-control, jump-to-time, replace-prompt

**Changes**:
- **Add**: now-playing, playback-control, jump-to-time, replace-prompt
- **Remove**: mpv-log, refreshing (less visually interesting, more technical)

## Category Breakdown

### Must-Have (Core Features)
- browser.svg — main view
- info.svg — media details
- search.svg — search functionality
- help.svg — documentation

### Should-Have (Key Differentiators)
- now-playing.svg — flagship playback UI
- playback-control.svg — global playback overlay
- jump-to-time.svg — new unique feature
- replace-prompt.svg — important UX flow

### Nice-to-Have (Supporting Features)
- subtitles.svg — accessibility
- after-ctrl-x.svg — theming

### Testing-Only (Not for README)
- All navigation verification screenshots (ctrl-n, backspace, space, seek, ctrl-k)
- All overlay context variants (web-url from different pages)
- Bottom bar format/truncation tests
- Timer poll verification
