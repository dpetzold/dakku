# Begin imports

import datetime
import os
import socket

from MySQLdb import cursors

from fabric import api as fab

from django.conf import settings
from django.db import connection, transaction

# End imports

# Begin support

mysqlbase = '{cmd} -h {host} -u {user} --password={password}'
mysql = mysqlbase.format(
    cmd='mysql',
    host=settings.DATABASES['default']['HOST'],
    user=settings.DATABASES['default']['USER'],
    password=settings.DATABASES['default']['PASSWORD'])
mysqladmin = mysqlbase.format(
    cmd='mysqladmin',
    host=settings.DATABASES['default']['HOST'],
    user=settings.DATABASES['default']['USER'],
    password=settings.DATABASES['default']['PASSWORD'])
mysqldump = mysqlbase.format(
    cmd='mysqldump',
    host=settings.DATABASES['default']['HOST'],
    user=settings.DATABASES['default']['USER'],
    password=settings.DATABASES['default']['PASSWORD'])

def resetdb(db_dump):

    # Backup drop and local the db
    output = fab.local('{mysqladmin} -f DROP {database}'.format(
                mysqladmin=mysqladmin,
                database=settings.DATABASES['default']['NAME']))

    output = fab.local('{mysqladmin} CREATE {database}'.format(
                mysqladmin=mysqladmin,
                database=settings.DATABASES['default']['NAME']))

    output = fab.local('{mysql} {database} < {db_dump}'.format(
                mysql=mysql,
                database=settings.DATABASES['default']['NAME'],
                db_dump=db_dump))


def execute_sql(cmd, hard_fail=False):
    cursor = connection.cursor()
    print(cmd)
    try:
        cursor.execute(cmd)
    except cursors.OperationalError as e:
        print(str(e))
        if hard_fail:
            raise e

def compress(filepath):
    fab.run('/bin/gzip %s' % (filepath))

    filepath += '.gz'

    filesize = os.stat(filepath).st_size
    if filesize == 0:
        raise BadFileSize('Bad filesize for "%s"' % (filepath))
    return filepath, filesize

# End support

# Begin tasks

@fab.task
def dumpdb_local():

    backup_dir = '{site_root}/../backup'.format(
        site_root=settings.SITE_ROOT)

    if not os.path.exists(backup_dir):
        os.mkdir(backup_dir)

    db_file = '{site_root}/../backup/{database}.{date}-{hostname}.gz'.format(
        site_root=settings.SITE_ROOT,
        database=settings.DATABASES['default']['NAME'],
        date=datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
        hostname=socket.gethostname())

    output = fab.local('{mysqldump} {database} | gzip > {db_file}'.format(
        mysqldump=mysqldump,
        db_file=db_file,
        database=settings.DATABASES['default']['NAME']))

    return db_file

@fab.task
@fab.roles('db')
def get_dbdump():

    with fab.cd(settings.SITE_ROOT):
        output = fab.run('{site_root}/../bin/fab mysql.dumpdb_local'.format(
            site_root=settings.SITE_ROOT))

    remote_path = output.split()[-2]
    fab.get(remote_path, '/tmp')
    filename = os.path.split(remote_path)[1]
    filepath = '/tmp/%s' % (filename)
    return filepath, os.stat(filepath).st_size

@fab.task
@fab.roles('db')
def syncdb():

    db_dump, size = get_dbdump()

    output = fab.local('gzip -d {db_dump}'.format(db_dump=db_dump))
    db_dump = os.path.splitext(db_dump)[0]

    if not os.path.exists('{site_root}/backup'.format(
        site_root=settings.SITE_ROOT)):
        fab.local('mkdir -p {site_root}/backup'.format(
            site_root=settings.SITE_ROOT))

    # Backup local db
    output = fab.local('{mysqldump} {database} | gzip > {site_root}/backup/{database}.{date}-{hostname}.gz'.format(
        mysqldump=mysqldump,
        site_root=settings.SITE_ROOT,
        database=settings.DATABASES['default']['NAME'],
        date=datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
        hostname=socket.gethostname()))

    # Backup drop and local the db
    resetdb(db_dump)


# End tasks
