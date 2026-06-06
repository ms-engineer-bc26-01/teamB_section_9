import asyncio
import uuid

from app.db.models.user import User
from app.db.session import SessionLocal

BYPASS_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
BYPASS_USER_EMAIL = "test@example.com"
DEFAULT_REGION_CODE = "13_01"


async def ensure_bypass_user() -> None:
    async with SessionLocal() as db:
        user = await db.get(User, BYPASS_USER_ID)
        if user is None:
            db.add(
                User(
                    id=BYPASS_USER_ID,
                    email=BYPASS_USER_EMAIL,
                    default_region_code=DEFAULT_REGION_CODE,
                )
            )
            await db.commit()
            return

        changed = False
        if user.email != BYPASS_USER_EMAIL:
            user.email = BYPASS_USER_EMAIL
            changed = True
        if user.default_region_code != DEFAULT_REGION_CODE:
            user.default_region_code = DEFAULT_REGION_CODE
            changed = True
        if changed:
            db.add(user)
            await db.commit()


async def main() -> None:
    await ensure_bypass_user()
    print(f"Seeded bypass user {BYPASS_USER_ID}")


if __name__ == "__main__":
    asyncio.run(main())
