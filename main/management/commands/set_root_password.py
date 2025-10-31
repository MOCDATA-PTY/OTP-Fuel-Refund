from django.core.management.base import BaseCommand
from main.models import RootPassword
import getpass

class Command(BaseCommand):
    help = 'Set or update the root password for dashboard access'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            help='Root password (if not provided, will prompt securely)',
        )
        parser.add_argument(
            '--show-current',
            action='store_true',
            help='Show if a root password is currently set',
        )

    def handle(self, *args, **options):
        if options['show_current']:
            root_password = RootPassword.get_or_create_root_password()
            if root_password.password_hash:
                self.stdout.write(
                    self.style.SUCCESS('Root password is currently set.')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('No root password is set. Using default: admin123')
                )
            return

        password = options['password']
        
        if not password:
            # Prompt for password securely
            password = getpass.getpass('Enter new root password: ')
            confirm_password = getpass.getpass('Confirm new root password: ')
            
            if password != confirm_password:
                self.stdout.write(
                    self.style.ERROR('Passwords do not match. Please try again.')
                )
                return
        
        if len(password) < 6:
            self.stdout.write(
                self.style.ERROR('Password must be at least 6 characters long.')
            )
            return
        
        # Set the root password
        root_password = RootPassword.get_or_create_root_password()
        root_password.set_password(password)
        root_password.save()
        
        self.stdout.write(
            self.style.SUCCESS('Root password has been set successfully!')
        )
        self.stdout.write(
            self.style.WARNING('Remember to keep this password secure. It provides access to the dashboard.')
        )