# Backend セットアップ

このディレクトリは FastAPI ベースのバックエンドです。依存管理には uv を使用し、ローカル実行と Docker による実行の両方に対応しています。

## 前提

- Python 3.12
- uv
- Docker / Docker Compose

Python のバージョンは `.python-version` と `pyproject.toml` で 3.12 系に固定されています。

## uv のインストール

### Linux / macOS

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

インストール後、シェルを再起動するか、必要に応じて PATH を反映してください。

### Homebrew を使う場合

```bash
brew install uv
```

インストール確認:

```bash
uv --version
```

## ローカル開発環境の構築

### 1. backend ディレクトリへ移動

```bash
cd backend
```

### 2. 仮想環境を作成

```bash
uv venv --python 3.12
```

`.venv` ディレクトリが作成されます。

### 3. 仮想環境を有効化

```bash
source .venv/bin/activate
```

### 4. 依存関係をインストール

```bash
uv sync
```

`uv.lock` に基づいて依存関係が同期されます。

### 5. マイグレーションを実行

DB スキーマを最新化するには、`DATABASE_URL` が設定された状態で以下を実行します。

```bash
uv run alembic upgrade head
```

現在のリビジョン確認:

```bash
uv run alembic current
```

1つ前のリビジョンへ戻す場合:

```bash
uv run alembic downgrade -1
```

## 仮想環境での backend 起動手順

仮想環境を有効化した状態で、以下を実行します。

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## BYPASS モード用の seed データ投入

`AUTH_BYPASS_ENABLED=true` で開発する場合は、モックユーザー `00000000-0000-0000-0000-000000000001` に対して服の初期データを投入できます。

### 前提条件

- `DATABASE_URL` が設定されていること
- マイグレーションが適用済みであること
- 開発用 DB が起動していること

マイグレーションが未適用の場合は先に実行してください。

```bash
cd backend
uv run alembic upgrade head
```

### 実行方法

リポジトリルートから Makefile 経由で実行します。

```bash
cd ..
make seed-bypass-clothes
```

または backend ディレクトリでスクリプトを直接実行しても構いません。

```bash
cd backend
uv run python scripts/seed_bypass_clothes.py
```

この seed は再実行可能で、同ユーザーに紐づく既存の服データを入れ替えた上で 20 件の服を登録します。データには複数のカテゴリ、季節、TPO を含めてあり、`/api/v1/outfits/suggest` の動作確認に使えます。

### 投入後の確認方法

BYPASS モードで API を起動している場合は、認証ヘッダなしで服一覧を確認できます。

```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

別ターミナルで次を実行してください。

```bash
curl -s "http://localhost:8000/api/v1/clothes?limit=100" | jq '.total'
curl -s "http://localhost:8000/api/v1/clothes?limit=5" | jq '.items[] | {name, category, season, tpo_tags}'
```

`total` が `20` で返れば、seed データの投入は完了です。

起動後の確認先:

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/api/v1/health

## 仮想環境を有効化せずに起動する方法

`uv run` を使うと、仮想環境を明示的に有効化しなくても起動できます。

```bash
cd backend
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker Compose による起動手順

Docker Compose の設定ファイルはリポジトリルートの `docker-compose.yml` にあります。`backend` ディレクトリではなく、ルートディレクトリで実行してください。

### 1. リポジトリルートへ移動

```bash
cd ..
```

すでにルートにいる場合はそのままで構いません。

### 2. 環境変数ファイルを作成

```bash
cp .env.example .env
```

### 3. backend と依存サービスを起動

```bash
docker compose up --build backend postgres redis
```

バックエンドは `postgres`、`redis` に依存しているため、あわせて起動します。

### 4. バックグラウンドで起動

```bash
docker compose up -d --build backend postgres redis
```

### 5. 停止

```bash
docker compose down
```

### 6. ボリュームも含めて停止

```bash
docker compose down -v
```

## Docker 起動時の確認先

- Backend API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## 補足

- Docker イメージ内でも uv を使って依存関係をインストールしています。
- Docker 起動時のアプリ実行コマンドは `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` です。
- ローカル開発では、プロジェクトルートではなく `backend` ディレクトリでコマンドを実行してください。
