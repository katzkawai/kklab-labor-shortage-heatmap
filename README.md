# 日本の職業別 人手不足ヒートマップ

厚生労働省「一般職業紹介状況（職業安定業務統計）」の**職業別有効求人倍率**（パートタイムを除く常用）をもとに、
日本でどの職業が人手不足かをヒートマップで可視化した静的サイトです。

- 依存ライブラリなし（`index.html` 1ファイルのみ）
- 2022年度・2023年度・2024年度を切り替えて表示
- 職業大分類 13区分 + 「専門的・技術的職業」の内訳 12区分

## データ出典

- 厚生労働省「[一般職業紹介状況（職業安定業務統計）](https://www.mhlw.go.jp/toukei/list/114-1.html)」
  第21表-14「有効求人倍率（パート除く常用）」
- 集計値の参照: [リクルートエージェント「有効求人倍率とは？」](https://www.r-agent.com/guide/start/32493/)

有効求人倍率 = 月間有効求人数 ÷ 月間有効求職者数（ハローワーク経由のみ。民間求人サイトは含まない）。
1倍を大きく超えるほど人手不足が深刻、1倍未満は求職過多を示す。

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

`index.html` 内の `<script>` 冒頭にある `majorCategories` / `proCategories` の
`values` 配列（`[2022年度, 2023年度, 2024年度]` の順）を、最新の公表値で更新してください。
年度を増やす場合は `YEARS` 配列と年度ボタンも合わせて追加します。
