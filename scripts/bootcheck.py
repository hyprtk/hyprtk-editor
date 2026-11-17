#!/usr/bin/env python3
"""Dev-only: load the QML tree headlessly and fail on warnings or no window."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import Q_ARG, QMetaObject, QPoint, QTimer, Qt, qInstallMessageHandler  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402

from hyprtk_editor.app import create  # noqa: E402

problems: list[str] = []


def handler(_mode, _ctx, message) -> None:
    if message.strip():
        problems.append(message)
        print(message)


def main() -> int:
    qInstallMessageHandler(handler)
    app, engine, _bridge = create([sys.argv[0]])
    if not engine.rootObjects():
        print("bootcheck: no root object")
        return 1
    root = engine.rootObjects()[0]

    def finish() -> None:
        print(f"bootcheck: root objects={len(engine.rootObjects())}, warnings={len(problems)}")
        app.exit(1 if problems else 0)

    def open_and_right_click() -> None:
        # An editor pane (and its context menu) only exists once a document is
        # open, so the boot check opens one and right-clicks it.
        path = Path(tempfile.gettempdir()) / "hyprtk-bootcheck.txt"
        path.write_text("one\ntwo\nthree\n", encoding="utf-8")
        QMetaObject.invokeMethod(root, "openPath", Q_ARG("QVariant", str(path)))
        QTimer.singleShot(500, right_click)

    def right_click() -> None:
        QTest.mouseClick(root, Qt.RightButton, Qt.NoModifier, QPoint(160, 70))
        QTimer.singleShot(500, finish)

    QTimer.singleShot(400, open_and_right_click)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
