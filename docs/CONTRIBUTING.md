# CONTRIBUTING.md — 開発運用ガイド

> **実装上の判断の優先順位：`docs/openapi.yaml` > `requirements.md` > `docs/PRD.md`**
> ルールや仕様の更新は必ず該当ファイルを直接変更する。このファイルの更新も PR 経由。

---

## 1. ブランチ命名規則

### フォーマット

```
<type>/<scope>-<brief-description>
```

すべて小文字 + ハイフン区切り。アンダースコア・大文字・日本語は使わない。

### type 一覧

| type | 用途 |
|---|---|
| `feat` `feature`| 新機能の追加 |
| `fix` | バグ修正 |
| `refactor` | 動作変更を伴わないリファクタリング |
| `test` | テストの追加・修正 |
| `docs` | ドキュメントのみの変更 |
| `chore` | ビルド設定・CI・依存パッケージ等 |
| `infra` | Docker・デプロイ設定 |

### scope 一覧

| scope | 対象 |
|---|---|
| `fe` | frontend のみ |
| `be` | backend のみ |
| `db` | マイグレーション・ER 変更 |
| `llm` | LLM プロンプト・llm_client |
| `ci` | GitHub Actions |
| `docs` | ドキュメント類 |

### 命名例

```bash
feat/fe-outfit-suggest-ui          # FE: コーデ提案画面
feat/be-clothes-crud               # BE: 服 CRUD エンドポイント
feat/be-llm-outfit-suggest         # BE: LLM コーデ提案
feat/be-stripe-webhook             # BE: Stripe Webhook 処理
feat/be-rate-limit-redis           # BE: Redis レート制限
fix/be-rate-limit-redis-key        # BE: Redis キーのバグ修正
feat/db-add-usage-logs-table       # DB: usage_logs テーブル追加
test/be-prompt-injection           # テスト: プロンプトインジェクション防御
feat/llm-outfit-prompt-v2          # LLM: プロンプト v2
docs/requirements-swagger-sync     # docs: Swagger との差分を反映
chore/ci-add-pip-audit             # CI: pip-audit の追加
infra/docker-compose-redis         # インフラ: Redis 設定追加
```

### ルール

- `main` への直接プッシュは禁止。必ず PR 経由でマージする
- ブランチはマージ後に削除する
- 1 PR = 1 機能・1 修正を原則とする（レビューを小さく保つ）

---

## 2. コミットメッセージ規則

[Conventional Commits](https://www.conventionalcommits.org/) に準拠。

```
<type>(<scope>): <短い説明>

<任意: 詳細説明>

<任意: Closes #issue番号>
```

例：
```
feat(be): add rate limiting for /outfits/suggest

Redis を使って 1 日あたりの提案回数を管理する。
free: 3 回/日, premium: 無制限。超過時 429 を返す。

Closes #42
```

---

## 3. PR の作り方

### 作成時のチェックリスト

- [ ] ブランチ名が命名規則に沿っている
- [ ] CI がグリーン（lint + test + 型チェック）
- [ ] `requirements.md` や `docs/openapi.yaml` の変更が必要な場合は同じ PR に含める
- [ ] レビュアーを最低 1 名アサインする
- [ ] PR タイトルがコミットメッセージ規則に沿っている

### PR タイトルフォーマット

```
feat(be): LLM コーデ提案エンドポイントの実装
fix(fe): 服一覧のページネーションバグを修正
docs: requirements.md に Swagger との差分を反映
```

### レビューの目安

- 必要なレビュアー数：1 名（通常）/ 2 名以上（API・DB スキーマ変更、セキュリティ関連）
- レビュー期限：24 時間以内を目安。超える場合は Slack で催促してよい
- マージ：レビュアーが Approve したら PR 作成者が **Squash Merge** する

---

## 4. スコープ別の注意事項

### API 仕様を変更するとき（`docs/openapi.yaml` / ルーターの変更）

1. `docs/openapi.yaml` を先に更新して同じ PR に含める
2. FE と BE を同じ PR または連続した PR で変更する（片方だけ先にマージして型が合わない状態を防ぐ）
3. PR 本文に「API の変更点（追加・変更・削除）」を箇条書きで明記する

### DB スキーマを変更するとき（Alembic マイグレーション）

1. `docs/er-diagram.md` を同じ PR で更新する
2. `requirements.md` の 4.1 節（テーブル定義）も同じ PR で更新する
3. マイグレーションスクリプトのロールバックが可能か確認する
4. `infra/scripts/seed.py` の更新が必要な場合は同じ PR に含める

### LLM プロンプトを変更するとき（`backend/app/prompts/`）

1. ファイル冒頭の動作確認日・モデルバージョンを更新する
2. TS-007（プロンプトインジェクション防御テスト）が引き続きパスすることを確認する
3. 変更前後の出力例を PR 本文に貼る（「何が変わったか」を見えるようにする）

### `requirements.md` を変更するとき

- 技術スタックの変更は全員の Approve が必要
- Swagger（`docs/openapi.yaml`）と矛盾する変更をしない（Swagger が正）
- 未確定論点が決定した場合は、12 節の表を更新してクローズする

---

## 5. ローカル開発環境セットアップ

```bash
# 1. リポジトリをクローン
git clone git@github.com:your-team/closet-app.git
cd closet-app

# 2. pre-commit をインストール（シークレット漏洩・lint の自動チェック）
pip install pre-commit
pre-commit install

# 3. .env を作成
cp .env.example .env
# → 代表者（C）から Slack DM で受け取った値を貼り付ける

# 4. Docker 起動
docker compose up

# 5. ブラウザで確認
# http://localhost:3000        フロントエンド
# http://localhost:8000/docs   FastAPI Swagger UI
```

**`.env` が更新されたとき**：`#env-updates` チャンネルの最新メッセージを `.env` に反映し、👍 リアクションで確認済みを報告する。

---

## 6. セキュリティ事故が起きたとき

| 事象 | 対応 |
|---|---|
| API キーが漏洩した（可能性含む）| 直ちに代表者（C）に連絡。該当サービスのダッシュボードでキーを無効化・ローテート |
| `.env` を誤ってコミットした | `git revert` + Force Push しても履歴には残るため、キーのローテートも必ず実施 |
| 依存パッケージに重大な脆弱性（CVSS 9.0 以上） | Dependabot の自動 PR を即日マージすることを目標にする |

---

## 7. GitHub Actionsのワークフロー

| ワークフロー | トリガー | 内容 |
|---|---|---|
| `ci.yml` | PR 作成・更新時 | gitleaks / ruff / mypy / ESLint / tsc / pytest / vitest / pip-audit / npm audit |
| `deploy.yml` | `main` にマージ時 | 本番デプロイ（ADVANCE。達成した段階で追加） |

CI が RED のままマージしない。修正できない場合は Slack で相談する。

---

## 8. API コントラクトチェック（CI `api-contract` ジョブ）

### 判定ルール

| 状態 | CI 結果 |
|---|---|
| FastAPI に `docs/openapi.yaml` にないエンドポイントが存在する | **FAIL**（マージ不可） |
| `docs/openapi.yaml` に定義されているがまだ未実装 | WARN（通過） |
| `docs/openapi.yaml` の YAML が不正 | **FAIL** |
| PR ブランチ名が命名規則に違反 | **FAIL** |

### ルーターを追加するときのフロー

1. **先に `docs/openapi.yaml` を更新**（同じ PR に含める）
2. FastAPI ルーターを実装
3. `make check` でローカル確認 → PR 作成

> 内部プローブ（`GET /api/v1/health`）はチェック対象外。新しい内部プローブを追加する場合は
> `backend/scripts/check_api_contract.py` の `EXCLUDED_PATHS` に追記すること。
