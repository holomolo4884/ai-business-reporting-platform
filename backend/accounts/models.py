from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Менеджер пользователей с email вместо username"""

    def create_user(self, email: str, password: str = None, **extra_fields):
        if not email:
            raise ValueError("Пользователь должен иметь email адрес")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Супер пользователь должен иметь is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Супер пользователь должен иметь is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Кастомная модель пользователя с email как основным идентификатором"""

    email = models.EmailField(unique=True, verbose_name="email address")
    username = models.CharField(max_length=150, blank=True)

    # Используем email для аутентификации
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
