# Changelog

## 0.2.0 — 2026-11-17

First wave of the v0.2 plan (see PLAN.md): the parts that make it feel finished.

- **Per-tab search.** Each document keeps its own query, replace text, match
  mode and match list, so `Ctrl+F` no longer drags a query from one file into
  the next. Switching tabs restores that file's search (and keeps the caret
  where it was); closing a tab drops its record.
- **Quick open (`Ctrl+P`).** One picker over the documents already open, the
  recent files and the current folder, ranked by a fuzzy subsequence score that
  prefers adjacent matches, word starts and shorter names (`main.py` beats
  `main_window_test.py`). The score lives in `search.fuzzy_score` / `search.rank`
  and is unit-tested without a display.
- **Tab strip.** Drag a tab to reorder (the model is only reordered on release,
  so the drag keeps its grab; a 2 px accent line marks the drop), middle-click
  closes a tab, and the wheel over the strip cycles tabs.
- The command palette and the quick-open picker now share one card
  (`components/PickerCard.qml`), so they cannot drift apart, and the shared
  component adds PageUp/PageDown paging and a "no matches" state.
- Fix: the minimap painted a solid slab on a short file — one bar per line
  scaled to the whole height and the viewport box was unclamped. Bars are
  capped at 3 px and the box is only drawn when the document is taller than the
  view.
- The headless boot check now drives the new paths (two tabs, find, tab switch,
  reorder, quick open) and fails if a QML function it calls is missing. It also
  runs against a throwaway XDG sandbox, so the gate no longer leaves its temp
  documents in the developer's real session.
- Documentation: the "part of the hyprtk suite" banner, the seven-repository
  table and the changelog footer that landed with the suite docs pass.

## 0.1.5 — 2026-11-17
- The right-click menu over the text (and over the find, replace, prompt and
  command-palette fields) now uses the editor palette. Qt Quick Controls hands
  out a `TextEditingContextMenu` painted from the control palette, so it came up
  in the stock black/blue of the Basic style, with the icon theme's coloured
  undo/cut/paste icons, next to a pywal window.
- It is a menu of the same actions in the app's own colours: surface panel,
  accent-tinted rounded border, accent hover, dimmed disabled entries, editor
  font, and no platform icons.
- Boot check now opens a document and right-clicks it, so a broken context menu
  fails the gate instead of shipping.

## 0.1.4 — 2026-11-17

- The file dialogs (Open, Save, Open Folder) no longer come up as the native GTK
  chooser. With `QT_QPA_PLATFORMTHEME=gtk3` — what the launcher sets — the
  platform theme hands out a GTK dialog, which ignores every colour this app
  could give it; the dialogs now insist on the Qt one and wear the editor
  palette instead: pywal background, surfaces, selection, headers, scrollbars
  and an accent-coloured primary button, in the editor font and size.
- The icon theme's blue floppy and red cross are stripped from the Save/Cancel
  buttons, so the dialogs read as part of the editor.
- Dialogs open at a workable size (900×560, capped to 70% of the screen) with a
  sidebar wide enough to read, and the long name filter no longer stretches the
  window to ~1570 px.
- The dressing survives `QFileDialog` rebuilding its buttons when the accept
  mode changes or the dialog is shown.

## 0.1.3 — 2026-11-17

- Fix: Ctrl+O, the Open file button, Save As and Open Folder opened nothing.
  The dialogs asked `QGuiApplication` for an `activeWindow` it does not have,
  so they died with an AttributeError before ever appearing. They are now built
  as `QFileDialog` instances marked transient for the editor window, so they
  float over it (Hyprland was tiling a parentless dialog beside the editor) and
  take keyboard focus.

## 0.1.2 — 2026-11-17

- Installer: `--system` installs under `/usr/local` (share + bin + desktop
  entry) for the live ISO, so every user gets the editor without a per-user
  install. Per-user remains the default.

## 0.1.1 — 2026-11-17

- Installer: fall back to a private PyPI venv when the distro's PySide6 lacks
  the QML bindings (Debian 12, Ubuntu 24.04) or Pygments is missing. The
  launcher prefers `venv/bin/python` when it exists.

## 0.1.0 — 2026-11-16

First working scaffold of the suite's text editor.

### Added
- Tabs with per-tab undo history, dirty markers, close guard and session restore
- Autosaved crash-recovery drafts with a recovery flow
- Open/save/save-as with atomic writes, mode preservation and stale-file protection
- Encoding (UTF-8, UTF-16 LE/BE, ISO-8859-1, Windows-1252), BOM and LF/CRLF/CR
  detection, preserved on save; binary and huge files open read-only
- Pygments syntax highlighting for 600+ languages, detected by extension or
  shebang, painted per visible block; language picker in the palette
- Current-line highlight, bracket matching, line numbers, minimap, word wrap,
  zoom, status bar
- Incremental find with case/whole-word/regex modes, live match painting,
  replace one/all
- Command palette over every action, including language, encoding and line endings
- Line operations: duplicate, move, delete, comment toggle, sort asc/desc/unique,
  trim trailing whitespace, join, case changes, indent/outdent, tabs↔spaces
- pywal/bar palette with palette-derived syntax colours and live reload
- File watching + reload, drag and drop, hyprtk-fm/terminal/clipboard integration
- Installer, desktop entry, icon, 73 unit tests and a QA script

---

Part of the **hyprtk suite** — [dotfiles](https://github.com/hyprtk/dotfiles) · [bar-qt](https://github.com/hyprtk/hyprtk-bar-qt) · [file manager](https://github.com/hyprtk/hyprtk-file-manager) · [editor](https://github.com/hyprtk/hyprtk-editor) · [config manager](https://github.com/hyprtk/hyprtk-hyprland-config-manager) · [hyprtk-usb](https://github.com/hyprtk/hyprtk-usb) · [ISO creator](https://github.com/hyprtk/Hyprtk-ISO-Creator)
