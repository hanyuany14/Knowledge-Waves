import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.append(project_root)

import src.backend.utils as utils
import src.backend.configs as configs

article_table_ref = f"{configs.PROJECT_ID}.{configs.DATASET_ID}.{configs.ARTICLE_INFO_TABLE_ID}"


# 獲取時間範圍
yesterday, today = utils.get_time_range()

# 查詢
query = f"""
SELECT DISTINCT tags
FROM `{article_table_ref}`
WHERE publish_date BETWEEN TIMESTAMP('{yesterday}') AND TIMESTAMP('{today}')
"""

# SELECT DISTINCT tag
# FROM (
#     SELECT
#         UNNEST(tags) AS tag
#     FROM
#         `{article_table_ref}`
#     WHERE
#         publish_date BETWEEN TIMESTAMP('{yesterday}') AND TIMESTAMP('{today}')
# )
# ORDER BY tag

# 執行查詢
query_job = utils.BQ_CLIENT.query(query)

# 獲取結果
distinct_tags = [tag for row in query_job.result() for tag in row.tags]

# 打印合并后的列表
print(distinct_tags)

print(f"set(distinct_tags): \n\n{set(distinct_tags)}")
