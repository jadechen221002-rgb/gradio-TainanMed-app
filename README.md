# 🏯 台南市開放資料檢視器

以 [Gradio](https://www.gradio.app/) 打造的網頁工具，可下載台南市政府資料開放平台的 CSV，
進行空值清理、關鍵字搜尋、欄位篩選，並下載篩選後的結果。

## 功能

- 輸入任意 CSV 連結並載入（預設為台南市開放資料）
- 自動處理繁體中文編碼（`utf-8-sig` → `big5` → `cp950`）
- 可選擇是否移除空值（`dropna`）
- 全欄位關鍵字搜尋、自訂顯示欄位
- 欄位資訊摘要（型態、非空值數、不重複值數）
- 下載目前篩選結果為 CSV

## 專案結構

```
.
├── app.py             # Gradio 主程式
├── requirements.txt   # 套件清單
├── render.yaml        # Render Blueprint 設定（選用）
└── README.md
```

## 本機執行

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

開啟 http://localhost:7860

## 部署到 Render

### 方法一：Blueprint（推薦）

1. 將專案推到 GitHub。
2. 登入 [Render](https://render.com)，選 **New → Blueprint**。
3. 選擇你的 GitHub repo，Render 會讀取 `render.yaml` 自動建立服務。
4. 部署完成後即可使用 Render 提供的網址。

### 方法二：手動建立 Web Service

1. Render 選 **New → Web Service**，連結 GitHub repo。
2. 設定：

   | 欄位 | 值 |
   | --- | --- |
   | Runtime | Python 3 |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `python app.py` |

3. 在 **Environment** 新增 `PYTHON_VERSION = 3.11.9`（選用，固定 Python 版本）。
4. 按 **Create Web Service**。

> `app.py` 會自動讀取 Render 提供的 `PORT` 環境變數，並綁定 `0.0.0.0`，不需額外設定。

## 環境變數（選用）

| 名稱 | 說明 |
| --- | --- |
| `DEFAULT_CSV_URL` | 介面載入時預設的 CSV 連結 |

## 注意事項

- Render 免費方案閒置約 15 分鐘後會休眠，再次開啟時需等待數十秒喚醒。
- 程式以 `verify=False` 下載資料（沿用原始設定，因部分政府網站憑證鏈不完整）。
  若資料來源憑證正常，建議改為 `verify=True`。
- 下載的資料僅在記憶體中處理，不會長期保存於伺服器。

## 授權

MIT
