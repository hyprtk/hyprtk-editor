# hyprtk-editor — plan

Status: **v0.1.0 scaffold is working** — it opens, edits, highlights, searches,
saves, restores sessions and recovers drafts. This file records what is done,
what is deliberately deferred, and how the app joins the suite.

## Decisions (and why)

| Decision | Rationale |
|---|---|
| **PySide6 + Qt Quick/QML** | QML chrome gives visual parity with bar-qt/hyprtk-fm; `QTextDocument` + `QSyntaxHighlighter` give a real text engine. PySide6 is already installed on all six package families for hyprtk-usb/iso-creator. |
| **One `TextArea` per tab** | Swapping text into a single editor would throw away per-tab undo history and scroll state. Tabs are created imperatively and destroyed on close. |
| **Pygments, one tokenise per document** | 600+ languages with no per-language rule maintenance; 135 ms for 6,000 lines is acceptable behind a 700 ms idle debounce. |
| **Viewport-scoped `rehighlightBlock`** | Whole-document `rehighlight()` is quadratic on QML (2.4 s at 6,000 lines, 40 s at 24,000). The measurements are in README/RESEARCH. |
| **Palette through `Bridge.palette`** | QML singletons cannot read context properties, and PySide6 singleton registration is unusable here. Values are converted to `QColor` in Python so alpha helpers work. |
| **Installer copies a tree, no venv** | Mirrors hyprtk-fm; PySide6/Pygments are distro packages. Avoids a second copy of Qt and keeps startup fast. |

## Done in v0.1.0

- [x] Tabs, dirty state, close guard, per-tab undo/scroll
- [x] Open/save/save-as, atomic writes, mode preservation, stale-file guard
- [x] Encoding/BOM/EOL detection and faithful save; binary/huge guards
- [x] Pygments highlighting with language detection (extension + shebang)
- [x] Viewport-scoped highlighting, current-line highlight, bracket matching
- [x] Find/replace with case, whole word, regex; live match painting
- [x] Command palette (all actions incl. language/encoding/EOL)
- [x] Line operations, sort/unique, trim, join, case, indent/outdent, tabs↔spaces
- [x] Line numbers, minimap, word wrap, zoom, status bar
- [x] Session restore, autosaved drafts, recovery flow
- [x] pywal/bar palette, palette-derived syntax colours, live wallpaper reload
- [x] File watching + reload, drag and drop, suite integration (fm/terminal/clipboard)
- [x] 73 unit tests, qmllint, headless boot check, installer round-trip

## v0.2 — make it feel finished

- [ ] **Per-tab find bar** — the query currently belongs to the window; Mousepad's
      per-tab entry is better once several files are open.
- [ ] **Quick open (`Ctrl+P`)** over recent files and the current folder.
- [ ] **Split view** (horizontal/vertical), sharing the tab model.
- [ ] **Markdown preview** side pane. Needs a renderer; prefer Qt's
      `QTextDocument.setMarkdown()` over a Python dependency.
- [ ] **Git diff gutter** — `git diff --unified=0` for the open file, painted in
      the margin.
- [ ] **Multi-cursor / column selection** — requires a custom selection layer;
      scope it before starting.
- [ ] **Tab drag-reorder** and middle-click close.
- [ ] **Restore window position** (size is already saved).
- [ ] **Print / export PDF** via `QTextDocument`.
- [ ] **Spell check** (Hunspell) as an optional, non-intrusive underline.
- [ ] **Whitespace/indent guides** — needs a margin painter or a QML overlay;
      do it with the document layout, not per-character formats.
- [ ] Move tokenising to a worker thread so files near the 400 KB ceiling do not
      pause the UI.
- [ ] A real icon set for the chrome (currently Nerd Font glyphs + text).

## v0.3 — code-aware (only after v0.2 is stable)

- [ ] LSP client over JSON-RPC (spawn `pylsp`/`clangd`/`gopls`/`rust-analyzer`)
- [ ] Diagnostics in the gutter + a problems panel
- [ ] Symbols / go-to-definition / hover
- [ ] Project sidebar (folder tree, filter)
- [ ] Build/run command per project

## Deliberately out of scope

- Plugin API (long-term support cost)
- vi mode (a separate input layer, not a feature flag)
- Terminal emulator integration
- Collaborative editing

## Suite integration checklist

The app lives in its own repo (`hyprtk-editor`), like hyprtk-fm and bar-qt.
When it is ready to ship with the suite:

- [ ] Create `github.com/hyprtk/hyprtk-editor`, push `main`, tag `v0.1.0`.
- [ ] Vendor the tree into `hyprtk-merged/installer/hyprtk-editor/`
      (exclude `.git`, `tests/`, `scripts/`, `PLAN.md`, `RESEARCH.md`, `shot.png`).
- [ ] Call `installer/hyprtk-editor/install.sh` from `1-install.sh` after the
      file manager, and add the uninstall path.
- [ ] Add the app to `hyprtk/packages/system.sh`? **No new packages needed** —
      PySide6 is already there; Pygments may need adding per family:
      `python-pygments`, `python3-pygments`, `python3-pygments`,
      `python3-pygments`, `python3-pygments`, `py3-pygments`.
      Run the T1 matrix to confirm the name on each family.
- [ ] Add a **bar quick link** ("Editor") and a `Super+E` style keybind, using
      the same pattern as the Files quick link.
- [ ] Add the desktop entry to the ISO package set / `airootfs` skel if the ISO
      should ship it.
- [ ] Decide the default handler: `xdg-mime default hyprtk-editor.desktop
      text/plain` in the installer, or leave it to `--set-default`.
- [ ] `push-all` (gate: T1 matrix, T2 dry-run, package audit) and reinstall the
      suite; verify `hyprtk-edit --version` from the installed copy.
- [ ] CHANGELOG + suite tag.

## Known constraints to keep in mind

- QML `TextArea` lays out the whole document; thresholds are 400 KB
  (no highlight/minimap) and 2 MB (read-only). Do not remove the guards without
  replacing the text engine.
- The gutter is hidden in wrap mode; a wrapped-line-aware gutter needs a custom
  layout pass.
- `QSyntaxHighlighter` must notify per block; never call `rehighlight()` on a
  large document.
- `QTextLayout.setFormats` in bulk is fast but **not painted** by
  QQuickTextEdit. Do not "optimise" the highlighter that way.
