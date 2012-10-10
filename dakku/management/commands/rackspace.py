from __future__ import print_function

from optparse import make_option

import datetime
import httplib
import os
import re
import socket
import ssl
import sys
import time
import django

from django.core.management.base import CommandError, BaseCommand
from django.conf import settings

import cloudfiles

class RackspaceCommand(object):

    def __init__(self, container_name, verbose, dry_run=False, forward=0,
            max_attempts=5):
        self.verbose = verbose
        self.dry_run = dry_run
        self.rp_conn = cloudfiles.get_connection(
            settings.RACKSPACE_USER,
            settings.RACKSPACE_API_KEY)
        self.start_time = datetime.datetime.now()
        self.container = self.rp_conn.get_container(container_name)
        self.max_attempts = max_attempts

        if forward == 0:
            self.start_time = datetime.datetime.now()
        else:
            self.start_time = datetime.datetime.now() + datetime.timedelta(days=forward)


    @property
    def culls(self):
        dates = []
        lastweeks = self.start_time - datetime.timedelta(weeks=1)

        # delete last weeks except mondays
        if lastweeks.weekday() != 1 and lastweeks.day != 1:
            dates.append(lastweeks.strftime('%Y%m%d'))

        # keep 8 weeks of mondays
        lastmonths = self.start_time - datetime.timedelta(weeks=8)
        if lastmonths.weekday() == 1 and lastmonths.day != 1:
            dates.append(lastmonths.strftime('%Y%m%d'))
        return dates


    def cull(self):
        culled = []
        for obj in self.container.get_objects():
            for date in self.culls:
                if self.verbose:
                    print('Checking %s %s' % (date, obj.name))
                search = re.search('\.%s_' % (date), obj.name)
                if search is not None:
                    if self.verbose:
                        print('Deleting %s' % (obj.name))
                    if not self.dry_run:
                        self.container.delete_object(obj.name)
                    culled.append(obj)
        return culled


    def download(self, dest):
        for obj in self.list():
            if obj.size == 0:
                continue
            filepath = '%s/%s' % (dest, obj.name)
            if not os.path.exists(filepath):
                head, tail = os.path.split(filepath)
                if not os.path.exists(head):
                    os.makedirs(head)
                obj.save_to_filename(filepath)

    def upload(self,  path):
        for root, dirs, files in os.walk(path, followlinks=True):
            for name in files:
                filepath = os.path.join(root, name)
                if filepath.startswith('./'):
                    filepath = filepath[2:]
                self.sync_file(filepath)


    def retry(self, func, *args):
        attempts = 0
        while True:
            try:
                return func(*args)
            except ssl.SSLError as e:
                if self.max_attempts == 0:
                    print('Failed %s %s (%s)' % (func.func_name, args, str(e)))
                    return None

                if attempts == self.max_attempts:
                    raise e

                attempts += 1
                if self.verbose:
                    print('Retrying %s %s (%s)' % (func.func_name, args,
                        attempts))
                time.sleep(.5)
            except httplib.CannotSendRequest as e:
                if self.verbose:
                    print('%s %s' % (filepath, str(e)))
                return None


    def sync_file(self, filepath):

        try:
            obj = self.retry(self.container.get_object, filepath)
        except cloudfiles.errors.NoSuchObject as e:
            self.upload(filepath)
        else:
            stat = os.stat(filepath)
            uploaded = time.mktime(time.strptime(
                obj.last_modified, '%a, %d %b %Y %H:%M:%S %Z'))
            if stat.st_mtime > uploaded or stat.st_size != obj.size:
                if self.verbose:
                    if stat.st_mtime > uploaded:
                        print('time: %s' % (stat.st_mtime - uploaded))
                    if stat.st_size != obj.size:
                        print('size: %s %s' % (stat.st_size, obj.size))
                self.upload(filepath)
            else:
                if self.verbose:
                    print('Skipping %s' % (filepath))
                    print('%s' % (datetime.datetime.fromtimestamp(stat.st_mtime)))
                    print('%s' % (datetime.datetime.fromtimestamp(uploaded)))
                    print('%s' % (obj.last_modified))
                    print('time: %s' % (stat.st_mtime - uploaded))
                    print('size: %s %s' % (stat.st_size, obj.size))


    def store(self, filepath, prefix=None):
        root, filename = os.path.split(filepath)
        if prefix is not None:
            filename = '%s/%s' % (prefix, filename)
        obj = self.retry(self.container.create_object, filename)
        self.retry(obj.load_from_filename, filepath)
        if self.verbose:
            print('Uploaded %s' % (filename))
        return obj


    def list(self, pattern=None):
        for obj in self.container.get_objects():
            if pattern is not None:
                search = re.search(pattern, obj.name)
                if search is not None:
                    yield obj
            else:
                yield obj


    def copy(self, destination):
        for obj in self.container.get_objects():
            if self.verbose:
                print('%s:%s -> %s:%s' % (self.container.name, obj.name,
                    destination, obj.name))
            self.retry(obj.copy_to, destination, obj.name)


    def delete(self, filename=None, pattern=None):
        if pattern is not None:
            deleted = []
            for obj in self.container.get_objects():
                search = re.search(pattern, obj.name)
                if search is not None:
                    print('Deleted %s' % (obj.name))
                    if not self.dry_run:
                        self.container.delete_object(obj.name)
        else:
            return self.container.delete_object(filename)


    def purge(self, filename):
        obj = self.container.get_object(filename)
        obj.purge_from_cdn('dpetzold@gmail.com')


    def get(self, objname, savedir=None):
        root, filename = os.path.split(objname)
        obj = self.container.get_object(objname)
        if savedir is not None:
            dstdir = '%s/%s' % (savedir, root)
            if not os.path.exists(dstdir):
                os.system('mkdir -p "%s"' % (destdir))
            filename = '%s/%s' % (dstdir, filename)
            obj.save_to_filename(filename)
        else:
            obj.save_to_filename(filename)
        return filename


    def info(self, filepath):

        obj = self.container.get_object(filepath)
        print('Name: %s' % (obj.name))
        print('Size: %s' % (obj.size))
        print('Last Modified: %s' % (obj.last_modified))

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--cull', action='store_true',
                    dest='cull', default=False,
                    help='Cull the remote backup files.'),
        make_option('-a', '--max-attempts', action='store',
                    dest='max_attempts',
                    default=5,
                    help='Max retry attemtps.'),
        make_option('-C', '--contianer', action='store',
                    dest='container',
                    default=settings.RACKSPACE_BACKUP_CONTAINER,
                    help='The container to use.'),
        make_option('-D', '--delete', action='store_true',
                    dest='delete', default=False,
                    help='Delete the specified file from container.'),
        make_option('-F', '--file', action='store',
                    dest='file', default=None,
                    help='Specify a file.'),
        make_option('--forward', action='store',
                    dest='forward', default=0,
                    help='Pretend to run the specified days forward.'),
        make_option('--copy', action='store',
                    dest='copy', default=None,
                    help='Copy contianer the container to the specified destination.'),
        make_option('--purge', action='store',
                    dest='purge', default=None,
                    help='Purge the file.'),
        make_option('--info', action='store',
                    dest='info', default=None,
                    help='Get the info for the specified object.'),
        make_option('--download', action='store',
                    dest='download', default=None,
                    help='Download the contianer to the specified path.'),
        make_option('--upload', action='store',
                    dest='upload', default=None,
                    help='Upload the specified path to contianer.'),
        make_option('--sync-file', action='store',
                    dest='sync_file', default=None,
                    help='Sync the specified path to contianer.'),
        make_option('-G', '--get', action='store',
                    dest='get', default=None,
                    help='Get the specified file.'),
        make_option('-L', '--list', action='store_true',
                    dest='list', default='',
                    help='List the backup dir.'),
        make_option('-N', '--dry-run', action='store_true',
                    dest='dry_run', default=False,
                    help='Dry run.'),
        make_option('-P', '--pattern', action='store',
                    dest='pattern', default=None,
                    help='Specify a pattern.'),
        make_option('--store', action='store',
                    dest='store', help='Upload the specified file to rackspace.'),
        make_option('-V', '--verbose', action='store_true',
                    dest='verbose', default=False,
                    help='Be verbose.'),
    )
    help = """Rackspace utility."""

    requires_model_validation = False
    can_import_settings = True

    def handle(self, *args, **options):

        rackspace = RackspaceCommand(
            options.get('container'),
            options.get('verbose'),
            options.get('dry_run'),
            int(options.get('forward')),
            int(options.get('max_attempts')))

        if options.get('cull'):
            deletes = rackspace.cull()
            for deleted in deletes:
                print('Deleted: %s' % (deleted.name))
        elif options.get('delete'):
            if options.get('pattern') is not None:
                rackspace.delete(pattern=options.get('pattern'))
            elif options.get('file'):
                rackspace.delete(options.get('file'))
            else:
                print('Must specify a pattern or a file')
        elif options.get('info'):
            rackspace.info(options.get('info'))
        elif options.get('list'):
            for obj in rackspace.list(options.get('pattern')):
                print('%s %s' % (obj.name, obj.size))
        elif options.get('get'):
            filename = rackspace.get(options.get('get'))
            print('Downloaded %s' % (filename))
        elif options.get('download'):
            rackspace.download(options.get('download'))
        elif options.get('upload'):
            rackspace.upload(options.get('upload'))
        elif options.get('sync_file'):
            rackspace.sync_file(options.get('sync_file'))
        elif options.get('copy'):
            rackspace.copy(options.get('copy'))
        elif options.get('purge'):
            rackspace.purge(options.get('purge'))
        elif options.get('store'):
            backup = rackspace.upload(options.get('upload'))
            print(backup)
