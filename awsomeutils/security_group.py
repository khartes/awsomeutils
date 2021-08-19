import boto3
import ipaddress
from .safe_kwargs import safe_kwargs

IPV4_REGEX = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(/([0-9]|[0-2][0-9]|3[0-2]))?$'
IPV6_REGEX = r'^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))(\/((1(1[0-9]|2[0-8]))|([0-9][0-9])|([0-9])))?$'

#######################################################################################################
#
#  update_security_group
#
#######################################################################################################
@safe_kwargs({
    'security_group_id': {'required': True, 'type': 'string', 'doc': 'the ID of the security group.'},
    'comment': {'type': 'string', 'doc': 'rule\'s description.'},
    'port': {'required': True, 'type': 'integer', 'doc': 'port for TCP and UDP protocols.'},
    'protocol': {'required': True, 'type': 'string', 'doc': 'IP protocol name (tcp, udp, icmp, icmpv6) or -1 to specify all protocols.'},
    'allowed_ipv4_addresses': {'required': True, 'type': 'list', 'schema': {'type': 'string', 'regex': IPV4_REGEX}, 'doc': 'IPv4 ranges. Use /32 to single IPv4 address.'},
    'allowed_ipv6_addresses': {'required': True, 'type': 'list', 'schema': {'type': 'string', 'regex': IPV6_REGEX}, 'doc': 'IPv6 ranges. Use /128 to single IPv6 address.'}
})
def update_security_group(**kwargs):
    """Update the rules of a security group.

    Args:
        **kwargs: keyword arguments. See below.

    Keyword Args:
        ${safe_kwargs}

    Raises:
        ValueError: in case of missing or invalid kwargs.

    Returns:
        The following dict for success: 
            {
                "port": 123,
                "protocol": 'string',
                "revoked_ipv4_addresses": ['string'],
                "authorized_ipv4_addresses": ['string'],
                "revoked_ipv6_addresses": ['string'],
                "authorized_ipv6_addresses": ['string']
            }
    """    
    try:
        new_rule = kwargs
        ec2 = boto3.resource('ec2')
        security_group = ec2.SecurityGroup(new_rule['security_group_id'])
        port = new_rule['port']
        protocol = new_rule['protocol']
        current_rule = _get_rule(security_group, port, protocol)

        new_rule['allowed_ipv4_addresses'] = [str(ipaddress.ip_network(ip)) for ip in new_rule['allowed_ipv4_addresses']]
        new_rule['allowed_ipv6_addresses'] = [str(ipaddress.ip_network(ip)) for ip in new_rule['allowed_ipv6_addresses']]
        
        revoking_addresses = _diff_addresses(current_rule, new_rule)
        _set_rule('revoke', security_group, port, protocol, revoking_addresses)
        
        authorizing_addresses = _diff_addresses(new_rule, current_rule)
        _set_rule('authorize', security_group, port, protocol, authorizing_addresses)

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
#  _diff_addresses
#------------------------------------------------------------------------------------------------------
def _diff_addresses(addresses1, addresses2):
    return {
        'allowed_ipv4_addresses': _diff_list(addresses1['allowed_ipv4_addresses'], addresses2['allowed_ipv4_addresses']),
        'allowed_ipv6_addresses': _diff_list(addresses1['allowed_ipv6_addresses'], addresses2['allowed_ipv6_addresses'])
    }

#------------------------------------------------------------------------------------------------------
#  _diff_list
#------------------------------------------------------------------------------------------------------
def _diff_list(list1, list2):
    return (list(set(list1) - set(list2)))

#------------------------------------------------------------------------------------------------------
#  _get_rule
#------------------------------------------------------------------------------------------------------
def _get_rule(security_group, port, protocol):
    allowed_ipv4_addresses = []
    allowed_ipv6_addresses = []

    for ip_permission in security_group.ip_permissions:
        if ip_permission.get('FromPort', None) == port and ip_permission.get('IpProtocol', None) == protocol:
            for ip_range in ip_permission.get('IpRanges', []):
                allowed_ipv4_addresses.append(ip_range['CidrIp'])
            
            for ip_range in ip_permission.get('Ipv6Ranges', []):
                allowed_ipv6_addresses.append(ip_range['CidrIpv6'])
            
    return {
        'allowed_ipv4_addresses': allowed_ipv4_addresses,
        'allowed_ipv6_addresses': allowed_ipv6_addresses
    }

#------------------------------------------------------------------------------------------------------
#  _set_rule
#------------------------------------------------------------------------------------------------------
def _set_rule(action, security_group, port, protocol, addresses):
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
            security_group.authorize_ingress(IpPermissions=ip_permissions)
        elif action == 'revoke':
            security_group.revoke_ingress(IpPermissions=ip_permissions)

    except Exception as e:
        raise e
