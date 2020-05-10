#!/bin/bash

aa="../autoauditor/autoauditor.py"
aa_venv="autoauditor_venv"
tmp_msfrpc="backup/msfrpc.py"
env_sh="gen_venv.sh"
req="requirements.txt"
dc="docker-compose"
dcyml="docker-compose.yml"
d="docker"
vpnf="client.ovpn"
red="\033[0;91m[-] "
green="\033[0;92m[+] "
blue="\033[94m[*] "
nc="\033[0m"

check_privileges()
{
    id -Gn `whoami` | grep '\bdocker\b' > /dev/null
    if [ $? -ne 0 ]; then
        echo -e "${red}User '`whoami`' must belong to 'docker' group to communicate with docker API.$nc"
        exit
    fi
}

start()
{
    cat <<EOF > $dcyml
version: '3'

services:
        mysql_12_2122:
                image: vulhub/mysql:5.5.23
                networks:
                        vulnerable_network:
                                ipv4_address: 10.10.0.3

        ssl_14_0160:
                build:
                        context: .
                        dockerfile: ./VulMach/CVE-2014-0160/Dockerfile

                volumes:
                        - ./VulMach/CVE-2014-0160/www:/var/www/html
                        - ./VulMach/CVE-2014-0160/conf:/etc/nginx
                networks:
                        vulnerable_network:
                                ipv4_address: 10.10.0.4

        ssh_18_15473:
                build:
                        context: .
                        dockerfile: ./VulMach/CVE-2018-15473/Dockerfile
                environment:
                        - ROOT_PASSWORD=vulhub
                networks:
                        vulnerable_network:
                                ipv4_address: 10.10.0.5

        http_14_6271:
                image: vulhub/bash:4.3.0-with-httpd
                volumes:
                        - ./VulMach/CVE-2014-6271/victim.cgi:/var/www/html/victim.cgi
                networks:
                        vulnerable_network:
                                ipv4_address: 10.10.0.6

        ssh_18_10933:
                image: vulhub/libssh:0.8.1
                networks:
                        vulnerable_network:
                                ipv4_address: 10.10.0.7

        vpn_server:
                image: kylemanna/openvpn
                cap_add:
                        - NET_ADMIN
                networks:
                        vulnerable_network:
                                ipv4_address: 10.10.0.2
                volumes:
                        - ./Vpn/server-data/conf:/etc/openvpn
                depends_on:
                        - mysql_12_2122
                        - ssl_14_0160
                        - ssh_18_15473
                        - http_14_6271
                        - ssh_18_10933

networks:
        vulnerable_network:
                driver: bridge
                ipam:
                        config:
                                - subnet: 10.10.0.0/24
EOF

    echo -e "${blue}Starting docker containers.$nc"

    $dc up -d > /dev/null
    wd=$(pwd)
    wd=$(echo ${wd##*/} | tr '[:upper:]' '[:lower:]')
    vpns=${wd}_vpn_server_1
    $d network connect bridge $vpns > /dev/null 2>&1
    ip=$($d inspect -f '{{.NetworkSettings.Networks.bridge.IPAddress}}' $vpns)

    if [ -f $vpnf ]; then
        sed -i "s/remote.*1194 udp/remote "$ip" 1194 udp/" $vpnf
    fi
}

chk_venv_pkg()
{
    echo -e "${blue}Checking virtualenv package.$nc"
    which virtualenv > /dev/null

    if [ $? -ne 0 ]; then
        which apt > /dev/null
        if [ $? -eq 0 ]; then
            apt install virtualenv -qq
        else
            echo -e "${red}Install virtualenv package manually.$nc"
            exit
        fi
    fi
}

gen_venv_sh()
{
    cat <<EOF > $env_sh
#!/bin/bash

check_venv()
{
    echo -e "${blue}Generating virtual environment.$nc"
    if [ ! -d $aa_venv ]; then
        virtualenv $aa_venv -p python3 > /dev/null
    fi
}

install_req_pip()
{
    source ${aa_venv}/bin/activate
    cat <<REQ > $req
msgpack==0.6.2
pymetasploit3
docker
REQ

    pip install -r $req > /dev/null
}

check_venv
install_req_pip
echo -e "${blue}Using msrpc.py backup until pymetasploit3 package gets updated.$nc"
cp $tmp_msfrpc $aa_venv/lib/python3.*/site-packages/pymetasploit3/
echo -e "${green}Virtual environment ready. Enable $aa_venv and execute $aa.$nc"

EOF

    chmod +x $env_sh

    echo -e "${green}Execute $env_sh to set up virtual environment.$nc"
}

stop()
{
    echo -e "${blue}Stopping docker containers.$nc"
    $dc stop > /dev/null
    $dc down -v > /dev/null
    $d stop vpncl msfrpc > /dev/null

    echo -e "${blue}Removing temporary files.$nc"
    rm $dcyml
    rm $req
    rm $env_sh
    rm -rf $aa_venv
}

usage()
{
    echo "Usage:"
    echo "    $0          Set up test environment."
    echo "    $0 -s       Clean up environment."
    echo "    $0 -h       Show this help."
}

check_privileges

while getopts ":sh" opt; do
  case ${opt} in
      s) stop;;
      h) usage;;
  esac
done

if [ $OPTIND -eq 1 ]; then
    start
    chk_venv_pkg
    gen_venv_sh
fi
