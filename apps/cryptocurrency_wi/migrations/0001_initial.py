# Generated by Django 5.1.4 on 2024-12-23 15:39

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CriptoCoin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coin', models.CharField(max_length=4)),
                ('short_title', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='CoinInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=2000)),
                ('rank', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)])),
                ('capitalization', models.FloatField()),
                ('diluted_valuation', models.FloatField()),
                ('dominance', models.FloatField()),
                ('circulating_offer', models.FloatField()),
                ('max_price', models.FloatField()),
                ('min_price', models.FloatField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('cripto_coin', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cryptocurrency_wi.criptocoin')),
            ],
        ),
    ]
