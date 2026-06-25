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

## スマホ実機での表示確認

同じ Wi-Fi に繋いだスマホの実機でアプリを確認できます。サーバは既に全インターフェイスで待ち受けている
（backend は `--host 0.0.0.0`、Next dev は起動時に `Network: http://<IP>:3000` を表示）ため、設定は最小限です。

1. **ホスト PC の LAN IP を調べる**（Windows）

   ```powershell
   ipconfig
   ```

   `IPv4 アドレス`（例: `192.168.1.20`）を控える。

2. **フロントの API 向き先をホスト IP に変更**

   `frontend/.env.local`（または `.env`）で:

   ```dotenv
   NEXT_PUBLIC_API_BASE_URL=http://192.168.1.20:8000/api/v1
   ```

   変更後はフロントを再起動する。

3. **CORS は編集不要（開発時のみ自動許可）**

   `APP_ENV=development` のとき、バックエンドは LAN IP:3000（`192.168.*` / `10.*` / `172.16-31.*`）からの
   アクセスを自動許可します。`BACKEND_CORS_ORIGINS` を IP 毎に編集する必要はありません。
   （本番では自動許可は無効。明示した許可オリジンのみ。）

4. **スマホを同じ Wi-Fi に繋ぎ、ブラウザで開く**

   ```text
   http://192.168.1.20:3000
   ```

5. **つながらない場合**
   - スマホと PC が**同じ Wi-Fi**か確認（ゲスト SSID は端末間通信が遮断されることがある）。
   - Windows ファイアウォールで **inbound の 3000 / 8000** を許可（初回アクセス時のダイアログで「許可」）。
   - `NEXT_PUBLIC_API_BASE_URL` を `localhost` のままにしていないか確認（スマホからは到達不可）。

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

GitHub Actions と同じ依存整合チェック・Lint・テスト（backend）・ビルド（frontend）がローカルで実行されます。
CI で弾かれる前にローカルで確認する習慣をつけてください。
