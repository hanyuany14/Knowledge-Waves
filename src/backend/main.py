"""
main 包含：
1. 使用者層：接收使用者 query 今日有興趣主題
- 使用者輸入：今日有興趣主題的自然語言
- 相似性搜尋：挑出使用者輸入相似的 tags
- 取得 tags 的文章標題：從 BigQuery 取得 tags 包含的所有文章標題
- 標題取得文章：從 GCS 取得該文章的內容
- LLM 總結：使用 LLM 將文章內容總結
- 回傳結果：將總結回傳給使用者

2. 資料層：爬蟲、embedding、上傳資料
每天早上 7:00 執行
- 爬蟲：爬取三個網站的文章內容
    - 包含：文章標題、文章內容、tags、文章網址、文章時間
- 上傳到 BigQuery：將爬取的資料上傳到 BigQuery
    - 包含：文章標題、tags、文章網址、文章時間、文章來源
- 上傳到 GCS：將爬取的資料上傳到 GCS
    - 包含：文章內容、文章標題
- Embedding 上傳到 vectorestore：將 tags 進行 embedding 並存在 google vectorestore
    - 包含：tags、embedding
"""


class Main:
    def __init__(self):
        pass

    def do_summarize(self, query: str):
        """
        使用者層：接收使用者 query 今日有興趣主題
        """
        # interested_tags = []
        # summaarized_content = ""
        # article_titles = [("title", "url")]

        interested_tags, summaarized_content, article_titles = Summarization.do_summary(query)

        return interested_tags, summaarized_content, article_titles

    def prepare_news(self):
        """
        資料層：爬蟲、embedding、上傳資料
        """
        return True

if __name__ == "__main__":
    main = Main()
    main.do_summarize("今日有興趣主題")