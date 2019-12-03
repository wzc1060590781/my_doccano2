from rest_framework.permissions import BasePermission


class LabelOperationPermission(BasePermission):
    def has_permission(self, request, view):
        user_id = request.user.id
        self.user_id = user_id
        if request.user.is_superuser:
            return True
        else:
            return False