from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from assets.models import Customer

class Command(BaseCommand):
    help = 'Creates customer profiles for users that don\'t have one'

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        created = 0
        for user in users:
            if not hasattr(user, 'customer'):
                Customer.objects.create(
                    user=user,
                    name=user.get_full_name() or user.username
                )
                created += 1
        self.stdout.write(
            self.style.SUCCESS(f'Created {created} customer profiles')
        )