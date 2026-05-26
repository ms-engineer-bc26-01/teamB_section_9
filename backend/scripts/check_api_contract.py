"""
API contract drift checker.

Rules:
  - FastAPI route present but absent from docs/openapi.yaml → EXIT 1 (fail CI)
  - docs/openapi.yaml path present but not yet in FastAPI   → WARN only (合格)

Excluded from check:
  - /api/v1/health        (内部プローブ、仕様書に載せない)
  - /openapi.json, /docs, /docs/oauth2-redirect, /redoc  (FastAPI フレームワーク)
"""

import sys
from pathlib import Path

import yaml

EXCLUDED_PATHS: set[str] = {
    "/api/v1/health",
    "/openapi.json",
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
}

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent.parent
    spec_path = repo_root / "docs" / "openapi.yaml"

    with spec_path.open(encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    spec_paths: dict[str, set[str]] = {
        path: {m.lower() for m in methods if m.lower() in HTTP_METHODS}
        for path, methods in (spec.get("paths") or {}).items()
    }

    backend_dir = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(backend_dir))

    from app.main import app  # noqa: E402

    app_paths: dict[str, set[str]] = {}
    for route in app.routes:
        if not hasattr(route, "methods") or not hasattr(route, "path"):
            continue
        path: str = route.path  # type: ignore[attr-defined]
        if path in EXCLUDED_PATHS:
            continue
        methods = {m.lower() for m in (route.methods or set())}
        app_paths.setdefault(path, set()).update(methods)

    exit_code = 0

    for path, methods in sorted(app_paths.items()):
        if path not in spec_paths:
            for method in sorted(methods):
                print(
                    f"[FAIL] Undocumented: {method.upper()} {path}"
                    " — docs/openapi.yaml に追加するかルートを削除してください"
                )
            exit_code = 1
        else:
            for method in sorted(methods - spec_paths[path]):
                print(f"[FAIL] Undocumented method: {method.upper()} {path}")
                exit_code = 1

    for path, methods in sorted(spec_paths.items()):
        if path not in app_paths:
            print(f"[WARN] Not yet implemented: {path}")
        else:
            for method in sorted(methods - app_paths[path]):
                print(f"[WARN] Not yet implemented: {method.upper()} {path}")

    if exit_code == 0:
        print("Contract check passed.")
    else:
        print("\nCI FAILED: docs/openapi.yaml にないエンドポイントは追加できません。")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
