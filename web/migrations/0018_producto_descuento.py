# Generated by Django 5.1.5 on 2025-03-10 18:30

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("web", "0017_venta_envio"),
    ]

    operations = [
        migrations.AddField(
            model_name="producto",
            name="descuento",
            field=models.IntegerField(
                default=0, help_text="Porcentaje de descuento (0-100)"
            ),
        ),
    ]
