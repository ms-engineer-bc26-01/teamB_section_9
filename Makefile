SHELL := bash

.PHONY: check install-check lint test secret-scan seed-bypass-clothes

check: install-check lint test  ## ローカルで全チェックを実行（PR 前に走らせる）

install-check:  ## frontend の依存定義と lockfile の整合性を確認
	cd frontend && npm ci --ignore-scripts

lint:  ## Linter を実行
	cd backend && uv run ruff check . && uv run ruff format --check .
	cd frontend && npm run lint

test:  ## テストを実行
	cd backend && uv run pytest -v --tb=short
	cd frontend && npm run build

seed-bypass-clothes:  ## BYPASSモード用の服seedを投入
	cd backend && uv run python scripts/seed_bypass_clothes.py

secret-scan:  ## シークレット漏洩チェック（要: gitleaks インストール）
	gitleaks detect --source . --verbose
