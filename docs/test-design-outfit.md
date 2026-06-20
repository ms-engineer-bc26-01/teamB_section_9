# コーデ（Outfit）テスト設計書

最終更新: 2026-06-19 / 対象: backend コーデ提案・保存（CRUD）+ コラージュ画像生成

## 1. 目的・対象範囲

コーデ提案（`POST /outfits/suggest`）と保存済みコーデの CRUD（`POST/GET/PATCH /outfits`）、
およびコラージュ画像生成統合・token 使用量計測のテスト観点を整理する。

| レイヤ | テストファイル |
|---|---|
| CRUD / API（保存・一覧・取得・更新） | `backend/tests/test_outfit_crud.py` |
| 提案サービス・API / 一覧取得 | `backend/tests/test_outfits.py` |
| 画像生成オーケストレーション | `backend/tests/test_outfit_image_service.py` |
| 画像生成クライアント | `backend/tests/test_image_client.py` |
| Storage アップロード | `backend/tests/test_storage_client.py` |
| 画像プロンプト生成 | `backend/tests/test_image_prompt_builder.py` |
| token 使用量ログ | `backend/tests/test_usage.py` |
| LLM クライアント結線（usage ログ発火） | `backend/tests/test_llm_client.py` |

方針: 外部依存（DB / OpenAI / Supabase Storage）は `monkeypatch` で Fake 置換し、
DB/ネットワーク不要のユニット〜結合テストとして実行する（`conftest.py` の `client` /
`stub_user_sync` を共用）。

## 2. CRUD テスト観点

### 2.1 アイテム表示解決（`_to_outfit_item_schema`）

| # | 観点 | 入力 | 期待結果 | テスト |
|---|---|---|---|---|
| 1 | owned は DB 値で表示 | `clothes` 解決済み | `clothing_item` あり・name/color が DB 値 | `test_to_outfit_item_schema_owned_uses_db_values` |
| 2 | suggested は snapshot 表示 | `clothes=None`, snapshot あり | `clothing_item=None`・snapshot 値 | `test_to_outfit_item_schema_suggested_uses_snapshot` |
| 3 | owned 服削除後も履歴保持 | `clothes=None`（SET NULL）, snapshot あり | snapshot から name/color を表示継続 | `test_to_outfit_item_schema_owned_deleted_falls_back_to_snapshot` |

### 2.2 保存（`POST /outfits`）

| # | 観点 | 期待結果 | テスト |
|---|---|---|---|
| 4 | 正常保存 | 201・owned/suggested の clothes_id が `OutfitCreateItem` で渡る | `test_create_outfit_persists_and_returns_201` |
| 5 | 不正 region_code | 400 `invalid region_code` | `test_create_outfit_rejects_invalid_region` |
| 6 | 他人の服を指定 | `OutfitItemNotOwnedError` → 400 | `test_create_outfit_rejects_not_owned_clothes` |
| 7 | items 空配列 | 422（バリデーション） | `test_create_outfit_rejects_empty_items` |

### 2.3 一覧・取得・更新

| # | 観点 | 期待結果 | テスト |
|---|---|---|---|
| 8 | 一覧取得（`GET /outfits`） | 200・`items`/`total` 返却（ページング・`is_favorite` フィルタ対応） | `test_list_outfits_returns_items_and_total` |
| 9 | 存在しない取得 | 404 | `test_get_outfit_returns_404_when_missing` |
| 10 | 取得成功 | 200・id 一致 | `test_get_outfit_returns_outfit` |
| 11 | is_favorite 切替 | 200・値反映 | `test_patch_outfit_toggles_favorite` |
| 12 | 存在しない更新 | 404 | `test_patch_outfit_returns_404_when_missing` |

## 3. コラージュ画像生成統合の観点

### 3.1 API 統合（`POST /outfits` の best-effort 画像生成）

| # | 観点 | 期待結果 | テスト |
|---|---|---|---|
| 13 | 生成成功 | 201・`coordinate_image_url` が保存・返却される | `test_create_outfit_sets_coordinate_image_url_on_success` |
| 14 | 生成失敗（best-effort） | 201・`coordinate_image_url=null`・URL 保存は呼ばれない | `test_create_outfit_succeeds_without_image_when_generation_fails` |

### 3.2 オーケストレーション（`image_service.generate_coordinate_image_url`）

| # | 観点 | 期待結果 | テスト |
|---|---|---|---|
| 15 | 正常系 | PromptBuilder→生成→アップロードを束ね公開 URL を返す・path=`outfits/{id}.png` | `test_generate_coordinate_image_url_success` |
| 16 | 画像生成エラー | `ImageGenerationError` → None（保存は継続） | `test_generate_coordinate_image_url_returns_none_on_image_error` |
| 17 | アップロード失敗 | `StorageError` → None | `test_generate_coordinate_image_url_returns_none_on_storage_error` |
| 18 | API キー未設定 | `ValueError` → None | `test_generate_coordinate_image_url_returns_none_when_api_key_missing` |

### 3.3 構成要素ユニット

| # | 観点 | 期待結果 | テスト |
|---|---|---|---|
| 19 | プロンプトに全 item 反映 | name/role/comment が含まれる | `test_build_image_prompt_includes_all_item_names_and_roles` |
| 20 | display_order 昇順整形 | 並び順が保たれる | `test_build_image_prompt_orders_items_by_display_order` |
| 21 | null color/pattern 省略 | 括弧注記を出さない | `test_build_image_prompt_omits_null_color_and_pattern` |
| 22 | comment 欠落フォールバック | 既定文言が入る | `test_build_image_prompt_uses_default_comment_when_empty` |
| 23 | 画像生成 正常 | b64 をデコードし bytes 返却・model/size/prompt 反映 | `test_generate_image_returns_decoded_bytes` |
| 24 | 画像生成 APIError ラップ | `ImageGenerationError`（`__cause__` に APIError） | `test_generate_image_wraps_api_error` |
| 25 | 空レスポンス | `ImageGenerationError`（no data / no image content） | `test_generate_image_raises_on_empty_data` ほか |
| 26 | Storage 公開 URL 組み立て | `.../object/public/{bucket}/{path}`・認証ヘッダ・upsert | `test_upload_image_returns_public_url_and_uploads` |
| 27 | Storage 未設定 | `StorageError`（not configured） | `test_upload_image_raises_when_not_configured` |
| 28 | Storage HTTP エラー | `StorageError`（failed to upload） | `test_upload_image_wraps_http_error` |

## 4. token 使用量計測の観点

`log_llm_usage` は出力フィールドを allowlist 固定し、LLM 呼び出し種別（`op`）・モデル名・
token 数のみを構造化ログに出す。ドメイン操作を表す `usage_logs.action` とは別概念のため
キー名を `op=` に分けている。

| # | 観点 | 期待結果 | テスト |
|---|---|---|---|
| 29 | usage を構造化ログ出力 | `op`/`model`/`input`/`output`/`total_tokens` がログに出る | `test_log_llm_usage_emits_tokens` |
| 30 | usage=None は no-op | ログを出さない | `test_log_llm_usage_noop_when_usage_none` |
| 31 | 欠損フィールド耐性 | 例外を出さず `None` 表記（`total_tokens` を計算で補完しない） | `test_log_llm_usage_handles_missing_fields` |
| 32 | client→ログ結線 | `generate_structured` が usage 付きレスポンスで `op=generate_structured` を発火 | `test_generate_structured_logs_token_usage` |
| 33 | prompt/response 非漏洩 | ログに prompt 本文・response 本文が混入しない（allowlist 担保） | `test_log_llm_usage_does_not_leak_prompt_or_response` |

## 5. 未カバー / 後続課題（TODO）

- 永続集計（UsageLog テーブルへの token 保存・コスト集計）。user_id 配管 +
  token カラムマイグレーションが前提。
- 実 OpenAI / Supabase を用いた E2E スモーク（手動）。`coordinate_image_url` が
  有効な公開 URL を指し画像表示できること。
- 同一コーデ再保存時の画像 upsert 挙動（`x-upsert: true`）の結合確認。

## 6. 実行方法

```bash
cd backend
APP_ENV=test \
DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/closet_test \
REDIS_URL=redis://localhost:6379/0 \
GOOGLE_API_KEY=test_dummy \
uv run pytest -v --tb=short
```

CI: `.github/workflows/ci.yml` が ruff(lint/format) + pytest を上記ダミー環境変数で実行する。
