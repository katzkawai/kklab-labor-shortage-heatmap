#!/usr/bin/env python3
"""厚生労働省「一般職業紹介状況」の最新月次データで index.html を更新する。

- 最新の報道発表ページを探し、参考統計表の「常用（除パート）」表から
  職業別有効求人倍率を抽出する
- サイトに未反映の月であれば index.html / README.md を書き換える
- 依存: 標準ライブラリ + pdftotext（poppler-utils）

使い方:
  python3 scripts/update_data.py           # 最新月を取得して反映（既に最新なら何もしない）
  python3 scripts/update_data.py --check   # 取得・解析だけ行い結果を表示（ファイルは変更しない）
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

BASE = "https://www.mhlw.go.jp"
TOPICS_URL = BASE + "/seisakunitsuite/bunya/koyou_roudou/koyou/topics.html"
UA = {"User-Agent": "Mozilla/5.0 (compatible; labor-shortage-heatmap updater)"}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML = os.path.join(ROOT, "index.html")
README_MD = os.path.join(ROOT, "README.md")

# JS 上のカテゴリ名 → 参考統計表の行名
ROW_MAP = {
    # 大分類
    "保安職業従事者": "保安職業従事者",
    "建設・採掘従事者": "建設・採掘従事者",
    "介護関係職種": "介護サービス職業従事者",  # 月次は4区分合算が取れないため
    "サービス職業従事者": "サービス職業従事者",
    "輸送・機械運転従事者": "輸送・機械運転従事者",
    "販売従事者": "販売従事者",
    "専門的・技術的職業従事者": "専門的・技術的職業従事者",
    "生産工程従事者": "生産工程従事者",
    "職業計（全体平均）": "職業計",
    "農林漁業従事者": "農林漁業従事者",
    "管理的職業従事者": "管理的職業従事者",
    "運搬・清掃・包装等従事者": "運搬・清掃・包装等従事者",
    "事務従事者": "事務従事者",
    # 専門的・技術的職業の内訳
    "その他の技術者": "その他の技術者",
    "建築・土木・測量技術者": "建築・土木・測量技術者",
    "医師・歯科医師・獣医師・薬剤師": "医師，歯科医師，獣医師，薬剤師",
    "医療技術者": "医療技術者",
    "社会福祉専門職業従事者": "社会福祉専門職業従事者",
    "製造技術者（開発）": "製造技術者（開発）",
    "保健師・助産師・看護師": "保健師，助産師，看護師",
    "その他の保健医療従事者": "その他の保健医療従事者",
    "情報処理・通信技術者": "情報処理・通信技術者",
    "製造技術者（開発を除く）": "製造技術者（開発を除く）",
    "その他の専門的職業": "その他の専門的職業",
    "美術家・デザイナー・写真家・映像撮影者": "美術家，デザイナー，写真家，映像撮影者",
}


def fetch(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", errors="replace")


def reiwa_to_ad(n):
    return 2018 + n


def find_latest_release():
    """雇用トピックスページから最新の「一般職業紹介状況（令和X年Y月分）」を探す。"""
    html = fetch(TOPICS_URL)
    pat = re.compile(
        r'href="(/stf/newpage_\d+\.html)"[^>]*>(?:(?!</a>).)*?'
        r"一般職業紹介状況[（(]令和(\d+)年(\d+)月分",
        re.S,
    )
    best = None
    for href, ry, rm in pat.findall(html):
        y, m = reiwa_to_ad(int(ry)), int(rm)
        if best is None or (y, m) > (best[0], best[1]):
            best = (y, m, BASE + href, int(ry))
    if best is None:
        sys.exit("error: 最新の報道発表ページが見つかりませんでした: " + TOPICS_URL)
    return best  # (AD年, 月, URL, 令和年)


def current_years(html):
    m = re.search(r"const YEARS = \[([^\]]*)\];", html)
    return re.findall(r'"([^"]+)"', m.group(1))


def extract_reference_pdf_text(release_url):
    """報道発表ページから参考統計表PDFを特定し、テキスト化して返す。"""
    html = fetch(release_url)
    pdfs = re.findall(r'href="(/content/11602000/[^"]+\.pdf)"', html)
    if not pdfs:
        sys.exit("error: 報道発表ページにPDFリンクがありません: " + release_url)
    for p in pdfs:
        data = fetch(BASE + p, binary=True)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(data)
            path = f.name
        try:
            text = subprocess.run(
                ["pdftotext", "-layout", path, "-"],
                check=True, capture_output=True, text=True,
            ).stdout
        finally:
            os.unlink(path)
        if "常用（除パート）" in text and "保安職業従事者" in text:
            return text
    sys.exit("error: 参考統計表（常用（除パート）を含むPDF）が見つかりませんでした")


def extract_block(text):
    """常用（除パート）の職業中分類別ブロック（参考統計表7-2相当）を切り出す。"""
    m = re.search(r"参考統計表7-2(.+?)参考統計表8", text, re.S)
    if m and "常用（除パート）" in m.group(1):
        return m.group(1)
    # 表番号が変わった場合のフォールバック: 最初の「常用（除パート）」セクション
    m = re.search(r"常用（除パート）(.+?)(?:参考統計表|\Z)", text, re.S)
    if m:
        return m.group(1)
    sys.exit("error: 常用（除パート）の職業別表が見つかりませんでした")


def parse_ratios(block):
    """各行の有効求人倍率（行末の数値）を {JSカテゴリ名: 値} で返す。"""
    row_re = (
        r"^\s*{name}\s+[\d,]+\s+[\d,]+\s+[\d,]+\s+[\d,]+\s+[\d,]+\s+[\d,]+"
        r"\s+[\d.]+\s+([\d.]+)\s*$"
    )
    out = {}
    for js_name, row_name in ROW_MAP.items():
        m = re.search(row_re.format(name=re.escape(row_name)), block, re.M)
        if not m:
            sys.exit(f"error: 行が見つかりません: {row_name}")
        out[js_name] = float(m.group(1))
    return out


def extract_publish_date(release_url):
    html = fetch(release_url)
    m = re.search(r"令和(\d+)年(\d+)月(\d+)日", html)
    if not m:
        return None
    return reiwa_to_ad(int(m.group(1))), int(m.group(2)), int(m.group(3))


def update_index_html(html, month_key, ratios, release_url, ry, rm, pub):
    # YEARS に追加
    html = re.sub(
        r"const YEARS = \[([^\]]*)\];",
        lambda m: f'const YEARS = [{m.group(1)}, "{month_key}"];',
        html, count=1,
    )
    # 各カテゴリの values に値を追加
    for js_name, val in ratios.items():
        pat = re.compile(
            r'(\{ name: "' + re.escape(js_name) + r'"[^\n]*?values: \[)([^\]]*)(\])'
        )
        html, n = pat.subn(lambda m: f"{m.group(1)}{m.group(2)}, {val:.2f}{m.group(3)}", html, count=1)
        if n != 1:
            sys.exit(f"error: index.html 内にカテゴリがありません: {js_name}")
    # 出典の月次行を更新
    pub_str = f"{pub[0]}年{pub[1]}月{pub[2]}日公表" if pub else "公表日不明"
    new_source = (
        f'月次（最新: {reiwa_to_ad(ry)}年{rm}月分）: 「'
        f'<a href="{release_url}" target="_blank" rel="noopener">'
        f"一般職業紹介状況（令和{ry}年{rm}月分）</a>」（{pub_str}）"
        "参考統計表7-2 職業中分類別 常用（除パート）。"
    )
    html, n = re.subn(
        r'(<span id="monthly-source">).*?(</span>)',
        lambda m: m.group(1) + new_source + m.group(2),
        html, count=1, flags=re.S,
    )
    if n != 1:
        sys.exit("error: index.html 内に monthly-source 要素がありません")
    return html


def update_readme(text, release_url, ry, rm, pub):
    pub_str = f"{pub[0]}年{pub[1]}月{pub[2]}日公表" if pub else "公表日不明"
    new_line = (
        f"  - {reiwa_to_ad(ry)}年{rm}月（単月・実数）: "
        f"「[一般職業紹介状況（令和{ry}年{rm}月分）]({release_url})」"
        f"（{pub_str}）参考統計表7-2 職業中分類別 常用（除パート）"
    )
    text, n = re.subn(r"^\s+- \d{4}年\d+月（単月・実数）:.*$", new_line, text, count=1, flags=re.M)
    if n != 1:
        sys.exit("error: README.md 内に月次データの出典行がありません")
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="取得・解析のみ（ファイル変更なし）")
    args = ap.parse_args()

    with open(INDEX_HTML, encoding="utf-8") as f:
        index = f.read()
    years = current_years(index)

    y, m, url, ry = find_latest_release()
    month_key = f"{y}-{m:02d}"
    print(f"最新の報道発表: 令和{ry}年{m}月分 ({month_key}) {url}")
    print(f"サイトの期間: {years}")

    if month_key in years:
        print("NO_UPDATE: 既に最新です")
        return

    text = extract_reference_pdf_text(url)
    ratios = parse_ratios(extract_block(text))
    pub = extract_publish_date(url)

    print(f"解析結果（{month_key}, パート除く常用 有効求人倍率）:")
    for k, v in ratios.items():
        print(f"  {k}: {v:.2f}")

    if args.check:
        print("CHECK_ONLY: ファイルは変更していません")
        return

    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(update_index_html(index, month_key, ratios, url, ry, m, pub))
    with open(README_MD, encoding="utf-8") as f:
        readme = f.read()
    with open(README_MD, "w", encoding="utf-8") as f:
        f.write(update_readme(readme, url, ry, m, pub))

    print(f"UPDATED: {month_key}")
    # GitHub Actions のステップ output（あれば）
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"updated=true\nmonth={month_key}\n")


if __name__ == "__main__":
    main()
