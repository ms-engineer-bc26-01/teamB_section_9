import asyncio
import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.models.clothes import Clothes, ClothesTpo
from app.db.models.user import User
from app.db.session import SessionLocal

BYPASS_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
BYPASS_USER_EMAIL = "test@example.com"
DEFAULT_REGION_CODE = "19_02"
BASE_IMAGE_URL = "https://example.com/seed"


@dataclass(frozen=True, slots=True)
class SeedClothing:
    id: uuid.UUID
    name: str
    category: str
    color: str | None
    pattern: str | None
    size: str | None
    season: list[str]
    tpo_tags: list[str]
    memo: str | None
    is_favorite: bool
    wear_count: int
    last_worn_at: datetime | None


SEED_CLOTHES: list[SeedClothing] = [
    SeedClothing(
        id=uuid.UUID("10000000-0000-0000-0000-000000000001"),
        name="オフホワイト オックスフォードシャツ",
        category="tops",
        color="off-white",
        pattern="solid",
        size="M",
        season=["spring", "autumn"],
        tpo_tags=["business", "smart-casual"],
        memo="きれいめ提案の基準になる定番シャツ",
        is_favorite=True,
        wear_count=14,
        last_worn_at=datetime(2026, 5, 28, 9, 0, tzinfo=UTC),
    ),
    SeedClothing(
        id=uuid.UUID("10000000-0000-0000-0000-000000000002"),
        name="スカイブルー リネンシャツ",
        category="tops",
        color="sky-blue",
        pattern="solid",
        size="M",
        season=["spring", "summer"],
        tpo_tags=["casual", "travel"],
        memo="暑い日の軽さを出しやすい",
        is_favorite=False,
        wear_count=8,
        last_worn_at=datetime(2026, 5, 31, 8, 30, tzinfo=UTC),
    ),
    SeedClothing(
        id=uuid.UUID("10000000-0000-0000-0000-000000000003"),
        name="チャコール ハイゲージニット",
        category="tops",
        color="charcoal",
        pattern="solid",
        size="M",
        season=["autumn", "winter"],
        tpo_tags=["business", "date"],
        memo="落ち着いた夜の外出向け",
        is_favorite=True,
        wear_count=11,
        last_worn_at=datetime(2026, 3, 2, 19, 0, tzinfo=UTC),
    ),
    SeedClothing(
        id=uuid.UUID("10000000-0000-0000-0000-000000000004"),
        name="グレー スウェットフーディ",
        category="tops",
        color="gray",
        pattern="solid",
        size="L",
        season=["autumn", "winter"],
        tpo_tags=["casual", "home", "outdoor"],
        memo="気温低めのラフな日用",
        is_favorite=False,
        wear_count=17,
        last_worn_at=datetime(2026, 4, 14, 7, 45, tzinfo=UTC),
    ),
    SeedClothing(
        id=uuid.UUID("10000000-0000-0000-0000-000000000005"),
        name="ネイビー ボーダーTシャツ",
        category="tops",
        color="navy",
        pattern="border",
        size="M",
        season=["spring", "summer"],
        tpo_tags=["casual", "travel"],
        memo="休日コーデの差し色用",
        is_favorite=False,
        wear_count=9,
        last_worn_at=datetime(2026, 5, 26, 10, 15, tzinfo=UTC),
    ),
    SeedClothing(
        id=uuid.UUID("10000000-0000-0000-0000-000000000006"),
        name="ブラック ワイドスラックス",
        category="bottoms",
        color="black",
        pattern="solid",
        size="M",
        season=["spring", "autumn", "winter"],
        tpo_tags=["business", "formal", "date"],
        memo="フォーマル寄りでも崩しやすい",
        is_favorite=True,
        wear_count=13,
        last_worn_at=datetime(2026, 5, 30, 18, 20, tzinfo=UTC),
    ),
    SeedClothing(
        id=uuid.UUID("10000000-0000-0000-0000-000000000007"),
        name="ベージュ チノパンツ",
        category="bottoms",
        color="beige",
        pattern="solid",
        size="M",
        season=["spring", "summer", "autumn"],
        tpo_tags=["casual", "smart-casual"],
        memo="幅広いトップスに合わせやすい",
        is_favorite=False,
        wear_count=15,
        last_worn_at=datetime(2026, 5, 24, 12, 0, tzinfo=UTC),
    ),
    SeedClothing(
        id=uuid.UUID("10000000-0000-0000-0000-000000000008"),
        name="インディゴ ストレートデニム",
        category="bottoms",
        color="indigo",
        pattern="solid",
        size="M",
        season=["all"],
        tpo_tags=["casual", "outdoor", "travel"],
        memo="全天候で使いやすいデニム",
        is_favorite=True,
        wear_count=22,
        last_worn_at=datetime(2026, 6, 1, 13, 10, tzinfo=UTC),
    ),
    SeedClothing(
        id=uuid.UUID("10000000-0000-0000-0000-000000000009"),
        name="オリーブ カーゴパンツ",
        category="bottoms",
        color="olive",
        pattern="solid",
        size="L",
        season=["spring", "autumn"],
        tpo_tags=["outdoor", "casual"],
        memo="アクティブな日や公園向け",
        is_favorite=False,
        wear_count=6,
        last_worn_at=datetime(2026, 5, 5, 9, 40, tzinfo=UTC),
    ),
    SeedClothing(
        id=uuid.UUID("10000000-0000-0000-0000-000000000010"),
        name="ブラック テーパードレインパンツ",
        category="bottoms",
        color="black",
        pattern="solid",
        size="M",
        season=["spring", "summer", "autumn"],
        tpo_tags=["rainy", "commute"],
        memo="雨予報の日に優先したい一本",
        is_favorite=False,
        wear_count=4,
        last_worn_at=datetime(2026, 5, 18, 8, 10, tzinfo=UTC),
    ),
    SeedClothing(
        id=uuid.UUID("10000000-0000-0000-0000-000000000011"),
        name="ネイビー ライトテーラードジャケット",
        category="outer",
        color="navy",
        pattern="solid",
        size="M",
        season=["spring", "autumn"],
        tpo_tags=["business", "date", "smart-casual"],
        memo="会食や打ち合わせで使いやすい",
        is_favorite=True,
        wear_count=10,
        last_worn_at=datetime(2026, 5, 29, 17, 45, tzinfo=UTC),
    ),
    SeedClothing(
        id=uuid.UUID("10000000-0000-0000-0000-000000000012"),
        name="ベージュ ステンカラーコート",
        category="outer",
        color="beige",
        pattern="solid",
        size="M",
        season=["spring", "autumn"],
        tpo_tags=["business", "travel"],
        memo="朝晩の寒暖差対策に向く",
        is_favorite=False,
        wear_count=7,
        last_worn_at=datetime(2026, 4, 9, 7, 20, tzinfo=UTC),
    ),
    SeedClothing(
        id=uuid.UUID("10000000-0000-0000-0000-000000000013"),
        name="カーキ マウンテンパーカー",
        category="outer",
        color="khaki",
        pattern="solid",
        size="L",
        season=["spring", "autumn"],
        tpo_tags=["outdoor", "rainy", "travel"],
        memo="軽い雨と風に対応しやすい",
        is_favorite=True,
        wear_count=12,
        last_worn_at=datetime(2026, 5, 12, 6, 50, tzinfo=UTC),
    ),
    SeedClothing(
        id=uuid.UUID("10000000-0000-0000-0000-000000000014"),
        name="ブラウン ウールチェスターコート",
        category="outer",
        color="brown",
        pattern="solid",
        size="M",
        season=["winter"],
        tpo_tags=["formal", "date", "business"],
        memo="寒い日の上品な主役アウター",
        is_favorite=False,
        wear_count=5,
        last_worn_at=datetime(2026, 2, 20, 18, 15, tzinfo=UTC),
    ),
    SeedClothing(
        id=uuid.UUID("10000000-0000-0000-0000-000000000015"),
        name="アイボリー ニットワンピース",
        category="onepiece",
        color="ivory",
        pattern="solid",
        size="M",
        season=["autumn", "winter"],
        tpo_tags=["date", "formal"],
        memo="一枚で柔らかい印象を作れる",
        is_favorite=True,
        wear_count=4,
        last_worn_at=datetime(2026, 1, 11, 12, 30, tzinfo=UTC),
    ),
    SeedClothing(
        id=uuid.UUID("10000000-0000-0000-0000-000000000016"),
        name="ブラック プレーンパンプス",
        category="shoes",
        color="black",
        pattern="solid",
        size="24.5",
        season=["all"],
        tpo_tags=["business", "formal", "date"],
        memo="きれいめ全般に合わせやすい",
        is_favorite=True,
        wear_count=18,
        last_worn_at=datetime(2026, 5, 28, 8, 55, tzinfo=UTC),
    ),
    SeedClothing(
        id=uuid.UUID("10000000-0000-0000-0000-000000000017"),
        name="ホワイト レザースニーカー",
        category="shoes",
        color="white",
        pattern="solid",
        size="25.0",
        season=["all"],
        tpo_tags=["casual", "travel", "smart-casual"],
        memo="清潔感のある抜け感を出す",
        is_favorite=True,
        wear_count=24,
        last_worn_at=datetime(2026, 6, 2, 9, 5, tzinfo=UTC),
    ),
    SeedClothing(
        id=uuid.UUID("10000000-0000-0000-0000-000000000018"),
        name="ブラック サイドゴアブーツ",
        category="shoes",
        color="black",
        pattern="solid",
        size="25.0",
        season=["autumn", "winter"],
        tpo_tags=["date", "outdoor", "rainy"],
        memo="雨でも使いやすい足元",
        is_favorite=False,
        wear_count=9,
        last_worn_at=datetime(2026, 4, 3, 7, 10, tzinfo=UTC),
    ),
    SeedClothing(
        id=uuid.UUID("10000000-0000-0000-0000-000000000019"),
        name="ブラック ミニショルダーバッグ",
        category="bag",
        color="black",
        pattern="solid",
        size=None,
        season=["all"],
        tpo_tags=["casual", "date", "travel"],
        memo="荷物が少ない日の外出向け",
        is_favorite=False,
        wear_count=16,
        last_worn_at=datetime(2026, 5, 27, 11, 30, tzinfo=UTC),
    ),
    SeedClothing(
        id=uuid.UUID("10000000-0000-0000-0000-000000000020"),
        name="グレー 大判ストール",
        category="accessory",
        color="gray",
        pattern="solid",
        size=None,
        season=["autumn", "winter"],
        tpo_tags=["business", "formal", "travel"],
        memo="寒い日の調整役として便利",
        is_favorite=False,
        wear_count=7,
        last_worn_at=datetime(2026, 2, 18, 7, 35, tzinfo=UTC),
    ),
]


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
        if user.default_region_code is None:
            user.default_region_code = DEFAULT_REGION_CODE
            changed = True
        if changed:
            db.add(user)
            await db.commit()


async def reseed_clothes() -> None:
    async with SessionLocal() as db:
        existing_items = (
            await db.scalars(
                select(Clothes)
                .where(Clothes.user_id == BYPASS_USER_ID)
                .options(selectinload(Clothes.tpo_tags))
            )
        ).all()

        for item in existing_items:
            await db.delete(item)

        for index, seed in enumerate(SEED_CLOTHES, start=1):
            image_slug = f"{index:02d}"
            clothes = Clothes(
                id=seed.id,
                user_id=BYPASS_USER_ID,
                name=seed.name,
                category=seed.category,
                color=seed.color,
                pattern=seed.pattern,
                size=seed.size,
                season=seed.season,
                image_url=f"{BASE_IMAGE_URL}/{image_slug}.jpg",
                thumbnail_url=f"{BASE_IMAGE_URL}/{image_slug}-thumb.jpg",
                memo=seed.memo,
                is_favorite=seed.is_favorite,
                wear_count=seed.wear_count,
                last_worn_at=seed.last_worn_at,
            )
            clothes.tpo_tags = [ClothesTpo(tpo_tag=tag) for tag in seed.tpo_tags]
            db.add(clothes)

        await db.commit()


async def main() -> None:
    await ensure_bypass_user()
    await reseed_clothes()
    print(f"Seeded {len(SEED_CLOTHES)} clothes for bypass user {BYPASS_USER_ID}")


if __name__ == "__main__":
    asyncio.run(main())
