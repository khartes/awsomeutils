import boto3
import os
import pytest
import sys
from moto import mock_ec2

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

test_dir = os.path.dirname(__file__)
package_dir = os.path.normpath(os.path.join(test_dir, '../'))
sys.path.append(package_dir)
from awsomeutils.security_group import update_security_group

#######################################################################################################
#
#  TestUpdateSecurityGroup
#
#######################################################################################################
ipv4_addresses = ['192.168.0.1/32', '192.168.0.2/32', '192.168.0.3/32']

event = {
    'port': 123,
    'protocol': 'tcp',
    'allowed_ipv4_addresses': [],
    'allowed_ipv6_addresses': []
}
expected_result = {
    'port': 123,
    'protocol': 'tcp',
    'revoked_ipv4_addresses': [],
    'authorized_ipv4_addresses': [],
    'revoked_ipv6_addresses': [],
    'authorized_ipv6_addresses': []
}

@mock_ec2
class TestUpdateSecurityGroup:
    def test_kwargs(self):
        ec2 = boto3.client('ec2')
        sg_id = ec2.create_security_group(Description='test', GroupName='test_kwargs')['GroupId']

        with pytest.raises(ValueError):
            update_security_group()

        with pytest.raises(ValueError):
            update_security_group(security_group_id=sg_id)

        with pytest.raises(ValueError):
            update_security_group(security_group_id=sg_id, port=123)

        with pytest.raises(ValueError):
            update_security_group(security_group_id=sg_id, port=123, protocol='tcp')

        with pytest.raises(ValueError):
            update_security_group(security_group_id=sg_id, port=123, protocol='tcp', allowed_ipv4_addresses=[])

        assert update_security_group(security_group_id=sg_id, port=123, protocol='tcp', allowed_ipv4_addresses=[], allowed_ipv6_addresses=[])

    def test_update(self):
        ec2 = boto3.client('ec2')
        sg_id = ec2.create_security_group(Description='test', GroupName='test_update')['GroupId']

        event['allowed_ipv4_addresses'] = [ipv4_addresses[0]]
        expected_result['authorized_ipv4_addresses'] = [ipv4_addresses[0]]
        assert update_security_group(security_group_id=sg_id, **event) == expected_result

        event['allowed_ipv4_addresses'] = [ipv4_addresses[0], ipv4_addresses[1]]
        expected_result['authorized_ipv4_addresses'] = [ipv4_addresses[1]]
        assert update_security_group(security_group_id=sg_id, **event) == expected_result

        event['allowed_ipv4_addresses'] = [ipv4_addresses[0], ipv4_addresses[1], ipv4_addresses[2]]
        expected_result['authorized_ipv4_addresses'] = [ipv4_addresses[2]]
        assert update_security_group(security_group_id=sg_id, **event) == expected_result

        event['allowed_ipv4_addresses'] = [ipv4_addresses[0], ipv4_addresses[1]]
        expected_result['authorized_ipv4_addresses'] = []
        expected_result['revoked_ipv4_addresses'] = [ipv4_addresses[2]]
        assert update_security_group(security_group_id=sg_id, **event) == expected_result

        event['allowed_ipv4_addresses'] = [ipv4_addresses[0]]
        expected_result['revoked_ipv4_addresses'] = [ipv4_addresses[1]]
        assert update_security_group(security_group_id=sg_id, **event) == expected_result

        event['allowed_ipv4_addresses'] = []
        expected_result['revoked_ipv4_addresses'] = [ipv4_addresses[0]]
        assert update_security_group(security_group_id=sg_id, **event) == expected_result
