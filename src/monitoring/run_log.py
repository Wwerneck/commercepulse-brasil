from dataclasses import asdict, dataclass
from datetime import datetime

import pandas as pd


@dataclass(frozen=True)
class PipelineRunLog:
    run_id: str
    pipeline_name: str
    started_at: datetime
    finished_at: datetime | None
    duration_seconds: float | None
    records_read: int
    records_written: int
    records_rejected: int
    source: str
    destination: str
    status: str
    error_message: str | None = None

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([asdict(self)])
