from datetime import datetime
from typing import List, Optional

from opennem.schema.core import BaseConfig


class ControllerReturn(BaseConfig):
    last_modified: Optional[datetime]
    total_records: int = 0
    inserted_records: int = 0
    processed_records: int = 0
    errors: int = 0
    error_detail: List[Optional[str]] = []
