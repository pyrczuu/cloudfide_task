"""Tools the agent can call. Pure Python: no LLM in here."""
import json
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from helpdesk.config import BOOKINGS_FILE, DATE_NOW

CENT = Decimal("0.01")


def _money(value) -> Decimal:
    # Go through str() so 0.1 becomes Decimal("0.1"), not a long binary float.
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def _load_bookings() -> list[dict]:
    with open(BOOKINGS_FILE, encoding="utf-8") as f:
        return json.load(f)


def _find(booking_id: str) -> dict | None:
    wanted = str(booking_id).strip().upper()
    for booking in _load_bookings():
        if booking["id"].upper() == wanted:
            return booking
    return None


def _not_found(booking_id) -> dict:
    return {
        "found": False,
        "booking_id": str(booking_id),
        "message": "No booking with this number exists.",
    }


def get_booking(booking_id: str) -> dict:
    """Return one booking, or a clear 'not found' result. Never raises."""
    booking = _find(booking_id)
    if booking is None:
        return _not_found(booking_id)
    return {"found": True, "booking": booking}


def calculate_refund(booking_id: str, now: datetime = DATE_NOW) -> dict:
    """How much does the customer get back if they cancel at `now`?

    `now` is NOT a parameter the model can set: the agent code never exposes it.
    Tests pass it explicitly so results are deterministic.
    """
    booking = _find(booking_id)
    if booking is None:
        return _not_found(booking_id)

    result = {
        "found": True,
        "booking_id": booking["id"],
        "status": booking["status"],
        "booking_fee_refund_eur": 0.0,  # never refunded
    }

    # Rule 1: only `confirmed` bookings can be cancelled.
    if booking["status"] != "confirmed":
        result.update(
            cancellable=False,
            rule_applied=f"Status is '{booking['status']}': it cannot be cancelled, nothing is refunded.",
            refund_percent=0,
            rental_refund_eur=0.0,
            deposit_refund_eur=0.0,
            total_refund_eur=0.0,
            refund_method=None,
        )
        return result

    # Rule 2: percentage of the rental price depends on time before start.
    # Compare timedeltas (exact) instead of floats, so 48h exactly means 48h.
    time_left = datetime.fromisoformat(booking["start"]) - now
    if time_left >= timedelta(hours=48):
        percent, rule = 100, "Cancelled 48 hours or more before the start: 100% of the rental price."
    elif time_left >= timedelta(hours=24):
        percent, rule = 50, "Cancelled 24 to 48 hours before the start: 50% of the rental price."
    else:
        percent, rule = 0, "Cancelled less than 24 hours before the start: 0% of the rental price."

    # Rule 3: deposit always comes back in full; booking fee never does.
    rental_refund = (_money(booking["rental_price_eur"]) * percent / 100).quantize(CENT, ROUND_HALF_UP)
    deposit_refund = _money(booking["deposit_eur"])
    total = rental_refund + deposit_refund

    # Rule 4: refund goes back the way it was paid.
    if booking["paid_with"] == "voucher":
        method = "A new voucher of the same value (never money)."
    else:
        method = "Back to the same card within 5 working days."

    result.update(
        cancellable=True,
        hours_before_start=round(time_left.total_seconds() / 3600, 2),
        rule_applied=rule,
        refund_percent=percent,
        rental_refund_eur=float(rental_refund),
        deposit_refund_eur=float(deposit_refund),
        total_refund_eur=float(total),
        refund_method=method,
    )
    return result


# Re-exported so every tool can be imported from one place.
from helpdesk.search import search_policies  # noqa: E402,F401