from django.db import models
from django.core import validators
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
        verbose_name=_('Аватар'),
        null=True,
    )
    gender = models.CharField(
        max_length=2,
        choices=Gender.choices,
        verbose_name=_('Пол'),
    )
    latitude = models.DecimalField(
        max_digits=16,
        decimal_places=13,
        validators=[validators.MinValueValidator(-180),
                    validators.MaxValueValidator(180)],
        verbose_name=_('Широта'),
        help_text=_('Восточное направление считается положительным. '
                    'Западное - отрицательным.')
    )
    longitude = models.DecimalField(
        max_digits=16,
        decimal_places=13,
        validators=[validators.MinValueValidator(-180),
                    validators.MaxValueValidator(180)],
        verbose_name=_('Долгота'),
        help_text=_('Северное направление считается положительным. '
                    'Южное - отрицательным.')
    )
    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('Пользователь')
    )
    lovers = models.ManyToManyField(
        to='Profile',
        symmetrical=False,
        blank=True,
        verbose_name=_('Оценившие'),
    )

    class Meta:
        """Класс настроек модели"""
        verbose_name = _('Профиль пользователя')
        verbose_name_plural = _('Профили пользователей')

    def __str__(self) -> str:
        return f'{_("Профиль")} пользователя {self.user}'
