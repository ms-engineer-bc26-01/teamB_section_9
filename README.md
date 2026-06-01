# teamB_section_9

最終課題(TeamB)

https://app.notion.com/p/ms-engineer/TeamB-35d8f7a036288067bdd4de4c99ea980d

# 設計

### PRD

https://app.notion.com/p/ms-engineer/PRD-35d8f7a0362881b59cb7c235855b89a7?pvs=25

### 要件定義書

Notion　https://app.notion.com/p/ms-engineer/35d8f7a0362881fc9812f317d1cc392c

Github　クローゼット管理アプリ　要件定義書

https://github.com/ms-engineer-bc26-01/teamB_section_9/blob/main/docs/requirements.md

### 技術選定

https://app.notion.com/p/ms-engineer/35d8f7a0362881dd9ac3cce2305dfdc3?pvs=25

### ディレクトリ構成

https://github.com/ms-engineer-bc26-01/teamB_section_9/blob/main/docs/requirements.md#section-9-directory-structure

###

### DB設計

4. データモデル 以降の部分　※URL含めて清書予定

https://app.notion.com/p/requirements-368f18761305805e948df4902f71d3c9#368f187613058194ba17ed13ac6843ea

### ER図

https://github.com/ms-engineer-bc26-01/teamB_section_9/blob/main/docs/er-diagram.md

### シーケンス図

https://github.com/ms-engineer-bc26-01/teamB_section_9/blob/main/docs/sequence-diagrams.md

### API設計

https://portal.swaggerhub.com/apis/tokyoelectron/GeneratedAPI_2026-05-19-1506/1.0.0?source=catalog

### テスト設計書

https://app.notion.com/p/ms-engineer/35d8f7a03628810ba4c9d98941e9d9a2

# 開発環境

## CONTRIBUTING.md — 開発運用ガイド

Contributing を参照。

## 開発環境セットアップガイド

https://github.com/ms-engineer-bc26-01/teamB_section_9/blob/main/docs/setup.md

# Docker Compose 起動方法

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
- `SUPABASE_*`（Auth・PostgreSQL・Storage を Supabase で管理。実装時に実値が必要）
- `REDIS_URL`

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
