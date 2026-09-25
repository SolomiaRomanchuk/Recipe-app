import os
from io import StringIO
from secrets import token_urlsafe
from unittest.mock import patch

from django.contrib.auth import authenticate, get_user_model
from django.core.management import call_command, CommandError
from django.test import TestCase


class EnsureSuperuserTests(TestCase):
    def setUp(self):
        self.password = token_urlsafe(32)
        self.environment = {
            'DJANGO_SUPERUSER_USERNAME': 'configured-admin',
            'DJANGO_SUPERUSER_EMAIL': 'admin@example.test',
            'DJANGO_SUPERUSER_PASSWORD': self.password,
        }
        self.patch = patch.dict(os.environ, self.environment)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def run_command(self, *args):
        output = StringIO()
        call_command('ensure_superuser', *args, stdout=output)
        for secret in self.environment.values():
            self.assertNotIn(secret, output.getvalue())
        return output.getvalue()

    def test_create_and_repeat_preserves_password_and_normal_users(self):
        User = get_user_model()
        normal = User.objects.create_user(username='normal')
        self.run_command()
        admin = User.objects.get(username=self.environment['DJANGO_SUPERUSER_USERNAME'])
        self.assertTrue(admin.is_active and admin.is_staff and admin.is_superuser)
        self.assertEqual(authenticate(username=admin.username, password=self.password), admin)
        original_hash = admin.password
        with patch.dict(os.environ, {'DJANGO_SUPERUSER_PASSWORD': token_urlsafe(32)}):
            self.run_command()
        admin.refresh_from_db()
        normal.refresh_from_db()
        self.assertEqual(admin.password, original_hash)
        self.assertFalse(normal.is_staff or normal.is_superuser)
        self.assertEqual(User.objects.count(), 2)

    def test_restore_existing_superuser_flags_and_explicit_reset(self):
        self.run_command()
        user = get_user_model().objects.get(username=self.environment['DJANGO_SUPERUSER_USERNAME'])
        user.is_active = user.is_staff = False
        user.save()
        self.run_command()
        user.refresh_from_db()
        self.assertTrue(user.is_active and user.is_staff and user.is_superuser)
        new_password = token_urlsafe(32)
        with patch.dict(os.environ, {'DJANGO_SUPERUSER_PASSWORD': new_password}):
            self.run_command('--reset-password')
        user.refresh_from_db()
        self.assertTrue(user.check_password(new_password))
        self.assertFalse(user.check_password(self.password))

    def test_collision_does_not_promote_or_reset_normal_account(self):
        user = get_user_model().objects.create_user(username=self.environment['DJANGO_SUPERUSER_USERNAME'])
        original_hash = user.password
        with self.assertRaisesMessage(CommandError, 'non-superuser'):
            self.run_command()
        user.refresh_from_db()
        self.assertFalse(user.is_staff or user.is_superuser)
        self.assertEqual(user.password, original_hash)

    def test_check_is_read_only(self):
        self.assertIn('does not exist', self.run_command('--check'))
        self.assertFalse(get_user_model().objects.exists())
        self.run_command()
        self.assertIn('is_superuser=True', self.run_command('--check'))

    def test_missing_credentials_and_pending_migrations_do_not_create(self):
        for key in self.environment:
            with patch.dict(os.environ, {key: ''}):
                with self.assertRaises(CommandError):
                    self.run_command()
        with patch('recipes.management.commands.ensure_superuser.MigrationExecutor') as executor:
            executor.return_value.migration_plan.return_value = [object()]
            with self.assertRaisesMessage(CommandError, 'Pending migrations'):
                self.run_command()
        self.assertFalse(get_user_model().objects.exists())
