from django.conf import settings
from django.db import models


class Organization(models.Model):
    """Модель организации."""

    name = models.CharField(
        max_length=255,
        verbose_name="Organization name",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created at",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated at",
    )

    class Meta:
        verbose_name = "organization"
        verbose_name_plural = "organizations"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class OrganizationMember(models.Model):
    """Связь пользователя с организацией."""

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="members",
        verbose_name="Organization",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
        verbose_name="User",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
        verbose_name="Role",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Joined at",
    )

    class Meta:
        verbose_name = "organization member"
        verbose_name_plural = "organization members"
        # Пользователь может быть участником организации только один раз
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"],
                name="unique_organization_member",
            )
        ]
        ordering = ["organization", "role"]

    def __str__(self):
        return f"{self.user.email} in {self.organization.name} ({self.role})"

    @property
    def is_owner(self) -> bool:
        return self.role == self.Role.OWNER

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN

    @property
    def is_member(self) -> bool:
        return self.role == self.Role.MEMBER
