from dataclasses import dataclass

from app.services.image_prompt_builder import build_image_prompt


@dataclass
class _FakeItem:
    name: str
    role: str
    color: str | None
    pattern: str | None
    display_order: int


def _items() -> list[_FakeItem]:
    return [
        _FakeItem(
            name="白いリネンシャツ",
            role="tops",
            color="白",
            pattern="無地",
            display_order=1,
        ),
        _FakeItem(
            name="黒のテーパードパンツ",
            role="bottoms",
            color="黒",
            pattern=None,
            display_order=2,
        ),
        _FakeItem(
            name="サングラス",
            role="accessory",
            color=None,
            pattern=None,
            display_order=3,
        ),
    ]


def test_build_image_prompt_includes_all_item_names_and_roles():
    # Arrange
    items = _items()

    # Act
    prompt = build_image_prompt("カジュアルな白基調コーデ", items)

    # Assert
    for item in items:
        assert item.name in prompt
        assert item.role in prompt
    assert "カジュアルな白基調コーデ" in prompt


def test_build_image_prompt_orders_items_by_display_order():
    # Arrange: わざと順不同で渡す
    items = list(reversed(_items()))

    # Act
    prompt = build_image_prompt("comment", items)

    # Assert: display_order 昇順で並ぶ
    pos_tops = prompt.index("白いリネンシャツ")
    pos_bottoms = prompt.index("黒のテーパードパンツ")
    pos_accessory = prompt.index("サングラス")
    assert pos_tops < pos_bottoms < pos_accessory


def test_build_image_prompt_omits_null_color_and_pattern():
    # Arrange
    items = [
        _FakeItem(
            name="サングラス",
            role="accessory",
            color=None,
            pattern=None,
            display_order=1,
        )
    ]

    # Act
    prompt = build_image_prompt("comment", items)

    # Assert: 欠損フィールドは括弧注記を出さない
    assert "サングラス" in prompt
    assert "color:" not in prompt
    assert "pattern:" not in prompt


def test_build_image_prompt_includes_color_and_pattern_when_present():
    # Arrange
    items = [
        _FakeItem(
            name="白いリネンシャツ",
            role="tops",
            color="白",
            pattern="無地",
            display_order=1,
        )
    ]

    # Act
    prompt = build_image_prompt("comment", items)

    # Assert
    assert "color: 白" in prompt
    assert "pattern: 無地" in prompt


def test_build_image_prompt_uses_default_comment_when_empty():
    # Arrange / Act
    prompt_none = build_image_prompt(None, _items())
    prompt_blank = build_image_prompt("   ", _items())

    # Assert: comment 欠落でもプロンプトが破綻せずフォールバックが入る
    assert "a well-coordinated everyday outfit" in prompt_none
    assert "a well-coordinated everyday outfit" in prompt_blank


def test_build_image_prompt_handles_empty_items():
    # Arrange / Act
    prompt = build_image_prompt("comment", [])

    # Assert: 空 items でも例外を出さず文字列を返す
    assert isinstance(prompt, str)
    assert "comment" in prompt
