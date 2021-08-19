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
    'message': {'required': True, 'doc': 'Message to be sent. Keys:', 'type': 'dict', 'schema': {
        'email': {'required': True, 'type': 'string', 'regex': EMAIL_REGEX, 'doc': 'Receiver\'s e-mail address'},
        'subject': {'required': True, 'type': 'string'},
        'body': {'required': True, 'type': 'string'}}},
    'host': {'required': True, 'type': 'string', 'doc': 'SMTP server\'s address'},
    'port': {'required': True, 'type': 'integer', 'doc': 'SMTP server\'s port'},
    'user': {'required': True, 'type': 'string', 'doc': 'SMTP server\'s username'},
    'password': {'required': True, 'type': 'string', 'doc': 'SMTP server\'s password'}
})
def send(**kwargs):
    """Send an e-mail message.

    Args:
        **kwargs: keyword arguments. See below.

    Keyword Args:
        ${safe_kwargs}

    Raises:
        ValueError: in case of missing or invalid kwargs.

    Returns:
        The following dict for success: { 'status_code': 200 }
    """    
    try:
        message = kwargs['message']
        server = _open_server_connection(kwargs['host'], kwargs['port'], kwargs['user'], kwargs['password'])

        mail = _build_message(message['subject'], message['body'])
        server.sendmail(kwargs['user'], message['email'], mail.as_string())

        server.close()      

        return {
            'status_code': 200
        }

    except Exception as e:
        raise e

#------------------------------------------------------------------------------------------------------
#  _build_message
#------------------------------------------------------------------------------------------------------
def _build_message(subject, body):
    try:
        msg = EmailMessage()

        msg['Subject'] = subject
        msg.set_content(body)
        
        return msg 

    except Exception as e:
       raise e

#------------------------------------------------------------------------------------------------------
#  _open_server_connection
#------------------------------------------------------------------------------------------------------
def _open_server_connection(host, port, user, password):
    try:   
        server = smtplib.SMTP_SSL(host, port)

        server.ehlo()
        server.login(user, password)

        return server

    except Exception as e:
        raise e 
