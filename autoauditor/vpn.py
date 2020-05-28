import utils
import docker
import os


def setup_vpn(ovpn_file, stop):
    client = docker.from_env()
    vpncont = None

    utils.log('succb', utils.VPNSTAT, end='\r')

    try:
        image = client.images.get('dperson/openvpn-client')
        utils.log('succg', utils.VPNEXIST)
    except docker.errors.ImageNotFound:
        utils.log('warn', utils.VPNDOWN, end='\r')
        image = client.images.pull('dperson/openvpn-client', 'latest')
        utils.log('succg', utils.VPNDONE)

    utils.log('succb', utils.VPNCSTAT, end='\r')

    vpn_l = client.containers.list(filters={'name':'vpncl'})
    if not vpn_l:
        if not stop:
            utils.log('warn', utils.VPNCSTART, end='\r')
            of = os.path.abspath(ovpn_file)

            ipam_pool = docker.types.IPAMPool(subnet='10.10.20.0/24')
            ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
            try:
                net = client.networks.get('attacker_network')
            except docker.errors.NotFound:
                net = client.networks.create('attacker_network', driver='bridge', ipam=ipam_config)

            vpncont = client.containers.run(image, 'sh -c "sleep 5 && /sbin/tini -- /usr/bin/openvpn.sh"',
                                            auto_remove=True,
                                            stdin_open=True, tty=True,
                                            detach=True, cap_add='NET_ADMIN',
                                            security_opt=['label:disable'],
                                            tmpfs={'/run': '', '/tmp':''},
                                            name='vpncl',
                                            network='attacker_network',
                                            volumes={'/dev/net': {'bind': '/dev/net', 'mode': 'z'},
                                                     of: {'bind': '/vpn/vpn.ovpn'}},
                                            environment={'DEFAULT_GATEWAY': 'false',
                                                         'ROUTE': '10.10.20.0/24'})
            try:
                net = client.networks.get('bridge')
            except docker.errors.NotFound:
                utils.log('error', "Docker 'bridge' network not found.", errcode=utils.ENOBRDGNET)
            else:
                net.connect('vpncl')
            utils.log('succg', utils.VPNCDONE)
        else:
            utils.log('succg', utils.VPNCNR)
    else:
        utils.log('succg', utils.VPNCR)
        vpncont = vpn_l[0]

    return vpncont
