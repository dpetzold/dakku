# Begin imports

import calendar
import datetime
import time

from fabric import api as fab
from fabric.api import settings as fab_settings
from fabric.contrib import django

import boto
from boto.ec2 import connection as aws

from django.conf import settings

# End imports

# Begin support

def isotime2datetime(isotime):
    stime = time.strptime(isotime, '%Y-%m-%dT%H:%M:%S.000Z')
    year, month, day, hour, minute, second = stime[:6]
    return datetime.datetime.utcfromtimestamp(
                calendar.timegm(tuple([year, month, day, hour, minute,
                    second])))

def instance2dict(i):
    return dict(
        id=i.id,
        type=i.instance_type,
        image_id=i.image_id,
        ip_address=i.ip_address,
        launch_time=isotime2datetime(i.launch_time),
        tags=[ t for t in i.tags if t != 'Name'])

def ec2_hosts():
    hosts = []
    conn = aws.EC2Connection(settings.AWS_ACCESS_KEY, settings.AWS_SECERT_KEY)
    for r in conn.get_all_instances():
        for i in r.instances:
            hosts.append(instance2dict(i))
    return hosts

roles = {}
for host in ec2_hosts():
    for tag in host['tags']:
        try:
            roles[tag].append(host['ip_address'])
        except KeyError:
            roles[tag] = [host['ip_address']]

fab.env.roledefs.update(roles)

ec2_conn = aws.EC2Connection(settings.AWS_ACCESS_KEY, settings.AWS_SECERT_KEY)

def host_yaml(host):
    s = '---\n'
    for key, val in host.iteritems():
        if hasattr(val, '__iter__'):
            s += '%s: %s\n' % (key, ', '.join(val))
        else:
            s += '%s: %s\n' % (key, val)
    return s.strip('\n')

# End support

# Begin tasks

@fab.task
def show_roles():
    print(host_yaml(roles))

@fab.task
def list():
    for host in ec2_hosts():
        print(host_yaml(host))

@fab.task
def add_tag(instance_id, name, value=''):
    instance = ec2_conn.get_all_instances(instance_id)[0].instances[0]
    instance.add_tag(name, value)
    print(host_yaml(instance2dict(instance)))

@fab.task
def remove_tag(instance_id, name):
    instance = ec2_conn.get_all_instances(instance_id)[0].instances[0]
    instance.remove_tag(name)
    print(host_yaml(instance2dict(instance)))

# End tasks
