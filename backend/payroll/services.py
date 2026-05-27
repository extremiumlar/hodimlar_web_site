"""Avtomatik oylik hisoblash."""
from __future__ import annotations
from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db.models import Sum

from accounts.models import User
from attendance.models import Attendance
from .models import MonthlyPayroll, Bonus, Penalty


def _parse_period(period: str) -> tuple[int, int]:
    y, m = period.split("-")
    return int(y), int(m)


def compute_payroll(user: User, period: str) -> MonthlyPayroll:
    """Berilgan oy uchun hodim oyligini hisoblaydi va saqlaydi."""
    year, month = _parse_period(period)
    days_in_month = monthrange(year, month)[1]
    start = date(year, month, 1)
    end = date(year, month, days_in_month)

    work_day_set = user.shift.work_day_set() if user.shift else {1, 2, 3, 4, 5}
    work_days_total = sum(1 for d in range(1, days_in_month + 1)
                          if date(year, month, d).isoweekday() in work_day_set)

    atts = Attendance.objects.filter(user=user, date__gte=start, date__lte=end)
    worked = atts.filter(check_in_time__isnull=False).count()
    late_min = atts.aggregate(s=Sum("late_minutes"))["s"] or 0
    weekend_worked = atts.filter(is_weekend=True, check_in_time__isnull=False).count()
    absent = max(0, work_days_total - atts.filter(
        is_weekend=False, check_in_time__isnull=False
    ).count())

    base = Decimal(user.base_salary or 0)
    # Dam olish kuni qo'shimchasi:
    # bir kunlik oddiy stavka = base / work_days_total
    per_day = (base / work_days_total) if work_days_total else Decimal("0")
    weekend_rate = Decimal(user.weekend_rate or 0) / Decimal("100")
    weekend_extra = (per_day * weekend_rate * weekend_worked).quantize(Decimal("0.01"))

    late_penalty = (Decimal(user.late_penalty_per_minute or 0) * late_min).quantize(Decimal("0.01"))

    bonus_total = Bonus.objects.filter(user=user, period=period).aggregate(
        s=Sum("amount"))["s"] or Decimal("0")
    penalty_total = Penalty.objects.filter(user=user, period=period).aggregate(
        s=Sum("amount"))["s"] or Decimal("0")

    # Asosiy oylikni kelmagan kunlarga proporsional kamaytirish:
    if work_days_total:
        effective_base = (base * (work_days_total - absent) / work_days_total).quantize(Decimal("0.01"))
    else:
        effective_base = base

    total = (
        effective_base + weekend_extra + bonus_total
        - penalty_total - late_penalty
    ).quantize(Decimal("0.01"))

    payroll, _ = MonthlyPayroll.objects.update_or_create(
        user=user, period=period,
        defaults=dict(
            base_salary=effective_base,
            weekend_extra=weekend_extra,
            bonus_total=bonus_total,
            penalty_total=penalty_total,
            late_penalty_total=late_penalty,
            total=total,
            worked_days=worked,
            weekend_days=weekend_worked,
            late_minutes=late_min,
            absent_days=absent,
        ),
    )
    return payroll


def compute_payroll_for_all(period: str) -> list[MonthlyPayroll]:
    return [compute_payroll(u, period) for u in User.objects.filter(is_active=True)]
