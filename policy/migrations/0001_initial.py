# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-21 22:59
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Configuration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.PositiveSmallIntegerField(choices=[(1, 'Challenge Token Length'), (2, 'Challenge Expiration (Minutes)'), (3, 'Enrollment Expiration (Minutes)')])),
                ('value', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='Policy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_updated_at', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Rule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.PositiveSmallIntegerField(choices=[(1, 'Device Selection Restriction'), (2, 'E-mail Domain Restriction')])),
                ('definition', django.contrib.postgres.fields.jsonb.JSONField()),
                ('policy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rules', to='policy.Policy')),
            ],
        ),
        migrations.AddField(
            model_name='configuration',
            name='policy',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='configurations', to='policy.Policy'),
        ),
        migrations.AlterUniqueTogether(
            name='rule',
            unique_together=set([('policy', 'kind')]),
        ),
        migrations.AlterUniqueTogether(
            name='configuration',
            unique_together=set([('policy', 'kind')]),
        ),
    ]
