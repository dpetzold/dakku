import datetime
import logging
import re
import socket
import subprocess
import os

from django.conf import settings

from . import exceptions as dakku_exception

logger = logging.getLogger(__name__)


class BackupBase(object):

    def deletefile(self, date_str):
        """Given a date in YYYYMMDD check if the file should be deleted or keep"""

        today = datetime.date.today()
        date = datetime.date(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))
        age = today - date

        if age < datetime.timedelta(weeks=2):
            if self.verbose:
                print('keeping < 2 weeks')
            return False
        if age < datetime.timedelta(weeks=8) and date.weekday() == 0:
            if self.verbose:
                print('keeping monday')
            return False
        if date.day == 2:
            if self.verbose:
                print('keeping first of the month')
            return False
        return True

class BackupUtil(object):

    def __init__(self, router, container_name, dry_run=False, verbose=False):
        from .mysql import MysqlUtil
        from .rackspace import RackspaceUtil

        self.mysql = MysqlUtil(router, verbose)
        self.rackspace = RackspaceUtil(container_name, verbose, dry_run=dry_run)
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
            raise dakku_exception.BadFileSize('Bad filesize for "%s"' % (filepath))
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
        self.backup_database()
        self.backup_site()
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

    def cull_local(self):
        culled = []
        files = os.listdir(settings.BACKUP_DIR)
        for filename in files:
            for date in self.culls():
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

    def cull(self):
        self.rackspace.cull()
        self.cull_local()
