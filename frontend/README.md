# Climo Frontend

Climo のフロントエンドアプリケーションです。

Climo は「天気 × TPO × 手持ちの服」から、その日に合うコーディネート選びをサポートするクローゼット管理アプリです。

> 朝の服選び、もう迷わない。

## 概要

このディレクトリは、Climo の Next.js フロントエンドを管理します。

主な役割は以下です。

- Supabase Auth を利用したログイン / 新規登録
- 認証済みユーザー向け画面の表示
- FastAPI バックエンドとの API 通信
- 登録済みの服一覧表示
- 服登録画面の UI
- 天気・TPO に合わせたコーデ提案画面の UI
- スマホファーストの共通レイアウト / ナビゲーション
- UI コンポーネントのサンプル確認

## 技術スタック

| 項目             | 内容                                              |
| ---------------- | ------------------------------------------------- |
| Framework        | Next.js App Router                                |
| Language         | TypeScript                                        |
| UI               | React / Tailwind CSS / shadcn-ui style components |
| Icons            | lucide-react / Hugeicons                          |
| Auth             | Supabase Auth                                     |
| State Management | Zustand                                           |
| API Client       | fetch wrapper                                     |
| E2E              | Playwright                                        |
| Package Manager  | npm                                               |

> このリポジトリでは npm のみを使用します。
> CI と Docker が `package-lock.json` に依存しているため、Yarn / pnpm / Bun は使用しないでください。

## 前提条件

ローカルで起動する前に、以下を準備してください。

- Node.js 24 系
- npm 11 系
- Git
- 必要に応じて Docker Desktop
- Supabase の接続情報
- バックエンド API の起動環境

## セットアップ

### 1. リポジトリをクローン

```bash
git clone git@github.com:ms-engineer-bc26-01/teamB_section_9.git
cd teamB_section_9/frontend
```

### 2. 依存関係をインストール

```bash
npm install
```

### 3. 環境変数を設定

フロントエンド単体で起動する場合は、`frontend/.env.local` を作成してください。

```bash
cp ../.env.example .env.local
```

最低限、以下の値を設定します。

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your-supabase-publishable-key
```

| 環境変数                               | 用途                                  |
| -------------------------------------- | ------------------------------------- |
| `NEXT_PUBLIC_API_BASE_URL`             | FastAPI バックエンドの API ベース URL |
| `NEXT_PUBLIC_SUPABASE_URL`             | Supabase プロジェクト URL             |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Supabase の publishable key           |

> `NEXT_PUBLIC_*` の値はブラウザに公開されます。
> secret key や service role key は設定しないでください。

### 4. 開発サーバーを起動

```bash
npm run dev
```

ブラウザで以下にアクセスします。

```txt
http://localhost:3000
```

## Docker Compose で起動する場合

プロジェクトルートから起動します。

```bash
cd ..
cp .env.example .env
docker compose up --build
```

起動後の接続先は以下です。

| サービス    | URL                        |
| ----------- | -------------------------- |
| Frontend    | http://localhost:3000      |
| Backend API | http://localhost:8000      |
| Swagger UI  | http://localhost:8000/docs |
| PostgreSQL  | localhost:5432             |
| Redis       | localhost:6379             |

停止する場合は以下を実行します。

```bash
docker compose down
```

DB ボリュームも削除する場合は以下を実行します。

```bash
docker compose down -v
```

## npm scripts

| コマンド             | 内容                          |
| -------------------- | ----------------------------- |
| `npm run dev`        | Next.js 開発サーバーを起動    |
| `npm run build`      | 本番ビルドを実行              |
| `npm run start`      | ビルド済みアプリを起動        |
| `npm run lint`       | ESLint を実行                 |
| `npm run type-check` | TypeScript の型チェックを実行 |

PR 作成前は以下を実行することを推奨します。

```bash
npm run lint
npm run type-check
npm run build
```

リポジトリ全体のチェックを行う場合は、プロジェクトルートで以下を実行します。

```bash
make check
```

## ディレクトリ構成

```txt
frontend/
├── public/                  # 静的ファイル
├── src/
│   ├── app/                 # Next.js App Router
│   │   ├── (app)/           # 認証が必要な画面
│   │   ├── login/           # ログイン画面
│   │   ├── register/        # 新規登録画面
│   │   ├── api-call-sample/ # API 通信サンプル
│   │   └── ui-sample/       # 共通 UI サンプル
│   ├── components/          # 共通コンポーネント
│   │   ├── auth/            # 認証関連コンポーネント
│   │   ├── clothes/         # 服関連コンポーネント
│   │   ├── layout/          # Header / Footer / BottomNavigation
│   │   ├── outfit/          # コーデ関連コンポーネント
│   │   └── ui/              # 汎用 UI コンポーネント
│   ├── features/            # 機能単位の API / 型定義
│   ├── lib/                 # 共通ライブラリ
│   │   └── api/             # API client / fetcher
│   └── stores/              # Zustand store
├── tests/
│   └── e2e/                 # Playwright E2E テスト
├── package.json
├── package-lock.json
├── next.config.ts
├── tsconfig.json
├── eslint.config.mjs
└── playwright.config.ts
```

## 関連ドキュメント

- [コーデ提案 API フロント接続メモ](../docs/frontend/outfit-suggest-integration.md)

## 画面一覧

この一覧は、現在のフロントエンド実装状況をもとに整理したものです。

API 欄は、`NEXT_PUBLIC_API_BASE_URL` 配下の相対パスで記載しています。

例: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1` の場合、`/auth/me` は `http://localhost:8000/api/v1/auth/me` を指します。

> 状態はフロントエンド実装の現在地を表します。
> 「実装済み」は画面または主要な表示・導線がある状態、
> 「API 接続中」は画面表示に加えて API 接続が進んでいる状態、
> 「未実装」は対応ルートまたは画面がまだない状態です。

| 画面ID | 画面名               | URL                      | 公開 / 認証 | 目的                                                            | 主な表示内容                                                         | 主な操作・遷移                               | API / 外部連携                                                  | 状態         |
| ------ | -------------------- | ------------------------ | ----------- | --------------------------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------- | --------------------------------------------------------------- | ------------ |
| UI-001 | ログイン画面         | `/login`                 | 公開        | 登録済みユーザーがログインする                                  | メールアドレス、パスワード、ログイン導線                             | ログイン、新規登録画面へ移動                 | Supabase Auth `signInWithPassword`                              | 実装済み     |
| UI-002 | アカウント登録画面   | `/register`              | 公開        | 新規ユーザーがアカウント登録する                                | 表示名、メールアドレス、パスワード、確認用パスワード                 | 登録、ログイン画面へ戻る                     | Supabase Auth `signUp`                                          | 実装済み     |
| UI-003 | ホーム画面           | `/`                      | 認証        | 今日の天気とおすすめコーデを確認する                            | 今日の日付、天気、気温、おすすめコーデ、登録服数、提案数             | シーン選択画面へ移動、コーデ確認画面へ移動   | `GET /auth/me`、`GET /weather/forecast`、`GET /outfits`         | API 接続中   |
| UI-004 | シーン選択画面       | `/outfits/scenes`        | 認証        | コーデ提案に使う利用シーンを選択する                            | ビジネス、カジュアル、フォーマル、セレモニー、レジャー               | 選択したシーンで提案生成中画面へ移動         | `POST /outfits/suggest` へつなぐ導線                            | 実装済み     |
| UI-005 | 提案生成中画面       | `/outfits/loading`       | 認証        | AI がコーデを生成している間の待機状態を表示する                 | ローディング表示、エラー表示                                         | コーデ提案取得後、詳細画面へ移動             | `POST /outfits/suggest`、`POST /outfits`                        | API 接続中   |
| UI-006 | コーデ詳細画面       | `/outfits/detail`        | 認証        | 提案されたコーデの内容とポイントを確認する                      | コーデタイトル、天気情報、TPO、アイテム一覧、コーデのポイント        | 保存、別案を見る、ホームへ戻る               | `GET /outfits/{id}`、保存済み outfit の表示                     | API 接続中   |
| UI-007 | マイページ画面       | `/mypage`                | 認証        | 登録情報や各種メニューへの入口を表示する                        | 表示名、メールアドレス、服登録件数、お気に入りコーデ数、設定ボタン   | 設定画面へ移動                               | `GET /auth/me`、`GET /clothes`、`GET /outfits?is_favorite=true` | 実装済み     |
| UI-008 | 登録した服一覧画面   | `/clothes`               | 認証        | ユーザーが登録した服を一覧で確認する                            | 登録済みの服一覧、未登録時メッセージ、服カード                       | 服登録画面へ移動                             | `GET /clothes`                                                  | API 接続済み |
| UI-009 | 服登録画面           | `/clothes/register`      | 認証        | 手入力で服情報を登録する                                        | 画像登録エリア、服名、カテゴリ、色、サイズ、柄、季節、TPO、メモ      | 服一覧へ戻る、服を登録する                   | `POST /clothes`                                                 | API 接続済み |
| UI-010 | 画像登録画面         | `/clothes/new/image`     | 認証        | 写真選択またはカメラ起動で服画像を登録する                      | 写真選択エリア、カメラ起動案内、画像プレビュー                       | 写真を選ぶ、次へ                             | `POST /clothes/upload-url`                                      | 未実装       |
| UI-011 | AI 判定中画面        | `/clothes/new/analyzing` | 認証        | AI が服のカテゴリや色を解析している間の待機状態を表示する       | ローディング表示、解析中メッセージ                                   | AI 判定結果確認画面へ移動                    | `POST /clothes/analyze-image`                                   | 未実装       |
| UI-012 | AI 判定結果確認画面  | `/clothes/new/confirm`   | 認証        | AI 判定結果をユーザーが確認・修正する                           | 画像プレビュー、カテゴリ、色、季節、TPO、修正可能な入力欄            | 修正する、登録する                           | `POST /clothes/analyze-image`、`POST /clothes`                  | 未実装       |
| UI-013 | 登録完了画面         | `/clothes/new/complete`  | 認証        | 服の登録完了をユーザーに知らせる                                | 登録完了メッセージ、登録した服の簡易情報                             | 服一覧へ、マイページへ、続けて登録する       | なし                                                            | 未実装       |
| UI-014 | お気に入り画面       | `/favorites`             | 認証        | お気に入り登録したコーデを一覧で確認する                        | お気に入りコーデ一覧、コーデカード                                   | コーデ詳細を見る、ホームへ戻る               | `GET /outfits?is_favorite=true`、`PATCH /outfits/{id}`          | 未実装       |
| UI-015 | コーデ履歴画面       | `/outfits`               | 認証        | 過去に提案されたコーデ履歴を確認する                            | 過去のコーデ一覧、日付、TPO、お気に入り状態                          | コーデ詳細を見る、絞り込み                   | `GET /outfits`、`PATCH /outfits/{id}`                           | 実装済み     |
| UI-016 | 設定画面             | `/settings`              | 認証        | ユーザー設定や地域設定を管理する                                | プロフィール情報、地域設定、ホームシーン、プラン情報                 | 地域変更、保存、ログアウト、マイページへ戻る | `GET /auth/me`、`GET /regions`、`PUT /auth/me`                  | API 接続中   |
| UI-017 | API 通信サンプル画面 | `/api-call-sample`       | 公開        | フロントエンドからバックエンド API を呼び出すサンプルを確認する | API 呼び出しボタン、レスポンス表示、エラー表示                       | API を呼び出す                               | `GET /health`                                                   | 開発用       |
| UI-018 | 共通 UI サンプル画面 | `/ui-sample`             | 公開        | 共通 UI コンポーネントの見た目を確認する                        | Button、Badge、Input、Select、Dialog、Drawer、服カード、コーデカード | UI の表示確認                                | なし                                                            | 開発用       |
| UI-019 | コーデプレビュー画面 | `/outfits/preview`       | 認証        | 最新または選択したコーデ提案を確認する                          | コーデのポイント、天気情報、アイテム一覧                             | ホームへ戻る、同じシーンで再提案する         | `GET /outfits`                                                  | API 接続中   |

---

## コーデ提案まわりの現在の方針

`items` が空の場合は `POST /outfits` で保存せず、`POST /outfits/suggest` の結果を `sessionStorage` に保存して詳細画面の空状態を表示します。
コーデ提案は、まずテキストベースの提案を正確に表示することを優先します。

画像生成・画像表示は後続対応とし、現時点では `POST /outfits/suggest` のレスポンスに含まれる `items` を詳細画面で表示できることを重視します。

現在のフロント実装方針（items がある場合）は以下です。

```text
/outfits/scenes
↓
/outfits/loading?tpo=...
↓
POST /outfits/suggest
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

詳細は以下を参照してください。

```text
../docs/frontend/outfit-suggest-integration.md
```

---

## 画面遷移

この表は、現在のフロントエンド実装と今後の予定を含めた画面遷移の整理です。

「未実装」または「予定」のものは、今後の PR で画面作成や API 連携を追加する想定です。

| No. | 起点                     | 操作・条件                                   | 遷移先                                             | 状態         | 補足                                                                                                |
| --- | ------------------------ | -------------------------------------------- | -------------------------------------------------- | ------------ | --------------------------------------------------------------------------------------------------- |
| 1   | URL 直接アクセス         | 未ログイン状態で認証が必要な画面へアクセス   | `/login?redirect=...`                              | 実装済み     | `(app)` 配下の画面はログイン必須です。                                                              |
| 2   | `/login`                 | ログイン成功                                 | `/` または redirect に指定された画面               | 実装済み     | Supabase Auth のログイン成功後に遷移します。                                                        |
| 3   | `/login`                 | 「新規登録はこちら」を押す                   | `/register`                                        | 実装済み     | 新規登録画面へ移動します。                                                                          |
| 4   | `/register`              | 登録に成功する                               | 画面内に確認メール送信メッセージを表示             | 実装済み     | 現状は自動ログインやホーム遷移は行いません。                                                        |
| 5   | `/register`              | 「ログインへ戻る」を押す                     | `/login`                                           | 実装済み     | 登録済みユーザー向けの導線です。                                                                    |
| 6   | `/`                      | シーン選択導線を押す                         | `/outfits/scenes`                                  | 実装済み     | コーデ提案のシーン選択へ移動します。                                                                |
| 7   | `/`                      | コーデ確認導線を押す                         | `/outfits/preview`                                 | 実装済み     | 最新または選択したコーデを確認する導線です。                                                        |
| 8   | `/outfits/scenes`        | シーンを選んで「このシーンで提案する」を押す | `/outfits/loading?tpo=...`                         | 実装済み     | TPO をクエリとして渡します。                                                                        |
| 9   | `/outfits/loading`       | `POST /outfits/suggest` が成功する           | `/outfits/detail?tpo=...&outfitId=...`             | API 接続中   | 提案結果を `POST /outfits` で保存し、保存済み outfit を sessionStorage に保存して詳細へ移動します。 |
| 10  | `/outfits/loading`       | `POST /outfits/suggest` が失敗する           | 同画面にエラー表示                                 | API 接続中   | エラーメッセージを表示します。                                                                      |
| 11  | `/outfits/detail`        | 保存済み outfit が sessionStorage にある     | 同画面で表示                                       | 実装済み     | outfitId とログインユーザーを照合します。                                                           |
| 12  | `/outfits/detail`        | sessionStorage に提案結果がない              | `GET /outfits/{id}` で再取得                       | API 接続中   | リロード時などのフォールバックです。                                                                |
| 13  | `/outfits/detail`        | 「別案」を押す                               | `/outfits/loading?tpo=...`                         | 実装済み     | 同じ TPO で再提案します。                                                                           |
| 14  | `/outfits/detail`        | 「ホームへ戻る」を押す                       | `/`                                                | 実装済み     | ホーム画面へ戻ります。                                                                              |
| 15  | `/outfits/detail`        | 「保存」を押す                               | 画面内で保存状態を更新、またはお気に入り画面へ移動 | 予定         | お気に入り保存 API との連携は今後整理が必要です。                                                   |
| 16  | `/clothes`               | 「服を登録する」を押す                       | `/clothes/register`                                | 実装済み     | 服登録画面へ移動します。                                                                            |
| 17  | `/clothes/register`      | 服情報を入力して登録する                     | `/clothes`                                         | API 接続済み | `POST /clothes` 成功後に服一覧へ戻ります。                                                          |
| 18  | `/clothes/register`      | 「服一覧へ戻る」を押す                       | `/clothes`                                         | 実装済み     | 登録した服一覧へ戻ります。                                                                          |
| 19  | `/clothes/register`      | 写真登録導線を使う                           | `/clothes/new/image`                               | 未実装       | 画像登録フローは今後実装予定です。                                                                  |
| 20  | `/clothes/new/image`     | 写真を選ぶ、またはカメラを起動する           | `/clothes/new/analyzing`                           | 未実装       | 画像アップロード後に AI 判定へ進む想定です。                                                        |
| 21  | `/clothes/new/analyzing` | AI 解析が完了する                            | `/clothes/new/confirm`                             | 未実装       | 画像解析 API と連携する想定です。                                                                   |
| 22  | `/clothes/new/confirm`   | 内容を確認して登録する                       | `/clothes/new/complete`                            | 未実装       | AI が推定した服情報を確認して登録する想定です。                                                     |
| 23  | `/clothes/new/complete`  | 「登録した服一覧へ」を押す                   | `/clothes`                                         | 未実装       | 登録完了後に服一覧へ戻る想定です。                                                                  |
| 24  | `/mypage`                | 「設定」を押す                               | `/settings`                                        | 実装済み     | 設定画面へ移動します。                                                                              |
| 25  | `/settings`              | 「マイページへ戻る」を押す                   | `/mypage`                                          | 実装済み     | マイページへ戻ります。                                                                              |
| 26  | `/settings`              | ログアウトする                               | `/login`                                           | 実装済み     | Supabase Auth のログアウト処理を行います。                                                          |
| 27  | 下部ナビゲーション       | 「ホーム」を押す                             | `/`                                                | 実装済み     | ホームへ移動します。                                                                                |
| 28  | 下部ナビゲーション       | 「登録」を押す                               | `/clothes/register`                                | 実装済み     | 服登録画面へ移動します。                                                                            |
| 29  | 下部ナビゲーション       | 「お気に入り」を押す                         | `/favorites`                                       | 導線のみ     | 画面は未実装です。                                                                                  |
| 30  | 下部ナビゲーション       | 「マイページ」を押す                         | `/mypage`                                          | 実装済み     | マイページへ移動します。                                                                            |

## 認証

認証には Supabase Auth を使用します。

- `AuthProvider` が Supabase のセッション状態を監視します。
- セッション情報は Zustand store に保存します。
- 認証が必要なページは `RequireAuth` で保護します。
- 未ログインの場合は `/login?redirect=...` にリダイレクトします。

関連ファイル:

```txt
src/components/auth/AuthProvider.tsx
src/components/auth/RequireAuth.tsx
src/lib/auth.ts
src/stores/auth-store.ts
```

## API 通信

バックエンド API との通信には `src/lib/api` 配下の fetch wrapper を使用します。

```txt
src/lib/api/client.ts
src/lib/api/fetcher.ts
src/lib/api/env.ts
```

認証が必要な API では Supabase の access token を `Authorization: Bearer <token>` として送信します。

服一覧では以下の API を呼び出します。

```txt
GET /clothes?limit=100
```

関連ファイル:

```txt
src/features/clothes/api.ts
src/features/clothes/types.ts
src/components/clothes/ClothesPageClient.tsx
```

## デザイン方針

Climo はスマホファーストで設計しています。

- 基準幅: 390px
- PC 表示時も中央にスマホ幅の UI を配置
- ベースカラー: `#FAF8F5`
- テキストカラー: `#2B2926`
- アクセントカラー: `#6B4F3A`
- UI はカードベース
- トーンは Natural / Minimal / Calm / Intelligent / Timeless

詳細は以下を参照してください。

```txt
../docs/design-system.md
../docs/frontend/common-layout.md
```

## 共通レイアウト

全体レイアウトは `src/app/layout.tsx` で定義しています。

- `lang="ja"`
- Supabase 認証 Provider
- Header
- max-width 390px の main 領域
- Footer
- BottomNavigation

下部ナビゲーションは以下の導線を持ちます。

| ラベル     | パス                |
| ---------- | ------------------- |
| ホーム     | `/`                 |
| 登録       | `/clothes/register` |
| お気に入り | `/favorites`        |
| マイページ | `/mypage`           |

> `/favorites` はナビゲーション上に存在しますが、画面実装状況は最新のコードを確認してください。

## E2E テスト

Playwright の設定ファイルは `playwright.config.ts` です。

テストファイルは以下に配置します。

```txt
tests/e2e/
```

Playwright を実行する場合は、必要に応じてブラウザをインストールしてください。

```bash
npx playwright install
npx playwright test
```

## 開発時の注意事項

- npm のみ使用してください。
- `package-lock.json` を更新した場合は必ずコミット対象に含めてください。
- `.env` / `.env.local` は Git 管理に含めないでください。
- Supabase の secret key / service role key はフロントエンドに設定しないでください。
- API 仕様を変更する場合は、バックエンドと `docs/openapi.yaml` の整合性も確認してください。
- UI を追加する場合は `docs/design-system.md` のデザイン方針に合わせてください。
- 認証が必要な画面は `src/app/(app)` 配下に配置してください。
- 一部の画面や機能は実装途中、またはモック表示を含む場合があります。

## 関連ドキュメント

| ドキュメント                        | 内容                         |
| ----------------------------------- | ---------------------------- |
| `../README.md`                      | リポジトリ全体の概要         |
| `../docs/setup.md`                  | 開発環境セットアップ         |
| `../docs/requirements.md`           | 要件定義                     |
| `../docs/design-system.md`          | デザインシステム             |
| `../docs/frontend/common-layout.md` | フロントエンド共通レイアウト |
| `../docs/openapi.yaml`              | API 仕様                     |
| `../backend/README.md`              | バックエンド README          |
