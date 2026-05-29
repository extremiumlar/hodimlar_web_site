"""Check-in / Check-out logikasi (faqat GPS tekshiruvi).

Hisoblash (kechikish, ishlangan vaqt) `Attendance.save()` ichida avtomatik
bajariladi — bu yerda faqat GPS tekshiruvi va vaqtlarni yozish.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from django.utils import timezone

from .models import Attendance
from .utils import haversine_distance


class CheckInError(Exception):
    """Check-in xatosi (foydalanuvchiga ko'rsatiladi)."""


@dataclass
class CheckInPayload:
    latitude: float
    longitude: float


def _validate_office(user, payload: CheckInPayload) -> int:
    office = user.office
    if office is None or not office.is_active:
        raise CheckInError("Sizga ofis biriktirilmagan. Adminga murojaat qiling.")

    distance = haversine_distance(
        float(office.latitude), float(office.longitude),
        payload.latitude, payload.longitude,
    )
    if distance > office.radius_meters:
        raise CheckInError(
            f"Siz ofis hududidan tashqaridasiz ({int(distance)} m). "
            f"Avval ofisga keling."
        )
    return int(distance)


def perform_check_in(user, payload: CheckInPayload) -> Attendance:
    if user.is_on_leave:
        raise CheckInError("Siz ta'tildasiz. Adminga murojaat qiling.")
    if user.shift is None:
        raise CheckInError("Sizga smena biriktirilmagan.")

    distance = _validate_office(user, payload)
    today = timezone.localdate()
    now = timezone.localtime()

    att, _ = Attendance.objects.get_or_create(user=user, date=today)
    if att.check_in_time:
        raise CheckInError("Siz bugun allaqachon check-in qilgansiz.")

    att.check_in_time = now
    att.check_in_lat = Decimal(str(payload.latitude))
    att.check_in_lng = Decimal(str(payload.longitude))
    att.check_in_distance_m = distance
    att.save()  # ← bu yerda recalculate() avtomatik chaqiriladi
    return att


def perform_check_out(user, payload: CheckInPayload) -> Attendance:
    today = timezone.localdate()
    try:
        att = Attendance.objects.get(user=user, date=today)
    except Attendance.DoesNotExist:
        raise CheckInError("Avval check-in qilishingiz kerak.")
    if not att.check_in_time:
        raise CheckInError("Avval check-in qilishingiz kerak.")
    if att.check_out_time:
        raise CheckInError("Siz bugun allaqachon check-out qilgansiz.")

    _validate_office(user, payload)
    now = timezone.localtime()
    att.check_out_time = now
    att.check_out_lat = Decimal(str(payload.latitude))
    att.check_out_lng = Decimal(str(payload.longitude))
    att.save()  # ← recalculate() worked_minutes, early_leave_minutes ni yangilaydi
    return att
