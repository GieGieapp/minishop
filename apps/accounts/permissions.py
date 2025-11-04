from rest_framework.permissions import BasePermission, SAFE_METHODS


def _group_names(user) -> set[str]:
    if not getattr(user, "is_authenticated", False):
        return set()
    if getattr(user, "is_superuser", False):
        return {"ADMIN", "MANAGER", "STAFF"}
    if not hasattr(user, "_grp_upper"):
        user._grp_upper = set(n.upper() for n in user.groups.values_list("name", flat=True))
    return user._grp_upper

def in_group(user, name: str) -> bool:
    return user.is_authenticated and (user.is_superuser or name.upper() in _group_names(user))

def in_any(user, names: list[str]) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    g = _group_names(user)
    want = {n.upper() for n in names}
    return not g.isdisjoint(want)


class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        return in_any(request.user, ["admin", "manager"])


class RBACUserPermission(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        if not u or not u.is_authenticated:
            return False
        if u.is_superuser or in_group(u, "admin"):
            return True
        if in_group(u, "manager"):
            return request.method in SAFE_METHODS
        if in_group(u, "staff"):
            return False
        return False


class RBACProductPermission(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        if not u or not u.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return in_any(u, ["admin", "manager"])

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return in_any(request.user, ["admin", "manager"])


class RBACOrderPermission(BasePermission):
    def has_permission(self, request, view):
        u = request.user

        if not u or not u.is_authenticated:
            return False
        if u.is_superuser or in_group(u, "admin"):
            return True
        if in_any(u, ["manager", "staff"]):
            return request.method in SAFE_METHODS
        return False

    def has_object_permission(self, request, view, obj):

        if request.method in SAFE_METHODS:
            return True
        return in_group(request.user, "admin")
