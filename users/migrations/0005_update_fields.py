from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_offerhistory'),
    ]

    operations = [
        migrations.RemoveField(model_name='negotiationsession', name='title'),
        migrations.RemoveField(model_name='negotiationsession', name='description'),
        migrations.RemoveField(model_name='negotiationsession', name='scenario'),
        migrations.RemoveField(model_name='negotiationsession', name='strategy'),
        migrations.RemoveField(model_name='negotiationsession', name='score'),
        migrations.RemoveField(model_name='negotiationsession', name='outcome'),
        migrations.AddField(model_name='negotiationsession', name='ai_reservation_price', field=models.FloatField(default=0)),
        migrations.AddField(model_name='negotiationsession', name='turn_count', field=models.IntegerField(default=0)),
        migrations.AddField(model_name='negotiationsession', name='status', field=models.CharField(choices=[('active', 'Active'), ('completed', 'Completed')], default='active', max_length=20)),
        migrations.AddField(model_name='negotiationsession', name='outcome', field=models.CharField(blank=True, choices=[('accepted', 'Accepted'), ('declined', 'Declined')], max_length=20, null=True)),
        migrations.AddField(model_name='negotiationsession', name='final_price', field=models.FloatField(blank=True, null=True)),
        migrations.AddField(model_name='negotiationsession', name='human_profit', field=models.FloatField(blank=True, null=True)),
        migrations.AddField(model_name='negotiationsession', name='ai_profit', field=models.FloatField(blank=True, null=True)),
        migrations.AddField(model_name='negotiationsession', name='ended_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='dialogueturn', name='turn_number', field=models.IntegerField(default=0)),
        migrations.AddField(model_name='offerhistory', name='turn_number', field=models.IntegerField(default=0)),
        migrations.AddField(model_name='offerhistory', name='concession_amount', field=models.FloatField(blank=True, null=True)),
        migrations.AddField(model_name='offerhistory', name='concession_percentage', field=models.FloatField(blank=True, null=True)),
    ]