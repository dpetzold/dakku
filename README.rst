Dakku
=====
Collection of utility stuff for use with django.

.. contents:: Contents
    :depth: 5

------
Fields
------

RandomCharField
---------------
Django field that auto populates with a unique random character field. Valid
options are:

- length - Specifiy the field length. Defaults to 8.
- digits_only - Only use digits. Defaults to False.
- alpha_only - Only use alpha characters. Defaults to False.
- lowercase - Lowercase the characters. Defaults to False.
- include_punctuation - Include punctuation characters. Defaults to False.

Here is some sample output:

    >>> class RandomCharTestModel(models.Model):
    >>>     chars = RandomCharField(length=12)
    YMNVm9GE

    >>> class RandomCharTestModelAlpha(models.Model):
    >>>     chars = RandomCharField(length=12, alpha_only=True)
    CxPWKJHDPnNO

    >>> class RandomCharTestModelDigits(models.Model):
    >>>     chars = RandomCharField(length=4, digits_only=True)
    7097

    >>> class RandomCharTestModelPunctuation(models.Model):
    >>>     chars = RandomCharField(length=12, include_punctuation=True)
    k[ZS.TR,0LHO    

    >>> class RandomCharTestModelLower(models.Model):
    >>>     chars = RandomCharField(length=12, lower=True, alpha_only=True)
    pzolbemetmok

    >>> class RandomCharTestModelLowerAlphaDigits(models.Model):
    >>>     chars = RandomCharField(length=12, lower=True, include_punctuation=False)
    wfaytk3msiin

--------
Commands
--------

backup
------
For backing up and restoring a mysql database to Rackspace Cloud Files. The database 
is dumped gzipped and then offloaded in the following format:

    <project name>.YYYYMMDD_HHMMSS-<hostname>.gz

Valid options are:

- list - List the avaliable backups.
- restore <dump> - Restore the database contained in the dumpfile.
- cull - Delete previous backups according to the cull schedule.

By default a backup is performed and could be used in cron like this

* 3 * * * /sites/advisordeck/advisordeck/manage.py backup --cull

to backup the database every morning at 3am deleting previous backups.

The cull schedule is to keep two weeks of daily backups. Eight weeks of
Monday's backup and the always keep the backup from the first of the 
month.

Ajax
----
Return a JSON HTTP response for use with Ajax.

The first argument indicates whether the request was successful. For every
kwarg the key/value pairs are marshalled into a "data" envenlope. For
example::

    >>> return AjaxResponse(True, blah=1)

Generates the following JSON::

    {
        "data": {
            "blah": 1
        },
        "success": true
    }

That could be use by JQuery with the following::

    $.ajax({
      url: URL,
      dataType: 'json',
      success: function(response) {
        if (response.success) {
            // Do something successful
            var blah = response.data['blah'];
        }
        else {
            // Do something else
        }
    });

If it was request was not succuessful the 'error' parameter is required. It
should contian a string message of why the request failed. For example::

    >>> AjaxResponse(False, error='You must logged to continue')

Email
-----

Sends an email in the following message format::

    Subject: {{ comment.user }} posted comment
    From: {{ settings.SITE_NAME }} <noreply@{{ settings.SITE_NAME }}>
    To: {{ email }}

    {{ comment.text|safe }}

The kwargs are passed to the template for subsitution::

    email_util.send_email(
        email,
        'email/comment_was_posted.msg',
        comment=comment,
        settings=settings)

Log
---

Some utilities for use with the logging module and django.::

    request:
        (): dakku.log.StripFormatter
        format: |
          ---
          Time: %(asctime)s
          Location: %(module)s.%(funcName)s:%(lineno)s
          Level: %(levelname)s
          SessionKey: %(session_key)s
          Email: %(user.email)s
          Path: %(path)s
          Message: '%(message)s'

    yaml:
        (): dakku.log.StripFormatter
        format: |
          ---
          Time: %(asctime)s
          Location: %(module)s.%(funcName)s:%(lineno)s
          Level: %(levelname)s
          Message: '%(message)s'

    color:
        (): dakku.log.ColoredFormatter
        format: |
            ---
            Time: %(asctime)s
            Location: %(module)s.%(funcName)s:%(lineno)s
            Level: %(levelname)s
            Message: '%(message)s'

        mappings:
            critical: colors.cyan
            debug: colors.white
            error: colors.red
            info: colors.green
            warning: colors.yellow
