import requests
import json

import feedparser
from datetime import datetime, timedelta
from typing import Set

import configs as configs


class Crawl:
    def __init__(self) -> None:
        self.yesterday = datetime.now().replace(day=datetime.now().day - 1)

        self.__medium_existed_article = set()
        self.__medium_existed_tags = set()

    def crawl(
        self,
    ) -> tuple[
        dict[str, list[dict[str, str | list[str] | datetime]]],
        dict[str, set[str]],
    ]:
        """
        爬蟲：爬取三個網站的文章內容

        Returns:
            crawl_results (dict[str, list[dict[str, str | list[str] | datetime]]): 爬取的文章內容 e.g. {"github": [{"title": "title", "content": "content", "tags": ["tag1", "tag2"], "url": "url", "publish_date": datetime}]}
            today_tags (dict[str, set[str]]): 今日爬取的 tags e.g. {"github": {"tag1", "tag2"}}
        """
        # github_result, github_tags = self.__crawl_from_github()
        medium_result, medium_tags = self.__crawl_from_medium()
        # csdn_result, csdn_tags = self.__crawl_from_csdn()

        github_result, github_tags = [], []
        csdn_result, csdn_tags = [], []

        crawl_results = {
            "github": github_result,
            "medium": medium_result,
            "csdn": csdn_result,
        }

        today_tags = {
            "github": github_tags,
            "medium": medium_tags,
            "csdn": csdn_tags,
        }
        return crawl_results, today_tags

    def __crawl_from_github(self) -> tuple[list[dict[str, str | list[str] | datetime]], set[str]]:

        result_list = [
            {
                "title": "title",
                "content": "content",
                "tags": ["tag1", "tag2"],
                "url": "url",
                "publish_date": datetime,
            }
        ]

        tags = self.__get_tags(result_list)

        return result_list, tags

    def __crawl_from_medium(self) -> tuple[list[dict[str, str | list[str] | datetime]], set[str]]:
        """Crwal articles from medium.com

        Returns:
            tuple[list[dict[str, str | list[str] | datetime]], set[str]]: A tuple containing the list of articles and the set of tags.
                - gloabl_medium_result(list[dict[str, str | list[str] | datetime]]): A list of dictionaries, each representing an article with keys like 'title', 'content', 'tags', 'url', and 'publish_date'.

                - tags(set[str]): A set of tags.
        """

        # categories = ["technology", "self-improvement", "software-development", "deep-learning", "python"]

        print(f"\nNow crawling from medium.com\n")

        max_times = 3
        gloabl_medium_result = []
        categories = ["technology"]
        self.__medium_existed_tags = self.__medium_existed_tags.union(categories)
        print(f"existed_tags: {self.__medium_existed_tags}")

        for i in range(max_times):
            print(f"\n----------------Processing round: {i+1}----------------\n")

            categories = categories[:1]  # for testing

            print(f"    The number of categories: {len(categories)}")

            parse_medium_result, parsed_tags = self.__crawl_medium_24hr_feed_by_categories(categories)

            if parse_medium_result == []:  # 第一個終止條件 - 這一輪查詢沒有出現任何新的文章
                print("parse_medium_result is empty, 結束爬蟲")
                break
            else:
                gloabl_medium_result.extend(parse_medium_result)

            # print(f"    existed_tags: {self.__medium_existed_tags}")
            # print(f"    parsed_tags: {parsed_tags}")
            if set(parsed_tags).issubset(
                self.__medium_existed_tags
            ):  # 第二個終止條件 - 本輪新的 tags 都已經存在於 existed_tags 中
                print("所有 tags 都已经存在于 existed_tags 中, 結束爬蟲")
                break
            else:
                categories = [tag for tag in parsed_tags if tag not in self.__medium_existed_tags]
                self.__medium_existed_tags = self.__medium_existed_tags.union(categories)
                # print(f"    新的 tags: {categories}")

        print(f"    爬取的文章數量: {len(gloabl_medium_result)}")
        tags = self.__get_tags(gloabl_medium_result)

        return gloabl_medium_result, tags

    def __crawl_from_csdn(self) -> tuple[list[dict[str, str | list[str] | datetime]], set[str]]:
        """ """
        result_list = [
            {
                "title": "title",
                "content": "content",
                "tags": ["tag1", "tag2"],
                "url": "url",
                "publish_date": datetime,
            }
        ]

        tags = self.__get_tags(result_list)

        return result_list, tags

    def __get_tags(self, parse_results_list: list[dict]) -> set[str]:
        # print(f"\n\n\n\nparse_result: {parse_results_list[0]}")
        # print(f"\n\n\n\nparse_result[0]['tags']: {parse_results_list[0]['tags']}")

        tags = [tag for parse_result in parse_results_list for tag in parse_result["tags"]]
        return set(tags)

    def __crawl_medium_url(self, url: str) -> dict:

        url = f"{url}?format=json"

        response = requests.get(url)
        if response.status_code == 200:
            if response.text.startswith("])}"):
                json_data = response.text[16:]
                data = json.loads(json_data)
                paragraphs = data["payload"]["value"]["content"]["bodyModel"]["paragraphs"]

                return {
                    # "sub_titles": data["payload"]["value"]["content"].get("subtitle", "No Subtitle"),
                    "content": "".join(paragraph["text"] for paragraph in paragraphs),
                }

        else:
            raise Exception(f"Failed to retrieve data: {response.status_code}")

        return {"content": ""}

    def __crawl_medium_24hr_feed_by_categories(self, categories: list[str]):

        parsed_tags: Set[str] = set()
        parse_medium_result = []

        for category in categories:
            print(f"Processing category: {category}")
            feed = feedparser.parse(f"{configs.MEDIUM_TAG_BASE_URL+category}")

            for entry in feed.entries:
                published_time = datetime(*entry.published_parsed[:6])

                if published_time > self.yesterday:

                    if entry.id in self.__medium_existed_article:
                        print(f"Article `{entry.title}` already existed")
                        continue

                    print(f"Processing article: {entry.title}")
                    try:
                        parse_result = self.__crawl_medium_url(entry.id)
                        tags = [tag.term for tag in entry.tags]
                        parse_result.update(
                            {
                                "title": entry.title,
                                "url": entry.id,
                                "tags": tags,
                                "publish_date": published_time,
                            }
                        )
                        parse_medium_result.append(parse_result)
                        self.__medium_existed_article.add(entry.id)
                        parsed_tags = parsed_tags.union(tags)

                    except Exception as e:
                        print(f"Failed to parse article: {e}")
                        parse_result = "failed"

            print(f"category: {category}, count: {len(parse_medium_result)}")

        return parse_medium_result, parsed_tags
