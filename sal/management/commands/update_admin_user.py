"""Creates an admin user if there aren't any existing superusers."""


from optparse import make_option

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Creates/Updates an Admin user'

    def add_arguments(self, parser):
        parser.add_argument('--username',
                            action='store',
                            dest='username',
                            default=None,
                            help='Admin username')

        parser.add_argument('--password',
                            action='store',
                            dest='password',
                            default=None,
                            help='Admin password')

    def handle(self, *args, **options):
        username = options.get('username')
        password = options.get('password')
        if not username or not password:
            raise CommandError('You must specify a username and password')
        # Get the current superusers
        su_count = User.objects.filter(is_superuser=True).count()
        if su_count == 0:
            # there aren't any superusers, create one
            user, created = User.objects.get_or_create(username=username)
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            print(f'{username} updated')
        else:
            print(f'There are already {su_count} superusers')
