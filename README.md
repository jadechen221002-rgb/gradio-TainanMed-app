# 🏯 台南市開放資料檢視器（PWA + RWD）

以 [Gradio](https://www.gradio.app/) 打造的網頁工具，可下載台南市政府資料開放平台的 CSV，
進行空值清理、關鍵字搜尋、欄位篩選，並下載篩選後的結果。
支援 **PWA（可安裝到手機／桌面）** 與 **RWD（手機、平板、桌機自適應）**。

## 功能

- 輸入任意 CSV 連結並載入（預設為台南市開放資料）
- 自動處理繁體中文編碼（`utf-8-sig` → `big5` → `cp950`）
- 可選擇是否移除空值（`dropna`）
- 全欄位關鍵字搜尋、自訂顯示欄位
- 欄位資訊摘要（型態、非空值數、不重複值數）
- 下載目前篩選結果為 CSV

### PWA

- Web App Manifest（名稱、主題色、圖示、standalone 模式）
- Service Worker：離線備援頁、Gradio 前端靜態檔快取
- 「📲 安裝 App」浮動按鈕（Chrome／Edge／Android）
- iOS Safari：點分享 → **加入主畫面**
- 含 maskable 圖示與 Apple Touch Icon

> 資料載入與搜尋需要連線伺服器，因此離線時會顯示離線提示頁，不會有離線資料查詢。

### RWD

- 手機（≤640px）：所有欄位直向堆疊、按鈕滿版、加大觸控區、輸入框 16px 避免 iOS 自動放大
- 平板／桌機：最大寬度 1200px 置中
- 表格橫向捲動，不撐破版面
- 支援瀏海螢幕安全區（`safe-area-inset`）
- 自動使用系統淺色／深色主題

## 專案結構

```
.
├── app.py                      # Gradio + FastAPI 主程式
├── pwa/
│   ├── manifest.webmanifest    # PWA 設定
│   ├── sw.js                   # Service Worker
│   ├── offline.html            # 離線備援頁
│   └── icons/                  # 192 / 512 / maskable / apple-touch
├── make_icons.py               # 圖示產生腳本（選用，需 Pillow）
├── requirements.txt
├── render.yaml                 # Render Blueprint
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

> Service Worker 只能在 **HTTPS** 或 **localhost** 運作，部署到 Render 後預設就是 HTTPS。

## 部署到 Render

### 方法一：Blueprint（推薦）

1. 將專案推到 GitHub。
2. Render → **New → Blueprint** → 選擇 repo，會讀取 `render.yaml` 自動建立服務。

### 方法二：手動建立 Web Service

| 欄位 | 值 |
| --- | --- |
| Language | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/healthz` |
| 環境變數 | `PYTHON_VERSION = 3.11.9`（選用） |

> ⚠️ Start Command 請用 `uvicorn app:app ...`，不要用 `python app.py`；兩者都能跑，
> 但 uvicorn 指令是 Render 上較標準的做法。

## 驗證 PWA

1. 用 Chrome 開啟部署網址 → F12 → **Application** 分頁。
2. **Manifest**：確認名稱、圖示無錯誤。
3. **Service Workers**：狀態應為 *activated and is running*。
4. 網址列右側會出現「安裝」圖示；也可執行 **Lighthouse → PWA** 檢測。

## 環境變數（選用）

| 名稱 | 說明 |
| --- | --- |
| `DEFAULT_CSV_URL` | 介面載入時預設的 CSV 連結 |

## 注意事項

- Render 免費方案閒置約 15 分鐘後會休眠，再次開啟需等待數十秒。
- 程式以 `verify=False` 下載資料（沿用原始設定）；若來源憑證正常，建議改為 `verify=True`。
- 更新 `sw.js` 時，請調整檔內的 `VERSION` 讓舊快取失效。

## 授權

MIT
