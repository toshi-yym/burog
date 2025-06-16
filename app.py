import streamlit as st
import requests
from bs4 import BeautifulSoup
import re

st.title("ブログ本文抽出＆Word変換ツール")

url = st.text_input("ブログ記事のURLを入力してください")

# 除外したいキーワード例
exclude_keywords = [
    "著者紹介", "店舗情報", "おすすめ記事", "関連記事", "この記事を書いた人", "プロフィール", "運営者情報", "PR", "広告", "シェア", "SNS", "コメント", "前の記事", "次の記事", "この記事をシェア", "人気記事", "タグ", "カテゴリー", "この記事を読んだ人はこんな記事も読んでいます"]

# 行数指定のUIを追加
head_cut = st.number_input("冒頭で削除する行数", min_value=0, max_value=50, value=0)
tail_cut = st.number_input("末尾で削除する行数", min_value=0, max_value=50, value=0)

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
            # 例: head_cut=3, tail_cut=5 → 先頭3行と末尾5行を除外
            if head_cut > 0 or tail_cut > 0:
                filtered_lines = filtered_lines[head_cut:len(filtered_lines)-tail_cut if tail_cut != 0 else None]

            filtered_content = "\n".join(filtered_lines).strip()

            if not filtered_content:
                filtered_content = "（本文が抽出できませんでした）"

            st.success("本文抽出に成功しました。タイトルと本文を表示します。")
            # タイトル編集欄
            editable_title = st.text_input("タイトル（編集可）", value=title)
            # 本文欄の初期値にタイトルを含める
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
