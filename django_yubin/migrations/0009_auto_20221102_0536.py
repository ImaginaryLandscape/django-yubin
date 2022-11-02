# Generated by Django 3.2.15 on 2022-11-02 10:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_yubin', '0008_auto_20200320_0407'),
    ]

    operations = [
        migrations.RenameField(
            model_name='message',
            old_name='encoded_message',
            new_name='_encoded_message',
        ),
        migrations.AlterField(
            model_name='log',
            name='date',
            field=models.DateTimeField(auto_now_add=True, verbose_name='date'),
        ),
        migrations.AlterField(
            model_name='message',
            name='_encoded_message',
            field=models.TextField(db_column='encoded_message', verbose_name='encoded message'),
        ),
    ]
