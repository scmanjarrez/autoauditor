import utils, docker, os


def setup_vpn(ovpn_file):
    client = docker.from_env()

    utils.log('succb', "VPN client image status: ", end='')

    try:
        image = client.images.get('dperson/openvpn-client')
        utils.log('succg', "exists, skipping.", reset=True)
    except docker.errors.ImageNotFound:
        utils.log('warn', "does not exist, downloading...", reset=True)
        image = client.images.pull('dperson/openvpn-client', 'latest')

    utils.log('succb', "VPN client container status: ", end='')

    vpn_l = client.containers.list(filters={'name':'vpncl'})
    if not vpn_l:
        utils.log('warn', "not running, starting...", reset=True)
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
            utils.log('error', "Docker 'bridge' network not found.", errcode=utils.EBDGNET)
        else:
            net.connect('vpncl')
    else:
        utils.log('succg', "running, skipping.", reset=True)
        vpncont = vpn_l[0]

    return vpncont
