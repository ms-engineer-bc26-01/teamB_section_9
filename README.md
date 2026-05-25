# teamB_section_9

## Docker Compose 起動方法

このプロジェクトはルートの `docker-compose.yml` を使ってローカル開発環境を起動します。

### 0. 環境変数ファイルを作成

```bash
cp .env.example .env
```

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
- MinIO API: http://localhost:9000
- MinIO Console: http://localhost:9001
