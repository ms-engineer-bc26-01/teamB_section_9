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

## 画面一覧

この一覧は、現在のフロントエンド実装と今後の設計予定をまとめたものです。

API 欄は、`NEXT_PUBLIC_API_BASE_URL` 配下の相対パスで記載しています。
例: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1` の場合、`/auth/me` は `http://localhost:8000/api/v1/auth/me` を指します。

> 現時点では、画面 UI が先行して実装されている箇所があります。
> API 連携や永続化は、今後の PR で順次追加される想定です。

| 画面ID | 画面名               | URL                      | 公開 / 認証 | 目的                                                            | 主な表示内容                                                                       | 主な操作・遷移                                 | API / 外部連携                                                                           | 状態      |
| ------ | -------------------- | ------------------------ | ----------- | --------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ---------------------------------------------- | ---------------------------------------------------------------------------------------- | --------- |
| UI-001 | ログイン画面         | `/login`                 | 公開        | 登録済みユーザーがアプリにログインする                          | アプリ名、メールアドレス入力欄、パスワード入力欄、ログイン案内                     | ログイン、新規登録画面へ移動                   | Supabase Auth `signInWithPassword`                                                       | 実装済み  |
| UI-002 | アカウント登録画面   | `/register`              | 公開        | 新規ユーザーがメールアドレスとパスワードを登録する              | 表示名、メールアドレス入力欄、パスワード入力欄、確認用パスワード入力欄             | 登録、ログイン画面へ戻る                       | Supabase Auth `signUp`                                                                   | 実装済み  |
| UI-003 | ホーム画面           | `/`                      | 認証        | 今日の天気とおすすめコーデを確認する                            | 今日の日付、天気、気温、降水確率、おすすめコーデ、登録服数、今週の提案数           | シーン選択画面へ移動、コーデ詳細系画面へ移動   | 現状は一部モック表示。将来的に `/auth/me`、`/outfits/suggest`、`/clothes` などと連携予定 | 実装中    |
| UI-004 | シーン選択画面       | `/outfits/scenes`        | 認証        | コーデ提案に使う利用シーンを選択する                            | ビジネス、カジュアル、フォーマル、セレモニー、レジャーの選択肢と説明文             | 選択したシーンで提案生成中画面へ移動           | 将来的に `POST /outfits/suggest` と連携予定                                              | 実装中    |
| UI-005 | 提案生成中画面       | `/outfits/loading`       | 認証        | AI がコーデを生成している間の待機状態を表示する                 | ローディング表示、「コーデを提案中です」などのメッセージ                           | 一定時間後にコーデ詳細画面へ移動               | 現状は画面遷移のみ。将来的に `POST /outfits/suggest` と連携予定                          | 実装済み    |
| UI-006 | コーデ詳細画面       | `/outfits/detail`        | 認証        | 提案されたコーデの内容とポイントを確認する                      | コーデタイトル、天気情報、TPO、アイテム一覧、コーデのポイント                      | 保存、別案を見る、ホームへ戻る                 | 将来的に `GET /outfits/{id}`、`PATCH /outfits/{id}` と連携予定                           | 実装中    |
| UI-007 | マイページ画面       | `/mypage`                | 認証        | 登録情報や各種メニューへの入口を表示する                        | 表示名、メールアドレス、服登録件数、お気に入りコーデ数、設定ボタン                 | 設定画面へ移動                                 | `GET /auth/me`、`GET /clothes`、`GET /outfits?is_favorite=true`                          | 実装済み  |
| UI-008 | 登録した服一覧画面   | `/clothes`               | 認証        | ユーザーが登録した服を一覧で確認する                            | 登録済みの服一覧、未登録時メッセージ、服カード、カテゴリ、色、季節、お気に入り状態 | 服登録画面へ移動                               | `GET /clothes`                                                                           | 実装済み  |
| UI-009 | 服登録画面           | `/clothes/register`      | 認証        | 手入力で服情報を登録するための UI を表示する                    | 画像登録エリア、服名、カテゴリ、色、サイズ、柄、季節、TPO、メモ入力欄              | 服一覧へ戻る、画像登録、登録                   | 将来的に `POST /clothes`、`POST /clothes/upload-url` と連携予定                          | UI 実装中 |
| UI-010 | 画像登録画面         | `/clothes/new/image`     | 認証        | カメラ起動または写真選択で服画像を登録する                      | 写真選択エリア、カメラ起動案内、選択した画像のプレビュー                           | 写真を選ぶ、カメラを起動する、次へ             | `POST /clothes/upload-url`                                                               | 未実装    |
| UI-011 | AI 判定中画面        | `/clothes/new/analyzing` | 認証        | AI が服のカテゴリや色を解析している間の待機状態を表示する       | ローディング表示、「服の情報を解析中」などのメッセージ                             | なし                                           | `POST /clothes/analyze-image`                                                            | 未実装    |
| UI-012 | AI 判定結果確認画面  | `/clothes/new/confirm`   | 認証        | AI が判定した服情報をユーザーが確認・修正する                   | 画像プレビュー、カテゴリ、色、季節、TPO、信頼度、修正可能な入力欄                  | 修正する、登録する                             | `POST /clothes/analyze-image`、`POST /clothes`                                           | 未実装    |
| UI-013 | 登録完了画面         | `/clothes/new/complete`  | 認証        | 服の登録完了をユーザーに知らせる                                | 登録完了メッセージ、登録した服の簡易情報                                           | 登録した服一覧へ、マイページへ、続けて登録する | なし                                                                                     | 未実装    |
| UI-014 | お気に入り画面       | `/favorites`             | 認証        | お気に入り登録したコーデを一覧で確認する                        | お気に入りコーデ一覧、コーデカード、登録日、TPO                                    | コーデ詳細を見る、ホームへ戻る                 | `GET /outfits?is_favorite=true`、`PATCH /outfits/{id}`                                   | 未実装    |
| UI-015 | コーデ履歴画面       | `/outfits`               | 認証        | 過去に提案されたコーデ履歴を確認する                            | 過去のコーデ一覧、日付、TPO、お気に入り状態                                        | コーデ詳細を見る、絞り込み                     | `GET /outfits`                                                                           | 未実装    |
| UI-016 | 設定画面             | `/settings`              | 認証        | ユーザー設定や通知設定を管理する                                | プロフィール情報、デフォルト地域、通知設定、プラン情報                             | 地域を変更する、保存する、マイページへ戻る     | `GET /auth/me`、`GET /regions`、`PUT /auth/me`                                           | 未実装    |
| UI-017 | API 通信サンプル画面 | `/api-call-sample`       | 公開        | フロントエンドからバックエンド API を呼び出すサンプルを確認する | API 呼び出しボタン、レスポンス表示、エラー表示                                     | API を呼び出す                                 | `GET /health`                                                                            | 開発用    |
| UI-018 | 共通 UI サンプル画面 | `/ui-sample`             | 公開        | 共通 UI コンポーネントの見た目を確認する                        | Button、Badge、Input、Select、Dialog、Drawer、服カード、コーデカード               | UI の表示確認                                  | なし                                                                                     | 開発用    |

## 画面遷移

この表は、現在のフロントエンド実装と今後の予定を含めた画面遷移の整理です。

> 現時点では、UI が先行して実装されている画面や、今後実装予定の画面も含まれています。
> `状態` が「予定」のものは、今後の PR で画面作成や API 連携を追加する想定です。

| No. | 起点                                       | 操作・条件                                   | 遷移先                                    | 状態         | 補足                                                                   |
| --- | ------------------------------------------ | -------------------------------------------- | ----------------------------------------- | ------------ | ---------------------------------------------------------------------- |
| 1   | URL 直接アクセス                           | 未ログイン状態で認証が必要な画面へアクセス   | `/login?redirect=...`                     | 実装済み     | `(app)` 配下の画面はログイン必須です。                                 |
| 2   | `/login` ログイン画面                      | メールアドレス・パスワードでログイン成功     | `/` または `redirect` に指定された画面    | 実装済み     | Supabase Auth のログイン成功後に遷移します。                           |
| 3   | `/login` ログイン画面                      | 「新規登録はこちら」を押す                   | `/register`                               | 実装済み     | 初回ユーザーは手動で新規登録画面へ移動します。                         |
| 4   | `/register` アカウント登録画面             | 登録に成功する                               | 画面内に確認メール送信メッセージを表示    | 実装済み     | 現状は自動ログインやホーム遷移は行いません。                           |
| 5   | `/register` アカウント登録画面             | 「ログインへ戻る」を押す                     | `/login`                                  | 実装済み     | 登録済みユーザー向けの導線です。                                       |
| 6   | `/` ホーム画面                             | 「別のシーンで提案を見る」を押す             | `/outfits/scenes`                         | 実装済み     | シーン選択画面へ移動します。                                           |
| 7   | `/` ホーム画面                             | 「コーデのポイントを見る」を押す             | `/outfits/preview`                        | 要確認       | 現状リンクはありますが、対応ページは未実装の可能性があります。         |
| 8   | `/outfits/scenes` シーン選択画面           | シーンを選んで「このシーンで提案する」を押す | `/outfits/loading?tpo=...`                | 実装済み     | ビジネス、カジュアル、フォーマル、セレモニー、レジャーを選択できます。 |
| 9   | `/outfits/loading` 提案生成中画面          | 一定時間経過                                 | `/outfits/detail?tpo=...`                 | 実装済み     | 現状はローディング表示後に画面遷移します。                             |
| 10  | `/outfits/detail` コーデ詳細画面           | 「別案」を押す                               | `/outfits/loading?tpo=...`                | 実装済み     | 同じ TPO で再提案する想定の導線です。                                  |
| 11  | `/outfits/detail` コーデ詳細画面           | 「ホームへ戻る」を押す                       | `/`                                       | 実装済み     | ホーム画面へ戻ります。                                                 |
| 12  | `/outfits/detail` コーデ詳細画面           | 「保存」を押す                               | `/favorites` または画面内で保存状態を更新 | 予定         | お気に入り保存 API との連携は今後実装予定です。                        |
| 13  | `/outfits/detail` コーデ詳細画面           | 保存済みコーデを確認する                     | `/favorites`                              | 予定         | お気に入り画面は今後実装予定です。                                     |
| 14  | `/` ホーム画面                             | 登録服が少ない、または服登録導線を選ぶ       | `/clothes/register`                       | 一部実装済み | 下部ナビゲーションや服一覧から服登録画面へ移動できます。               |
| 15  | `/clothes` 登録した服一覧画面              | 「服を登録する」を押す                       | `/clothes/register`                       | 実装済み     | 服登録画面へ移動します。                                               |
| 16  | `/clothes/register` 服登録画面             | 「服一覧へ戻る」を押す                       | `/clothes`                                | 実装済み     | 登録した服一覧画面へ戻ります。                                         |
| 17  | `/clothes/register` 服登録画面             | 手入力で登録する                             | 登録完了画面、または `/clothes`           | 予定         | 現状、登録ボタンは disabled です。                                     |
| 18  | `/clothes/register` 服登録画面             | 写真で登録する                               | `/clothes/new/image`                      | 予定         | 画像登録画面は今後実装予定です。                                       |
| 19  | `/clothes/new/image` 画像登録画面          | 写真を選ぶ、またはカメラを起動する           | `/clothes/new/analyzing`                  | 予定         | 画像アップロード後に AI 判定へ進む想定です。                           |
| 20  | `/clothes/new/analyzing` AI 判定中画面     | AI 解析が完了する                            | `/clothes/new/confirm`                    | 予定         | 画像解析 API と連携する想定です。                                      |
| 21  | `/clothes/new/confirm` AI 判定結果確認画面 | 内容を修正・確認して登録する                 | `/clothes/new/complete`                   | 予定         | AI が推定した服情報を確認して登録する想定です。                        |
| 22  | `/clothes/new/complete` 登録完了画面       | 「登録した服一覧へ」を押す                   | `/clothes`                                | 予定         | 登録完了後に服一覧へ戻る想定です。                                     |
| 23  | `/clothes/new/complete` 登録完了画面       | 「続けて登録する」を押す                     | `/clothes/register`                       | 予定         | 続けて服を登録する導線です。                                           |
| 24  | `/mypage` マイページ画面                   | 「設定」を押す                               | `/settings`                               | 一部実装済み | リンクはありますが、設定画面は今後実装予定です。                       |
| 25  | `/mypage` マイページ画面                   | お気に入りコーデを確認する                   | `/favorites`                              | 予定         | お気に入り画面は今後実装予定です。                                     |
| 26  | `/mypage` マイページ画面                   | コーデ履歴を確認する                         | `/outfits`                                | 予定         | コーデ履歴画面は今後実装予定です。                                     |
| 27  | `/settings` 設定画面                       | 「マイページへ戻る」を押す                   | `/mypage`                                 | 予定         | 設定画面実装時に追加する想定です。                                     |
| 28  | `/favorites` お気に入り画面                | コーデカードを選ぶ                           | `/outfits/detail`                         | 予定         | お気に入りコーデの詳細を見る想定です。                                 |
| 29  | `/outfits` コーデ履歴画面                  | コーデカードを選ぶ                           | `/outfits/detail`                         | 予定         | 過去の提案コーデの詳細を見る想定です。                                 |
| 30  | 下部ナビゲーション                         | 「ホーム」を押す                             | `/`                                       | 実装済み     | 下部ナビゲーションからホームへ移動します。                             |
| 31  | 下部ナビゲーション                         | 「登録」を押す                               | `/clothes/register`                       | 実装済み     | 下部ナビゲーションから服登録画面へ移動します。                         |
| 32  | 下部ナビゲーション                         | 「お気に入り」を押す                         | `/favorites`                              | 一部実装済み | リンクはありますが、お気に入り画面は今後実装予定です。                 |
| 33  | 下部ナビゲーション                         | 「マイページ」を押す                         | `/mypage`                                 | 実装済み     | 下部ナビゲーションからマイページへ移動します。                         |

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
