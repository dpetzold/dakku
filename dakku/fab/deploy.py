from __future__ import print_function

# Begin imports

import calendar
import datetime
import socket
import time

import json
import requests
import yaml


from fabric import api as fab
from fabric.api import settings as fab_settings
from fabric.contrib import django

from django.conf import settings
from django.utils.timesince import timesince


# http://docs.fabfile.org/en/latest/tutorial.html
# http://readthedocs.org/docs/fabric/en/latest/usage/execution.html

# End imports

# Begin tasks

@fab.task
@fab.roles('git')
def add_repo(name):
    fab.sudo('mkdir /repo/%s.git' % (name))
    with fab.cd('/repo/%s.git' % (name)):
        fab.sudo('git init --bare .')
    fab.sudo('chgrp -R git /repo/%s.git' % (name))
    fab.sudo('chmod -R g+w /repo/%s.git' % (name))


@fab.task
@fab.roles('db', 'fastcgi')
def git_pull(branch=None):
    with fab.cd(settings.SITE_ROOT):
        if branch is not None:
            fab.run('git pull %s' % (branch))
        else:
            fab.run('git pull')
        fab.run("find . -name '*.pyc' | xargs rm -f")

@fab.task
@fab.roles('fastcgi')
def pip_install(package=None):
    with fab.cd(settings.SITE_ROOT):
        fab.run('{site_root}/../bin/pip install {package}'.format(
            site_root=settings.SITE_ROOT, package=package))

@fab.task
def pip_update():

    requirements = getattr(settings, 'REQUIREMENTS_TXT', 'requirements.txt')
    with fab.cd(settings.SITE_ROOT):
        fab.run('{site_root}/../bin/pip install --timeout=5 -r {requirements}'.format(
            site_root=settings.SITE_ROOT,
            requirements=requirements))

@fab.task
@fab.roles('fastcgi')
def pip_upgrade():
    with fab.cd(settings.SITE_ROOT):
        fab.run('{site_root}/../bin/pip install --upgrade -r requirements.txt'.format(
            site_root=settings.SITE_ROOT))

@fab.task
@fab.roles('db', 'fastcgi')
def site_update():
    git_pull()
    pip_update()

@fab.task
@fab.roles('db')
def db_update():
    git_pull()

@fab.task
@fab.roles('fastcgi')
def fastcgi_update():
    git_pull()
    pip_upgrade()

@fab.task
@fab.roles('fastcgi')
def fastcgi_restart():
    name = settings.SITE_ROOT.split('/')[2]
    fab.sudo('restart {name}'.format(name=name))

@fab.task
@fab.roles('fastcgi')
def uwsgi_restart(name=settings.SITE_NAME):
    # XXX: remove run path hardcode
    fab.sudo('kill -INT `cat /var/run/uwsgi/{name}.pid`'.format(name=name))

@fab.task(default=True)
@fab.roles('db', 'fastcgi')
def deploy(name=settings.SITE_NAME):
    """Do the deployment."""
    # XXX: Alter scripts should run here.
    git_pull()
    uwsgi_restart(name)

@fab.task
@fab.roles('db')
def deploy_media():
    """Do the deployment."""
    # XXX: Alter scripts should run here.
    db_update()

@fab.task
@fab.roles('nginx')
def test_local():
    if settings.SITE_NAME.endswith('.dev'):
        r = requests.get(settings.SITE_URL, verify=False)
        assert r.status_code == 200, 'Error expected "200" got "%s"' % (r.status_code)
        print('%s: OK' % (settings.SITE_URL))

    else:
        for i in range(len(fab.env.roledefs['fastcgi'])):
            r = requests.get(settings.SITE_URL, verify=False)
            assert r.status_code == 200, 'Error expected "200" got "%s"' % (r.status_code)
            print('%s: OK' % (fab.env.roledefs['fastcgi'][i]))

@fab.task
@fab.roles('nginx')
def test():
    with fab.cd(settings.SITE_ROOT):
        output = fab.run('{site_root}/../bin/fab deploy.test_local'.format(
            site_root=settings.SITE_ROOT))

@fab.task
@fab.roles('db', 'fastcgi')
def deploy_full():
    """Do the deployment."""
    # XXX: Alter scripts should run here.
    site_update()
    pip_upgrade()
    fastcgi_restart()

# End tasks
