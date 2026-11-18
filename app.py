# ============================================================
# 台南市開放資料檢視器 — Gradio + PWA + RWD
#   * Gradio 介面掛載在 FastAPI 之下
#   * FastAPI 額外提供 manifest / service worker / 圖示 / 離線頁
# 本機執行:  uvicorn app:app --host 0.0.0.0 --port 7860
# ============================================================
import io
import os
import tempfile
from pathlib import Path

import gradio as gr
import pandas as pd
import requests
import urllib3
from fastapi import FastAPI
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = Path(__file__).parent
PWA_DIR = BASE_DIR / "pwa"

DEFAULT_URL = os.environ.get(
    "DEFAULT_CSV_URL",
    "https://data.tainan.gov.tw/File/ResourceCsvDownload/6c16b2c8-92b6-49d9-98b5-02966462172c",
)


# ====================== 資料處理 ======================
def load_data(url, drop_na):
    """下載 CSV 並轉成 DataFrame"""
    url = (url or "").strip()
    if not url:
        raise gr.Error("請輸入 CSV 連結")
    try:
        response = requests.get(url, verify=False, timeout=30)
        response.raise_for_status()
    except Exception as e:
        raise gr.Error(f"下載失敗:{e}")

    # 繁體中文編碼:先試 utf-8-sig,失敗再試 big5 / cp950
    df = None
    for enc in ("utf-8-sig", "big5", "cp950"):
        try:
            df = pd.read_csv(io.BytesIO(response.content), encoding=enc)
            break
        except Exception:
            continue
    if df is None:
        raise gr.Error("無法解析 CSV 編碼")

    raw_rows = len(df)
    if drop_na:
        df = df.dropna()

    status = (
        f"✅ 載入成功:原始 **{raw_rows:,}** 筆"
        f"{'，移除空值後 **' + format(len(df), ',') + '** 筆' if drop_na else ''}"
        f"，共 **{df.shape[1]}** 個欄位"
    )
    cols = list(df.columns)
    return df, df, status, gr.update(choices=cols, value=cols), describe(df)


def describe(df):
    """欄位資訊摘要"""
    return pd.DataFrame(
        {
            "欄位": df.columns,
            "型態": [str(t) for t in df.dtypes],
            "非空值數": df.notna().sum().values,
            "不重複值數": df.nunique().values,
        }
    )


def apply_filter(df, keyword, columns):
    """關鍵字搜尋 + 欄位篩選"""
    if df is None or len(df) == 0:
        return pd.DataFrame(), "⚠️ 請先載入資料", None
    out = df
    if keyword and keyword.strip():
        mask = out.astype(str).apply(
            lambda col: col.str.contains(keyword.strip(), case=False, na=False, regex=False)
        ).any(axis=1)
        out = out[mask]
    if columns:
        out = out[[c for c in columns if c in out.columns]]

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    out.to_csv(tmp.name, index=False, encoding="utf-8-sig")
    return out, f"🔎 顯示 **{len(out):,}** / {len(df):,} 筆", tmp.name


# ====================== PWA:<head> 注入 ======================
HEAD = """
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#0d9488">
<meta name="application-name" content="台南資料">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="台南資料">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="apple-touch-icon" href="/pwa/icons/apple-touch-icon.png">
<link rel="icon" type="image/png" href="/pwa/icons/icon-192.png">
<script>
  // 註冊 Service Worker
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(function (e) {
        console.warn("SW 註冊失敗", e);
      });
    });
  }

  // 「安裝 App」浮動按鈕(Chrome / Edge / Android)
  var deferredPrompt = null;
  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    deferredPrompt = e;
    if (document.getElementById("pwa-install-btn")) return;
    var btn = document.createElement("button");
    btn.id = "pwa-install-btn";
    btn.textContent = "📲 安裝 App";
    btn.onclick = function () {
      btn.remove();
      deferredPrompt.prompt();
      deferredPrompt.userChoice.finally(function () { deferredPrompt = null; });
    };
    document.body.appendChild(btn);
  });
  window.addEventListener("appinstalled", function () {
    var b = document.getElementById("pwa-install-btn");
    if (b) b.remove();
  });
</script>
"""

# ====================== RWD:CSS ======================
CSS = """
:root { --brand: #0d9488; }

/* 支援瀏海 / 安全區 */
.gradio-container {
  max-width: 1200px !important;
  margin: 0 auto !important;
  padding-left: max(12px, env(safe-area-inset-left)) !important;
  padding-right: max(12px, env(safe-area-inset-right)) !important;
  padding-bottom: max(12px, env(safe-area-inset-bottom)) !important;
}

#title { text-align: center; padding: 18px 0 6px; }
#title h1 { font-size: clamp(1.4rem, 5vw, 2.2rem); margin: 0 0 4px; line-height: 1.25; }
#title p  { color: #64748b; font-size: clamp(.85rem, 3vw, 1rem); margin: 0; }

/* 表格:橫向可捲動,不撐破版面 */
#data-table, #info-table { overflow-x: auto; }
#data-table table, #info-table table { font-size: .92rem; }

/* 浮動安裝按鈕 */
#pwa-install-btn {
  position: fixed; right: 16px; bottom: calc(16px + env(safe-area-inset-bottom));
  z-index: 9999; border: 0; border-radius: 999px; padding: 12px 20px;
  background: var(--brand); color: #fff; font-size: 1rem; font-weight: 600;
  box-shadow: 0 6px 18px rgba(0,0,0,.25); cursor: pointer;
}

/* 平板以下 */
@media (max-width: 900px) {
  .gradio-container { padding-top: 4px !important; }
}

/* 手機:所有 Row 直向堆疊,按鈕/輸入滿版,加大觸控區 */
@media (max-width: 640px) {
  .gradio-container .row { flex-wrap: wrap !important; }
  .gradio-container .row > * { min-width: 100% !important; flex: 1 1 100% !important; }
  .gradio-container button { min-height: 46px; font-size: 1rem; }
  .gradio-container input, .gradio-container textarea { font-size: 16px !important; } /* 避免 iOS 聚焦自動放大 */
  #data-table table, #info-table table { font-size: .85rem; }
}

/* PWA 獨立視窗模式:隱藏 Gradio 頁尾 */
@media (display-mode: standalone) {
  footer { display: none !important; }
}
"""

theme = gr.themes.Soft(
    primary_hue="teal",
    secondary_hue="cyan",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Noto Sans TC"), "sans-serif"],
)

# ====================== Gradio 介面 ======================
with gr.Blocks(theme=theme, css=CSS, head=HEAD, title="台南開放資料檢視器") as demo:
    gr.HTML(
        """
        <div id="title">
          <h1>🏯 台南市開放資料檢視器</h1>
          <p>下載、清理並搜尋台南市政府資料開放平台的 CSV 資料</p>
        </div>
        """
    )

    df_state = gr.State(None)

    with gr.Group():
        with gr.Row():
            url_in = gr.Textbox(label="CSV 連結", value=DEFAULT_URL, scale=5, lines=1)
            drop_na = gr.Checkbox(label="移除空值 (dropna)", value=True, scale=1, min_width=160)
            load_btn = gr.Button("📥 載入資料", variant="primary", scale=1, min_width=140)
        status = gr.Markdown("尚未載入資料")

    with gr.Tabs():
        with gr.Tab("📋 資料表"):
            with gr.Row():
                keyword = gr.Textbox(
                    label="關鍵字搜尋(搜尋所有欄位)",
                    placeholder="例如:區名、路名…",
                    scale=3,
                )
                search_btn = gr.Button("🔎 搜尋", variant="secondary", scale=1, min_width=120)
            col_select = gr.CheckboxGroup(label="顯示欄位", choices=[], value=[])
            filter_info = gr.Markdown()
            table = gr.Dataframe(
                label="資料內容", interactive=False, wrap=True,
                max_height=520, elem_id="data-table",
            )
            download = gr.File(label="⬇️ 下載目前結果 (CSV)")

        with gr.Tab("📊 欄位資訊"):
            info_table = gr.Dataframe(label="欄位摘要", interactive=False, elem_id="info-table")

    load_btn.click(
        load_data,
        inputs=[url_in, drop_na],
        outputs=[df_state, table, status, col_select, info_table],
    )
    for trigger in (search_btn.click, keyword.submit, col_select.change):
        trigger(
            apply_filter,
            inputs=[df_state, keyword, col_select],
            outputs=[table, filter_info, download],
        )


# ====================== FastAPI:PWA 端點 ======================
app = FastAPI(title="Tainan Open Data PWA")


@app.get("/manifest.webmanifest", include_in_schema=False)
def manifest():
    return FileResponse(
        PWA_DIR / "manifest.webmanifest",
        media_type="application/manifest+json",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/sw.js", include_in_schema=False)
def service_worker():
    # 必須從網站根目錄提供,Service Worker 的 scope 才能涵蓋整站
    return FileResponse(
        PWA_DIR / "sw.js",
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"},
    )


@app.get("/offline", include_in_schema=False)
def offline():
    return FileResponse(PWA_DIR / "offline.html", media_type="text/html")


@app.get("/healthz", include_in_schema=False)
def healthz():
    return PlainTextResponse("ok")


app.mount("/pwa", StaticFiles(directory=PWA_DIR), name="pwa")

# Gradio 掛載在根路徑(需在其他路由之後)
app = gr.mount_gradio_app(app, demo, path="/")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))
