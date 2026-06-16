# コーデ提案（LLM）設計メモ — クローゼット参照ハイブリッド

対象エンドポイント: `POST /api/v1/outfits/suggest`
関連実装: `backend/app/domain/outfits/service.py` / `backend/app/prompts/outfit_suggest.md` /
`backend/app/api/v1/routers/outfits.py` / `backend/app/api/v1/schemas/outfits.py`

## 目的

ユーザーのクローゼット（登録済みの服）を使って、その日の天気・TPO に合ったコーディネートを
LLM に提案させる。まずはテキストベースの提案を正確に表示できることを優先する（画像生成は後続）。

- ① 該当アカウントの登録アイテムを取り出す
- ② 取り出した一覧から LLM がコーディネート提案を作る

## 方式：ハイブリッド選定

1. クローゼットを **id 付き** でプロンプトに渡す（`_format_clothes` が `id=<uuid>` を含めて整形）。
2. LLM は **手持ち服を優先** して選定し、選んだ服の `clothes_id` を返す。
3. 手持ちで埋まらないカテゴリ（role）に限り、**補完アイテムを提案**してよい（`clothes_id=null`）。
4. バックエンドは `clothes_id` をユーザー所有の服に解決する：
   - 一致 → `clothing_item` に服詳細（id・image_url 等）を設定
   - 不一致 / null → `clothing_item=null`（name/role/color/pattern のみの補完提案）

### リクエスト指定の扱い

- `exclude_clothing_ids`: プロンプトに渡す前にクローゼット候補から除外。
- `clothing_ids`: 「必ず含める服」として id 付きでプロンプトに明記（`_format_must_include`）。

## レスポンス形状

`outfits` のみを返す（旧 `weather_summary` / `region_used` / `cached` / `source` は廃止）。
天気は提案入力としては利用するが、レスポンスには含めない。

```jsonc
{
  "outfits": [
    {
      "id": "<uuid（一時生成）>",
      "user_id": "<uuid>",
      "tpo": "casual",
      "comment": "コーデのポイント…",
      "is_favorite": false,
      "items": [
        {
          "name": "白いリネンシャツ",
          "role": "tops",
          "color": "白",
          "pattern": "無地",
          "display_order": 1,
          "clothing_item": { /* 手持ちなら ClothingItem 全体、補完提案なら null */ }
        }
      ],
      "created_at": "2026-06-16T…"
    }
  ]
}
```

スキーマ定義は `SuggestOutfit` / `SuggestOutfitItem`（`schemas/outfits.py`）。
保存済みコーデ一覧（`GET /outfits`）は別スキーマ `SuggestedOutfit` を維持（DB 由来のため）。

## スコープと今後

- **現状は DB 保存しない**（テキスト表示優先）。`id` / `created_at` はレスポンス用に一時生成する。
- 履歴化（`outfits` + `outfit_items` への保存）と提案結果キャッシュ（Redis TTL24h）は後続
  「コーデ提案 CRUD 実装」で対応。
- そのときの永続化設計は、手持ちでない補完アイテムも保存できるよう
  `outfit_items.clothes_id` を nullable 化し、`source_type`(owned/suggested) と
  `item_snapshot`(JSONB) を追加する想定（前方互換：本レスポンスの item 形状がそのまま対応する）。

## 関連 PR との関係（注意）

同一エンドポイントを Miwa さんが別方向で改修中：

- PR #99 `feat/be-outfit-suggest`: クローゼット非参照・DB保存なしで LLM が自由にアイテムを
  文字生成（`clothing_item` は常に null）。→ 本設計（クローゼット参照ハイブリッド）と方向が異なる。
- PR #97 `feat/be-llm-response`: LLM へ渡す天気情報の縮約。

→ マージ前にレスポンス契約をどちらに寄せるかチームで合意すること。
