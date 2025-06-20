# Generated by Django 3.2.16 on 2022-12-19 07:31

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('helpdesk', '0008_approvalcode_cashapprover_frequest'),
    ]

    operations = [
        migrations.CreateModel(
            name='frequestdetail',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('datecreated', models.DateField(default=datetime.date.today)),
                ('type', models.CharField(max_length=50, null=True)),
                ('sn', models.CharField(max_length=50, null=True)),
                ('startdate', models.DateField(null=True)),
                ('starttime', models.CharField(max_length=15, null=True)),
                ('finishdate', models.DateField(null=True)),
                ('finishtime', models.CharField(max_length=15, null=True)),
                ('hardware', models.CharField(max_length=50, null=True)),
                ('software', models.CharField(max_length=50, null=True)),
                ('description', models.TextField(null=True)),
                ('prf_accepted', models.CharField(max_length=15, null=True)),
                ('prf_inbudget', models.BooleanField(default=False, null=True, verbose_name='In Budget?')),
                ('prf_underfive', models.BooleanField(default=False, null=True, verbose_name='underfive?')),
                ('prf_notes', models.TextField(null=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='helpdesk.employee')),
                ('frequest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='helpdesk.frequest')),
            ],
        ),
        migrations.CreateModel(
            name='crequest',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('code', models.CharField(max_length=20)),
                ('requestor', models.CharField(max_length=100, null=True)),
                ('costcentre', models.CharField(max_length=20)),
                ('proposaldate', models.DateField()),
                ('proposalyear', models.IntegerField(null=True)),
                ('amount', models.DecimalField(decimal_places=10, max_digits=19)),
                ('needdate', models.DateField()),
                ('purpose', models.TextField(null=True)),
                ('status', models.CharField(default='DELAYED', max_length=15, null=True)),
                ('datecreated', models.DateField(default=datetime.date.today)),
                ('timecreated', models.TimeField(auto_now=True)),
                ('est_settle', models.DateField(null=True)),
                ('department', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='helpdesk.department')),
                ('deptuser', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='deptuser', to='helpdesk.department')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='helpdesk.employee')),
                ('requestorid', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='requestorid', to='helpdesk.employee')),
            ],
        ),
        migrations.CreateModel(
            name='approvalfrhistory',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('datecreated', models.DateField(default=datetime.date.today)),
                ('status', models.CharField(max_length=18)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='helpdesk.department')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='helpdesk.employee')),
                ('frequest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='helpdesk.frequest')),
            ],
        ),
        migrations.CreateModel(
            name='approvalcrhistory',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('datecreated', models.DateField(default=datetime.date.today)),
                ('status', models.CharField(max_length=18)),
                ('crequest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='helpdesk.crequest')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='helpdesk.department')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='helpdesk.employee')),
            ],
        ),
    ]
