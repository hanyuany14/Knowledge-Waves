from pydantic import BaseModel
from typing import List, Tuple, Dict


class SummarizeResponse(BaseModel):
    interested_tags: List[str]
    summarized_content: str
    article_titles: Dict[str, List[Tuple[str, str, int, str | None]]]


class ShortcutResponseWithLikes(BaseModel):
    class ArticleWithLikes(BaseModel):
        title: str
        source: str
        url: str
        likes: str

    articles: List[ArticleWithLikes]
    summarized_content: str


# class ShortcutResponse(BaseModel):
#     class Article(BaseModel):
#         title: str
#         url: str
#         source: str
#         likes: str

#     articles: List[Article]
#     summarized_content: str


class TagsResponse(BaseModel):
    tag: List[str]
