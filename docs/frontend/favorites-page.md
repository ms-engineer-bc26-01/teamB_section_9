# お気に入り画面仕様書

## 概要

登録済みコーデのうち、お気に入りに設定されたコーデを一覧で確認する画面。
下部ナビゲーションの「お気に入り」から遷移する。

## 対象URL

| 項目 | 内容 |
| --- | --- |
| ページURL | `/favorites` |
| 認証 | 必須 |
| 主な導線 | 下部ナビゲーション `/favorites` |
| 詳細導線 | `/outfits/preview?id=<outfitId>` |

## 使用API

### お気に入り一覧取得

```http
GET /api/v1/outfits?is_favorite=true
```

フロントエンドでは既存の API 関数を利用する。

```ts
getOutfits({ isFavorite: true })
```

レスポンス:

```ts
type OutfitsListResponse = {
  items: SuggestedOutfit[];
  total: number;
};
```

### お気に入り解除

```http
PATCH /api/v1/outfits/{outfit_id}
```

フロントエンドでは既存の API 関数を利用する。

```ts
updateOutfit(outfitId, { is_favorite: false })
```

解除後は画面上の一覧から対象コーデを取り除き、件数を更新する。

## 表示仕様

### 初期表示

- ページタイトル「お気に入り」
- 補足テキスト
- 読み込み中表示

### 一覧表示

各コーデカードに以下を表示する。

- コーデ画像
  - `coordinate_image_url` がある場合は画像表示
  - ない場合はテキストベースのプレースホルダー
- TPO
- 作成日時
- コーデコメント
- アイテム一覧の先頭数件
- 詳細を見るボタン
- お気に入り解除ボタン

### 空状態

お気に入りコーデが0件の場合、以下を表示する。

- 空状態メッセージ
- `/outfits/scenes` への導線
- `/outfits/closet` への導線

### エラー状態

API取得に失敗した場合、エラーメッセージと再読み込みボタンを表示する。

## 遷移仕様

| 起点 | 操作 | 遷移先 |
| --- | --- | --- |
| 下部ナビ | お気に入りを押す | `/favorites` |
| お気に入りカード | 詳細を見る | `/outfits/preview?id=<outfitId>` |
| 空状態 | シーンを選ぶ | `/outfits/scenes` |
| 空状態 | クローゼット服で提案 | `/outfits/closet` |

## 実装対象

| ファイル | 内容 |
| --- | --- |
| `frontend/src/app/(app)/favorites/page.tsx` | お気に入り画面本体 |
| `frontend/src/components/layout/BottomNavigation.tsx` | `/favorites` の現在地表示 |
| `frontend/src/components/layout/Header.tsx` | ページタイトル追加 |

## 補足

- 一覧からの詳細表示は保存済みコーデの取得に向いている `/outfits/preview?id=...` を利用する。
- `/outfits/detail` は提案直後の `sessionStorage` 利用が混ざるため、一覧系画面からは原則使わない。
