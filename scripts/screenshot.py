#!/usr/bin/env python3
"""Dev-only: render the window offscreen to a PNG for visual checks."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QTimer  # noqa: E402

from hyprtk_editor.app import create  # noqa: E402

SAMPLE = """#!/usr/bin/env python3
\"\"\"A sample document used to check the editor's highlighting.\"\"\"

import json
from pathlib import Path

MAX_LINES = 4096


class Sample:
    \"\"\"Small class with a docstring.\"\"\"

    def __init__(self, name: str, value: int = 0) -> None:
        self.name = name
        self.value = value

    def double(self) -> int:
        # A comment with a number 42 and a string "hello"
        return self.value * 2


def main() -> int:
    sample = Sample("hyprtk", 21)
    data = {"name": sample.name, "value": sample.double()}
    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def main() -> int:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "shot.png"
    sample = Path("/tmp/opencode/hyprtk-sample.py")
    sample.parent.mkdir(parents=True, exist_ok=True)
    sample.write_text(SAMPLE, encoding="utf-8")

    app, engine, bridge = create([sys.argv[0], str(sample)])
    root = engine.rootObjects()[0]

    def grab() -> None:
        image = root.grabWindow()
        image.save(str(target))
        print(f"wrote {target} ({image.width()}x{image.height()})")
        app.quit()

    QTimer.singleShot(1400, grab)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
