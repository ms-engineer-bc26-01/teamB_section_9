# 開発環境セットアップガイド

> 対象：チームメンバー全員 / 最終更新：2026-06-02

---

## 前提条件

- Docker Desktop がインストール済みであること
- Git がインストール済みであること
- Python 3.12 以上がインストール済みであること（pre-commit のインストールに使用）
- Node.js 24.15.x がインストール済みであること（CI と同じ前提）
- npm 11.12.x を使用すること（frontend は npm / package-lock.json 前提）

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

これで `git commit` のたびに APIキー漏洩・Lint・フォーマットチェックに加え、frontend の package.json と package-lock.json の整合チェックが自動実行されます。

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

## LAN 上の別端末からアクセスする場合

スマートフォンや別の PC など、ホストマシンと同じ LAN にいる端末からフロントエンドにアクセスする場合は、追加の設定が必要です。

**なぜ設定が必要か**

- `NEXT_PUBLIC_API_BASE_URL` の `localhost` はブラウザ側の端末で解決されるため、ホストマシンの backend に届きません。
- `BACKEND_CORS_ORIGINS` に LAN IP のオリジンが含まれていないと CORS でブロックされます。

**手順**

1. ホストマシンの LAN IP を確認します（例: `192.168.11.37`）。

   ```bash
   # macOS / Linux
   ip a | grep 'inet ' | grep -v 127
   # または
   ifconfig | grep 'inet ' | grep -v 127
   ```

2. `.env` の以下の 2 項目をホストマシンの LAN IP で書き換えます。

   ```env
   NEXT_PUBLIC_API_BASE_URL=http://192.168.11.37:8000/api/v1
   BACKEND_CORS_ORIGINS=["http://localhost:3000","http://192.168.11.37:3000"]
   ```

3. コンテナを再起動します。

   ```bash
   docker compose up --build
   ```

4. LAN 上の端末から `http://192.168.11.37:3000` にアクセスしてください。

> **注意**: LAN IP はルーター・DHCP 設定によって変わることがあります。IP が変わった場合は同じ手順で `.env` を更新してください。

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

GitHub Actions と同じ依存整合チェック・Lint・テスト（backend）・ビルド（frontend）がローカルで実行されます。
CI で弾かれる前にローカルで確認する習慣をつけてください。
