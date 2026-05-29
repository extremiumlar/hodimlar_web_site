from datetime import timedelta
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from accounts.permissions import IsHRRole
from .models import Attendance
from .serializers import AttendanceSerializer, CheckInRequestSerializer
from .services import perform_check_in, perform_check_out, CheckInError, CheckInPayload


class AttendanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Attendance.objects.select_related("user", "user__department").all()
    serializer_class = AttendanceSerializer
    filterset_fields = ["user", "date", "status", "is_weekend"]
    ordering_fields = ["date", "check_in_time"]

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if not u.is_hr_role:
            qs = qs.filter(user=u)
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs

    @action(detail=False, methods=["post"], url_path="check-in")
    def check_in(self, request):
        ser = CheckInRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            att = perform_check_in(
                request.user,
                CheckInPayload(
                    latitude=ser.validated_data["latitude"],
                    longitude=ser.validated_data["longitude"],
                ),
            )
        except CheckInError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        # Notify on late
        if att.late_minutes > 0:
            from notifications.telegram import notify_late_check_in
            notify_late_check_in(att)
        return Response(AttendanceSerializer(att).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="check-out")
    def check_out(self, request):
        ser = CheckInRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            att = perform_check_out(
                request.user,
                CheckInPayload(
                    latitude=ser.validated_data["latitude"],
                    longitude=ser.validated_data["longitude"],
                ),
            )
        except CheckInError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        if att.early_leave_minutes > 0:
            from notifications.telegram import notify_early_leave
            notify_early_leave(att)
        return Response(AttendanceSerializer(att).data)

    @action(detail=False, methods=["get"], url_path="today")
    def today(self, request):
        """Bugungi davomat (foydalanuvchi uchun)."""
        today = timezone.localdate()
        att = Attendance.objects.filter(user=request.user, date=today).first()
        if not att:
            return Response({"detail": "Bugun hali check-in qilinmagan."}, status=204)
        return Response(AttendanceSerializer(att).data)

    @action(detail=False, methods=["get"], url_path="live",
            permission_classes=[permissions.IsAuthenticated, IsHRRole])
    def live(self, request):
        """Hozir ofisda kim borligi (admin uchun)."""
        today = timezone.localdate()
        present = Attendance.objects.filter(
            date=today,
            check_in_time__isnull=False,
            check_out_time__isnull=True,
        ).select_related("user")
        absent = User.objects.filter(
            is_active=True, is_on_leave=False
        ).exclude(
            attendances__date=today, attendances__check_in_time__isnull=False,
        ).values("id", "first_name", "last_name", "username")
        return Response({
            "in_office": AttendanceSerializer(present, many=True).data,
            "absent": list(absent),
            "on_leave": list(User.objects.filter(is_on_leave=True).values(
                "id", "first_name", "last_name", "username"
            )),
        })

    @action(detail=False, methods=["get"], url_path="stats",
            permission_classes=[permissions.IsAuthenticated, IsHRRole])
    def stats(self, request):
        """Haftalik / oylik statistika."""
        days = int(request.query_params.get("days", 30))
        since = timezone.localdate() - timedelta(days=days)

        qs = Attendance.objects.filter(date__gte=since)
        by_day = (
            qs.values("date")
              .annotate(
                  total=Count("id"),
                  late=Count("id", filter=Q(status="late")),
                  present=Count("id", filter=Q(status="present")),
                  absent=Count("id", filter=Q(status="absent")),
              )
              .order_by("date")
        )
        late_top = (
            qs.values("user__id", "user__first_name", "user__last_name", "user__username")
              .annotate(
                  late_count=Count("id", filter=Q(status="late")),
                  late_total_min=Sum("late_minutes"),
              )
              .order_by("-late_total_min")[:10]
        )
        worked_top = (
            qs.values("user__id", "user__first_name", "user__last_name", "user__username")
              .annotate(worked=Sum("worked_minutes"))
              .order_by("-worked")[:10]
        )
        return Response({
            "by_day": list(by_day),
            "late_top": list(late_top),
            "worked_top": list(worked_top),
        })
