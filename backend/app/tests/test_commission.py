"""Commission calculation tests."""

from app.services.commission import calculate_commission


def test_commission_below_target():
    b = calculate_commission(photos_printed=50, target_photos=100)
    assert b.photos_at_base_rate == 50
    assert b.photos_at_bonus_rate == 0
    assert b.base_commission == 300.0
    assert b.bonus_commission == 0.0
    assert b.total_commission == 300.0


def test_commission_at_target():
    b = calculate_commission(photos_printed=100, target_photos=100)
    assert b.photos_at_base_rate == 100
    assert b.photos_at_bonus_rate == 0
    assert b.total_commission == 600.0
    assert b.target_met is True


def test_commission_above_target():
    b = calculate_commission(photos_printed=120, target_photos=100)
    assert b.photos_at_base_rate == 100
    assert b.photos_at_bonus_rate == 20
    assert b.base_commission == 600.0
    assert b.bonus_commission == 240.0
    assert b.total_commission == 840.0


def test_commission_no_target():
    b = calculate_commission(photos_printed=30, target_photos=0)
    assert b.total_commission == 180.0  # 30 * 6
