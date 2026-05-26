SHELL := bash

.PHONY: check lint test secret-scan

check: lint test  ## ローカルで全チェックを実行（PR 前に走らせる）

lint:  ## Linter を実行
	cd backend && uv run ruff check . && uv run ruff format --check .
	cd frontend && npm run lint

test:  ## テストを実行
	cd backend && uv run pytest -v --tb=short
	cd frontend && npm test -- --passWithNoTests

secret-scan:  ## シークレット漏洩チェック（要: gitleaks インストール）
	gitleaks detect --source . --verbose
