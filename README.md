# 日本の職業別 人手不足ヒートマップ

厚生労働省「一般職業紹介状況（職業安定業務統計）」の**職業別有効求人倍率**（パートタイムを除く常用）をもとに、
日本でどの職業が人手不足かをヒートマップで可視化した静的サイトです。

> このサイトは **Kimi-K3**（Kimi Code CLI）を用いて作成されました。

## サイトの内容

- **職業大分類ヒートマップ**: 保安・建設・介護・サービス・事務など13区分の有効求人倍率を色で表示
- **専門的・技術的職業の内訳ヒートマップ**: 技術者・医療・福祉系など12区分を個別に表示
- **年度・月次切替**: 2022年度・2023年度・2024年度（年度平均）と 2026年5月（月次・最新）をボタンで切り替えて表示
- **カラースケール**: 青（求職過多・0倍）→ 白（1倍）→ 赤（深刻な人手不足・8倍以上）の発散スケール
- 読み方・注意点、データ出典リンク、免責事項を併記

## 技術仕様

- 依存ライブラリ・ビルド工程なし。**`index.html` 1ファイルのみ**（HTML + CSS + バニラ JavaScript）
- データは `<script>` 内の配列（`majorCategories` / `proCategories`）に埋め込み。外部API通信なし
- 配色は発散カラースケールを線形補間で動的計算（0〜8倍にクリップ、背景の濃さに応じて文字色を白/黒で自動切替）
- CSS Grid（`auto-fill, minmax(200px, 1fr)`）によるレスポンシブレイアウト
- GitHub Pages へのデプロイは `main` ブランチのルートを公開するだけで OK

## データ出典

- 厚生労働省「[一般職業紹介状況（職業安定業務統計）](https://www.mhlw.go.jp/toukei/list/114-1.html)」
  - 2022〜2024年度（年度平均）: 第21表-14「有効求人倍率（パート除く常用）」
  - 2026年5月（単月・実数）: 「[一般職業紹介状況（令和8年5月分）](https://www.mhlw.go.jp/stf/newpage_74004.html)」（2026年6月30日公表）参考統計表7-2 職業中分類別 常用（除パート）
- 年度データ集計値の参照: [リクルートエージェント「有効求人倍率とは？」](https://www.r-agent.com/guide/start/32493/)

有効求人倍率 = 月間有効求人数 ÷ 月間有効求職者数（ハローワーク経由のみ。民間求人サイトは含まない）。
1倍を大きく超えるほど人手不足が深刻、1倍未満は求職過多を示す。
月次データは単月の実数値のため、年度平均とは直接比較できない（季節変動あり）。

## 免責事項

掲載内容の正確性・最新性は保証しません。本サイトのデータ・情報の利用によって生じた
いかなる損失・不利益についても、運営者は一切の責任を負いません。
正確な数値は必ず厚生労働省の一次情報を確認してください。

## GitHub Pages で公開する方法

1. GitHub に新しいリポジトリを作成する（例: `labor-shortage-heatmap`）
2. このディレクトリのファイルを push する

   ```bash
   git init
   git add index.html README.md
   git commit -m "Add labor shortage heatmap"
   git branch -M main
   git remote add origin git@github.com:<ユーザー名>/<リポジトリ名>.git
   git push -u origin main
   ```

3. GitHub のリポジトリ画面で **Settings → Pages** を開く
4. **Source** で `Deploy from a branch` を選び、Branch に `main` / `/ (root)` を指定して **Save**
5. 数分後に `https://<ユーザー名>.github.io/<リポジトリ名>/` で公開される

## ローカルでの確認

ブラウザで `index.html` を直接開くだけで動作します。サーバーを立てる場合:

```bash
python3 -m http.server 8000
# → http://localhost:8000
```

## データの更新方法

**自動更新（GitHub Actions）**: `.github/workflows/update-data.yml` が毎月2日 10:23 JST に
`scripts/update_data.py` を実行し、厚生労働省の最新報道発表（前月分・月末公表）を取り込みます。
新しい月のデータがあれば `index.html`（YEARS・各カテゴリの values・出典）と README を更新して
自動で commit & push され、期間タブ（月次ボタン）が追加されます。Actions タブから手動実行
（workflow_dispatch）も可能です。

手動で更新する場合は、リポジトリ直下で以下を実行します（要 `pdftotext` / poppler-utils）:

```bash
python3 scripts/update_data.py          # 最新月を取得して反映
python3 scripts/update_data.py --check  # 取得・解析の確認のみ（ファイル変更なし）
```

データ本体は `index.html` 内の `<script>` 冒頭にある `YEARS` 配列と
`majorCategories` / `proCategories` の `values` 配列（YEARS と同順）です。
