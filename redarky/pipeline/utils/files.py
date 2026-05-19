import json
from pathlib import Path


def load_json(path: str):
    return json.loads(
        Path(path).read_text(encoding="utf-8")
    )


def save_json(path: str, data):
    Path(path).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )