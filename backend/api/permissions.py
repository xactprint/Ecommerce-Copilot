from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsStaffOrReadOnly(BasePermission):
    """Autorise la lecture à tout utilisateur connecté, l'écriture au staff.

    L'authentification reste assurée par ``IsAuthenticated``. Cette permission
    ajoute uniquement la restriction des créations, modifications et
    suppressions aux comptes staff, y compris pour le compte de démonstration.
    """

    message = "Les opérations d'écriture sont réservées aux comptes staff."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )
