# Generated by Django 5.0 on 2023-12-06 10:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recommender', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='formatted_image',
            field=models.ImageField(blank=True, null=True, upload_to='clients/'),
        ),
        migrations.AlterField(
            model_name='client',
            name='inferred_model',
            field=models.FileField(blank=True, null=True, upload_to='clients/'),
        ),
        migrations.AlterField(
            model_name='client',
            name='model_image',
            field=models.ImageField(blank=True, null=True, upload_to='clients/'),
        ),
        migrations.AlterField(
            model_name='client',
            name='overlayed_image',
            field=models.ImageField(blank=True, null=True, upload_to='clients/'),
        ),
        migrations.AlterField(
            model_name='review',
            name='formatted_image',
            field=models.ImageField(blank=True, null=True, upload_to='reviews/'),
        ),
        migrations.AlterField(
            model_name='review',
            name='inferred_model',
            field=models.FileField(blank=True, null=True, upload_to='reviews/'),
        ),
        migrations.AlterField(
            model_name='review',
            name='model_image',
            field=models.ImageField(blank=True, null=True, upload_to='reviews/'),
        ),
        migrations.AlterField(
            model_name='review',
            name='overlayed_image',
            field=models.ImageField(blank=True, null=True, upload_to='reviews/'),
        ),
    ]
