"""Supabase Storage への画像アップロードユーティリティ。

コラージュ画像・服画像の双方から共通利用できる汎用関数。Supabase Storage の
REST API（`/storage/v1/object/...`）を httpx で直接叩く（重い SDK を足さない）。
サーバ側アップロードは RLS をバイパスする service role key を用いる。
"""

import httpx

from app.core.config import settings


class StorageError(Exception):
    """Storage への保存失敗（未設定・HTTP エラー等）を表す。"""


async def upload_image(
    *,
    path: str,
    data: bytes,
    content_type: str = "image/png",
    upsert: bool = True,
) -> str:
    """画像を Storage の `STORAGE_BUCKET/{path}` に保存し、公開 URL を返す。

    path 例: ``"outfits/<outfit_id>.png"`` / ``"clothes/<clothes_id>.png"``。
    バケットが public 前提で公開オブジェクト URL を組み立てて返す。
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise StorageError(
            "Supabase storage is not configured "
            "(SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)"
        )

    base = settings.SUPABASE_URL.rstrip("/")
    bucket = settings.STORAGE_BUCKET
    object_path = path.lstrip("/")
    upload_url = f"{base}/storage/v1/object/{bucket}/{object_path}"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": content_type,
        # 既存パスへの再アップロード（同一 outfit の再生成など）を許可する。
        "x-upsert": "true" if upsert else "false",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(upload_url, content=data, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise StorageError(f"failed to upload image to storage: {exc}") from exc

    return f"{base}/storage/v1/object/public/{bucket}/{object_path}"
