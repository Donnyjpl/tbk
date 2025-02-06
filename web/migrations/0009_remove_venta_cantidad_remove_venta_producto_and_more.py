# Generated by Django 5.1.5 on 2025-02-06 04:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("web", "0008_venta_talla"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="venta",
            name="cantidad",
        ),
        migrations.RemoveField(
            model_name="venta",
            name="producto",
        ),
        migrations.RemoveField(
            model_name="venta",
            name="talla",
        ),
        migrations.AddField(
            model_name="venta",
            name="total",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.CreateModel(
            name="LineaVenta",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("cantidad", models.PositiveIntegerField()),
                (
                    "precio_unitario",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                (
                    "producto",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="web.producto"
                    ),
                ),
                (
                    "talla",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="web.productotalla",
                    ),
                ),
                (
                    "venta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lineas",
                        to="web.venta",
                    ),
                ),
            ],
        ),
        migrations.DeleteModel(
            name="Factura",
        ),
    ]
