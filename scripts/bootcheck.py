#!/usr/bin/env python3
"""Dev-only: load the QML tree headlessly and fail on warnings or no window."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QTimer, qInstallMessageHandler  # noqa: E402

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

    def finish() -> None:
        print(f"bootcheck: root objects={len(engine.rootObjects())}, warnings={len(problems)}")
        app.exit(1 if problems else 0)

    QTimer.singleShot(600, finish)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
