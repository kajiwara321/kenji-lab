# Smile of the Day

世界中の今日の笑顔を地球儀に貼って見せるウェブアート。

## Phase 1: データ収集パイプライン（現在のスコープ）

Flickr APIからジオタグ付き笑顔写真を毎日収集し、SQLiteに保存する。

### セットアップ

```bash
# 1. 依存パッケージのインストール
pip install -r requirements.txt

# 2. APIキーの設定
cp .env.example .env
# .env を編集して Flickr API キーを設定する
```

### Flickr APIキーの取得

⚠️ **Flickr Proアカウントが必要**

1. https://www.flickr.com/services/api/ にアクセス
2. "Request an API key" をクリック
3. .env の `FLICKR_API_KEY` と `FLICKR_SECRET` に設定

### 手動実行（テスト）

```bash
cd /path/to/smile-of-the-day
python -m pipeline.run
```

### cron 設定（毎日 09:00 JST = UTC 00:00）

```
0 0 * * * cd /path/to/smile-of-the-day && python -m pipeline.run >> data/run.log 2>&1
```

### DBの確認

```bash
sqlite3 data/smiles.db "SELECT COUNT(*), AVG(emotion_happy_prob) FROM photos;"
```

---

## Phase 2（予定）: 地球儀フロントエンド

globe.gl + Three.js で地球儀にピンを立てて可視化する。

## Phase 3（予定）: デプロイ

Vercel（フロントエンド） + Supabase（DB）に移行して公開。
