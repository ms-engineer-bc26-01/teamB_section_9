"""Supabase Storage への画像アップロードユーティリティ。

**コラージュ画像（AI 生成）専用の BE 経由アップロード**。OpenAI が base64 を返す
ため BE で受け取って Storage へ送る必要がある。Supabase Storage の REST API
（`/storage/v1/object/...`）を httpx で直接叩く（重い SDK を足さない）。サーバ側
アップロードは RLS をバイパスする service role key を用いる。

NOTE: 服画像は設計どおり「BE が署名付き upload URL を発行 → FE が直接 PUT →
storage_path 通知」の別フロー（requirements.md:147、BE をプロキシにしない）。
本関数は服画像には流用しない。共有するのはバケット規約のみ。
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
    """画像を Storage の `SUPABASE_STORAGE_BUCKET/{path}` に保存し、公開 URL を返す。

    path 例: ``"outfits/<outfit_id>.png"``。バケットが public 前提で公開オブジェクト
    URL を組み立てて返す（署名 URL 化は follow-up）。
    upsert=True のため同一 path への再生成は上書きされる（同一 outfit の再生成想定）。
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise StorageError(
            "Supabase storage is not configured "
            "(SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)"
        )

    base = settings.SUPABASE_URL.rstrip("/")
    bucket = settings.SUPABASE_STORAGE_BUCKET
    object_path = path.lstrip("/")
    upload_url = f"{base}/storage/v1/object/{bucket}/{object_path}"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": content_type,
        # 既存パスへの再アップロード（同一 outfit の再生成など）を許可する。
        "x-upsert": "true" if upsert else "false",
    }

    try:
        timeout = settings.SUPABASE_STORAGE_TIMEOUT_SECONDS
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(upload_url, content=data, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise StorageError(f"failed to upload image to storage: {exc}") from exc

    return f"{base}/storage/v1/object/public/{bucket}/{object_path}"
