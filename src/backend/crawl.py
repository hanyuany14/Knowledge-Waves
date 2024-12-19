import requests
import json
import base64
import feedparser
from datetime import datetime, timedelta
from typing import Set, Tuple, List, Dict
from bs4 import BeautifulSoup
import markdown  # 引入 markdown 庫
import re  # 用於處理 Markdown 語法

import configs as configs  # 確保configs.py中包含必要的配置，如GITHUB_PERSONAL_ACCESS_TOKEN和MEDIUM_TAG_BASE_URL


class Crawl:
    def __init__(self) -> None:
        # 使用timedelta確保日期處理正確
        self.yesterday = datetime.utcnow() - timedelta(days=1)

        # 跟踪已處理的Medium文章和標籤
        self.__medium_existed_article = set()
        self.__medium_existed_tags = set()

        # 跟踪已處理的GitHub倉庫
        self.__github_existed_repo = set()

    def crawl(
        self,
    ) -> Tuple[
        Dict[str, List[Dict[str, object]]],
        Dict[str, Set[str]],
    ]:
        """
        爬蟲：爬取三個網站的文章內容

        Returns:
            crawl_results (dict): 爬取的文章內容
            today_tags (dict): 今日爬取的標籤
        """
        # 爬取GitHub
        github_result, github_tags = self.__crawl_from_github()

        # 爬取Medium (已註解)
        # medium_result, medium_tags = self.__crawl_from_medium()

        # 爬取CSDN (已註解)
        # csdn_result, csdn_tags = self.__crawl_from_csdn()

        # 若需要測試其他平台，請解除以下註解並相應調整
        medium_result, medium_tags = [], set()
        csdn_result, csdn_tags = [], set()

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

    def __crawl_from_github(self) -> Tuple[List[Dict[str, object]], Set[str]]:
        """
        爬取GitHub倉庫資訊

        Returns:
            Tuple: (倉庫資訊列表, 標籤集合)
        """
        print("\n現在正在從GitHub爬取\n")
        result_list = []

        try:
            # 使用GitHub API爬取過去24小時內創建的倉庫
            repos = self.fetch_github_repos()
            print(f"從GitHub API抓取了 {len(repos)} 個倉庫。")
        except Exception as e:
            print(f"抓取GitHub倉庫失敗：{e}")
            repos = []

        # 過濾已存在的倉庫
        for repo in repos:
            if repo["url"] in self.__github_existed_repo:
                print(f"倉庫 `{repo['title']}` 已存在。")
                continue
            result_list.append(repo)
            self.__github_existed_repo.add(repo["url"])

        # 使用BeautifulSoup爬取GitHub Trending頁面
        try:
            trending_repos = self.fetch_github_trending()
            print(f"從GitHub Trending頁面抓取了 {len(trending_repos)} 個熱門倉庫。")
        except Exception as e:
            print(f"抓取GitHub Trending倉庫失敗：{e}")
            trending_repos = []

        for repo in trending_repos:
            if repo["url"] in self.__github_existed_repo:
                print(f"熱門倉庫 `{repo['title']}` 已存在。")
                continue
            result_list.append(repo)
            self.__github_existed_repo.add(repo["url"])

        # 提取標籤
        tags = self.__get_tags(result_list)

        return result_list, tags

    def fetch_github_repos(self) -> List[Dict[str, object]]:
        """
        使用GitHub API抓取過去24小時內創建的倉庫

        Returns:
            List[Dict]: 包含倉庫資訊的字典列表
        """
        base_url = "https://api.github.com/search/repositories"
        # 定義過去24小時的時間範圍
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        time_range = yesterday.strftime("%Y-%m-%dT%H:%M:%SZ")

        # 查詢參數：過去24小時內創建的倉庫，按星標降序排序
        query_params = {
            "q": f"created:>{time_range}",
            "sort": "stars",
            "order": "desc",
            "per_page": 100,  # GitHub API每頁最大100
        }

        headers = {
            "Authorization": f"token {configs.GITHUB_PERSONAL_ACCESS_TOKEN}",  # 從configs導入
            "Accept": "application/vnd.github.v3+json",
        }

        response = requests.get(base_url, headers=headers, params=query_params)
        if response.status_code != 200:
            raise Exception(f"抓取GitHub倉庫失敗：{response.status_code}, {response.json().get('message', '')}")

        repos = response.json().get("items", [])
        result = []
        for repo in repos:
            # 提取倉庫詳情
            title = repo.get("full_name", "無標題")
            repo_url = repo.get("html_url", "無URL")
            description = repo.get("description", "無描述")
            language = repo.get("language", "無語言指定")
            stars = repo.get("stargazers_count", 0)
            forks = repo.get("forks_count", 0)
            created_at_str = repo.get("created_at", "無創建日期")
            try:
                created_at = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ")
                publish_date = created_at.isoformat()  # 轉換為字符串
            except ValueError:
                publish_date = self.yesterday.isoformat()  # 如果日期格式不正確，設置為昨天並轉換為字符串

            # 獲取README內容
            readme_content = self.fetch_readme(title, headers)

            # 獲取倉庫主題（topics）
            topics = self.fetch_topics(title, headers)

            repo_data = {
                "title": title,
                "content": description,
                "tags": topics,  # 使用topics作為tags
                "url": repo_url,
                "publish_date": publish_date,  # 轉換為字符串
                "readme": readme_content,  # 可選：添加README內容
            }

            result.append(repo_data)

        return result

    def fetch_readme(self, repo_full_name: str, headers: Dict[str, str]) -> str:
        """
        獲取倉庫的README內容

        Args:
            repo_full_name (str): 倉庫全名，例如 "owner/repo"
            headers (Dict[str, str]): HTTP請求頭

        Returns:
            str: README內容（前500字符）
        """
        readme_url = f"https://api.github.com/repos/{repo_full_name}/readme"
        response = requests.get(readme_url, headers=headers)
        if response.status_code == 200:
            readme_data = response.json()
            try:
                readme_content = base64.b64decode(readme_data.get("content", "")).decode("utf-8", errors="ignore")

                if not readme_content.strip():
                    print(f"Readme for {repo_full_name} is empty.")
                    return "README內容為空。"

                # 判斷是否為Markdown格式（簡單判斷是否包含Markdown語法）
                if re.search(r"[#*_\-`~]", readme_content):
                    # 將 Markdown 轉換為 HTML
                    readme_html = markdown.markdown(readme_content)
                    # 使用 BeautifulSoup 解析 HTML
                    readme_text = BeautifulSoup(readme_html, "html.parser").get_text()
                else:
                    # 直接解析 HTML
                    readme_text = BeautifulSoup(readme_content, "html.parser").get_text()

                return readme_text[:500] + "..." if len(readme_text) > 500 else readme_text
            except Exception as e:
                print(f"解碼 {repo_full_name} 的README失敗：{e}")
                return "無法解碼README內容。"
        else:
            return "README無法訪問或未找到。"

    def fetch_topics(self, repo_full_name: str, headers: Dict[str, str]) -> List[str]:
        """
        獲取倉庫的主題（topics）

        Args:
            repo_full_name (str): 倉庫全名，例如 "owner/repo"
            headers (Dict[str, str]): HTTP請求頭

        Returns:
            List[str]: 主題列表
        """
        topics_url = f"https://api.github.com/repos/{repo_full_name}/topics"
        topics_headers = {**headers, "Accept": "application/vnd.github.mercy-preview+json"}
        response = requests.get(topics_url, headers=topics_headers)
        if response.status_code == 200:
            topics_data = response.json()
            return topics_data.get("names", [])
        else:
            return ["無法訪問或未找到主題"]

    def fetch_github_trending(self) -> List[Dict[str, object]]:
        """
        使用BeautifulSoup爬取GitHub Trending頁面

        Returns:
            List[Dict]: 包含Trending倉庫資訊的字典列表
        """
        trending_url = "https://github.com/trending?since=daily"
        response = requests.get(trending_url)
        if response.status_code != 200:
            raise Exception(f"抓取GitHub Trending頁面失敗：{response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        repo_elements = soup.find_all("article", class_="Box-row")
        trending_repos = []

        headers = {
            "Authorization": f"token {configs.GITHUB_PERSONAL_ACCESS_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }

        for repo in repo_elements:
            # 提取倉庫名稱（格式：owner/repo）
            repo_name_tag = repo.find("h2", class_="h3")
            if not repo_name_tag:
                continue
            repo_name = repo_name_tag.text.strip().replace("\n", "").replace(" ", "")
            if "/" not in repo_name:
                continue
            owner, repo_title = repo_name.split("/")

            # 構建倉庫URL
            repo_url = f"https://github.com/{repo_name}"

            # 提取倉庫描述
            repo_description_tag = repo.find("p", class_="col-9 color-fg-muted my-1 pr-4")
            repo_description = repo_description_tag.text.strip() if repo_description_tag else "無描述提供"

            # 提取編程語言
            repo_language_tag = repo.find("span", itemprop="programmingLanguage")
            repo_language = repo_language_tag.text.strip() if repo_language_tag else "無語言指定"

            # 提取星標數量
            star_element = repo.find("a", class_="Link--muted d-inline-block mr-3")
            star_count = star_element.text.strip().replace(",", "") if star_element else "0"
            try:
                star_count = int(star_count)
            except ValueError:
                star_count = 0

            # 獲取倉庫主題（topics）
            topics = self.fetch_topics(repo_name, headers)

            # 獲取README內容
            readme_content = self.fetch_readme(repo_name, headers)

            # 處理 publish_date 為字符串
            publish_date = self.yesterday.isoformat()  # 由於Trending頁面沒有創建日期，設置為昨天並轉換為字符串

            repo_data = {
                "title": repo_name,
                "content": repo_description,
                "tags": topics,
                "url": repo_url,
                "publish_date": publish_date,  # 轉換為字符串
                "readme": readme_content,
            }

            trending_repos.append(repo_data)

        return trending_repos

    def __crawl_from_medium(self) -> Tuple[List[Dict[str, object]], Set[str]]:
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

    def __crawl_from_csdn(self) -> Tuple[List[Dict[str, object]], Set[str]]:
        """ """
        # 這裡可以根據CSDN的爬蟲實現進行填充
        # 目前返回一個空列表和空集合
        result_list = []
        tags = set()
        return result_list, tags

    def __get_tags(self, parse_results_list: List[Dict[str, object]]) -> Set[str]:
        """
        提取所有唯一標籤

        Args:
            parse_results_list (List[Dict]): 解析後的結果列表

        Returns:
            Set[str]: 唯一標籤集合
        """
        tags = [tag for parse_result in parse_results_list for tag in parse_result.get("tags", [])]
        return set(tags)

    def __crawl_medium_url(self, url: str) -> Dict[str, str]:
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

                return {
                    # "sub_titles": data["payload"]["value"]["content"].get("subtitle", "No Subtitle"),
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
                        parse_result.update(
                            {
                                "title": entry.title,
                                "url": entry.id,
                                "tags": tags,
                                "publish_date": publish_date,  # 轉換為字符串
                            }
                        )
                        parse_medium_result.append(parse_result)
                        self.__medium_existed_article.add(entry.id)
                        parsed_tags = parsed_tags.union(tags)

                    except Exception as e:
                        print(f"解析文章失敗：{e}")
                        # parse_result = "failed"  # 這裡不需要賦值，因為不會被使用

            print(f"類別：{category}, 計數：{len(parse_medium_result)}")

        return parse_medium_result, parsed_tags


if __name__ == "__main__":
    crawl = Crawl()
    crawl_results, today_tags = crawl.crawl()

    # 合併 crawl_results 和 today_tags 到一個字典中
    # 將 today_tags 中的 set 轉換為 list，以便 JSON 序列化
    combined_results = {"crawl_results": crawl_results, "today_tags": {k: list(v) for k, v in today_tags.items()}}

    # 保存到一個 JSON 文件
    with open("combined_crawl_results.json", "w", encoding="utf-8") as f:
        json.dump(combined_results, f, ensure_ascii=False, indent=2)
    print("Combined crawl results 已保存到 combined_crawl_results.json")
