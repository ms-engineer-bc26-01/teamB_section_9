# クローゼット服コーデ提案ページ仕様

## 概要

トップページから登録済みのクローゼット服を使ったコーデ提案を行い、提案結果を同一ページ内に表示する。

バックエンドの提案APIは `POST /api/v1/outfits/suggest` を利用する。APIの詳細なレスポンス設計は `docs/outfit-suggest-llm.md` を正とし、本書ではフロントエンドの導線、画面状態、リクエスト、表示仕様を定義する。

## 対象URL

| 項目 | 内容 |
| --- | --- |
| ページURL | `/outfits/closet` |
| 追加導線 | トップページ `/` |
| 使用API | `POST /api/v1/outfits/suggest` |

## トップページ導線

トップページの「別のシーンで提案を見る」ボタンの下に、以下のボタンを追加する。

| 項目 | 内容 |
| --- | --- |
| 表示文言 | クローゼット服で提案を見る |
| 遷移先 | `/outfits/closet` |
| 表示位置 | 「別のシーンで提案を見る」ボタンの直下 |
| スタイル | 既存のトップページCTAと同等。必要に応じて `Shirt` などのアイコンを使用する |

## ページの目的

ユーザーがTPOを選択し、登録済みのクローゼット服をもとにコーデ提案を取得する。

既存の `/outfits/scenes` はシーン選択から提案開始へ遷移する画面だが、`/outfits/closet` は提案の入力、実行、結果表示をページ内で完結させる。

## 入力仕様

### TPO選択

TPOはユーザーに選ばせる。

初期候補は既存実装に合わせて以下の5種類とする。

| 値 | 表示ラベル | 用途 |
| --- | --- | --- |
| `business` | ビジネス | 出勤、商談、仕事向け |
| `casual` | カジュアル | 休日、買い物、普段着向け |
| `formal` | フォーマル | 会食、きれいめな外出向け |
| `ceremony` | セレモニー | 式典、行事向け |
| `leisure` | レジャー | 公園、旅行、屋外の外出向け |

初期選択値は `casual` とする。

### 地域

初期実装では画面上に地域選択を出さず、`region_code` は送信しない。

バックエンド側でログインユーザーの `default_region_code`、またはバックエンド既定値を利用する。将来的に地域を選択する場合は、このページに地域選択UIを追加し、`region_code` を送信する。

### 日付

初期実装では `date` は送信しない。

バックエンド側の現行仕様に合わせ、現在日付の天気情報で提案する。

### 服の指定

初期実装では `clothing_ids` は送信しない。

バックエンドはユーザーの登録済み服一覧を取得し、クローゼット全体から提案する。将来的に「この服を使う」を指定する場合は、服選択UIを追加し、選択した服IDを `clothing_ids` に渡す。

## APIリクエスト

提案ボタン押下時に以下を送信する。

```json
{
  "tpo": "casual"
}
```

将来拡張時の例:

```json
{
  "tpo": "business",
  "region_code": "13_01",
  "clothing_ids": ["<clothes-id>"],
  "exclude_clothing_ids": ["<clothes-id>"]
}
```

## 結果表示仕様

提案結果は `/outfits/closet` ページ内で表示する。

表示する項目は以下とする。

| 項目 | 表示内容 |
| --- | --- |
| TPO | 選択したTPOのラベル |
| コーデコメント | `outfits[0].comment` |
| アイテム一覧 | `outfits[0].items` を `display_order` 昇順で表示 |
| アイテム名 | `item.name`、なければ `item.clothing_item.name` |
| 色 | `item.color`、なければ `item.clothing_item.color` |
| 柄 | `item.pattern`、なければ `item.clothing_item.pattern` |
| 登録服判定 | `item.clothing_item` があれば登録済み服、なければ補完提案 |

登録済み服には「クローゼット服」、補完提案には「提案アイテム」などのバッジを表示する。

## 保存仕様

初期実装では、`POST /api/v1/outfits/suggest` の結果を表示するだけではDB保存しない。

ユーザーが「保存」ボタンを押した場合のみ、既存の `POST /api/v1/outfits` を呼び出して保存する。

保存時のpayloadは、既存の提案保存処理に合わせる。

```ts
{
  tpo: suggestedOutfit.tpo,
  region_code: suggestedOutfit.region_code,
  comment: suggestedOutfit.comment,
  is_favorite: false,
  items: suggestedOutfit.items.map((item) => ({
    name: item.name ?? item.clothing_item?.name ?? "アイテム名未設定",
    role: item.role,
    color: item.color,
    pattern: item.pattern,
    display_order: item.display_order,
    clothes_id: item.clothing_item?.id ?? null,
  })),
}
```

保存成功後は、同一ページ内に保存完了状態を表示する。必要であれば保存済みコーデ詳細へのリンクを表示する。

## 画面状態

| 状態 | 表示 |
| --- | --- |
| 初期表示 | TPO選択、提案実行ボタン、クローゼット服を使う旨の短い説明 |
| 提案中 | ローディング表示。ボタンは無効化 |
| 提案成功 | 結果カード、アイテム一覧、保存ボタン、再提案ボタン |
| 保存中 | 保存ボタンを無効化し、保存中表示 |
| 保存成功 | 保存完了メッセージを表示 |
| 未ログイン | ログインが必要である旨を表示 |
| 登録服0件 | 服登録ページ `/clothes/register` への導線を表示 |
| API失敗 | エラーメッセージと再試行ボタンを表示 |

## エラー仕様

| ケース | 表示方針 |
| --- | --- |
| 未ログイン | ログインが必要であることを表示 |
| クローゼット服が0件 | 登録服がないため提案できないことを表示し、服登録へ誘導 |
| `POST /outfits/suggest` が失敗 | 提案に失敗した旨を表示し、再試行可能にする |
| `POST /outfits` が失敗 | 保存に失敗した旨を表示し、結果表示は維持する |
| 提案結果が空 | 提案結果を取得できなかった旨を表示 |

## 実装対象

| 種別 | 対象 |
| --- | --- |
| トップページ | `frontend/src/app/(app)/page.tsx` |
| 新規ページ | `frontend/src/app/(app)/outfits/closet/page.tsx` |
| クライアントコンポーネント | `frontend/src/app/(app)/outfits/closet/outfit-closet-content.tsx` |
| API | `frontend/src/features/outfits/api.ts` の `suggestOutfit` / `createOutfit` を利用 |
| 服一覧取得 | `frontend/src/features/clothes/api.ts` の `fetchClothes` を利用、または共通APIクライアントへ寄せる |

## テスト観点

- トップページに「クローゼット服で提案を見る」が表示される
- ボタン押下で `/outfits/closet` に遷移する
- TPOを選択できる
- 提案ボタン押下で `POST /api/v1/outfits/suggest` が呼ばれる
- 提案成功時にコーデコメントとアイテム一覧が表示される
- 登録済み服と補完提案が区別して表示される
- 保存ボタン押下で `POST /api/v1/outfits` が呼ばれる
- 登録服0件時に `/clothes/register` への導線が表示される
- API失敗時にエラーと再試行導線が表示される

## 未決事項

- TPO候補を5種類すべて表示するか、MVPとして `business` / `casual` のみに絞るか
- 保存成功後に詳細ページへ遷移するか、同一ページ内で保存完了だけ表示するか
- 将来的にユーザーが特定の服を選んで `clothing_ids` を送るUIを追加するか
