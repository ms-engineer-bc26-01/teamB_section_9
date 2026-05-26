# 開発環境セットアップガイド

> 対象：チームメンバー全員 / 最終更新：2026-05-26

---

## 前提条件

- Docker Desktop がインストール済みであること
- Git がインストール済みであること
- Python 3.12 以上がインストール済みであること（pre-commit のインストールに使用）
- Node.js 20 以上がインストール済みであること

---

## セットアップ手順

### 1. リポジトリをクローン

```bash
git clone git@github.com:ms-engineer-bc26-01/teamB_section_9.git
cd teamB_section_9
```

### 2. pre-commit をインストール（コミット前自動チェック）

```bash
pip install pre-commit
pre-commit install
```

これで `git commit` のたびに APIキー漏洩・Lint・フォーマットチェックが自動実行されます。

### 3. `.env` ファイルを作成

```bash
cp .env.example .env
```

代表者（C）から Slack DM で受け取った値を `.env` に貼り付けてください。

> `.env` は Git 管理対象外です。絶対に `git add` しないでください。

### 4. Docker でサービスを起動

```bash
docker compose up
```

初回は Docker イメージのビルドに数分かかります。

### 5. 動作確認

- フロントエンド: <http://localhost:3000>
- バックエンド API: <http://localhost:8000/docs>（Swagger UI）

`docker compose up` のログにエラーが出ていなければ OK です。

---

## `.env` が更新されたとき

Slack の `#env-updates` チャンネルを確認し、最新の値を自分の `.env` に反映してください。
反映が完了したら 🔄 リアクションをつけてください。

---

## よくあるトラブル

### `docker compose up` でエラーが出る

`.env` の値が正しく設定されているか確認してください。

```bash
# .env.example と比較して項目漏れがないか確認
diff .env.example .env
```

### `pre-commit` でエラーが出る

自動修正可能な場合は修正済みファイルが生成されます。
`git add` してから再度 `git commit` してください。

### ポートが競合する

別のアプリが 3000 / 5432 / 6379 を使用している場合は停止してから起動してください。

---

## ローカルでの CI チェック（PR 前推奨）

```bash
make check
```

GitHub Actions と同じ Lint・テスト（backend）・ビルド（frontend）がローカルで実行されます。
CI で弾かれる前にローカルで確認する習慣をつけてください。
