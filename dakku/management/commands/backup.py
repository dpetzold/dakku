from __future__ import print_function

from optparse import make_option

import datetime
import logging
import re
import socket
import subprocess
import sys
import os

import django
from django.core.management.base import CommandError, BaseCommand
from django.conf import settings

from django_extensions.management.commands.mysql import MysqlCommand
from django_extensions.management.commands.rackspace import RackspaceCommand

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)

class BackupCommand(object):

    def __init__(self, router, container_name, verbose=False):
        self.mysql = MysqlCommand(router, verbose)
        self.rackspace = RackspaceCommand(container_name, verbose)
        self.verbose = verbose
        self.start_time = datetime.datetime.utcnow()
        if not os.path.exists(settings.BACKUP_DIR):
            os.mkdir(settings.BACKUP_DIR)

    def _run_cmd(self, cmd, filepath, ext=None):
        if self.verbose:
            print(cmd)
        subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        if ext is not None:
            filepath += ext
        filesize = os.stat(filepath).st_size
        if filesize == 0:
            raise baku_exception.BadFileSize('Bad filesize for "%s"' % (filepath))
        return filepath, filesize

    def tar_directory(self, directory, prefix=None):
        root, name = os.path.split(directory)
        name = '%s.%s-%s.tar.bz2' % \
            (name, self.start_time.strftime('%Y%m%d_%H%M%S'), socket.gethostname())
        if prefix is not None:
            backup_dir = '%s/%s' % (settings.BACKUP_DIR, prefix)
        else:
            backup_dir = settings.BACKUP_DIR
        if not os.path.exists(backup_dir):
            os.mkdir(backup_dir)
        filepath = '%s/%s' % (backup_dir, name)
        cmd = '/bin/tar cfj %s %s -C %s' % (filepath, directory, root)
        return self._run_cmd(cmd, filepath)

    def cull(self):
        culled = []
        files = os.listdir(settings.BACKUP_DIR)
        for filename in files:
            for date in self.rackspace.culls:
                if self.verbose:
                    print('Checking %s %s' % (date, filename))
                search = re.search('\.%s_' % (date), filename)
                if search is not None:
                    filepath = '%s/%s/' % (settings.BACKUP_DIR, filename)
                    if self.verbose:
                        print('Deleting %s' % (filepath))
                    if not self.dry_run:
                        os.unlink(filepath)
                    culled.append(filepath)
        return culled

    def backup_database(self):
        dbfile = self.mysql.dump()
        uploaded = self.rackspace.store(dbfile, 'db')
        logger.info('Uploaded %s to %s %s' % (dbfile, uploaded.name, uploaded.size))
        if self.verbose:
            print(uploaded.name)
        return uploaded

    def backup_site(self):
        filepath, filesize = self.tar_directory(settings.SITE_ROOT, 'site')
        if self.verbose:
            print('%s %s' % (filepath, filesize))
        uploaded = self.rackspace.store(filepath, 'site')
        logger.info('Uploaded %s to %s %s' % (filepath, uploaded.name, uploaded.size))
        if self.verbose:
            print(uploaded.name)
        return uploaded

    def backup_all(self):
        db_upload = self.backup_database()
        site_upload = self.backup_site()
        deletes = self.rackspace.cull()
        for deleted in deletes:
            logger.info('Deleted %s' % (deleted.name))
            if self.verbose:
                print('Deleted: %s' % (deleted.name))
        deletes = self.cull()
        for deleted in deletes:
            logger.info('Deleted %s' % (deleted.name))
            if self.verbose:
                print('Deleted: %s' % (deleted.name))

    def restore(self, filename=None, remote=None):
        self.mysql.dump()
        self.mysql.drop()
        self.mysql.create()
        if remote is not None:
            filename = self.rackspace.get(remote, settings.BACKUP_DIR)
        return self.mysql.source(filename)

    def list(self):
        for obj in self.rackspace.list():
            print('%s %s' % (obj.name, obj.size))

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--db', action='store_true',
                    dest='db', default=False,
                    help='Backup the database.'),
        make_option('-C', '--contianer', action='store',
                    dest='container',
                    default=settings.RACKSPACE_BACKUP_CONTAINER,
                    help='The container to use.'),
        make_option('--cull', action='store_true',
                    dest='cull', default=False,
                    help='Cull the backup files.'),
        make_option('-F', '--file', action='store',
                    dest='file', default=None,
                    help='Specify a file.'),
        make_option('-L', '--list', action='store_true',
                    dest='list', default=False,
                    help='List the avalible backups.'),
        make_option('-R', '--remote', action='store',
                    dest='remote', default=None,
                    help='Use the specified remote file.'),
        make_option('--restore', action='store_true',
                    dest='restore', default=False,
                    help='Restore (drop, create, source) the db from specified local or remote file.'),
        make_option('--router', action='store',
                    dest='router', default='default',
                    help='Use this router and not the default.'),
        make_option('--site', action='store_true',
                    dest='site', default=False,
                    help='Backup the site directory.'),
        make_option('-U', '--upload', action='store',
                    dest='upload', help='Upload the file to rackspace.'),
        make_option('-V', '--verbose', action='store_true',
                    dest='verbose', default=False,
                    help='Be verbose.'),
    )
    help = """Backups the database and the site directory."""

    requires_model_validation = False
    can_import_settings = True

    def handle(self, *args, **options):

        backup = BackupCommand(
            options.get('router'),
            options.get('container'),
            options.get('verbose'))

        if options.get('cull'):
            backup = backup.cull()
        elif options.get('db'):
            backup = backup.backup_database()
        elif options.get('list'):
            backup = backup.list()
        elif options.get('restore'):
            if options.get('file'):
                dbfile = backup.restore(filename=options.get('file'))
            elif options.get('remote'):
                dbfile = backup.restore(remote=options.get('remote'))
            else:
                print('Must specify a file name or remote name.')
        elif options.get('site'):
            backup = backup.backup_site()
        else:
            backup.backup_all()
