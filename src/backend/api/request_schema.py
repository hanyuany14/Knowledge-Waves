from pydantic import BaseModel
from typing import List, Optional


class SummarizeRequest(BaseModel):
    query: str
    sources: Optional[List[str]] = ["github", "medium", "csdn"]
