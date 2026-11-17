# Research: Linux text editors, and what hyprtk-editor borrows

Survey done 2026-11-16. The goal was not to clone one editor but to pick the
strongest idea from each desktop and fit it into the suite's stack.

## The field

| Desktop | Default editor | Stack | Ideas worth taking |
|---|---|---|---|
| GNOME | Text Editor (`gnome-text-editor`) | GTK4 / libadwaita | Session restore on by default; autosave drafts; style-scheme previewer; deliberately no tabs |
| KDE | Kate | Qt / KTextEditor | 400+ languages, LSP, splits, sessions/projects, multi-cursor, column select, vi mode, embedded terminal, minimap, swap-file recovery, MD/HTML/SVG preview, replace-in-files |
| Xfce | Mousepad | GTK3 | Tiny footprint, per-tab search bar, instant match highlighting, column select, Hunspell, plugin skeleton |
| Cinnamon | Xed | GTK3 | gedit-style plugins, file-browser sidebar, regex find/replace, sort lines, modelines, word/character/byte stats, print preview |
| MATE | Pluma | GTK3 | Snippets, spell check, plugin API (same lineage as Xed) |
| LXQt | FeatherPad | Qt Widgets | Tab drag-detach/attach, per-tab search entry, side pane, **auto-save**, non-interrupting prompts, column select, session |
| elementary | Code | GTK | Minimal chrome, regex search, terminal plugin |
| Cross-DE | Geany | GTK / Scintilla | Symbols pane, code folding, bookmarks, build commands, projects, "send selection to command" |
| Cross-DE | VS Code / Sublime | Electron / C++ | Command palette, minimap, multi-cursor, diff gutter, extensions |
| Cross-DE | Zed / Lapce | Rust / GPU | Tree-sitter, LSP, collaboration, GPU text rendering |
| Terminal | micro | Go | Sane defaults, persistent undo, diff gutter, mouse-rich selection, Lua plugins |
| Terminal | Neovim / Helix | C / Rust | Modal editing, composability |

## Recurring gaps

1. **Data loss** — unsaved work lives in RAM or a swap file; few combine
   autosave drafts, session restore *and* crash recovery, and almost none show
   the recovery clearly.
2. **Search is hidden or modal** — Kate and Mousepad get this right; GNOME Text
   Editor and FeatherPad bury it.
3. **Theme drift** — none follow pywal, so the editor never matches the desktop.
4. **Overload** — Kate/VS Code drown a quick edit in panels; Text Editor and
   Mousepad refuse to grow.
5. **Suite integration** — no clean handoff to a specific file manager, bar,
   clipboard history or terminal.

## What hyprtk-editor takes

| Borrowed | From | How it appears here |
|---|---|---|
| Session restore + autosave drafts | GNOME Text Editor, FeatherPad, Kate swap files | `session.json` + per-document drafts in the cache; unsaved buffers are recoverable after a crash |
| No-tab-empty state with recents | GNOME | Welcome page with recent files and a recovery banner |
| Regex/whole-word search with live match highlighting | Kate, Mousepad | Find bar, debounced, matches painted through the highlighter |
| Command palette as the only menu | VS Code / Sublime / Zed | `Ctrl+K` covers every action, including language, encoding and EOL |
| Minimap | Kate, VS Code | Scaled line bars with a viewport box; click/drag to scroll |
| Line operations | Kate, Geany | Duplicate/move/delete/comment/sort/unique/trim/join/case/indent |
| Bracket match, current-line highlight | Kate, Geany | Painted by the document highlighter, not a second widget |
| Tabs that keep undo history | Kate, FeatherPad | One `TextArea` per document, created imperatively |
| Non-interrupting prompts | FeatherPad | Toast for success/info; modal only for destructive choices |
| Atomic saves, mode preservation | Kate | Temp file + `os.replace`, `chmod` from the original |
| Encoding/BOM/EOL control | Geany, Kate, Xed | Status bar + palette commands; byte-faithful save |
| Instant startup, small surface | Mousepad, Leaflet-class | No plugin system, no project model, no background daemons |

## What is deliberately **not** in v0.1

- Plugin system (Geany/gedit lineage): a plugin API is a long-term maintenance
  contract, not a first-release feature.
- LSP and project symbols (Kate/Zed): planned for v0.3, after the editor core is
  solid.
- Multi-cursor and column selection (Kate/Geany): planned for v0.2.
- Split view: v0.2, after tab state handling settles.
- vi mode: a mode layer over the text engine is a separate project.

## Stack investigation

- **PySide6 is already a suite dependency** (`hypr/packages/system.sh` installs
  it on all six package families for hyprtk-usb and hyprtk-iso-creator), so a Qt
  editor adds no new distro package surface.
- **Quickshell + Python** would match hyprtk-fm, but `TextArea` has no
  virtualised rendering and no C++ highlighter hook without building a plugin.
- **Qt Widgets + `QPlainTextEdit`** has the strongest text engine
  (virtualised, real undo stack), but would not share the QML visual language.
- **PySide6 + Qt Quick/QML** was chosen: QML chrome for suite parity, and a real
  `QTextDocument`/`QSyntaxHighlighter` underneath. Verified on Qt 6.12 that a
  Python `QSyntaxHighlighter` attaches to a QML `TextArea` through
  `QQuickTextDocument` and that the formats paint.

Measured costs on this machine (offscreen, software backend):

| Operation | Cost |
|---|---|
| Pygments tokenise, 6,000 lines / 78 KB | 135 ms |
| `QSyntaxHighlighter.rehighlight()`, 300 blocks | 21 ms |
| … 1,500 blocks | 158 ms |
| … 6,000 blocks | 2.4 s |
| … 24,000 blocks | 40 s |
| Plain edit + repaint, 6,000 lines | 2 ms |
| Plain edit + repaint, 24,000 lines | 8 ms |
| `rehighlightBlock`, one block at 6,000 lines | ~0.8 ms |
| `rehighlightBlock`, one block at 24,000 lines | ~3.4 ms |
| Bulk `QTextLayout.setFormats`, 24,000 blocks | 54 ms (not painted by QQuickTextEdit) |

Conclusion: tokenise once, paint only the viewport. That is what the
implementation does.

## Sources

- Kate features — https://kate-editor.org/about-kate/
- Kate overview — https://apps.kde.org/kate/
- GNOME Text Editor — https://apps.gnome.org/TextEditor/
- Mousepad — https://docs.xfce.org/apps/mousepad/4.18/start
- Xed — https://en.wikipedia.org/wiki/Xed
- FeatherPad — https://github.com/tsujan/FeatherPad
- Geany manual — https://www.geany.org/manual/current/
- micro — https://github.com/zyedidia/micro
- Zed docs — https://zed.dev/docs/
- hyprtk suite package manifest — `hyprtk-merged/hypr/packages/system.sh`
- Qt Quick `TextEdit`/`TextArea` API, checked live against Qt 6.12
