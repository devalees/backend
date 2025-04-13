from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('filtering', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestGroupingModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(max_length=100)),
                ('subcategory', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=100)),
                ('value', models.IntegerField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
    ] 