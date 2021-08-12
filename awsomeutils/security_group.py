import boto3
import ipaddress
from cerberus import Validator, schema_registry

EC2 = boto3.resource('ec2')
VALIDATOR = Validator()

IPV4_REGEX = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(/([0-9]|[0-2][0-9]|3[0-2]))?$'
IPV6_REGEX = r'^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))(\/((1(1[0-9]|2[0-8]))|([0-9][0-9])|([0-9])))?$'

#######################################################################################################
#
#  update_security_group
#
#######################################################################################################
schema_registry.add('update_security_group', {
    'security_group_id': {'required': True, 'type': 'string'},
    'comment': {'type': 'string'},
    'port': {'required': True, 'type': 'integer'},
    'protocol': {'required': True, 'type': 'string'},
    'allowed_ipv4_addresses': {'required': True, 'type': 'list', 'schema': {'type': 'string', 'regex': IPV4_REGEX}},
    'allowed_ipv6_addresses': {'required': True, 'type': 'list', 'schema': {'type': 'string', 'regex': IPV6_REGEX}}
})
def update_security_group(**kwargs):
    try:
        if not VALIDATOR.validate(kwargs, schema_registry.get('update_security_group')): raise ValueError(VALIDATOR.errors)

        new_rule = kwargs
        security_group_id = new_rule['security_group_id']
        port = new_rule['port']
        protocol = new_rule['protocol']
        current_rule = get_rule(security_group_id, port, protocol)

        new_rule['allowed_ipv4_addresses'] = [str(ipaddress.ip_network(ip)) for ip in new_rule['allowed_ipv4_addresses']]
        new_rule['allowed_ipv6_addresses'] = [str(ipaddress.ip_network(ip)) for ip in new_rule['allowed_ipv6_addresses']]
        
        revoking_addresses = diff_addresses(current_rule, new_rule)
        set_rule('revoke', security_group_id, port, protocol, revoking_addresses)
        
        authorizing_addresses = diff_addresses(new_rule, current_rule)
        set_rule('authorize', security_group_id, port, protocol, authorizing_addresses)

        return {
            "port": port,
            "protocol": protocol,
            "revoked_ipv4_addresses": revoking_addresses['allowed_ipv4_addresses'],
            "authorized_ipv4_addresses": authorizing_addresses['allowed_ipv4_addresses'],
            "revoked_ipv6_addresses": revoking_addresses['allowed_ipv6_addresses'],
            "authorized_ipv6_addresses": authorizing_addresses['allowed_ipv6_addresses']
        }

    except Exception as e:
        raise e

#------------------------------------------------------------------------------------------------------
#  diff_addresses
#------------------------------------------------------------------------------------------------------
def diff_addresses(addresses1, addresses2):
    return {
        'allowed_ipv4_addresses': diff_list(addresses1['allowed_ipv4_addresses'], addresses2['allowed_ipv4_addresses']),
        'allowed_ipv6_addresses': diff_list(addresses1['allowed_ipv6_addresses'], addresses2['allowed_ipv6_addresses'])
    }

#------------------------------------------------------------------------------------------------------
#  diff_list
#------------------------------------------------------------------------------------------------------
def diff_list(list1, list2):
    return (list(set(list1) - set(list2)))

#------------------------------------------------------------------------------------------------------
#  get_rule
#------------------------------------------------------------------------------------------------------
def get_rule(security_group_id, port, protocol):
    allowed_ipv4_addresses = []
    allowed_ipv6_addresses = []

    for ip_permission in EC2.SecurityGroup(security_group_id).ip_permissions:
        if ip_permission.get('FromPort', None) == port and ip_permission.get('IpProtocol', None) == protocol:
            for ip_range in ip_permission['IpRanges']:
                allowed_ipv4_addresses.append(ip_range['CidrIp'])
            
            for ip_range in ip_permission['Ipv6Ranges']:
                allowed_ipv6_addresses.append(ip_range['CidrIpv6'])
            
    return {
        'allowed_ipv4_addresses': allowed_ipv4_addresses,
        'allowed_ipv6_addresses': allowed_ipv6_addresses
    }

#------------------------------------------------------------------------------------------------------
#  set_rule
#------------------------------------------------------------------------------------------------------
def set_rule(action, security_group_id, port, protocol, addresses):
    try:
        if len(addresses['allowed_ipv4_addresses']) == 0 and len(addresses['allowed_ipv6_addresses']) == 0:
            return

        ip_permissions = [{
            "FromPort": port,
            "IpProtocol": protocol,
            "IpRanges": [ {'CidrIp': ip} for ip in addresses['allowed_ipv4_addresses'] ],
            "Ipv6Ranges": [ {'CidrIpv6': ip} for ip in addresses['allowed_ipv6_addresses'] ],
            "PrefixListIds": [],
            "ToPort": port,
            "UserIdGroupPairs": []
        }]

        if action == 'authorize':
            EC2.SecurityGroup(security_group_id).authorize_ingress(IpPermissions=ip_permissions)
        elif action == 'revoke':
            EC2.SecurityGroup(security_group_id).revoke_ingress(IpPermissions=ip_permissions)

    except Exception as e:
        raise e
