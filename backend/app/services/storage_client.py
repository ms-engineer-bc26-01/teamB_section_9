"""Supabase Storage への画像アップロードユーティリティ。

**コラージュ画像（AI 生成）専用の BE 経由アップロード**。OpenAI が base64 を返す
ため BE で受け取って Storage へ送る必要がある。Supabase Storage の REST API
（`/storage/v1/object/...`）を httpx で直接叩く（重い SDK を足さない）。サーバ側
アップロードは RLS をバイパスする service role key を用いる。

NOTE: 服画像は設計どおり「BE が署名付き upload URL を発行 → FE が直接 PUT →
storage_path 通知」の別フロー（requirements.md:147、BE をプロキシにしない）。
`upload_image`（BE 経由アップロード）は服画像には流用しない。ただし公開 URL 組み立て
（`build_public_url`）は服画像 `/upload-url` の image_url にも共用する（#133）。
"""

import uuid
from collections.abc import Mapping

import httpx

from app.core.config import settings


class StorageError(Exception):
    """Storage への保存失敗（未設定・HTTP エラー等）を表す。"""


def _resolve_signed_upload_url(base: str, payload: Mapping[str, object]) -> str:
    signed = payload.get("url") or payload.get("signedURL") or payload.get("signedUrl")

    if not isinstance(signed, str) or not signed:
        raise StorageError("signed upload url response missing signed URL")

    if signed.startswith("http"):
        return signed

    if signed.startswith("/storage/v1"):
        return f"{base}{signed}"

    return f"{base}/storage/v1{signed}"


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

    return build_public_url(object_path)


_ALLOWED_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _ensure_storage_config() -> tuple[str, str, str]:
    base = settings.SUPABASE_URL
    service_role_key = settings.SUPABASE_SERVICE_ROLE_KEY
    bucket = settings.SUPABASE_STORAGE_BUCKET

    if not base or not service_role_key or not bucket:
        raise StorageError(
            "Supabase storage is not configured "
            "(SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY / SUPABASE_STORAGE_BUCKET)"
        )

    return (
        base.rstrip("/"),
        service_role_key,
        bucket,
    )


def build_public_url(storage_path: str) -> str:
    """storage_path から公開オブジェクト URL を組み立てる。

    バケットが public 前提（署名 URL 化は follow-up）。`upload_image` の戻り値と
    `/upload-url` レスポンスの image_url を同一ロジックに揃えるための共通関数。
    公開 URL は base + bucket のみで構成でき service role key に依存しない（署名や
    アップロードと違い、read 経路など key を持たない文脈からも安全に呼べる）。
    """
    base = settings.SUPABASE_URL
    bucket = settings.SUPABASE_STORAGE_BUCKET
    if not base or not bucket:
        raise StorageError(
            "Supabase storage is not configured "
            "(SUPABASE_URL / SUPABASE_STORAGE_BUCKET)"
        )
    object_path = storage_path.lstrip("/")
    return f"{base.rstrip('/')}/storage/v1/object/public/{bucket}/{object_path}"


def _resolve_extension(filename: str, content_type: str) -> str:
    return _ALLOWED_EXTENSIONS[content_type]


def _build_clothing_storage_path(
    user_id: uuid.UUID, filename: str, content_type: str
) -> str:
    ext = _resolve_extension(filename, content_type)
    return f"clothes/{user_id}/{uuid.uuid4().hex}{ext}"


async def create_signed_upload_url(
    *,
    user_id: uuid.UUID,
    filename: str,
    content_type: str,
) -> tuple[str, str]:
    base, service_role_key, bucket = _ensure_storage_config()
    storage_path = _build_clothing_storage_path(user_id, filename, content_type)
    sign_endpoint = f"{base}/storage/v1/object/upload/sign/{bucket}/{storage_path}"
    headers = {
        "Authorization": f"Bearer {service_role_key}",
        "Content-Type": "application/json",
    }

    try:
        timeout = settings.SUPABASE_STORAGE_TIMEOUT_SECONDS
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                sign_endpoint,
                json={"upsert": False},
                headers=headers,
            )
            response.raise_for_status()
            try:
                payload = response.json()
            except ValueError as exc:
                raise StorageError(
                    "failed to create signed upload url: invalid JSON response"
                ) from exc

            if not isinstance(payload, dict):
                raise StorageError(
                    "failed to create signed upload url: unexpected response payload"
                )
    except httpx.HTTPError as exc:
        raise StorageError(f"failed to create signed upload url: {exc}") from exc

    upload_url = _resolve_signed_upload_url(base, payload)
    return upload_url, storage_path
