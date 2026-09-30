"""Source-agnostic ingestion contracts for AQUA-SENSE AI."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Protocol

@dataclass(frozen=True)
class RawRecord:
    """One provider-native record plus provenance metadata."""
    source_id: str
    retrieved_at: datetime
    payload: dict[str, Any]
    source_location: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            'source_id': self.source_id,
            'retrieved_at': self.retrieved_at.isoformat(),
            'source_location': self.source_location,
            'payload': self.payload,
        }

class SourceAdapter(Protocol):
    """Interface every future external-data adapter must implement."""
    source_id: str

    def fetch(self, **params: Any) -> Iterable[RawRecord]:
        ...

def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for ingestion provenance."""
    return datetime.now(timezone.utc)
