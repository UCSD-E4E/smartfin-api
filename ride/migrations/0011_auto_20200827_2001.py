# Generated by Django 3.1 on 2020-08-27 20:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ride', '0010_auto_20200827_1900'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ridedata',
            old_name='city',
            new_name='loc1',
        ),
        migrations.RenameField(
            model_name='ridedata',
            old_name='state',
            new_name='loc2',
        ),
        migrations.AddField(
            model_name='ridedata',
            name='loc3',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]