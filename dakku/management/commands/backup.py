from optparse import make_option

import logging

from django.core.management.base import BaseCommand
from django.conf import settings

from dakku.backup import BackupUtil

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--db', action='store_true',
                    dest='db', default=True,
                    help='Backup the database.'),
        make_option('-C', '--contianer', action='store',
                    dest='container',
                    default=settings.RACKSPACE_BACKUP_CONTAINER,
                    help='The container to use.'),
        make_option('--cull', action='store_true',
                    dest='cull', default=False,
                    help='Cull the backup files after the backup.'),
        make_option('--cull-only', action='store_true',
                    dest='cull_only', default=False,
                    help='Only cull the backup files.'),
        make_option('--list', action='store_true',
                    dest='list', default=False,
                    help='List the avalible backups.'),
        make_option('--restore', action='store',
                    dest='restore', default=False,
                    help='Restore (drop, create, source) the db'
                         ' from specified local or remote file.'),
        make_option('--router', action='store',
                    dest='router', default='default',
                    help='Use this router and not the default.'),
        make_option('--site', action='store_true',
                    dest='site', default=False,
                    help='Backup the site directory.'),
        make_option('--dry-run', action='store_true',
                    dest='dry_run', default=False,
                    help='Dry run.'),
        make_option('--verbose', action='store_true',
                    dest='verbose', default=False,
                    help='Be verbose.'),
    )
    help = """Backups the database and the site directory."""

    requires_model_validation = False
    can_import_settings = True

    def handle(self, *args, **options):

        backup = BackupUtil(
            options.get('router'),
            options.get('container'),
            dry_run=options.get('dry_run'),
            verbose=options.get('verbose'))

        if options.get('cull_only'):
            backup = backup.cull()
        elif options.get('list'):
            backup = backup.list()
        elif options.get('restore'):
            backup.restore(remote=options.get('restore'))
        elif options.get('site'):
            backup = backup.backup_site()
        else:
            backup = backup.backup_database()
            if options.get('cull'):
                backup.cull()
