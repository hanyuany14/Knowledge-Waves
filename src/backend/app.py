from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.backend.api.response_schema import SummarizeResponse, ShortcutResponseWithLikes, ShortcutResponse
from src.backend.api.request_schema import SummarizeRequest
from src.backend.main import Main
from src.backend.shortcut import ShortcutsUtil

app = FastAPI()
main_service = Main()
shortcuts_util = ShortcutsUtil()


# 啟用 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """
    API 首頁，提供歡迎訊息。
    """
    return {
        "message": "朱茂茂要丟下咱們脫單了，大家一同祝賀他",
        "routes": [
            {"path": "/docs", "description": "進入了解 api 文件"},
            {"path": "/summarize", "description": "使用者輸入主題，獲取文章總結"},
        ],
    }


@app.post("/summarize", response_model=SummarizeResponse)
def do_summarize(request: SummarizeRequest):
    """
    Summarize articles based on user query and optional sources.

    使用者層：接收使用者 query 今日有興趣主題
    - 使用者輸入：今日有興趣主題的自然語言
    - 相似性搜尋：挑出使用者輸入相似的 tags
    - 取得 tags 的文章標題：從 BigQuery 取得 tags 包含的所有文章標題
    - 標題取得文章：從 GCS 取得該文章的內容
    - LLM 總結：使用 LLM 將文章內容總結
    - 回傳結果：將總結回傳給使用者
    """
    try:
        interested_tags, summarized_content, article_titles = main_service.do_summarize(
            query=request.query, sources=request.sources
        )
        return SummarizeResponse(
            interested_tags=interested_tags, summarized_content=summarized_content, article_titles=article_titles
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/shortcut/question1", response_model=ShortcutResponseWithLikes)
def get_question_1():
    """
    提問 1：今天最受歡迎的文章前五篇文章分別為何？
    """
    try:
        articles, summarized_content = shortcuts_util.question_1()
        formatted_articles = [ShortcutResponseWithLikes.ArticleWithLikes(**article) for article in articles]
        return ShortcutResponseWithLikes(articles=formatted_articles, summarized_content=summarized_content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/shortcut/question2", response_model=ShortcutResponseWithLikes)
def get_question_2():
    """
    提問 2：今天內關於「AI」的文章中，點讚數最高的三篇文章標題是什麼？
    """
    try:
        articles, summarized_content = shortcuts_util.question_2()
        formatted_articles = [ShortcutResponseWithLikes.ArticleWithLikes(**article) for article in articles]
        return ShortcutResponseWithLikes(articles=formatted_articles, summarized_content=summarized_content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/shortcut/question3", response_model=ShortcutResponse)
def get_question_3():
    """
    提問 3：對所有來源今日的文章關於 LLM RAG 的內容進行介紹
    """
    try:
        articles, summarized_content = shortcuts_util.question_3()
        formatted_articles = [ShortcutResponse.Article(**article) for article in articles]
        return ShortcutResponse(articles=formatted_articles, summarized_content=summarized_content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/shortcut/question4", response_model=ShortcutResponse)
def get_question_4():
    """
    提問 4：目前資料中來自「medium」的五篇最熱門文章是什麼？
    """
    try:
        articles, summarized_content = shortcuts_util.question_4()
        formatted_articles = [ShortcutResponse.Article(**article) for article in articles]
        return ShortcutResponse(articles=formatted_articles, summarized_content=summarized_content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
