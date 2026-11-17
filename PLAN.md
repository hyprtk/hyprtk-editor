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

Waves 1–2 shipped as **0.2.0** and **0.2.1** (2026-11-17). Planned 2026-11-17. Four waves, each a release; the order is by dependency and
risk, not by glamour. Everything below was probed against Qt 6.12 before being
written down.

### Wave 1 — feel (0.2.0)

- [x] **Per-tab find bar.** The query belongs to the window today
      (`win.matches`/`win.matchIndex`, one `findBar`). Store per document:
      `find = {docId: {query, replacement, case, word, regex, replaceMode,
      visible, matchIndex, matches}}`; `openFind/runSearch/applyMatchHighlight/
      selectMatch/closeFind` operate on the active record, `activateTab` stores
      the bar into the outgoing record and re-applies the incoming one, and the
      per-document ranges keep painting through `Bridge.setSearch`. No Python
      change.
- [x] **Tab drag-reorder, middle-click close, wheel to cycle.** Non-live drag:
      track `dragTabId`/`dropIndex` from pointer x over the strip's children,
      draw a 2 px accent insertion line, commit with `moveDocument()` on
      release. Never reorder during the drag — reordering a `Repeater` model
      destroys the delegate that owns the mouse grab.
- [x] **Quick open (`Ctrl+P`).** Extract the card chrome out of
      `CommandPalette.qml` into `components/PickerCard.qml` (field, list,
      footer, key handling) so both pickers look identical. Bridge gains
      `quickOpen(current_path)` (recents then the current folder, deduped) and
      `rankFiles(items, query)`. Ranking is `search.fuzzy_score()` — a
      subsequence score with contiguity and word-start bonuses — so it is
      unit-testable and reusable by the command palette. Empty query = recents.

### Wave 2 — performance and precision (0.2.1)

- [x] **Off-thread tokenising.** `Bridge.recompute` submits
      `(key, text, alias, generation)` to a single-worker `ThreadPoolExecutor`
      and applies the spans on a `Signal` (auto-queued, so `QSyntaxHighlighter`
      is only touched on the GUI thread). Stale generations are dropped; files
      under ~40 KB stay synchronous so small buffers never flicker.
- [x] **Git diff gutter.** New `gitdiff.py`: `rev-parse --show-toplevel`,
      `diff -U0 --no-color -- <rel>`, parse `@@` hunks into new-side
      `{line: add|mod|del}`, cached on `(path, mtime)` and recomputed on
      open/save/activate (never per keystroke — the working tree only changes
      on save). Painted as a 6 px stripe **left of** the gutter so it survives
      `wrap` mode and the `line_numbers` toggle, plus bars in the minimap
      canvas. Parser tested against fixed diff text.
- [x] **Print / export PDF.** `printdoc.py` builds a **fresh** light-theme
      `QTextDocument` from the buffer (the live one carries dark-palette
      formats): mono font, page margins, file/page header, optional syntax
      colour by re-tokenising with the existing `spans()`. `exportPdf(docId,
      path)` writes through `QPdfWriter`; `printDoc(docId)` opens a
      `QPrintDialog`, transient-parented exactly like the file dialogs.

### Wave 3 — the big one (0.2.2)

- [ ] **Split view**, and the refactor it forces. `Bridge._editors` and the QML
      `panes` map are keyed by **document** id, so one document cannot have two
      views. Introduce `paneId`: `attach(area, paneId, docId)` and every
      `refresh/recompute/setSearch/setBrackets/setCurrentLine/setLanguage/
      setPath/detach` takes the pane key. **Drafts and sessions stay
      document-keyed** — a draft belongs to a document, not a view. Then a
      two-pane layout with a dragged handle, `focusPane` tracking, `Ctrl+\`
      toggle, `Ctrl+1/2` to focus, and the rule that a document lives in one
      pane (no text mirroring, so undo stays sound). Split ratio and pane
      assignment persist in the session.
- [ ] **Markdown preview** in the secondary pane — nearly free once 3 lands:
      `Bridge.markdownHtml(text)` runs `QTextDocument.setMarkdown()` then
      `toHtml()` with palette CSS injected, rendered by a read-only
      `TextEdit` (`TextEdit.RichText`). Going through Python rather than QML's
      `TextEdit.MarkdownText` guarantees heading/code/link colours against the
      dark palette instead of trusting Qt's default black. `onLinkActivated` →
      `Qt.openUrlExternally`. No images in v1 (needs a resource loader).

### Wave 4 — polish (as it fits)

- [ ] **Spell check**, runtime-optional: no `hunspell` binary or dictionary is
      installed on this box (`enchant-2` has no backends, no `python-enchant`),
      so detect `hunspell` + dictionary at startup and hide the setting when
      absent. `spell.py` speaks the `hunspell -a` line protocol through one
      persistent subprocess; paint `WaveUnderline` via a `Highlighter` word set
      (visible blocks only, 500 ms debounce, cached by text hash). Only for
      `text`/`markdown` aliases, skipping words with digits or underscores.
      Adding `hunspell-en_US` to all six families + the ISO is a separate
      decision that costs a full T1/T2 gate.
- [ ] **Whitespace / indent guides.** A `Canvas` between the pane's base
      rectangle and the `ScrollView` (the TextArea's background is already
      `null`, so it shows through): 1 px guides at each indent stop for the
      visible range, offset by `-contentY`, using the `lineHeight`/`charWidth`
      the pane already computes. Whitespace dots ride the same canvas behind a
      toggle, capped to the visible range.
- [ ] **Restore maximized state** and document that a fixed window position is
      a Hyprland window rule, not an app setting — Wayland ignores
      `ApplicationWindow.x/y`; only the size is saved today.
- [ ] **Toolbar icons.** Nerd Font glyphs are the suite convention (the bar
      uses the same font), so keep `Glyph.qml` and only replace the three text
      buttons in the tab strip (Save / Find / Commands) with glyph + tooltip.

### Cut from v0.2

- [ ] ~~Multi-cursor / column selection.~~ `QQuickTextEdit` exposes one cursor
      and cannot be painted inside; the only shadow (painting N ranges through
      the `Highlighter`) gives invisible carets, and multi-range edits would
      have to fake undo grouping — the one place a bug corrupts documents. It
      needs a custom text engine, so it moves next to the v0.3 work.

### Release discipline for each wave

`make qa` (unit tests, compileall, qmllint, shell syntax, headless bootcheck,
CLI version, installer round-trip — `scripts/qa.sh` hardcodes the version
string, so bump it with the release), extend `bootcheck.py` with the wave's new
interaction, bump `CHANGELOG`/`README`, tag the standalone repo, vendor
byte-identically into `hyprtk-merged/installer/hyprtk-editor/`, then `push-all`.

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

- [x] Create `github.com/hyprtk/hyprtk-editor`, push `main`, tag `v0.1.1`.
- [x] Vendor the tree into `hyprtk-merged/installer/hyprtk-editor/`
      (exclude `.git`, `tests/`, `scripts/`, `PLAN.md`, `RESEARCH.md`, `shot.png`).
- [x] Call `installer/hyprtk-editor/install.sh` from `1-install.sh` after the
      file manager (the suite installer has no uninstall path).
- [x] Add Pygments per family (`python-pygments`, `python3-pygments`,
      `python3-pygments`, `python3-pygments`, `python3-Pygments`,
      `py3-pygments`) plus the QML runtime modules where the distro splits them;
      T1 resolved every name.
- [x] Add the **Editor** quick link (quick links + arc menu) and the `Super+E`
      keybind.
- [x] ISO: `packages.hyprtk` bakes `pyside6` + `python-pygments`;
      `customize_airootfs.sh` installs bar/fm/editor **system-wide** with
      `--system` into `/usr/local`; `hyprtk-first-run` only seeds per-user
      config/themes, `~/.local/bin` links, the palette and XDG defaults, and
      gates the stamp on both the bar and `hyprtk-edit`.
- [x] Default handler: `text/plain` and `text/markdown` via
      `set-default-apps.sh` and the installer's `--set-default`.
- [x] `push-all` gate: T1 1340 resolvable / 26 AUR / 89 allowed / 0 unexpected,
      T2 9/9, audit 1455 rows / 0 unexpected (16 provides-only `Extra (TODO)`,
      15 pre-existing). Suite v1.6.0 tagged on dotfiles, live fast-forwarded.
- [x] Reinstall: editor 0.1.1, bar 0.43.7, default handlers set, bar restarted.

Release state: **hyprtk-editor 0.2.1** (v0.2 waves 1–2: per-tab find, quick
open, tab reorder, off-thread tokenising, git gutter, print/PDF), hyprtk-fm
1.8.7, bar-qt 0.43.8, suite v1.7.4 (dotfiles `eccc5edbc`).

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
