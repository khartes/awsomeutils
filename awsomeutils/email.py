import smtplib
from email.message import EmailMessage
from .safe_kwargs import safe_kwargs

EMAIL_REGEX = r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'

#######################################################################################################
#
#  send
#
#######################################################################################################
@safe_kwargs({
    'message': {'required': True, 'type': 'dict', 'schema': {
        'email': {'required': True, 'type': 'string', 'regex': EMAIL_REGEX},
        'subject': {'required': True, 'type': 'string'},
        'body': {'required': True, 'type': 'string'}}},
    'host': {'required': True, 'type': 'string'},
    'port': {'required': True, 'type': 'integer'},
    'user': {'required': True, 'type': 'string'},
    'password': {'required': True, 'type': 'string'}
})
def send(**kwargs):
    try:
        message = kwargs['message']
        server = open_server_connection(kwargs['host'], kwargs['port'], kwargs['user'], kwargs['password'])

        mail = build_message(message['subject'], message['body'])
        server.sendmail(kwargs['user'], message['email'], mail.as_string())

        server.close()      

        return {
            'status_code': 200
        }

    except Exception as e:
        raise e

#------------------------------------------------------------------------------------------------------
#  build_message
#------------------------------------------------------------------------------------------------------
def build_message(subject, body):
    try:
        msg = EmailMessage()

        msg['Subject'] = subject
        msg.set_content(body)
        
        return msg 

    except Exception as e:
       raise e

#------------------------------------------------------------------------------------------------------
#  open_server_connection
#------------------------------------------------------------------------------------------------------
def open_server_connection(host, port, user, password):
    try:   
        server = smtplib.SMTP_SSL(host, port)

        server.ehlo()
        server.login(user, password)

        return server

    except Exception as e:
        raise e 
