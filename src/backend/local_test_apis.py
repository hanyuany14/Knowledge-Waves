import requests

BASE_URL = "http://127.0.0.1:8000"


def test_summarize(query: str, sources: list[str] = ["medium", "github"]):
    """
    測試 /summarize API
    """
    payload = {
        "query": query,
        "sources": sources,
    }
    response = requests.post(f"{BASE_URL}/summarize", json=payload)
    if response.status_code == 200:
        print("Summarize API:")
        print(response.json())
    else:
        print(f"Summarize API failed with status code: {response.status_code}")
        print(response.text)


def test_prepare_news():
    """
    測試 /prepare-news API
    """
    response = requests.post(f"{BASE_URL}/prepare-news")
    if response.status_code == 200:
        print("Prepare News API:")
        print(response.json())
    else:
        print(f"Prepare News API failed with status code: {response.status_code}")
        print(response.text)


if __name__ == "__main__":

    # print("\nTesting Prepare News API...")
    # test_prepare_news()

    print("\nTesting Summarize API...")
    query = "給我自然語言模型和資料科學相關文章"
    test_summarize(query, ["medium", "github"])
