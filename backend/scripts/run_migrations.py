"""
Helper to run alembic migrations from Python. Usage:
  python -m backend.scripts.run_migrations upgrade head

This will use the DATABASE_URL environment variable if set, otherwise it will
pick DATABASE_URL from backend.app.core.config.settings.
"""
import os
import sys
from alembic.config import Config
from alembic import command

# calculate project root and alembic ini path
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
ALEMBIC_INI = os.path.join(PROJECT_ROOT, 'alembic.ini')

if not os.path.exists(ALEMBIC_INI):
    print('alembic.ini not found at', ALEMBIC_INI)
    sys.exit(1)

alembic_cfg = Config(ALEMBIC_INI)
# allow overriding via env var
db_url = os.getenv('DATABASE_URL')
if not db_url:
    try:
        from backend.app.core.config import settings
        db_url = getattr(settings, 'DATABASE_URL', None)
    except Exception:
        db_url = None

if db_url:
    alembic_cfg.set_main_option('sqlalchemy.url', db_url)

# forward CLI args to alembic.command
if len(sys.argv) < 2:
    print('Usage: python -m backend.scripts.run_migrations <alembic command> [args]')
    print('Examples: upgrade head, downgrade -1, revision --autogenerate -m "init"')
    sys.exit(1)

cmd = sys.argv[1]
args = sys.argv[2:]

if cmd == 'upgrade':
    target = args[0] if args else 'head'
    command.upgrade(alembic_cfg, target)
elif cmd == 'downgrade':
    target = args[0] if args else '-1'
    command.downgrade(alembic_cfg, target)
elif cmd == 'revision':
    # e.g. revision --autogenerate -m "init"
    command.revision(alembic_cfg, *args)
else:
    # generic dispatch
    func = getattr(command, cmd, None)
    if func is None:
        print('Unknown alembic command:', cmd)
        sys.exit(2)
    func(alembic_cfg, *args)
