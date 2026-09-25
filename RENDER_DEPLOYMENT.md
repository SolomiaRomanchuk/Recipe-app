# Render administrator provisioning

The repository previously had no superuser provisioning or Render scripts. The
configured database is SQLite at `BASE_DIR / 'db.sqlite3'`; this file is ignored
by Git. Local accounts are not shipped in a repository deployment. Production
account history and dashboard settings cannot be determined from this checkout.

## Deploy the fix

1. Commit `build.sh`, `start.sh`, `recipes/management/__init__.py`,
   `recipes/management/commands/__init__.py`,
   `recipes/management/commands/ensure_superuser.py`,
   `recipes/test_superuser_command.py`, and this document. Also include the
   pending authentication fixes in `recipes/forms.py`,
   `recipes/templates/registration/signup.html`, and `recipes/tests.py`.
   Never commit `.env` or `db.sqlite3`.
2. Push that commit to the GitHub branch linked to the existing Render service.
3. In that service's Environment settings, retain/set these variable names:
   `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DJANGO_SUPERUSER_USERNAME`,
   `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD`.
   Disable production debug mode. Include the service hostname in allowed hosts.
   Keep the secret key stable. Configure credentials only through Render's
   private environment settings; never put them in commands or logs.
4. Set Build Command to `sh build.sh`.
5. Set Start Command to `sh start.sh`. Leave Pre-Deploy Command empty for this
   SQLite setup. Run a single service instance. The start script runs migrations
   and provisioning against the runtime database, then executes
   `python -m gunicorn recipe_project.wsgi:application --bind "0.0.0.0:${PORT:-8000}"`.
6. Save settings. If no deployment starts automatically, use Manual Deploy →
   Deploy latest commit. Confirm the deployed commit includes these files.
7. Runtime logs must show `Applying database migrations...`, Django's migration
   output (`Applying ... OK` or `No migrations to apply.`), then
   `Database migrations completed.`, then `Configured administrator created`
   or `Configured administrator verified`. Gunicorn starts only after success.
8. In the running service's Render Shell, run:

   ```sh
   python manage.py ensure_superuser --check
   python manage.py showmigrations
   ```

   The first command is read-only and prints existence and account flags, never
   credentials. The flags should all be True. Applied migrations have `[X]`.
9. Open `/admin/` over HTTPS in a private browser window and log in with the
   intended administrator. Verify the admin index loads. Log out and test the
   same account at `/accounts/login/`. An existing administrator keeps its old
   password; changing the environment password alone does not reset it.
10. If that existing administrator's password is unknown or invalid, explicitly
    reset it from the securely configured environment password in Render Shell:

    ```sh
    python manage.py ensure_superuser --reset-password
    ```

    This uses Django's password hashing and may invalidate existing sessions for
    that administrator. Do not add this option to the Start Command.
11. Verify a normal user's signup/login still works and `/admin/` rejects it.
    Provisioning never changes unrelated accounts. If the configured username
    already belongs to a non-superuser, provisioning refuses to change it and
    startup stops. Verify the account's ownership before any manual promotion;
    alternatively configure a distinct administrator username. Do not blindly
    promote the conflicting normal account.

## Persistence is a separate required follow-up

This restores access by creating a missing configured administrator; it does
not recover a deleted account, its original ID, recipes, or other records.
There is no confirmed production database-loss diagnosis without runtime
inspection. Migrations recreate schema, not historical users.

Render's default filesystem is ephemeral. With the current SQLite path outside
persistent storage, new users and recipes can disappear after restart/redeploy.
The startup command can recreate the configured administrator but cannot restore
normal users or recipes. Do not redeploy expecting those records to persist.
Back up important existing production data before deployment using a consistent
SQLite backup; keep it private because it contains account data.

After restoring access, either attach a paid Render persistent disk and change
the SQLite database path to a file inside its mount (safely backing up and moving
the existing database first), or plan a migration to persistent PostgreSQL.
Simply attaching a disk elsewhere or defining DATABASE_URL will not change the
current hard-coded database settings. No database migration or storage change
has been performed here.

Persistent disks are available at runtime, not during build/pre-deploy commands:
https://render.com/docs/disks
