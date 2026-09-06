import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BronzeTableManifest:
    name: str
    destination: str
    rows_read: int
    columns_read: int
    source_reference: str


@dataclass(frozen=True)
class BronzeIngestionManifest:
    batch_id: str
    source: str
    started_at: datetime
    finished_at: datetime
    tables: list[BronzeTableManifest]
    missing_references: list[str]
    manifest_path: str

    @property
    def files_written(self) -> int:
        return len(self.tables)

    @property
    def records_read(self) -> int:
        return sum(table.rows_read for table in self.tables)


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def write_manifest(manifest: BronzeIngestionManifest, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        **asdict(manifest),
        "files_written": manifest.files_written,
        "records_read": manifest.records_read,
    }
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default),
        encoding="utf-8",
    )
    return destination
