# コーデ画像生成 実環境 E2E スモークテスト手順（Issue #125）

> 対象: バックエンドのコラージュ画像生成（保存 → 背景タスク → OpenAI 画像生成 → Supabase Storage アップロード → `coordinate_image_url` 反映）
> 種別: **手動スモーク**（実 OpenAI / 実 Supabase を使用）。CI の単体テストは外部依存を Fake 置換しているため本経路は未カバー。
> 関連: #123（テスト設計）, #124（token 永続集計）

---

## 0. 確認したいこと（受け入れ条件）

1. コーデ保存後、背景タスク完了で `coordinate_image_url` が **有効な公開 URL** になり、その URL が **200 / PNG** を返す（フロントで表示可能）。
2. 同一 `outfit_id` の画像を再生成したとき、Storage の同一パス `outfits/{outfit_id}.png` が **上書き（upsert）** される（`x-upsert: true`）。

> ⚠️ **重要な前提（テスト設計上の注意）**
> `POST /api/v1/outfits` は **毎回新しい `outfit_id`** を発行するため、UI から「同じコーデをもう一度保存」しても
> 書き込み先は別パス `outfits/{別id}.png` になり、**upsert（同一パス上書き）は発火しません**。
> 現状 “同一 outfit の画像再生成” を行う API エンドポイントは無いため、受け入れ条件 2 は
> **Storage 層を直接叩く検証（手順 B）** で確認します。

---

## 1. 必要な環境変数（リポジトリルートの `.env`）

`docker-compose.yml` は frontend / backend とも **リポジトリルートの `.env`**（`env_file: .env`）を読む。
代表者（C）から Slack DM で受け取る値を設定（`docs/setup.md` 参照）。本スモークで必須なのは以下。

> backend 起動に必須の `DATABASE_URL` などは `.env.example` の既定値が前提（`cp .env.example .env` で引き継がれる）。
> 本表は画像生成スモークに直接効く変数のみを抜粋。

| 変数 | 用途 | 既定 / 例 |
|---|---|---|
| `OPENAI_API_KEY` | 画像生成（必須） | Slack DM |
| `OPENAI_IMAGE_MODEL` | 画像モデル | `gpt-image-1-mini` |
| `OPENAI_IMAGE_QUALITY` | 画質（コスト/時間に影響） | `medium` |
| `OPENAI_IMAGE_SIZE` | 画像サイズ | `1024x1024` |
| `OPENAI_IMAGE_TIMEOUT_SECONDS` | 生成タイムアウト | `60` |
| `SUPABASE_URL` | Storage アップロード（必須） | Slack DM |
| `SUPABASE_SERVICE_ROLE_KEY` | アップロード認可（RLS バイパス・必須） | Slack DM |
| `SUPABASE_STORAGE_BUCKET` | 保存先バケット | `clothes-images` |
| `APP_ENV` | 開発判定 | `development` |
| `AUTH_BYPASS_ENABLED` | 認証バイパス（ローカル検証用） | `true`（後述） |

> いずれか未設定だと best-effort 経路で握り潰され、`coordinate_image_url` が **null のまま**になる（[§5 切り分け](#5-失敗時の切り分けbest-effort)）。

---

## 2. 事前準備

### 2-1. 起動

```bash
cp .env.example .env   # 値を Slack DM から貼り付け（OPENAI / SUPABASE を実値に）
docker compose up -d --build
# 確認: http://localhost:8000/docs が開ける
```

### 2-2. 認証（どちらかを選ぶ）

- **A. 認証バイパス（ローカル検証が手軽）**: `.env` で `APP_ENV=development` かつ `AUTH_BYPASS_ENABLED=true`。
  - 認証ヘッダ不要。固定モックユーザー（`id=00000000-0000-0000-0000-000000000001`）として動作。
  - 実装: `backend/app/dependencies/auth.py`（`_is_auth_bypass_enabled()`）。
- **B. 実 JWT**: フロントでログインして得た Supabase JWT を `Authorization: Bearer <token>` で送る。

> 以降の例は **A（バイパス）** 前提。B の場合は各 `curl` に `-H "Authorization: Bearer <jwt>"` を足す。

---

## 3. 手順 A: 公開 URL 表示の確認（受け入れ条件 1）

### A-1. コーデを保存（背景タスクが起動）

```bash
curl -s -X POST http://localhost:8000/api/v1/outfits \
  -H "Content-Type: application/json" \
  -d '{
    "tpo": "casual",
    "region_code": "13_01",
    "comment": "スモークテスト",
    "is_favorite": false,
    "items": [
      {"name": "白T", "role": "top", "color": "white", "pattern": null, "display_order": 0, "clothes_id": null},
      {"name": "デニム", "role": "bottom", "color": "blue", "pattern": null, "display_order": 1, "clothes_id": null}
    ]
  }'
```

- 期待: **201**、レスポンスに `id` が含まれ、`coordinate_image_url` は **null**（即時返却・画像は背景生成）。
- 返ってきた `id` を控える（以下 `OUTFIT_ID`）。

### A-2. 背景タスク完了後に URL を確認

数〜数十秒待ってから取得（OpenAI + Supabase のレイテンシ依存）:

```bash
OUTFIT_ID="<A-1で控えたid>"
curl -s http://localhost:8000/api/v1/outfits/$OUTFIT_ID | python -m json.tool
```

- 期待: `coordinate_image_url` が
  `https://<project>.supabase.co/storage/v1/object/public/clothes-images/outfits/<OUTFIT_ID>.png`
  形式の **公開 URL** になっている。
- まだ null の場合は数秒待って再取得（生成中）。一定時間経っても null ならログを確認（§4）。

### A-3. 公開 URL が実体（PNG）を返すか

```bash
URL="<A-2で得た coordinate_image_url>"
curl -s -o /tmp/outfit.png -w "HTTP=%{http_code} TYPE=%{content_type} SIZE=%{size_download}\n" "$URL"
```

- 期待: `HTTP=200`、`TYPE=image/png`、`SIZE` が 0 でない。
- フロント（履歴・詳細画面）で当該コーデのカードに画像が表示されることも目視確認。

---

## 4. 手順 B: upsert（同一パス上書き）の確認（受け入れ条件 2）

§0 の前提どおり、API 経由では同一パスを再生成できないため、**Storage クライアントを直接呼ぶ**。
`backend` コンテナ内で実行（実 `SUPABASE_*` が読まれる）:

```bash
docker compose exec backend uv run python - <<'PY'
import asyncio
from app.services.storage_client import upload_image

# 既存の OUTFIT_ID を使うと本物のコーデ画像を上書きしてしまうため、検証用パスを使う
PATH = "outfits/SMOKE-UPSERT-TEST.png"
RED  = bytes.fromhex(  # 1x1 赤 PNG
  "89504e470d0a1a0a0000000d49484452000000010000000108020000009077"
  "53de0000000c4944415408d763f8cfc0000000030001ffff7f0c0000000049"
  "454e44ae426082")
BLUE = bytes.fromhex(  # 1x1 青 PNG
  "89504e470d0a1a0a0000000d49484452000000010000000108020000009077"
  "53de0000000c4944415408d76360f8ff1f0000040001ffff5c0c0000000049"
  "454e44ae426082")

async def main():
    u1 = await upload_image(path=PATH, data=RED)   # 1回目
    u2 = await upload_image(path=PATH, data=BLUE)   # 同一パスへ2回目（x-upsert: true）
    print("url1:", u1)
    print("url2:", u2)
    assert u1 == u2, "同一パスなら同一公開URLのはず"
    print("OK: 2回目のアップロードが 409 にならず上書きされた（upsert 有効）")

asyncio.run(main())
PY
```

- 期待: 例外なく完了し `OK: ...` が出る。`x-upsert: true` が無ければ 2 回目は Supabase が
  `409 Duplicate`（`StorageError`）になる。
- 追加確認（任意）: 公開 URL を `curl` し、2 回目にアップした **青** の内容（Content-Length が RED と異なる）になっていれば上書き成立。

  ```bash
  # SUPABASE_URL / SUPABASE_STORAGE_BUCKET は .env の値に置換（バケットを変えている環境にも追従）
  BUCKET="${SUPABASE_STORAGE_BUCKET:-clothes-images}"
  curl -s -o /tmp/upsert.png -w "HTTP=%{http_code} SIZE=%{size_download}\n" \
    "$SUPABASE_URL/storage/v1/object/public/$BUCKET/outfits/SMOKE-UPSERT-TEST.png"
  ```

- 後始末（任意）: 検証オブジェクトを Storage（Supabase ダッシュボード）から削除。

---

## 5. 失敗時の切り分け（best-effort）

画像生成は **best-effort**（失敗してもコーデ保存自体は成功し、`coordinate_image_url=null` のまま）。
背景タスクのログ（`docker compose logs -f backend`）で失敗フェーズを確認できる。

| フェーズ | 失敗ログ例 | よくある原因 |
|---|---|---|
| `prompt_build` | プロンプト生成失敗（API 未呼び出し） | テンプレート/入力不備 |
| `image_generate` | `ImageGenerationError` | `OPENAI_API_KEY` 未設定/無効、課金上限、タイムアウト |
| `storage_upload` | `StorageError` | `SUPABASE_URL`/`SERVICE_ROLE_KEY` 未設定、バケット権限、`x-upsert` 無効時の 409 |

- コード参照: `backend/app/domain/outfits/image_service.py`（`generate_coordinate_image_url` / `generate_and_store_coordinate_image`）、
  `backend/app/services/storage_client.py`（`upload_image` / `build_public_url`）、
  `backend/app/services/image_client.py`（`OpenAIImageClient`）。
- `coordinate_image_url` の格納先: `backend/app/db/models/outfit.py`（`String(512)`、nullable）。

---

## 6. チェックリスト（実行記録用）

- [ ] `.env` に実 `OPENAI_*` / `SUPABASE_*` を設定し `docker compose up` 成功
- [ ] A-1: `POST /api/v1/outfits` が 201、`coordinate_image_url=null`
- [ ] A-2: しばらく後の `GET /api/v1/outfits/{id}` で `coordinate_image_url` が公開 URL
- [ ] A-3: 公開 URL が `HTTP=200` / `image/png` を返す＋フロントで画像表示
- [ ] B: 同一パス 2 回アップロードが 409 にならず上書き（upsert 有効）
- [ ] （任意）検証用 `SMOKE-UPSERT-TEST.png` を削除

---

## 7. 補足（コスト・運用）

- 画像生成は OpenAI 課金が発生する。スモークは最小回数で。`OPENAI_IMAGE_QUALITY` を下げると時間・コストを抑えられる。
- token / コストの永続集計は #124（別タスク・金額換算は未対応）。
- 公開バケット前提で URL を組み立てている（署名 URL 化は follow-up）。バケットの public 設定が前提。
