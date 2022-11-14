# Generated by Django 4.1.3 on 2022-11-14 06:53

from django.db import migrations, models
import django.db.models.deletion
import studios.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Class',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('coach', models.CharField(max_length=200)),
                ('capacity', models.PositiveIntegerField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
            ],
            options={
                'verbose_name': 'Class',
                'verbose_name_plural': 'Classes',
            },
        ),
        migrations.CreateModel(
            name='Studio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('address', models.CharField(max_length=200)),
                ('latitude', models.DecimalField(decimal_places=8, max_digits=10, validators=[studios.models.validate_latitude])),
                ('longitude', models.DecimalField(decimal_places=8, max_digits=11, validators=[studios.models.validate_longitude])),
                ('postal_code', models.CharField(max_length=6, unique=True)),
                ('phone', models.CharField(max_length=10)),
            ],
            options={
                'verbose_name': 'Studio',
                'verbose_name_plural': 'Studios',
            },
        ),
        migrations.CreateModel(
            name='StudioImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, null=True, upload_to='images/')),
                ('studio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='studios.studio')),
            ],
            options={
                'verbose_name': 'Studio Image',
                'verbose_name_plural': 'Studio Images',
            },
        ),
        migrations.CreateModel(
            name='StudioAmenities',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=200)),
                ('quantity', models.PositiveIntegerField()),
                ('studio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='studios.studio')),
            ],
            options={
                'verbose_name': 'Studio Amenities',
                'verbose_name_plural': 'Studio Amenities',
            },
        ),
        migrations.CreateModel(
            name='Keyword',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('word', models.CharField(max_length=255)),
                ('cls', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='studios.class')),
            ],
            options={
                'verbose_name': 'Keyword',
                'verbose_name_plural': 'Keywords',
            },
        ),
        migrations.CreateModel(
            name='ClassTime',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.IntegerField(choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')])),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('cls', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='studios.class')),
            ],
            options={
                'verbose_name': 'Class Time',
                'verbose_name_plural': 'Class Times',
            },
        ),
        migrations.CreateModel(
            name='ClassInstance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('start_date_and_time', models.DateTimeField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('enrolled', models.PositiveIntegerField(default=0)),
                ('capacity', models.PositiveIntegerField()),
                ('coach', models.CharField(max_length=200)),
                ('cls', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='studios.class')),
            ],
            options={
                'verbose_name': 'Class Instance',
                'verbose_name_plural': 'Class Instances',
            },
        ),
        migrations.AddField(
            model_name='class',
            name='studio',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='studios.studio'),
        ),
    ]
