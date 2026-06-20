"""コーデ内容からコラージュ画像生成用プロンプトを組み立てる。

保存対象コーデの items（name/role/color/pattern/display_order）と comment から、
OpenAI Image API へ渡す指示文を生成する純粋ロジック。副作用・I/O を持たず、
ユニットテスト可能に保つ。テンプレートは `app/prompts/outfit_image.md` を
`outfit_suggest.md` と同じ置換方式で利用する。
"""

from pathlib import Path
from typing import Protocol, Sequence, runtime_checkable

_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "outfit_image.md"
try:
    _PROMPT_TEMPLATE: str = _PROMPT_PATH.read_text(encoding="utf-8")
except OSError as exc:  # pragma: no cover - 起動時に存在を担保するための保険
    raise RuntimeError(f"outfit_image.md が見つかりません: {_PROMPT_PATH}") from exc

# comment が無いコーデでもプロンプトが破綻しないためのフォールバック。
_DEFAULT_COMMENT = "a well-coordinated everyday outfit"
# items が空のときの items セクション（防御的フォールバック。通常は1点以上）。
_EMPTY_ITEMS = "(a single coordinated outfit)"


@runtime_checkable
class OutfitItemLike(Protocol):
    """画像プロンプト生成に必要な item の最小形状（duck typing）。

    `SuggestedOutfitItemResult`（dataclass）・`OutfitCreateItem`/`SuggestedOutfitItem`
    （Pydantic）など、name/role/color/pattern/display_order を持つ任意の型を受ける。
    """

    name: str
    role: str
    color: str | None
    pattern: str | None
    display_order: int


def build_image_prompt(
    comment: str | None,
    items: Sequence[OutfitItemLike],
) -> str:
    """コーデ内容から画像生成プロンプト文字列を組み立てる。"""
    items_block = _format_items(items)
    comment_text = (comment or "").strip() or _DEFAULT_COMMENT
    return _PROMPT_TEMPLATE.replace("{{ items }}", items_block).replace(
        "{{ comment }}", comment_text
    )


def _format_items(items: Sequence[OutfitItemLike]) -> str:
    """items を display_order 昇順で `N. role: name (color, pattern)` 形式へ整形。"""
    if not items:
        return _EMPTY_ITEMS

    lines: list[str] = []
    for item in sorted(items, key=lambda i: i.display_order):
        line = f"{item.display_order}. {item.role}: {item.name}"
        attrs: list[str] = []
        if item.color:
            attrs.append(f"color: {item.color}")
        if item.pattern:
            attrs.append(f"pattern: {item.pattern}")
        if attrs:
            line += f" ({', '.join(attrs)})"
        lines.append(line)
    return "\n".join(lines)
