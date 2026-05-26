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

## 仮想環境での backend 起動手順

仮想環境を有効化した状態で、以下を実行します。

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

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
- Supabase（Auth / Storage）: 外部サービス。`.env` の `SUPABASE_*` に実値を設定して利用

## 補足

- Docker イメージ内でも uv を使って依存関係をインストールしています。
- Docker 起動時のアプリ実行コマンドは `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` です。
- ローカル開発では、プロジェクトルートではなく `backend` ディレクトリでコマンドを実行してください。
