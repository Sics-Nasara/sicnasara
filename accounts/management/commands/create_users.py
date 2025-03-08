from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Creates four superusers with specific emails and all permissions'

    def handle(self, *args, **options):
        users_data = [
            {'username': 'Enrico', 'email': 'enrico.sonno@gmail.com', 'password': 'password123'},
            {'username': 'Marinella', 'email': 'marinellapieraccini@yahoo.it', 'password': 'password123'},
            {'username': 'Kazoni', 'email': 'kazoniherbert@gmail.com', 'password': 'password123'},
            {'username': 'Alixkabore', 'email': 'pingdwendealixkabore@gmail.com', 'password': 'password123'},
        ]

        for user_data in users_data:
            username = user_data['username']
            email = user_data['email']
            password = user_data['password']

            if not User.objects.filter(username=username).exists():
                user = User.objects.create_superuser(username, email, password)
                self.stdout.write(self.style.SUCCESS(f'Successfully created superuser {username} with email {email}'))
            else:
                self.stdout.write(self.style.WARNING(f'Superuser {username} already exists'))
