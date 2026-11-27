#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

echo "== unit tests =="
PYTHONPATH=. python3 -m unittest discover -s tests

echo "== python syntax =="
python3 -m compileall -q hyprtk_editor tests scripts

echo "== qml lint =="
# Qt6's qmllint only; /usr/bin/qmllint on this box is Qt 5 (version "1.0") and
# cannot see QtQuick 6 modules. Stylistic warnings are not gated (they are
# legitimate style choices here); load errors and unknown types are.
QML_LINT=""
for candidate in /usr/lib/qt6/bin/qmllint qmllint6; do
    if [ -x "$candidate" ] || command -v "$candidate" >/dev/null 2>&1; then
        if "$candidate" --version 2>&1 | grep -q '^qmllint 6'; then
            QML_LINT="$candidate"
            break
        fi
    fi
done
if [ -n "$QML_LINT" ]; then
    lint_fail=0
    while IFS= read -r f; do
        out=$("$QML_LINT" "$f" 2>&1 || true)
        if printf '%s\n' "$out" | grep -Eq '^Error:|\[syntax\]|was not found|Cannot assign to non-existent|is not a type'; then
            printf '%s\n' "$out" | grep -E '^Error:|\[syntax\]|was not found|Cannot assign to non-existent|is not a type'
            lint_fail=1
        fi
    done < <(find hyprtk_editor/qml -name '*.qml')
    test "$lint_fail" -eq 0
else
    echo "Qt 6 qmllint not found — skipped"
fi

echo "== shell syntax =="
bash -n install.sh
sh -n bin/hyprtk-edit

echo "== headless boot =="
timeout 40 python3 scripts/bootcheck.py

echo "== cli =="
VERSION=$(PYTHONPATH=. python3 -c "import hyprtk_editor; print(hyprtk_editor.__version__)")
test "$(PYTHONPATH=. python3 -m hyprtk_editor --version)" = "hyprtk-edit $VERSION"

echo "== installer round-trip =="
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
HOME="$TMP" XDG_DATA_HOME="$TMP/.local/share" ./install.sh >/dev/null
test -x "$TMP/.local/bin/hyprtk-edit"
test -f "$TMP/.local/share/applications/hyprtk-editor.desktop"
test -f "$TMP/.local/share/hyprtk-editor/hyprtk-editor.svg"
HOME="$TMP" XDG_DATA_HOME="$TMP/.local/share" "$TMP/.local/share/hyprtk-editor/bin/hyprtk-edit" --version >/dev/null
HOME="$TMP" XDG_DATA_HOME="$TMP/.local/share" ./install.sh --uninstall >/dev/null
test ! -e "$TMP/.local/share/hyprtk-editor"

echo "QA PASS"
