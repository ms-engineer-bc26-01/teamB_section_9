FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.7.3 /uv /uvx /bin/

WORKDIR /app

# 依存定義だけを先にコピーしてレイヤーを分離
COPY pyproject.toml uv.lock ./

# 仮想環境を作成して依存を同期
RUN uv sync --frozen --no-dev

# アプリケーションコードをコピー
COPY . .

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# 本番向け起動。--reload（開発モード）は使わない。
# worker 数はインスタンスの CPU に応じて調整する（目安: 2×コア数）。
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]