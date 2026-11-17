#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

echo "== unit tests =="
PYTHONPATH=. python3 -m unittest discover -s tests

echo "== python syntax =="
python3 -m compileall -q hyprtk_editor tests scripts

echo "== qml lint =="
if command -v qmllint >/dev/null 2>&1; then
    while IFS= read -r f; do qmllint "$f"; done < <(find hyprtk_editor/qml -name '*.qml')
else
    echo "qmllint not installed — skipped"
fi

echo "== shell syntax =="
bash -n install.sh
sh -n bin/hyprtk-edit

echo "== headless boot =="
timeout 40 python3 scripts/bootcheck.py

echo "== cli =="
test "$(PYTHONPATH=. python3 -m hyprtk_editor --version)" = "hyprtk-edit 0.1.3"

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
