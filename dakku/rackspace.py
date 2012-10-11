import datetime
import httplib
import os
import re
import ssl
import time

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

    def upload(self, path):
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
                    print('%s %s' % (args, str(e)))
                return None


    def sync_file(self, filepath):

        try:
            obj = self.retry(self.container.get_object, filepath)
        except cloudfiles.errors.NoSuchObject:
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
                os.system('mkdir -p "%s"' % (dstdir))
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
