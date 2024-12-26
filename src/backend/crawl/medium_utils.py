import requests
import json
import feedparser
from datetime import datetime, timedelta
from typing import Set, Tuple, List, Dict

from base import CrawlBase
from ..configs import configs


class MediumCrawl(CrawlBase):
    def __init__(self) -> None:
        super().__init__()
        self.__medium_existed_article = set()
        self.__medium_existed_tags = set()

    def crawl(self) -> Tuple[List[Dict[str, object]], Set[str]]:
        """爬取medium.com的文章

        Returns:
            tuple: (文章列表, 標籤集合)
        """

        print(f"\n現在正在從medium.com爬取\n")

        max_times = 3
        gloabl_medium_result = []
        categories = ["technology"]
        self.__medium_existed_tags = self.__medium_existed_tags.union(categories)
        print(f"已存在的標籤：{self.__medium_existed_tags}")

        for i in range(max_times):
            print(f"\n----------------處理輪次：{i+1}----------------\n")

            categories = categories[:1]  # 用於測試

            print(f"    類別數量：{len(categories)}")

            parse_medium_result, parsed_tags = self.__crawl_medium_24hr_feed_by_categories(categories)

            if parse_medium_result == []:  # 第一個終止條件 - 這一輪查詢沒有出現任何新的文章
                print("parse_medium_result 為空，結束爬蟲")
                break
            else:
                gloabl_medium_result.extend(parse_medium_result)

            if set(parsed_tags).issubset(
                self.__medium_existed_tags
            ):  # 第二個終止條件 - 本輪新的 tags 都已經存在於 existed_tags 中
                print("所有標籤都已經存在於 existed_tags 中，結束爬蟲")
                break
            else:
                categories = [tag for tag in parsed_tags if tag not in self.__medium_existed_tags]
                self.__medium_existed_tags = self.__medium_existed_tags.union(categories)

        print(f"    爬取的文章數量：{len(gloabl_medium_result)}")
        tags = self.__get_tags(gloabl_medium_result)

        return gloabl_medium_result, tags

    def __crawl_medium_url(self, url: str) -> dict:
        """
        獲取Medium文章內容

        Args:
            url (str): Medium文章URL

        Returns:
            Dict[str, str]: 文章內容
        """
        url = f"{url}?format=json"

        response = requests.get(url)
        if response.status_code == 200:
            if response.text.startswith("])}"):
                json_data = response.text[16:]
                data = json.loads(json_data)

                paragraphs = data["payload"]["value"]["content"]["bodyModel"]["paragraphs"]
                clap_count = data["payload"]["value"]["virtuals"]["totalClapCount"]
                language = data["payload"]["value"]["detectedLanguage"]

                return {
                    "likes": clap_count,
                    "language": language,
                    "content": "".join(paragraph["text"] for paragraph in paragraphs),
                }

        else:
            raise Exception(f"無法獲取資料：{response.status_code}")

        return {"content": ""}

    def __crawl_medium_24hr_feed_by_categories(self, categories: List[str]) -> Tuple[List[Dict[str, object]], Set[str]]:
        """
        爬取Medium特定類別的24小時內發布的文章

        Args:
            categories (List[str]): 類別列表

        Returns:
            Tuple: (文章列表, 標籤集合)
        """
        parsed_tags: Set[str] = set()
        parse_medium_result = []

        for category in categories:
            print(f"處理類別：{category}")
            feed = feedparser.parse(f"{configs.MEDIUM_TAG_BASE_URL}{category}")

            for entry in feed.entries:
                # 解析發布時間
                published_time = datetime(*entry.published_parsed[:6])
                publish_date = published_time.isoformat()

                if published_time > self.yesterday:

                    if entry.id in self.__medium_existed_article:
                        print(f"文章 `{entry.title}` 已存在")
                        continue

                    print(f"處理文章：{entry.title}")
                    try:
                        parse_result = self.__crawl_medium_url(entry.id)
                        tags = [tag.term for tag in entry.tags] if "tags" in entry else []

                        parse_result["title"] = entry.title
                        parse_result["url"] = entry.id
                        parse_result["tags"] = tags
                        parse_result["publish_date"] = publish_date

                        parse_medium_result.append(parse_result)
                        self.__medium_existed_article.add(entry.id)
                        parsed_tags = parsed_tags.union(tags)

                    except Exception as e:
                        print(f"解析文章失敗：{e}")
                        # parse_result = "failed"  # 這裡不需要賦值，因為不會被使用

            print(f"類別：{category}, 計數：{len(parse_medium_result)}")

        return parse_medium_result, parsed_tags


if __name__ == "__main__":
    crawl = MediumCrawl()
    crawl_results, today_tags = crawl.crawl()
    print(f"\n\ncrawl_results:\n\n{crawl_results}")
    print(f"\n\ntoday_tags:\n\n{today_tags}")
