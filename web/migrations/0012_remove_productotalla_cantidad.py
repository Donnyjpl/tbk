# Generated by Django 5.1.5 on 2025-02-22 04:44

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("web", "0011_color_profile_acepta_terminos_lineaventa_color_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="productotalla",
            name="cantidad",
        ),
    ]
