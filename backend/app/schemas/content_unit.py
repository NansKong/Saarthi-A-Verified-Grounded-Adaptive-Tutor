from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ContentUnit(BaseModel):
    unit_id: str
    source_id: str
    source_type: str

    location: Dict[str, Any]

    chunk_index: Optional[int] = None

    text: str

    visual_description: Optional[str] = None

    topic: Optional[str] = None
    subtopic: Optional[str] = None

    concept_ids: List[str] = []