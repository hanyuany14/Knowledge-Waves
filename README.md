# Stream-Assistant

專案資料夾與專案管理連結：https://drive.google.com/drive/folders/1FbrOP67h589Kwe6aG64Ev_NbQj6-e0VY


# poetry 小抄
1. 設定 poetry 的安裝虛擬環境在本專案
poetry config virtualenvs.in-project true

2. 設定 poetry 用 python3.11
poetry env use python3.11

3. 下載套件
poetry install

4. 下載額外的套件
pip install == poetry add
pip uninstall == poetry remove

5. 啟動 py
python xxx.py
-> 要改成
poetry run python xxx.py


6. 執行 api server
poetry run uvicorn src.backend.app:app --reload