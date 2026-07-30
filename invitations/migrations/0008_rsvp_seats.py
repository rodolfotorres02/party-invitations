from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("invitations", "0007_alter_party_template_choice"),
    ]

    operations = [
        migrations.AddField(
            model_name="rsvp",
            name="seats",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                help_text=(
                    "Seats the guest confirmed, up to the invitation's num_guests."
                ),
            ),
        ),
    ]
