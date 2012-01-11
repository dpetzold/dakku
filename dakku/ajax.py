from django.http import HttpResponse
import json

from bakku import util

class AjaxResponse(HttpResponse):

    """
    Return a JSON HTTP response for use with Ajax.

    The first argument indicates whether the request was successful. For every
    kwarg the key/value pairs are marshalled into a "data" envenlope. For
    example

    >>> return AjaxResponse(True, blah=1)

    Generates the following JSON:

        {
            "data": {
                "blah": 1
            },
            "success": true
        }

    That could be use by JQuery with the following:

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
    should contian a string message of why the request failed. For example:

    >>> AjaxResponse(False, error='You must logged to continue')

    This is the server response returned by the first command:

    HTTP/1.1 200 OK
    Server: nginx/1.1.4
    Date: Wed, 02 Nov 2011 07:02:36 GMT
    Content-Type: text/json
    Transfer-Encoding: chunked
    Connection: close
    Last-Modified: Wed, 02 Nov 2011 07:02:36 GMT
    Expires: Wed, 02 Nov 2011 07:12:36 GMT
    Cache-Control: max-age=600
    Set-Cookie: sessionid=2e16c990e98c48689e60237e0ff290e0; expires=Wed, 02-Nov-2011 09:02:36 GMT; Max-Age=7200; Path=/

    3f
    {
        "data": {
            "blah": 1
        },
        "success": true
    }
    0
    """

    def __init__(self, success, **kwargs):
        if not success:
            assert 'error' in kwargs, 'error is required when success is false'
        response = dict(success=success)
        if success and len(kwargs) > 0:
           response['data'] = kwargs
        elif not success:
            response.update(kwargs)
        super(AjaxResponse, self).__init__(
            json.dumps(
                response,
                indent=4), content_type='text/json')

    @staticmethod
    def decode(response):
        return util.dict2bag(json.loads(response.read()))
