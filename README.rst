Dakku
=====
Collection of utility stuff for use with django.

.. contents:: Contents
    :depth: 5

ajax
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
        }
        else {
            // Do something else
        }
    });

If it was request was not succuessful the 'error' parameter is required. It
should contian a string message of why the request failed. For example::

    >>> AjaxResponse(False, error='You must logged to continue')

email
-----

Sends an email in the following message format::

    Subject: {{ comment.user }} posted comment
    From: {{ settings.SITE_NAME }} <noreply@{{ settings.SITE_NAME }}>
    To: {{ email }}

    {{ comment.text|safe }}

The kwargs are passed to the template for subsitution

    email_util.send_email(
        email,
        'email/comment_was_posted.msg',
        comment=comment,
        settings=settings)

log
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
