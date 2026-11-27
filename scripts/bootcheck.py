#!/usr/bin/env python3
"""Dev-only: load the QML tree headlessly and fail on warnings or no window."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

# Keep the gate hermetic: the app writes a session, drafts and settings under the
# XDG dirs, and a boot check that takes longer than the 900 ms session debounce
# would otherwise leave its temp documents in the developer's own session.
_SANDBOX = tempfile.mkdtemp(prefix="hyprtk-boot-")
for _var in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME"):
    os.environ[_var] = os.path.join(_SANDBOX, _var.split("_")[1].lower())

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import Q_ARG, QMetaObject, QPoint, QTimer, Qt, qInstallMessageHandler  # noqa: E402
from PySide6.QtQml import QQmlEngine, QQmlExpression  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402

from hyprtk_editor.app import create  # noqa: E402

problems: list[str] = []


def handler(_mode, _ctx, message) -> None:
    if message.strip():
        problems.append(message)
        print(message)


def main() -> int:
    qInstallMessageHandler(handler)
    app, engine, bridge = create([sys.argv[0]])
    if not engine.rootObjects():
        print("bootcheck: no root object")
        return 1
    root = engine.rootObjects()[0]

    def finish() -> None:
        for problem in problems:
            print(f"bootcheck: FAILED: {problem}")
        print(f"bootcheck: root objects={len(engine.rootObjects())}, warnings={len(problems)}")
        app.exit(1 if problems else 0)

    def call(name: str, *args) -> None:
        """Invoke a QML function and fail the gate if it is missing.

        A renamed or deleted QML function used to make this check pass
        vacuously, because invokeMethod's return value was ignored.
        """
        if not QMetaObject.invokeMethod(root, name, *args):
            problems.append(f"bootcheck: {name}() is not invokable")

    def qml(expression: str):
        """Evaluate an expression in the window's own context.

        Ids such as ``welcome`` are not properties of the root object, and the
        window itself is a QQuickWindow, so a plain property read cannot see
        them. An expression runs in the component's scope, exactly like QML.
        """
        expression = QQmlExpression(QQmlEngine.contextForObject(root), root, expression)
        value = expression.evaluate()
        if isinstance(value, tuple):  # PySide6 hands back (value, isUndefined)
            value = value[0]
        if expression.hasError():
            problems.append(f"bootcheck: expression failed: {expression.error().toString()}")
            return None
        return value.toVariant() if hasattr(value, "toVariant") else value

    def open_first() -> None:
        # An editor pane only exists once a document is open.
        path = Path(tempfile.gettempdir()) / "hyprtk-bootcheck.txt"
        path.write_text("one\ntwo\nthree\n", encoding="utf-8")
        call("openPath", Q_ARG("QVariant", str(path)))
        QTimer.singleShot(300, opened_document)

    def opened_document() -> None:
        # The document must actually be on screen. A tab strip entry and a
        # status-bar count are not enough: the welcome screen sits above the
        # panes, so a half-finished tab activation shows a "file opened" tab
        # over an empty editor.
        view = qml("welcome.visible")
        if view is not False:
            problems.append(f"bootcheck: welcome visible with a document open ({view!r})")
        text = qml("win.activePane() ? win.activePane().area.text : null")
        if text != "one\ntwo\nthree\n":
            problems.append(f"bootcheck: opened pane text is {text!r}")
        # Settings written from QML must reach the bridge *and* the QML-side
        # config: JS objects and arrays cross as QJSValue, which once made every
        # one of these a no-op.
        before = bridge.config.get("line_numbers")
        qml("Bridge.updateSettings({ line_numbers: !Bridge.config.line_numbers })")
        expected = not before
        if bridge.config.get("line_numbers") != expected:
            problems.append("bootcheck: updateSettings() from QML did not apply")
        if qml("win.cfg.line_numbers") != expected:
            problems.append("bootcheck: settings change did not reach the QML config")
        qml("Bridge.updateSettings({ line_numbers: !!Bridge.config.line_numbers })")
        QTimer.singleShot(150, new_document)

    def new_document() -> None:
        # Two tabs, so the strip, the drag helpers and per-tab find all run.
        call("newDocument")
        QTimer.singleShot(150, open_find)

    def open_find() -> None:
        call("openFind", Q_ARG("QVariant", False))
        QTimer.singleShot(200, cycle)

    def cycle() -> None:
        # Switching tabs must load the other document's find record, not this
        # one's query.
        call("cycleTab", Q_ARG("QVariant", 1))
        QTimer.singleShot(150, reorder)

    def reorder() -> None:
        active = str(root.property("activeId") or "")
        if active:
            call("moveDocument", Q_ARG("QVariant", active), Q_ARG("QVariant", 0))
        QTimer.singleShot(150, quick_open)

    def quick_open() -> None:
        call("openQuickOpen")
        QTimer.singleShot(250, quick_close)

    def quick_close() -> None:
        call("toggleQuickOpen")
        QTimer.singleShot(150, close_find)

    def close_find() -> None:
        call("closeFind")
        QTimer.singleShot(150, export_pdf)

    def export_pdf() -> None:
        # The PDF path is the same one the Export dialog uses, minus the dialog.
        active = str(root.property("activeId") or "")
        target = os.path.join(_SANDBOX, "bootcheck.pdf")
        result = bridge.writePdf(active, target)
        if not result.get("ok") or not os.path.exists(target):
            problems.append(f"bootcheck: writePdf failed: {result}")
        git = bridge.gitStatus(os.path.abspath(__file__))
        if not isinstance(git, dict) or "lines" not in git:
            problems.append(f"bootcheck: gitStatus returned {git!r}")
        QTimer.singleShot(150, right_click)

    def right_click() -> None:
        QTest.mouseClick(root, Qt.RightButton, Qt.NoModifier, QPoint(160, 70))
        QTimer.singleShot(400, finish)

    QTimer.singleShot(400, open_first)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
