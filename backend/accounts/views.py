from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import User, Department, Shift, OfficeLocation
from .serializers import (
    UserSerializer, UserCreateSerializer,
    DepartmentSerializer, ShiftSerializer, OfficeLocationSerializer,
    MeSerializer,
)
from .permissions import IsHRRole


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related("department", "shift", "office").all()
    filterset_fields = ["role", "department", "is_active", "is_on_leave"]
    search_fields = ["username", "first_name", "last_name", "email", "phone"]
    ordering_fields = ["date_joined", "username", "first_name"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in {"list", "create", "destroy", "partial_update", "update"}:
            return [permissions.IsAuthenticated(), IsHRRole()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if not u.is_hr_role:
            qs = qs.filter(id=u.id)
        return qs

    @action(detail=False, methods=["get", "patch"], url_path="me")
    def me(self, request):
        if request.method == "GET":
            return Response(MeSerializer(request.user).data)
        ser = MeSerializer(request.user, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    @action(detail=True, methods=["post"], url_path="set-password",
            permission_classes=[permissions.IsAuthenticated, IsHRRole])
    def set_password(self, request, pk=None):
        user = self.get_object()
        pwd = request.data.get("password")
        if not pwd or len(pwd) < 6:
            return Response({"detail": "Parol kamida 6 ta belgi."}, status=400)
        user.set_password(pwd)
        user.save(update_fields=["password"])
        return Response({"detail": "Parol yangilandi."})


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsHRRole]


class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [permissions.IsAuthenticated, IsHRRole]


class OfficeLocationViewSet(viewsets.ModelViewSet):
    queryset = OfficeLocation.objects.all()
    serializer_class = OfficeLocationSerializer
    permission_classes = [permissions.IsAuthenticated, IsHRRole]
