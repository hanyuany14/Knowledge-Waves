# Stream-Assistant

專案資料夾與專案管理連結：https://drive.google.com/drive/folders/1FbrOP67h589Kwe6aG64Ev_NbQj6-e0VY


# poetry 小抄
1. 設定 poetry 的安裝虛擬環境在本專案
poetry config virtualenvs.in-project true

2. 下載套件
poetry install

3. 下載額外的套件
pip install == poetry add
pip uninstall == poetry remove

4. 啟動 py
python xxx.py
-> 要改成
poetry run python xxx.py