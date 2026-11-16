# huili

## 資料檔（供其他網頁使用）

每次執行會隨網頁一起發布 `https://markwu27928.github.io/huili/data.json`，財報評分網頁（twse-fundamentals）會讀取它顯示分點進出。

- `version`：資料格式版本（目前 1）；`unit`：金額單位（仟元）；`top_n`：每天買超、賣超各收錄前幾名
- `names`：{代號: 名稱}
- `days`：由舊到新，每天 `{"d": "YYYYMMDD", "r": [[代號, 買進金額, 賣出金額, 買進張數, 賣出張數], ...]}`，張數可能為 null
- 只含當天上榜的股票，沒上榜不代表沒有交易

修改格式時請一併提高 `version`，以免讀取端誤解欄位。

