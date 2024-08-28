# Generated by Django 4.1.7 on 2023-05-19 02:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shioaji_app', '0004_kbar_stock'),
    ]

    operations = [
        migrations.CreateModel(
            name='Industry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=10)),
            ],
        ),
        migrations.AddField(
            model_name='stock',
            name='industries',
            field=models.ManyToManyField(to='shioaji_app.industry'),
        ),
    ]
