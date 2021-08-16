import smtplib
import os
import pytest
import sys
from minimock import Mock

smtplib.SMTP_SSL = Mock('smtplib.SMTP_SSL')
smtplib.SMTP_SSL.mock_returns = Mock('smtp_server')

test_dir = os.path.dirname(__file__)
package_dir = os.path.normpath(os.path.join(test_dir, '../'))
sys.path.append(package_dir)
from awsomeutils import email

#######################################################################################################
#
#  class TestEmail
#
#######################################################################################################
event = {
    'message': {
        'email': 'test@test.com',
        'subject': 'Lorem Ipsum',
        'body': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'
    },
    'host': '127.0.0.1',
    'port': 25,
    'user': 'user',
    'password': 'passwd'
}

class TestEmail:
    def test_kwargs(self):
        with pytest.raises(ValueError):
            email.send()
        with pytest.raises(ValueError):
            email.send(message=event['message'])
        with pytest.raises(ValueError):
            email.send(message=event['message'], host='localhost')
        with pytest.raises(ValueError):
            email.send(message=event['message'], host='localhost', port=25)
        with pytest.raises(ValueError):
            email.send(message=event['message'], host='localhost', port=25, user='user')

    def test_send(self):
        assert email.send(**event)['status_code'] == 200
