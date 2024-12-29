from pydantic import BaseModel
from typing import List, Optional


class TextSearchSummarizeRequest(BaseModel):
    query: str
    sources: Optional[List[str]] = ["github", "medium", "csdn"]


class SelectedTagsSummarizeRequest(BaseModel):
    selected_tags: list[str]
    sources: Optional[List[str]] = ["github", "medium", "csdn"]
