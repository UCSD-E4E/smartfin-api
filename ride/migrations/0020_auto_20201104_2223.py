# Generated by Django 3.1 on 2020-11-04 22:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ride', '0019_auto_20201104_2223'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ridedata',
            name='motionData',
        ),
        migrations.RemoveField(
            model_name='ridedata',
            name='oceanData',
        ),
    ]
