# Generated by Django 4.0.2 on 2022-02-25 06:02

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avatar', models.ImageField(upload_to='user_avatars', verbose_name='Аватар')),
                ('gender', models.CharField(choices=[('M', 'Мужской'), ('F', 'Женский')], max_length=2, verbose_name='Пол')),
                ('latitude', models.DecimalField(decimal_places=13, help_text='Восточное направление считается положительным. Западное - отрицательным.', max_digits=16, validators=[django.core.validators.MinValueValidator(-180), django.core.validators.MaxValueValidator(180)], verbose_name='Широта')),
                ('longitude', models.DecimalField(decimal_places=13, help_text='Северное направление считается положительным. Южное - отрицательным.', max_digits=16, validators=[django.core.validators.MinValueValidator(-180), django.core.validators.MaxValueValidator(180)], verbose_name='Долгота')),
                ('lovers', models.ManyToManyField(blank=True, to='clients.Profile', verbose_name='Оценившие')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Профиль пользователя',
                'verbose_name_plural': 'Профили пользователей',
            },
        ),
    ]
