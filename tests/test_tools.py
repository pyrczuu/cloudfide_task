from datetime import datetime, timedelta, timezone

import pytest

from helpdesk.config import DATE_NOW
from helpdesk.tools import calculate_refund, get_booking

TZ = timezone(timedelta(hours=2))


# ---------- get_booking ----------
def test_get_booking_found():
    r = get_booking("CW-1001")
    assert r["found"] is True
    assert r["booking"]["bike_type"] == "city"


def test_get_booking_is_forgiving_about_case_and_spaces():
    assert get_booking("  cw-1001 ")["found"] is True


def test_get_booking_not_found_does_not_raise():
    assert get_booking("CW-9999")["found"] is False


@pytest.mark.parametrize("bad", ["", "   ", "banana", None, 123])
def test_get_booking_garbage_input_does_not_raise(bad):
    assert get_booking(bad)["found"] is False


# ---------- calculate_refund: one test per rule ----------
def test_100_percent_when_far_ahead():
    r = calculate_refund("CW-1001")  # 73h ahead, rental 40, deposit 50
    assert r["refund_percent"] == 100
    assert r["total_refund_eur"] == 90.0


def test_50_percent_between_24_and_48_hours():
    r = calculate_refund("CW-1002")  # 33h ahead, 2 e-bikes: rental 80, deposit 300
    assert r["refund_percent"] == 50
    assert r["rental_refund_eur"] == 40.0
    assert r["total_refund_eur"] == 340.0


def test_0_percent_under_24_hours_but_deposit_still_returned():
    r = calculate_refund("CW-1003")  # 6h ahead
    assert r["refund_percent"] == 0
    assert r["rental_refund_eur"] == 0.0
    assert r["total_refund_eur"] == 50.0


def test_booking_fee_is_never_refunded():
    assert calculate_refund("CW-1001")["booking_fee_refund_eur"] == 0.0


# ---------- boundaries (lower bound is inclusive) ----------
def test_exactly_48_hours_is_100_percent():
    r = calculate_refund("CW-1007")  # starts exactly 48h after DATE_NOW
    assert r["hours_before_start"] == 48.0
    assert r["refund_percent"] == 100
    assert r["total_refund_eur"] == 186.0


def test_exactly_24_hours_is_50_percent():
    r = calculate_refund("CW-1010")  # starts exactly 24h after DATE_NOW
    assert r["hours_before_start"] == 24.0
    assert r["refund_percent"] == 50
    assert r["total_refund_eur"] == 170.0


def test_one_minute_later_drops_to_the_next_band():
    later = DATE_NOW + timedelta(minutes=1)
    assert calculate_refund("CW-1007", now=later)["refund_percent"] == 50
    assert calculate_refund("CW-1010", now=later)["refund_percent"] == 0


# ---------- payment method ----------
def test_voucher_is_refunded_as_voucher():
    r = calculate_refund("CW-1004")
    assert r["total_refund_eur"] == 73.0
    assert "voucher" in r["refund_method"].lower()


def test_card_refund_mentions_card_and_5_days():
    r = calculate_refund("CW-1001")
    assert "card" in r["refund_method"].lower()
    assert "5 working days" in r["refund_method"]


# ---------- statuses that cannot be cancelled ----------
@pytest.mark.parametrize("booking_id", ["CW-1005", "CW-1006", "CW-1008"])
def test_non_confirmed_bookings_get_nothing(booking_id):
    r = calculate_refund(booking_id)
    assert r["cancellable"] is False
    assert r["total_refund_eur"] == 0.0


# ---------- other cases ----------
def test_start_already_passed_gives_0_percent():
    late = datetime(2026, 6, 13, 12, 0, tzinfo=TZ)  # after CW-1001 started
    r = calculate_refund("CW-1001", now=late)
    assert r["refund_percent"] == 0
    assert r["total_refund_eur"] == 50.0


def test_refund_works_across_timezones():
    # Same instant as DATE_NOW, written in UTC. Result must not change.
    now_utc = datetime(2026, 6, 10, 7, 0, tzinfo=timezone.utc)
    assert calculate_refund("CW-1007", now=now_utc)["refund_percent"] == 100


def test_refund_unknown_booking_does_not_raise():
    assert calculate_refund("NOPE")["found"] is False


def test_seven_day_booking_uses_stored_discounted_price():
    assert calculate_refund("CW-1009")["total_refund_eur"] == 169.0