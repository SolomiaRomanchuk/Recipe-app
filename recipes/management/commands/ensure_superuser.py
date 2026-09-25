"""Provision only the explicitly configured administrator, without logging secrets."""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.migrations.executor import MigrationExecutor


class Command(BaseCommand):
    help = 'Create the environment-configured superuser after migrations; preserve existing passwords.'

    def add_arguments(self, parser):
        parser.add_argument('--check', action='store_true', help='Report safe account status without changes.')
        parser.add_argument('--reset-password', action='store_true', help='Explicitly reset the administrator password from the environment.')

    def handle(self, *args, **options):
        if options['check'] and options['reset_password']:
            raise CommandError('Use --check separately from --reset-password.')
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        if not username:
            raise CommandError('DJANGO_SUPERUSER_USERNAME is required.')
        executor = MigrationExecutor(connection)
        if executor.migration_plan(executor.loader.graph.leaf_nodes()):
            raise CommandError('Pending migrations. Run python manage.py migrate --noinput first.')
        User = get_user_model()
        with transaction.atomic():
            user = User.objects.select_for_update().filter(username=username).first()
            if options['check']:
                if user is None:
                    self.stdout.write('Configured administrator does not exist.')
                else:
                    self.stdout.write(
                        f'Configured account exists: is_active={user.is_active}, '
                        f'is_staff={user.is_staff}, is_superuser={user.is_superuser}, '
                        f'usable_password={user.has_usable_password()}'
                    )
                return
            # A username collision is not proof that an ordinary account belongs to the operator.
            if user is not None and not user.is_superuser:
                raise CommandError('Configured username belongs to a non-superuser. No changes made. Verify ownership before choosing an administrator username.')
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
            if user is None or options['reset_password']:
                if not password:
                    raise CommandError('DJANGO_SUPERUSER_PASSWORD is required for creation or an explicit reset.')
            if user is None:
                email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
                if not email:
                    raise CommandError('DJANGO_SUPERUSER_EMAIL is required for creation.')
                User.objects.create_superuser(username=username, email=email, password=password)
                message = 'Configured administrator created: is_active=True, is_staff=True, is_superuser=True.'
            else:
                fields = []
                for name in ('is_active', 'is_staff'):
                    if not getattr(user, name):
                        setattr(user, name, True)
                        fields.append(name)
                if options['reset_password']:
                    user.set_password(password)
                    fields.append('password')
                if fields:
                    user.save(update_fields=fields)
                message = 'Configured administrator verified: is_active=True, is_staff=True, is_superuser=True. '
                message += 'Password explicitly reset.' if options['reset_password'] else 'Existing password preserved.'
        self.stdout.write(self.style.SUCCESS(message))
