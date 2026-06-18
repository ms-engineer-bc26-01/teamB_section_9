# コーデ提案 API フロント接続メモ

## 目的

`POST /api/v1/outfits/suggest` のレスポンスに含まれるコーデ提案を、フロントエンドで正確に表示するための接続方針を整理する。

画像生成・画像表示は後続対応とし、まずは LLM が提案したコーディネートの `items` を詳細画面に表示できる状態を優先する。

---

## チーム確認済み事項

- `POST /api/v1/outfits/suggest` のレスポンスには、LLM が提案したアイテム一覧 `items` が入る想定。
- レスポンスの `outfit.id` は、現状のフロント実装でも必要。
- `outfit.id` は詳細画面への遷移、`sessionStorage` の保存キー、保存済みコーデ取得に使う。
- 今回のフロント実装では、`POST /api/v1/outfits/suggest` のレスポンスに含まれる `items` をもとに `POST /outfits` でコーデを保存し、保存済み outfit を詳細画面表示に使う。

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

### 1. `suggestOutfit()` の結果をもとに保存済み outfit を作成する

`/outfits/loading` で `suggestOutfit({ tpo })` を呼び、返ってきた `outfits[0].items` を表示用のアイテム情報として利用する。

ただし、`POST /api/v1/outfits/suggest` のレスポンスに含まれる `id` は、詳細画面をリロードしたときに `GET /outfits/{id}` で再取得できない可能性がある。

そのため、現時点のフロント実装では、`suggestOutfit()` の結果をもとに `createOutfit()` を呼び出し、保存済み outfit の `id` を詳細画面URLに渡す。

基本フローは以下。

```text
/outfits/scenes
↓
/outfits/loading?tpo=casual
↓
POST /api/v1/outfits/suggest
↓
result.outfits[0].items を受け取る
↓
POST /outfits で保存
↓
保存済み outfit を sessionStorage に保存
↓
/outfits/detail?outfitId=<savedOutfit.id>
↓
保存済み outfit.items を表示
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

### 3. 詳細画面では保存済み outfit の ID を使う

`POST /api/v1/outfits/suggest` のレスポンスに含まれる `items` は、コーデ提案の表示内容として利用する。

ただし、詳細画面の URL に渡す `outfitId` は、リロードや別タブ表示でも再取得できる必要がある。

そのため、現時点のフロント実装では、`POST /api/v1/outfits/suggest` の結果をもとに `POST /outfits` で保存し、保存済み outfit の `id` を `/outfits/detail?outfitId=...` に渡す。

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
