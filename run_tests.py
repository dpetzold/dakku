#!/usr/bin/env python

import sys
from django.conf import settings
from django.core.management import call_command

def main():
    # Dynamically configure the Django settings with the minimum necessary to
    # get Django running tests

    settings.configure(
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.admin',
            'django.contrib.sessions',
            'dakku',
            'dakku.tests',
        ],
        # Django replaces this, but it still wants it. *shrugs*
        DATABASE_ENGINE='django.db.backends.sqlite3',
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
            }
        },
        MEDIA_ROOT='/tmp/dakku_test_media/',
        MEDIA_PATH='/media/',
        ROOT_URLCONF='dakku.tests.urls',
        DEBUG=True,
        TEMPLATE_DEBUG=True,
    )

    from django.db import transaction, connection, connections, DEFAULT_DB_ALIAS
    from django.test.testcases import restore_transaction_methods, connections_support_transactions
    connection.creation.destroy_test_db = lambda *args, **kwargs: None

    from django.test.utils import get_runner
    test_runner = get_runner(settings)(verbosity=2, interactive=True)
    failures = test_runner.run_tests(['dakku'])
    sys.exit(failures)

if __name__ == '__main__':
    main()
