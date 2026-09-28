"""Unit tests for Vietnamese 82-class traffic sign catalog."""

import pytest

from trafficvision.data.catalog import (
    VIETNAM_TRAFFIC_SIGN_CATALOG,
    SignClass,
    get_catalog_by_id,
    get_class_names,
)


def test_catalog_length_and_ids() -> None:
    """Catalog must contain exactly 82 classes with contiguous IDs 0..81."""
    assert len(VIETNAM_TRAFFIC_SIGN_CATALOG) == 82
    ids = [sc.id for sc in VIETNAM_TRAFFIC_SIGN_CATALOG]
    assert ids == list(range(82))


def test_catalog_codes_are_unique_and_non_empty() -> None:
    """Each class must have a unique, non-empty code."""
    codes = [sc.code for sc in VIETNAM_TRAFFIC_SIGN_CATALOG]
    assert len(set(codes)) == 82
    for sc in VIETNAM_TRAFFIC_SIGN_CATALOG:
        assert isinstance(sc.code, str)
        assert len(sc.code.strip()) > 0


def test_catalog_vietnamese_names_non_empty() -> None:
    """Each class must have a non-empty Vietnamese name."""
    for sc in VIETNAM_TRAFFIC_SIGN_CATALOG:
        assert isinstance(sc.name_vi, str)
        assert len(sc.name_vi.strip()) > 0


def test_catalog_categories_valid() -> None:
    """Each class must have a recognized, non-empty category."""
    valid_categories = {"cấm", "hiệu lệnh", "cảnh báo", "chỉ dẫn", "nguy hiểm", "tín hiệu"}
    for sc in VIETNAM_TRAFFIC_SIGN_CATALOG:
        assert isinstance(sc.category, str)
        assert sc.category in valid_categories


def test_get_class_names_returns_ordered_vietnamese_names() -> None:
    """get_class_names() must return 82 Vietnamese names in exact ID order."""
    names = get_class_names()
    assert len(names) == 82
    for i, name in enumerate(names):
        assert name == VIETNAM_TRAFFIC_SIGN_CATALOG[i].name_vi


def test_catalog_spot_checks() -> None:
    """Check specific key classes matching HF star092304/Traffic-sign-detection-VietNam."""
    c0 = VIETNAM_TRAFFIC_SIGN_CATALOG[0]
    assert c0.id == 0
    assert c0.code == "No Entry"
    assert c0.name_vi == "Cấm đi ngược chiều"
    assert c0.category == "cấm"

    c1 = VIETNAM_TRAFFIC_SIGN_CATALOG[1]
    assert c1.id == 1
    assert c1.code == "Turn Right Only"
    assert c1.name_vi == "Đi về bên phải"
    assert c1.category == "hiệu lệnh"

    c7 = VIETNAM_TRAFFIC_SIGN_CATALOG[7]
    assert c7.id == 7
    assert c7.code == "Danger"
    assert c7.name_vi == "Cảnh báo nguy hiểm"
    assert c7.category == "nguy hiểm"

    c11 = VIETNAM_TRAFFIC_SIGN_CATALOG[11]
    assert c11.id == 11
    assert c11.code == "Road with Surveillance Camera"
    assert c11.name_vi == "Đường có camera giám sát"
    assert c11.category == "chỉ dẫn"

    c54 = VIETNAM_TRAFFIC_SIGN_CATALOG[54]
    assert c54.id == 54
    assert c54.code == "Green Light"
    assert c54.name_vi == "Đèn xanh"
    assert c54.category == "tín hiệu"

    c64 = VIETNAM_TRAFFIC_SIGN_CATALOG[64]
    assert c64.id == 64
    assert c64.code == "Stop"
    assert c64.name_vi == "Dừng lại"
    assert c64.category == "cấm"

    c81 = VIETNAM_TRAFFIC_SIGN_CATALOG[81]
    assert c81.id == 81
    assert c81.code == "Slippery Road"
    assert c81.name_vi == "Đường trơn"
    assert c81.category == "cảnh báo"


def test_sign_class_immutability() -> None:
    """SignClass should be immutable (frozen dataclass)."""
    sc = SignClass(id=0, code="No Entry", name_vi="Cấm đi ngược chiều", category="cấm")
    with pytest.raises((AttributeError, TypeError, Exception)):
        sc.id = 99  # type: ignore[misc]


def test_get_catalog_by_id() -> None:
    """get_catalog_by_id returns the class or raises ValueError/KeyError for invalid id."""
    sign = get_catalog_by_id(42)
    assert sign.id == 42
    assert sign.code == "Level Crossing with Barriers"

    with pytest.raises((KeyError, ValueError, IndexError)):
        get_catalog_by_id(999)

    with pytest.raises((KeyError, ValueError, IndexError)):
        get_catalog_by_id(-1)
