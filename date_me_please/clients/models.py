from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class Profile(models.Model):
    """
    Модель профиля пользователя.

    Создана для расширения базовой модели пользователя.
    """

    class Gender(models.TextChoices):
        """Класс для выбора гендера"""

        MALE = 'M', _('Мужской')
        FEMALE = 'F', _('Женский')

    avatar = models.ImageField(
        upload_to='user_avatars',
        null=True,
        blank=True,
        verbose_name=_('Аватар'),
    )
    gender = models.CharField(
        max_length=2,
        choices=Gender.choices,
        verbose_name=_('Пол'),
    )
    lovers = models.ManyToManyField(
        to='Profile',
        symmetrical=False,
        blank=True,
        verbose_name=_('Оценившие'),
    )
    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('Пользователь')
    )

    class Meta:
        """Класс настроек модели"""
        verbose_name = _('Профиль пользователя')
        verbose_name_plural = _('Профили пользователей')

    def __str__(self) -> str:
        return f'{self.user} profile'
