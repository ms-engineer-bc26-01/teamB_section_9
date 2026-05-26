# teamB_section_9

## Docker Compose 起動方法

このプロジェクトはルートの `docker-compose.yml` を使ってローカル開発環境を起動します。

### 0. 環境変数ファイルを作成

```bash
cp .env.example .env
```

### 起動に必要な環境変数

現時点で `docker compose up --build` に必要な環境変数は、PostgreSQL コンテナ初期化用の以下 3 つです。

```env
POSTGRES_USER=app
POSTGRES_PASSWORD=app
POSTGRES_DB=closet
```

これらが未設定だと、`postgres` サービスの起動に必要な値が渡らず、結果として `backend` も起動できません。

以下の値は `.env.example` に含まれていますが、現時点では起動に必須ではありません。

- `DATABASE_URL`
  - 将来アプリケーション側で DB 接続実装を追加する想定のための値です。
  - 現在の backend 実装では参照していません。
- `GOOGLE_API_KEY`
- `LLM_MODEL`
- `STRIPE_*`
- `SUPABASE_*`
- `REDIS_URL`
- `STORAGE_*`

まずは `.env.example` をそのままコピーすれば、起動に必要な最低限の値は揃います。

### 1. 起動

```bash
docker compose up --build
```

### 2. バックグラウンド起動

```bash
docker compose up -d --build
```

### 3. 停止

```bash
docker compose down
```

### 4. ボリュームも含めて停止（DBデータ削除）

```bash
docker compose down -v
```

## 起動後の接続先

- Frontend: http://localhost:3000
- Backend (FastAPI): http://localhost:8000
- Backend API Docs (Swagger): http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379
