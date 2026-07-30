import django.db.models.deletion
from django.db import migrations, models


def backfill_message_history(apps, schema_editor):
    """Seed one history row per message that already exists.

    Without this the trail would begin at each guest's *next* edit, and the
    note the host has been reading for weeks would appear nowhere in it — the
    first edit would look like the original. Every message on record is
    therefore entered as its own first version.
    """
    RSVP = apps.get_model("invitations", "RSVP")
    RSVPMessage = apps.get_model("invitations", "RSVPMessage")
    for rsvp in RSVP.objects.exclude(message="").iterator():
        version = RSVPMessage.objects.create(rsvp=rsvp, body=rsvp.message)
        # `auto_now_add` stamps the insert with "now" and discards anything
        # passed to create(), so the real send time has to be written back
        # through a queryset update, which skips pre_save. Skipping this step
        # would have every pre-existing message claim it was sent the moment
        # this migration ran.
        RSVPMessage.objects.filter(pk=version.pk).update(
            created_at=rsvp.responded_at, updated_at=rsvp.responded_at
        )


class Migration(migrations.Migration):

    dependencies = [
        ("invitations", "0008_rsvp_seats"),
    ]

    operations = [
        migrations.CreateModel(
            name="RSVPMessage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("body", models.TextField()),
                (
                    "rsvp",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="message_history",
                        to="invitations.rsvp",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at", "id"],
            },
        ),
        # Reversing drops the table outright, so the backfill needs no undo of
        # its own — noop rather than a delete that would run just before it.
        migrations.RunPython(backfill_message_history, migrations.RunPython.noop),
    ]
