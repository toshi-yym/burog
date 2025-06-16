import streamlit as st
import requests
from bs4 import BeautifulSoup
import re

# --- カスタムCSSでリッチなデザイン ---
st.markdown(
    """
    <style>
    body {
        background: linear-gradient(120deg, #f0f4ff 0%, #f9f9f9 100%);
    }
    .main-title {
        font-size: 2.6em;
        font-weight: bold;
        color: #4F8BF9;
        margin-bottom: 0.1em;
        letter-spacing: 2px;
    }
    .desc {
        font-size: 1.1em;
        color: #555;
        margin-bottom: 1.5em;
    }
    .card {
        background: #fff;
        border-radius: 16px;
        box-shadow: 0 4px 16px rgba(79,139,249,0.08);
        padding: 2em 1.5em 1.5em 1.5em;
        margin-bottom: 1.5em;
        border: 1px solid #e3e6f0;
    }
    .stButton>button {
        background: linear-gradient(90deg, #4F8BF9 0%, #6BCB77 100%);
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 0.8em 2em;
        font-size: 1.1em;
        box-shadow: 0 2px 8px rgba(79,139,249,0.1);
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #6BCB77 0%, #4F8BF9 100%);
        color: #fff;
    }
    .stTextInput>div>div>input, .stTextArea textarea {
        background: #f8faff;
        border-radius: 8px;
        border: 1px solid #dbeafe;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- タイトル＆説明 ---
st.markdown('<div class="main-title">📝 ブログ本文抽出＆Word変換ツール</div>', unsafe_allow_html=True)
st.markdown('<div class="desc">URLを入力するだけで、記事本文だけを自動抽出しWord形式でダウンロードできます。不要な冒頭・末尾の行やおすすめ記事もカット！</div>', unsafe_allow_html=True)

url = st.text_input("ブログ記事のURLを入力してください")
# 行数指定をメインエリアのURL入力欄の直下に移動
col1, col2 = st.columns(2)
with col1:
    head_cut = st.number_input("冒頭で削除する行数", min_value=0, max_value=100, value=0)
with col2:
    tail_cut = st.number_input("末尾で削除する行数", min_value=0, max_value=100, value=0)

# 除外したいキーワード例
exclude_keywords = [
    "著者紹介", "店舗情報", "おすすめ記事", "関連記事", "この記事を書いた人", "プロフィール", "運営者情報", "PR", "広告", "シェア", "SNS", "コメント", "前の記事", "次の記事", "この記事をシェア", "人気記事", "タグ", "カテゴリー", "この記事を読んだ人はこんな記事も読んでいます"]

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    if st.button("Word形式に変換"):
        if not url:
            st.warning("URLを入力してください。")
        else:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                html = response.text
                soup = BeautifulSoup(html, "html.parser")

                # タイトル抽出
                title = soup.title.string.strip() if soup.title and soup.title.string else "タイトル不明"

                # 本文候補の抽出（pタグやarticleタグなどを優先）
                main_content = ""
                # まずarticleタグを優先
                article = soup.find("article")
                if article:
                    main_content = article.get_text("\n", strip=True)
                else:
                    # mainやsectionタグも候補
                    main = soup.find("main")
                    if main:
                        main_content = main.get_text("\n", strip=True)
                    else:
                        # pタグを全部連結
                        ps = soup.find_all("p")
                        main_content = "\n".join([p.get_text(strip=True) for p in ps])

                # 除外キーワードを含む行を除去
                lines = main_content.splitlines()
                filtered_lines = []
                for line in lines:
                    if not any(kw in line for kw in exclude_keywords):
                        filtered_lines.append(line)

                # ユーザー指定の冒頭・末尾カット
                if head_cut > 0 or tail_cut > 0:
                    filtered_lines = filtered_lines[head_cut:len(filtered_lines)-tail_cut if tail_cut != 0 else None]

                filtered_content = "\n".join(filtered_lines).strip()

                if not filtered_content:
                    filtered_content = "（本文が抽出できませんでした）"

                st.success("本文抽出に成功しました。タイトルと本文を表示します。")
                editable_title = st.text_input("タイトル（編集可）", value=title)
                content_with_title = f"【タイトル】{editable_title}\n{filtered_content}"
                content = st.text_area("本文＋タイトル（編集・一括コピー可）", content_with_title, height=400)

                # Word出力用処理
                from io import BytesIO
                from docx import Document
                import re

                def sanitize_filename(name):
                    # ファイル名に使えない文字を除去
                    return re.sub(r'[\\/:*?\"<>|]', '', name)

                if st.button("Wordファイルをダウンロード"):
                    doc = Document()
                    doc.add_paragraph(content)
                    buf = BytesIO()
                    doc.save(buf)
                    buf.seek(0)
                    safe_title = sanitize_filename(editable_title) or "記事"
                    st.download_button(
                        label="Wordファイルをダウンロード",
                        data=buf,
                        file_name=f"{safe_title}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
            except Exception as e:
                st.error(f"HTMLの取得または本文抽出に失敗しました: {e}")
