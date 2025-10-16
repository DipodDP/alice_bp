from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("alice_skill", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="bloodpressuremeasurement",
            name="user_id",
            field=models.CharField(max_length=255, db_index=True),
            preserve_default=False,
        ),
    ]


