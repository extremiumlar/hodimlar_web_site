from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.db import models


class Department(models.Model):
    name = models.CharField("Nomi", max_length=100, unique=True)
    description = models.TextField("Tavsif", blank=True)

    class Meta:
        verbose_name = "Bo'lim"
        verbose_name_plural = "Bo'limlar"

    def __str__(self) -> str:
        return self.name


class Shift(models.Model):
    """Hodimning ish smenasi (masalan 09:00 - 18:00)."""
    name = models.CharField("Nomi", max_length=100)
    start_time = models.TimeField("Boshlanish")
    end_time = models.TimeField("Tugash")
    grace_minutes = models.PositiveIntegerField(
        "Kechikishga ruxsat (daqiqa)", default=5,
        help_text="Shu daqiqadan keyin kechikish hisoblanadi.",
    )
    work_days = models.CharField(
        "Ish kunlari",
        max_length=20,
        default="1,2,3,4,5",
        help_text="Vergul bilan: 1=Du, 7=Ya",
    )

    class Meta:
        verbose_name = "Smena"
        verbose_name_plural = "Smenalar"

    def __str__(self) -> str:
        return f"{self.name} ({self.start_time:%H:%M}-{self.end_time:%H:%M})"

    def work_day_set(self):
        return {int(x) for x in self.work_days.split(",") if x.strip().isdigit()}


class OfficeLocation(models.Model):
    """Ofis joyi: GPS markazi + radius + ruxsat berilgan IP whitelist."""
    name = models.CharField("Nomi", max_length=100)
    latitude = models.DecimalField("Kenglik", max_digits=9, decimal_places=6)
    longitude = models.DecimalField("Uzunlik", max_digits=9, decimal_places=6)
    radius_meters = models.PositiveIntegerField("Radius (m)", default=150)
    allowed_ips = models.TextField(
        "Ruxsat berilgan IP lar",
        blank=True,
        help_text="Har bir IP yangi qatorda. Bo'sh bo'lsa IP tekshirilmaydi.",
    )
    is_active = models.BooleanField("Faol", default=True)

    class Meta:
        verbose_name = "Ofis joyi"
        verbose_name_plural = "Ofis joylari"

    def __str__(self) -> str:
        return self.name

    def ip_whitelist(self) -> list[str]:
        return [ip.strip() for ip in self.allowed_ips.splitlines() if ip.strip()]


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        HR = "hr", "HR / Manager"
        EMPLOYEE = "employee", "Hodim"

    role = models.CharField(
        "Rol", max_length=20, choices=Role.choices, default=Role.EMPLOYEE
    )
    phone = models.CharField("Telefon", max_length=20, blank=True)
    telegram_id = models.CharField("Telegram ID", max_length=50, blank=True)

    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="employees", verbose_name="Bo'lim",
    )
    shift = models.ForeignKey(
        Shift, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="employees", verbose_name="Smena",
    )
    office = models.ForeignKey(
        OfficeLocation, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="employees", verbose_name="Ofis",
    )

    base_salary = models.DecimalField(
        "Asosiy oylik", max_digits=12, decimal_places=2, default=Decimal("0.00"),
    )
    weekend_rate = models.DecimalField(
        "Dam olish kuni stavkasi (%)", max_digits=5, decimal_places=2,
        default=Decimal("150.00"),
        help_text="Oddiy kun stavkasiga nisbatan foiz. 150 = 1.5x",
    )
    late_penalty_per_minute = models.DecimalField(
        "1 daqiqa kechikish jarimasi", max_digits=10, decimal_places=2,
        default=Decimal("0.00"),
    )
    is_on_leave = models.BooleanField("Ta'tilda", default=False)

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self) -> str:
        return self.get_full_name() or self.username

    @property
    def is_admin_role(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_hr_role(self) -> bool:
        return self.role in {self.Role.ADMIN, self.Role.HR} or self.is_superuser
