from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone

from .models import Invitation

User = get_user_model()

from rest_framework import serializers

ROLE_ALIAS = {
    "ADMIN": "ADMIN", "MANAGER": "MANAGER", "STAFF": "STAFF",
    "ROLE_ADMIN": "ADMIN", "ROLE_MANAGER": "MANAGER", "ROLE_STAFF": "STAFF",
    "MGR": "MANAGER",
}


def derive_role(user):
    if user.is_superuser:
        return "ADMIN"
    names = [g.name for g in user.groups.all()]  # get ALL groups
    up = [ROLE_ALIAS.get(n, n).upper() for n in names]

    for want in ("ADMIN", "MANAGER", "STAFF"):
        if want in up:
            return want

    return "STAFF"


class UserMeSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    groups = serializers.SlugRelatedField(slug_field="name", many=True, read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name",
                  "is_staff", "is_superuser", "groups", "role"]

    def get_role(self, obj):
        return derive_role(obj)


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    role = serializers.ChoiceField(choices=["admin", "manager", "staff"], required=False)  # <- writable

    class Meta:
        model = User
        fields = ("id","username","email","first_name","last_name",
                  "is_staff","is_superuser","password","role")
        read_only_fields = ("id","is_superuser")

    # representasi tetap otomatis dari groups
    def to_representation(self, instance):
        data = super().to_representation(instance)
        names = set(instance.groups.values_list("name", flat=True))
        data["role"] = "admin" if "admin" in names else ("manager" if "manager" in names else "staff")
        return data

    def _apply_role(self, user, role: str | None):
        if not role:
            return
        role = role.lower()
        if role not in ("admin","manager","staff"):
            raise serializers.ValidationError({"role":"Invalid role."})

        # hanya admin yang boleh set admin
        req = self.context.get("request")
        if role == "admin":
            ok = req and req.user and (req.user.is_superuser or req.user.groups.filter(name="admin").exists())
            if not ok:
                raise serializers.ValidationError({"role":"Only admin can assign admin role."})

        user.groups.clear()
        grp, _ = Group.objects.get_or_create(name=role)
        user.groups.add(grp)
        user.is_staff = (role in ("admin","manager"))

    def create(self, validated):
        pwd = validated.pop("password", None)
        role = validated.pop("role", None)
        user = User(**validated)
        user.set_password(pwd) if pwd else user.set_unusable_password()
        user.save()
        self._apply_role(user, role)
        user.save(update_fields=["is_staff"])
        return user

    def update(self, instance, validated):
        pwd = validated.pop("password", None)
        role = validated.pop("role", None)
        for k, v in validated.items():
            setattr(instance, k, v)
        if pwd:
            instance.set_password(pwd)
        self._apply_role(instance, role)
        instance.save()
        return instance

class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = ["id", "email", "role", "token", "expires_at", "used_at", "revoked_at", "created_at"]
        read_only_fields = ["id", "token", "used_at", "revoked_at", "created_at", "expires_at"]

    def get_status(self, obj):
        return obj.status

    def validate(self, attrs):
        if Invitation.objects.filter(
                email=attrs["email"],
                revoked_at__isnull=True,
                used_at__isnull=True,
                expires_at__gt=timezone.now(),
        ).exists():
            raise serializers.ValidationError("An active invitation for this email still exists.")
        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError("Email is already registered as a user.")
        return attrs

    def create(self, validated):
        validated["invited_by"] = self.context["request"].user
        validated["expires_at"] = timezone.now() + timezone.timedelta(hours=72)
        return super().create(validated)


class AcceptInvitationSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            inv = Invitation.objects.get(token=attrs["token"])
        except Invitation.DoesNotExist:
            raise serializers.ValidationError("Token is not valid.")

        if not inv.is_active:
            raise serializers.ValidationError("Token has been used, revoked, or expired.")

        if User.objects.filter(username=attrs["username"]).exists():
            raise serializers.ValidationError("Username is already taken.")

        if User.objects.filter(email=inv.email).exists():
            raise serializers.ValidationError("Email is already registered.")

        attrs["invitation"] = inv
        return attrs

    def create(self, validated):
        inv = validated["invitation"]
        user = User.objects.create_user(
            username=validated["username"],
            email=inv.email,
            password=validated["password"],
            is_staff=(inv.role in ["admin", "manager"]),
        )
        grp, _ = Group.objects.get_or_create(name=inv.role)
        user.groups.add(grp)
        inv.mark_used()
        return user