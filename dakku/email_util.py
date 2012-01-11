from django.core import mail
from django.template import loader, Context, Template

class EmailUtil(object):

    def __init__(self):
        super(EmailUtil, self).__init__()

    def send_email(self, email, filename, **kwargs):

        if not 'email' in kwargs.keys():
            kwargs['email'] = email

        if 'html' in kwargs.keys():
            html = kwargs['html']
        else:
            html = False

        msg = loader.render_to_string(filename, dictionary=kwargs)

        in_body = False
        headers = {}
        message = ''
        for line in msg.split('\n'):
            if line == '':
                in_body = True
                continue

            if not in_body:
                key, value = line.split(':')
                headers[key] = value.strip()
            else:
                message += line + '\n'

        connection = mail.get_connection(fail_silently=False)

        message = mail.message.EmailMessage(
                    subject=headers['Subject'],
                    body=message,
                    from_email=headers['From'],
                    to=[email])

        if html:
            message.content_subtype = 'html'
        return connection.send_messages([message])

send_email = EmailUtil().send_email
