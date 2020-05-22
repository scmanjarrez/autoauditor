from pymetasploit3.msfrpc import MsfRpcClient, MsfRpcError
from io import BytesIO as fobj
import utils, json, os, sys, docker, time

def start_msfrpcd(ovpn, loot_dir):
    client = docker.from_env()

    utils.log('succb',"Metasploit image status: ", end='')

    try:
        image = client.images.get('msfrpci')
        utils.log('succg', "exists, skipping.", reset=True)
    except docker.errors.ImageNotFound:
        utils.log('warn', "does not exist, downloading...", reset=True)
        dckf = fobj(b'FROM phocean/msf\n'
                    b'RUN apt update && apt install -y iproute2 iputils-ping traceroute\n'
                    b'CMD ./msfrpcd -P dummypass && tail -f /dev/null')
        try:
            image, _ = client.images.build(fileobj=dckf, tag='msfrpci')
        except docker.errors.BuildError:
            utils.log('error', "Building error.", errcode=utils.EBUILD)

    utils.log('succb',"Metasploit container status: ", end='')

    cont_l = client.containers.list(filters={'name':'msfrpc'})
    if not cont_l:
        utils.log('warn', "not running, starting...", reset=True)

        loot = os.path.join(os.getcwd(), loot_dir)
        if ovpn:
            msfcont = client.containers.run(image,
                                            'sh -c "ip route replace default via 10.10.20.2 && ./msfrpcd -P dummypass && tail -f /dev/null"',
                                            auto_remove=True, detach=True, name='msfrpc',
                                            cap_add='NET_ADMIN', network='attacker_network',
                                            volumes={loot: {'bind': '/root/.msf4/loot'}},
                                            ports={55553:55553})
        else:
            msfcont = client.containers.run(image, auto_remove=True,
                                            detach=True, name='msfrpc',
                                            volumes={loot: {'bind': '/root/.msf4/loot'}},
                                            ports={55553:55553})
        time.sleep(10)
    else:
        utils.log('succg', "running, skipping.", reset=True)
        msfcont = cont_l[0]

    return MsfRpcClient('dummypass', ssl=True), msfcont

def launch_metasploit(client, rc_file, log_file):
    with open(rc_file, 'r') as f:
        rc = json.load(f)

    with open(log_file, 'w') as f:
        utils.log('succb', "Metasploit output log: {}".format(log_file))
        for mtype in rc:
            for mname in rc[mtype]:
                try:
                    mod = client.modules.use(mtype, mname)
                except MsfRpcError:
                    utils.log('error', "Invalid module type: {}. Check {}.".format(mtype, rc_file))
                    continue
                except TypeError:
                    utils.log('error', "Invalid module: {}. Check {}.".format(mname, rc_file))
                    continue

                for expl in rc[mtype][mname]:
                    for opt in expl:
                        try:
                            if opt[0] == "ACTION":
                                mod.action = opt[1]
                            else:
                                mod[opt[0]] = opt[1]
                        except KeyError:
                            utils.log('error', "Invalid option: {}. Check {}.".format(opt[0], rc_file))
                    cid = client.consoles.console().cid
                    exp = "{}/{}".format(mtype, mname)
                    utils.log('succg', "Logging output: {}".format(exp))
                    f.write("##### {} #####\n\n".format(exp))
                    f.write(client.consoles.console(cid).run_module_with_output(mod))
                    f.write("\n######{}######\n\n".format("#"*len(exp)))
                    client.consoles.destroy(cid)
