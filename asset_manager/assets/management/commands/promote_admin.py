from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from assets.models import UserRole

class Command(BaseCommand):
    help = 'Promotes a user to administrator role'

    def add_arguments(self, parser):
        parser.add_argument('username', nargs='?', type=str, help='Username to promote')

    def handle(self, *args, **options):
        username = options.get('username')
        
        if not username:
            username = input('Enter username to promote to administrator: ')

        try:
            user = User.objects.get(username=username)
            
            # Confirm promotion
            confirm = input(f'Are you sure you want to promote "{username}" to administrator? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write(self.style.WARNING('Operation cancelled'))
                return

            user.is_staff = True
            user.is_superuser = True
            user.save()

            # Create or update UserRole
            user_role, created = UserRole.objects.get_or_create(user=user)
            user_role.role = 'admin'
            user_role.save()

            self.stdout.write(
                self.style.SUCCESS(f'Successfully promoted user "{username}" to administrator')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User "{username}" not found')
            )