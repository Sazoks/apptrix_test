# Generated by Django 4.0.2 on 2022-02-23 07:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0002_alter_profile_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='lovers',
            field=models.ManyToManyField(to='clients.Profile', verbose_name='Оценившие'),
        ),
    ]