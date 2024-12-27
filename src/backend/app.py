from fastapi import FastAPI, HTTPException
from src.backend.api.response_schema import SummarizeResponse
from src.backend.api.request_schema import SummarizeRequest
from src.backend.main import Main

app = FastAPI()
main_service = Main()


@app.get("/")
def root():
    """
    API 首頁，提供歡迎訊息。
    """
    return {
        "message": "歡迎來到 Stream-Assistant API！",
        "routes": [
            {"path": "/summarize", "description": "使用者輸入主題，獲取文章總結"},
            {"path": "/prepare-news", "description": "每日執行爬蟲、上傳資料、Embedding"},
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
