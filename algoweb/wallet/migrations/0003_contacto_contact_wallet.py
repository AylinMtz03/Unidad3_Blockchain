# Generated migration to add contact_wallet field
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0002_contacto'),
    ]

    operations = [
        migrations.AddField(
            model_name='contacto',
            name='contact_wallet',
            field=models.CharField(max_length=58, null=True, blank=True),
        ),
    ]
