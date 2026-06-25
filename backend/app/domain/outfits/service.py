import uuid
from dataclasses import dataclass
from pathlib import Path

from openai import APIError
from pydantic import BaseModel, ConfigDict

from app.api.v1.schemas.clothes import ClothingItem
from app.api.v1.schemas.outfits import DEFAULT_CLOSET_MODE, ClosetMode
from app.services.base_llm import LLMStructuredResponseError
from app.services.llm_client import get_llm_client
from app.services.usage import LlmUsage
from app.services.weather_client import OutfitPromptWeather

_PROMPT_DIR = Path(__file__).resolve().parents[2] / "prompts"
_PROMPT_PATHS = {
    "owned": _PROMPT_DIR / "outfit_suggest.md",
    "free": _PROMPT_DIR / "outfit_suggest_free.md",
}


def _read_prompt_template(mode: ClosetMode) -> str:
    path = _PROMPT_PATHS[mode]
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"{path.name} が見つかりません: {path}") from exc


_PROMPT_TEMPLATES = {
    "owned": _read_prompt_template("owned"),
    "free": _read_prompt_template("free"),
}

_DEFAULT_GENDER = "女性"


class OutfitSuggestionError(Exception):
    """コーデ提案の失敗。

    LLM が refusal / parse 失敗を返した場合でも token は消費済みのため、取得できて
    いれば `usage` を載せて router 側で best-effort 永続化できるようにする。
    """

    def __init__(self, message: str, *, usage: "LlmUsage | None" = None) -> None:
        super().__init__(message)
        self.usage = usage


class LLMOutfitSuggestionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    role: str
    color: str | None
    pattern: str | None
    # 手持ち服を選んだ場合は、プロンプトで提示した clothes の id を返す。
    # 手持ちにない補完アイテムを提案した場合は null。
    clothes_id: str | None = None


class LLMOutfitSuggestionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comment: str
    items: list[LLMOutfitSuggestionItem] = []


class OutfitService:
    def __init__(self):
        try:
            self.llm = get_llm_client()
        except ValueError as exc:
            raise OutfitSuggestionError("failed to generate outfit suggestion") from exc

    async def suggest(
        self,
        *,
        tpo: str,
        clothes: list[ClothingItem],
        weather: OutfitPromptWeather,
        gender: str = _DEFAULT_GENDER,
        closet_mode: ClosetMode = DEFAULT_CLOSET_MODE,
        clothing_ids: list[uuid.UUID] | None = None,
        exclude_clothing_ids: list[uuid.UUID] | None = None,
    ) -> "OutfitSuggestion":
        """クローゼットを参照して LLM にコーデを提案させる。

        - 手持ち服（clothes）を id 付きでプロンプトに渡し、LLM が選定する。
        - 手持ちで埋まらないカテゴリは、LLM が補完アイテム（clothes_id=null）を
          提案してよい（ハイブリッド）。
        - exclude_clothing_ids は候補から除外し、clothing_ids は優先使用を
          指示する（LLM 選定のため含有はサーバ保証ではなく best-effort）。
        """
        pool = clothes
        if closet_mode == "free":
            pool = []
        elif exclude_clothing_ids:
            excluded = set(exclude_clothing_ids)
            pool = [c for c in pool if c.id not in excluded]

        weather_summary = self._format_weather(weather)
        gender_text = gender.strip() or _DEFAULT_GENDER
        prompt = self._build_prompt(
            closet_mode=closet_mode,
            tpo=tpo,
            pool=pool,
            weather_summary=weather_summary,
            gender_text=gender_text,
            clothing_ids=clothing_ids,
        )

        try:
            payload, usage = await self.llm.generate_structured(
                prompt,
                response_format=LLMOutfitSuggestionPayload,
            )
        except LLMStructuredResponseError as exc:
            # refusal/parse 失敗。消費 token を取りこぼさないよう usage を引き継ぐ
            raise OutfitSuggestionError(
                "failed to generate outfit suggestion", usage=exc.usage
            ) from exc
        except APIError as exc:
            raise OutfitSuggestionError("failed to generate outfit suggestion") from exc

        clothes_by_id = {str(item.id): item for item in pool}
        items: list[SuggestedOutfitItemResult] = []
        for display_order, llm_item in enumerate(payload.items, start=1):
            owned = self._resolve_owned(llm_item.clothes_id, clothes_by_id)
            if owned is not None:
                # 手持ち服は DB の値を正として返す（LLM の表記揺れで
                # clothing_item と食い違わせない）。role は提案上の役割なので LLM 値。
                items.append(
                    SuggestedOutfitItemResult(
                        name=owned.name,
                        role=llm_item.role,
                        color=owned.color,
                        pattern=owned.pattern,
                        display_order=display_order,
                        clothing_item=owned,
                    )
                )
            else:
                items.append(
                    SuggestedOutfitItemResult(
                        name=llm_item.name,
                        role=llm_item.role,
                        color=llm_item.color,
                        pattern=llm_item.pattern,
                        display_order=display_order,
                        clothing_item=None,
                    )
                )

        return OutfitSuggestion(
            comment=payload.comment.strip(),
            items=items,
            usage=usage,
        )

    @staticmethod
    def _build_prompt(
        *,
        closet_mode: ClosetMode,
        tpo: str,
        pool: list[ClothingItem],
        weather_summary: str,
        gender_text: str,
        clothing_ids: list[uuid.UUID] | None,
    ) -> str:
        prompt = (
            _PROMPT_TEMPLATES[closet_mode]
            .replace("{{ weather }}", weather_summary)
            .replace("{{ tpo }}", tpo)
            .replace("{{ gender }}", gender_text)
        )
        if closet_mode == "owned":
            prompt = prompt.replace(
                "{{ clothes }}", OutfitService._format_clothes(pool)
            )
            prompt = prompt.replace(
                "{{ must_include }}",
                OutfitService._format_must_include(pool, clothing_ids),
            )
        return prompt

    @staticmethod
    def _resolve_owned(
        clothes_id: str | None,
        clothes_by_id: dict[str, ClothingItem],
    ) -> ClothingItem | None:
        """LLM が返した clothes_id を手持ち服に解決する。

        前後空白や、プロンプト提示の `id=<uuid>` 形式が混ざっても拾えるよう正規化する。
        手持ちに無い ID / None は補完提案として None を返す。
        """
        if not clothes_id:
            return None
        key = clothes_id.strip()
        if key.startswith("id="):
            key = key[len("id=") :].strip()
        return clothes_by_id.get(key)

    @staticmethod
    def _format_must_include(
        pool: list[ClothingItem],
        clothing_ids: list[uuid.UUID] | None,
    ) -> str:
        """clothing_ids で優先使用を指示する手持ち服を id 付きで列挙する。

        プロンプトで「優先して含めたい服」として提示するための整形。含有自体は
        LLM 選定に委ねるため best-effort（サーバ側で含有を保証はしない）。
        """
        if not clothing_ids:
            return "指定なし"
        forced = {str(cid) for cid in clothing_ids}
        lines = [
            f"- id={item.id} - {item.name}" for item in pool if str(item.id) in forced
        ]
        return "\n".join(lines) if lines else "指定なし"

    @staticmethod
    def _select_clothes(
        *,
        tpo: str,
        clothes: list[ClothingItem],
        clothing_ids: list[uuid.UUID] | None = None,
        exclude_clothing_ids: list[uuid.UUID] | None = None,
    ) -> list["SuggestedClothingSelection"]:
        """アルゴリズムでコーデを構成する服を選定する（スコアリング選定）。

        注: 現在の `suggest()` は LLM 主導選定に移行したため、本メソッドは
        提案フローからは呼ばれていない（ユニットテストのみが参照）。スコアリング
        選定ロジックは後続の画像生成フォールバック等での再利用を見込んで残置している。

        TODO: 画像生成フォールバックで再利用するか判断する。再利用しないと決まったら、
        LLM フローとの乖離（死蔵コード化）を避けるため本メソッド・`_select_torso`・
        `_score_item`・`SuggestedClothingSelection` と関連テストごと削除する。

        ※ 下記の clothing_ids「必ず含める」保証は、アルゴリズムで強制 include する
          本メソッド固有の挙動。LLM 主導の `suggest()` 側は LLM への優先指示に留まる
          best-effort（含有はサーバ保証ではない）であり、契約レベルの扱いが異なる。

        仕様 (Issue #61):
        - exclude_clothing_ids: その服を候補から完全に除外する（提案に出さない）。
        - clothing_ids: その服を必ず提案に含める（ユーザー指定を最優先）。
          同カテゴリ複数指定や onepiece と tops/bottoms の同時指定も、
          すべて結果に含める（通常の 1カテゴリ1点・onepiece 排他より優先）。
        - 指定で埋まらないカテゴリは、除外・指定済みを除いた手持ちから
          従来のスコア選定ロジックで自動補完する。
        - clothing_ids が（除外後の）手持ちに無い場合は含めようがないため無視する。
        """
        pool = clothes
        if exclude_clothing_ids:
            excluded = set(exclude_clothing_ids)
            pool = [c for c in pool if c.id not in excluded]

        forced_ids = set(clothing_ids or [])
        forced = [c for c in pool if c.id in forced_ids]
        forced_id_set = {c.id for c in forced}
        auto_pool = [c for c in pool if c.id not in forced_id_set]

        forced_by_category: dict[str, list[ClothingItem]] = {}
        for item in forced:
            forced_by_category.setdefault(item.category, []).append(item)

        selected: list[SuggestedClothingSelection] = []
        display_order = 1

        def add(item: ClothingItem, role: str) -> None:
            nonlocal display_order
            selected.append(
                SuggestedClothingSelection(
                    clothing_item=item,
                    role=role,
                    display_order=display_order,
                )
            )
            display_order += 1

        def best_of(category: str) -> ClothingItem | None:
            cands = [i for i in auto_pool if i.category == category]
            if not cands:
                return None
            return max(cands, key=lambda i: OutfitService._score_item(i, tpo))

        # outer
        if "outer" in forced_by_category:
            for item in forced_by_category["outer"]:
                add(item, "outer")
        else:
            best = best_of("outer")
            if best:
                add(best, "outer")

        # torso（onepiece か tops/bottoms）
        forced_onepiece = forced_by_category.get("onepiece", [])
        forced_tops = forced_by_category.get("tops", [])
        forced_bottoms = forced_by_category.get("bottoms", [])
        if forced_onepiece or forced_tops or forced_bottoms:
            for item in forced_onepiece:
                add(item, "onepiece")
            for item in forced_tops:
                add(item, "tops")
            for item in forced_bottoms:
                add(item, "bottoms")
            # onepiece 指定が無ければ tops/bottoms の欠けを自動補完
            if not forced_onepiece:
                if not forced_tops and (best := best_of("tops")):
                    add(best, "tops")
                if not forced_bottoms and (best := best_of("bottoms")):
                    add(best, "bottoms")
        else:
            torso = OutfitService._select_torso(
                tpo=tpo,
                clothes=auto_pool,
                selected_ids=set(),
            )
            for item, role in torso:
                add(item, role)

        # shoes / bag / accessory
        for category in ("shoes", "bag", "accessory"):
            if category in forced_by_category:
                for item in forced_by_category[category]:
                    add(item, category)
            elif best := best_of(category):
                add(best, category)

        # 上記以外のカテゴリで指定された服は末尾に含める（取りこぼし防止）
        handled = {"outer", "onepiece", "tops", "bottoms", "shoes", "bag", "accessory"}
        for item in forced:
            if item.category not in handled:
                add(item, item.category)

        return selected

    @staticmethod
    def _select_torso(
        *,
        tpo: str,
        clothes: list[ClothingItem],
        selected_ids: set,
    ) -> list[tuple[ClothingItem, str]]:
        tops_cands = [
            i for i in clothes if i.category == "tops" and i.id not in selected_ids
        ]
        btms_cands = [
            i for i in clothes if i.category == "bottoms" and i.id not in selected_ids
        ]
        one_cands = [
            i for i in clothes if i.category == "onepiece" and i.id not in selected_ids
        ]
        best_tops = (
            max(tops_cands, key=lambda i: OutfitService._score_item(i, tpo))
            if tops_cands
            else None
        )
        best_btms = (
            max(btms_cands, key=lambda i: OutfitService._score_item(i, tpo))
            if btms_cands
            else None
        )
        best_one = (
            max(one_cands, key=lambda i: OutfitService._score_item(i, tpo))
            if one_cands
            else None
        )

        if best_one:
            one_score = OutfitService._score_item(best_one, tpo)
            tb_scores = [
                OutfitService._score_item(i, tpo)
                for i in (best_tops, best_btms)
                if i is not None
            ]
            if not tb_scores or one_score > max(tb_scores):
                return [(best_one, "onepiece")]

        return [
            (item, role)
            for item, role in ((best_tops, "tops"), (best_btms, "bottoms"))
            if item
        ]

    @staticmethod
    def _score_item(item: ClothingItem, tpo: str) -> tuple[int, int, int, int]:
        return (
            1 if tpo in item.tpo_tags else 0,
            1 if item.is_favorite else 0,
            1 if "all" in item.season else 0,
            item.wear_count,
        )

    @staticmethod
    def _format_clothes(clothes: list[ClothingItem]) -> str:
        if not clothes:
            return "服の登録はありません。"

        lines = []
        for item in clothes:
            details = [f"id={item.id}", item.category, item.name]
            if item.color:
                details.append(f"color={item.color}")
            if item.pattern:
                details.append(f"pattern={item.pattern}")
            if item.size:
                details.append(f"size={item.size}")
            if item.season:
                details.append(f"season={', '.join(item.season)}")
            if item.tpo_tags:
                details.append(f"tpo={', '.join(item.tpo_tags)}")
            if item.memo:
                details.append(f"memo={item.memo}")
            lines.append(" - ".join(details))

        return "\n".join(lines)

    @staticmethod
    def _format_weather(weather: OutfitPromptWeather) -> str:
        return "\n".join(
            [
                f"現在の気温: {weather['current_temperature']}C",
                f"現在の天気: {weather['current_weather']}",
                f"今日の天気: {weather['today_weather']}",
                f"今日の最高気温: {weather['today_temperature_max']}C",
                f"今日の最低気温: {weather['today_temperature_min']}C",
                f"今日の降水確率: {weather['today_precipitation_probability']}%",
            ]
        )


@dataclass(frozen=True, slots=True)
class SuggestedClothingSelection:
    clothing_item: ClothingItem
    role: str
    display_order: int


@dataclass(frozen=True, slots=True)
class SuggestedOutfitItemResult:
    """LLM 提案の 1 アイテム。

    手持ちなら clothing_item に解決済みの服が入り、手持ちにない補完アイテムなら
    clothing_item は None（name/role/color/pattern のみ）。
    """

    name: str
    role: str
    color: str | None
    pattern: str | None
    display_order: int
    clothing_item: ClothingItem | None


@dataclass(frozen=True, slots=True)
class OutfitSuggestion:
    comment: str
    items: list[SuggestedOutfitItemResult]
    # LLM 呼び出しの token 使用量（取得不可なら None）。上位層で永続化に使う。
    usage: LlmUsage | None = None
