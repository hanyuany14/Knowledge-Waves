from pydantic import BaseModel
from typing import List, Tuple, Dict


class SummarizeResponse(BaseModel):
    interested_tags: List[str]
    summarized_content: str
    article_titles: Dict[str, List[Tuple[str, str]]]


class PrepareNewsResponse(BaseModel):
    status: str
    message: str
