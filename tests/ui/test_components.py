import pytest

from trafficvision.ui.components import extract_mini_badge


@pytest.mark.parametrize(
    ("class_name", "expected_icon"),
    [
        ("Cấm xe tải", "🚚"),
        ("Cảnh báo Khu vực có trẻ em", "🧒"),
        ("Đường có camera giám sát", "📷"),
        ("Bến xe buýt", "🚌"),
    ],
)
def test_extract_mini_badge_uses_pictogram_matching_named_sign(
    class_name: str, expected_icon: str
) -> None:
    """A generic category icon must not replace a named traffic-sign pictogram."""
    icon, _ = extract_mini_badge(class_name)

    assert icon == expected_icon


def test_extract_mini_badge_uses_neutral_sign_for_unknown_class() -> None:
    """Unknown classes must not be misleadingly rendered as traffic lights."""
    icon, style = extract_mini_badge("Lớp biển chưa xác định")

    assert icon == "◇"
    assert "#64748b" in style


def test_extract_mini_badge_uses_warning_icon_for_generic_vietnamese_warning() -> None:
    """Vietnamese warning labels need a warning sign, not a traffic light."""
    icon, style = extract_mini_badge("Cảnh báo đường cong phía trước")

    assert icon == "⚠️"
    assert "#f59e0b" in style
