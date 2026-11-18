# ============================================================
# 台南市開放資料檢視器 (Gradio) - 可部署至 Render / 本機 / Colab
# ============================================================
import io
import os
import tempfile

import gradio as gr
import pandas as pd
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_URL = os.environ.get(
    "DEFAULT_CSV_URL",
    "https://data.tainan.gov.tw/File/ResourceCsvDownload/6c16b2c8-92b6-49d9-98b5-02966462172c",
)


# ---------- 核心功能 ----------
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
    return (
        df,
        df,
        status,
        gr.update(choices=cols, value=cols),
        describe(df),
    )


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


# ---------- 介面 ----------
theme = gr.themes.Soft(
    primary_hue="teal",
    secondary_hue="cyan",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Noto Sans TC"), "sans-serif"],
)

css = """
.gradio-container {max-width: 1200px !important; margin: auto;}
#title {text-align: center; padding: 18px 0 6px;}
#title h1 {font-size: 2.1rem; margin-bottom: 4px;}
#title p {color: #64748b;}
"""

with gr.Blocks(theme=theme, css=css, title="台南開放資料檢視器") as demo:
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
            drop_na = gr.Checkbox(label="移除空值 (dropna)", value=True, scale=1)
            load_btn = gr.Button("📥 載入資料", variant="primary", scale=1)
        status = gr.Markdown("尚未載入資料")

    with gr.Tabs():
        with gr.Tab("📋 資料表"):
            with gr.Row():
                keyword = gr.Textbox(
                    label="關鍵字搜尋(搜尋所有欄位)",
                    placeholder="例如:區名、路名…",
                    scale=3,
                )
                search_btn = gr.Button("🔎 搜尋", variant="secondary", scale=1)
            col_select = gr.CheckboxGroup(label="顯示欄位", choices=[], value=[])
            filter_info = gr.Markdown()
            table = gr.Dataframe(label="資料內容", interactive=False, wrap=True, max_height=520)
            download = gr.File(label="⬇️ 下載目前結果 (CSV)")

        with gr.Tab("📊 欄位資訊"):
            info_table = gr.Dataframe(label="欄位摘要", interactive=False)

    # ---------- 事件 ----------
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


if __name__ == "__main__":
    # Render 會提供 PORT 環境變數,且必須綁定 0.0.0.0
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
    )
