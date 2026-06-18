# コーデ提案 API フロント接続メモ

## 目的

`POST /api/v1/outfits/suggest` のレスポンスに含まれるコーデ提案を、フロントエンドで正確に表示するための接続方針を整理する。

画像生成・画像表示は後続対応とし、まずは LLM が提案したコーディネートの `items` を詳細画面に表示できる状態を優先する。

---

## チーム確認済み事項

- `POST /api/v1/outfits/suggest` のレスポンスには、LLM が提案したアイテム一覧 `items` が入る想定。
- レスポンスの `outfit.id` は、現状のフロント実装でも必要。
- `outfit.id` は詳細画面への遷移、`sessionStorage` の保存キー、保存済みコーデ取得に使う。
- 今回のフロント実装では、`POST /api/v1/outfits/suggest` のレスポンスをそのまま詳細画面表示に使う。

---

## フロントで表示したいレスポンス形状

```jsonc
{
  "outfits": [
    {
      "id": "00000000-0000-0000-0000-000000000777",
      "user_id": "00000000-0000-0000-0000-000000000123",
      "tpo": "casual",
      "comment": "軽やかな白シャツと黒パンツを合わせたカジュアルコーデです。",
      "is_favorite": false,
      "items": [
        {
          "name": "白シャツ",
          "role": "tops",
          "color": "white",
          "pattern": "plain",
          "display_order": 1,
          "clothing_item": null,
        },
        {
          "name": "黒パンツ",
          "role": "bottoms",
          "color": "black",
          "pattern": "plain",
          "display_order": 2,
          "clothing_item": null,
        },
      ],
      "created_at": "2026-06-04T00:00:00Z",
    },
  ],
}
```

---

## フロント実装方針

### 1. suggestOutfit() の結果を詳細画面表示に使う

`/outfits/loading` で `suggestOutfit({ tpo })` を呼び、返ってきた `outfits[0]` を詳細画面表示に使う。

基本フローは以下。

```text
/outfits/scenes
↓
/outfits/loading?tpo=casual
↓
POST /api/v1/outfits/suggest
↓
result.outfits[0] を sessionStorage に保存
↓
/outfits/detail?outfitId=<outfit.id>
↓
result.outfits[0].items を表示
```

### 2. items をコーデ詳細画面に表示する

コーデ詳細画面では、`outfits[0].items` を `display_order` 順に並べて表示する。

表示対象の候補は以下。

- `role`
- `name`
- `color`
- `pattern`
- `clothing_item` の有無による「手持ちの服 / 提案アイテム」の区別

`clothing_item` が `null` の場合でも、`name` / `role` / `color` / `pattern` を使って表示できるようにする。

### 3. POST /outfits の追加呼び出しは行わない

今回のフロント実装では、`POST /api/v1/outfits/suggest` のレスポンスに含まれる `outfits[0]` をそのまま詳細画面表示に使う。

そのため、`/outfits/loading` では追加で `POST /outfits` を呼ばない。

---

## フロント側の主な対象ファイル

```text
frontend/src/features/outfits/types.ts
frontend/src/app/(app)/outfits/loading/outfit-loading-content.tsx
frontend/src/app/(app)/outfits/detail/outfit-detail-content.tsx
```

---

## 実装時の確認ポイント

- `items` が空でない場合に、アイテム一覧が表示されること。
- `clothing_item: null` の提案アイテムでも、アイテム名が表示されること。
- `display_order` 順に表示されること。
- `color` / `pattern` が `null` または未指定でも画面が崩れないこと。
- `outfit.id` を使って詳細画面へ遷移できること。

---

## 今は対象外

- コーディネート画像生成
- コーディネート画像表示
- 服画像アップロード
- 画面ベース作成
- 大きなデザイン変更

---

## 保存する

貼り付けたら保存してください。

### Mac の場合

```text
Cmd + S
```

### Windows / Linux の場合

```text
Ctrl + S
```

---

## 保存できたか確認する

保存したら、ターミナルで以下を実行してください。

```bash
git status
```

### 期待する表示

次のように出れば OK です。

```text
Untracked files:
  docs/frontend/outfit-suggest-integration.md
```

また、今までの 2 ファイルも引き続き表示される想定です。

```text
modified:
  frontend/src/app/(app)/outfits/detail/outfit-detail-content.tsx
  frontend/src/app/(app)/outfits/loading/outfit-loading-content.tsx
```
