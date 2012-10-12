import datetime
import socket
import os

from django.conf import settings

class MysqlUtil(object):

    def __init__(self, router, verbose=False):

        self.db = settings.DATABASES[router]
        self.verbose = verbose
        cmd = '%s '
        if self.db['HOST'] != '':
            cmd += '-h %s' % (self.db['HOST'])
        if self.db['PORT'] != '':
            cmd += ' -p %s' % (self.db['PORT'])
        cmd += '-u {user} --password={password}'.format(
            user=self.db['USER'],
            password=self.db['PASSWORD'])
        self.mysqlbase = cmd

    @property
    def mysql(self):
        return self.mysqlbase % ('mysql')

    @property
    def mysqladmin(self):
        return self.mysqlbase % ('mysqladmin')

    @property
    def mysqldump(self):
        return self.mysqlbase % ('mysqldump')

    def drop(self):
        cmd = 'echo "DROP DATABASE IF EXISTS {database}" | {mysql}'.format(
            mysql=self.mysql,
            database=self.db['NAME'])
        if self.verbose:
            print(cmd)
        os.system(cmd)

    def create(self):
        create_cmd = """
echo "CREATE DATABASE {database} CHARACTER SET utf8 COLLATE utf8_bin" | {mysql};
"""
        cmd = create_cmd.format(
            mysql=self.mysql,
            database=self.db['NAME'])
        if self.verbose:
            print(cmd)
        os.system(cmd)

    def source(self, dbfile):
        if dbfile.endswith('.bz2'):
            cmd = '{mysql} {database} < /bin/bzip2 -dc {dbfile}'
        elif dbfile.endswith('.gz'):
            cmd = '/bin/gzip -dc {dbfile} | {mysql} {database}'
        else:
            cmd = '{mysql} {database} < {dbfile}'
        cmd = cmd.format(
            mysql=self.mysql,
            database=self.db['NAME'],
            dbfile=dbfile)
        if self.verbose:
            print(cmd)
        os.system(cmd)

    def dump(self, prefix='db'):
        backup_dir = '%s/%s' % (settings.BACKUP_DIR, prefix)
        if not os.path.exists(backup_dir):
            os.mkdir(backup_dir)
        dbfile = '{backup_dir}/{database}.{date}-{hostname}.gz'.format(
            backup_dir=backup_dir,
            database=self.db['NAME'],
            date=datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S'),
            hostname=socket.gethostname())
        cmd = '{mysqldump} {database} | gzip > {db_file}'.format(
            mysqldump=self.mysqldump,
            db_file=dbfile,
            database=self.db['NAME'])

        if self.verbose:
            print(cmd)
        os.system(cmd)
        return dbfile
