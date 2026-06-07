import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.config import settings

S3_LAYERS = ("raw", "processed", "dead-letter")


class LocalS3Storage:
    def __init__(self, base_path: str | None = None) -> None:
        self.base_path = Path(base_path or settings.LOCAL_S3_BASE_PATH).resolve()
        for layer in S3_LAYERS:
            (self.base_path / layer).mkdir(parents=True, exist_ok=True)

    def write_json(self, layer: str, mission_id: str, payload: list[dict]) -> str:
        if layer not in S3_LAYERS:
            raise ValueError(f"Unsupported layer: {layer}")
        date_partition = datetime.now(UTC).strftime("%Y-%m-%d")
        file_name = f"{uuid4()}.json"
        file_path = self.base_path / layer / mission_id / date_partition / file_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")
        return str(file_path)

    def read_json(self, path: str) -> list[dict]:
        return json.loads(Path(path).read_text(encoding="utf-8"))
