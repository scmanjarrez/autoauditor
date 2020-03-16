#!/bin/bash

aa="autoauditor"
aa_env="autoauditor_venv"
env_sh="gen_venv.sh"
req="requirements.txt"
dc="docker-compose"
dcyml="docker-compose.yml"
d="docker"


check_privileges()
{
    if [ "$EUID" -ne 0 ]; then
	echo "Please run as root in order to communicate with docker."
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

        smb_17_7494:
                image: vulhub/samba:4.6.3
                volumes:
                        - ./VulMach/CVE-2017-7494/smb.conf:/usr/local/samba/etc/smb.conf
                networks:
                        vulnerable_network:
                                ipv4_address: 10.10.0.5

        ssh_18_15473:
                build:
                        context: .
                        dockerfile: ./VulMach/CVE-2018-15473/Dockerfile
                environment:
                        - ROOT_PASSWORD=vulhub
                networks:
                        vulnerable_network:
                                ipv4_address: 10.10.0.6

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
                        - ssh_18_15473

networks:
        vulnerable_network:
                driver: bridge
                ipam:
                        config:
                                - subnet: 10.10.0.0/24
EOF

    $dc up -d
    wd=$(pwd)
    wd=$(echo ${wd##*/} | tr '[:upper:]' '[:lower:]')
    $d network connect bridge ${wd}_vpn_server_1 2>/dev/null
}

chk_venv_pkg()
{
    which virtualenv > /dev/null

    if [ $? -ne 0 ]; then
	which apt > /dev/null
	if [ $? -eq 0 ]; then
	    apt install virtualenv -qq
	else
	    echo "Please install virtualenv package manually."
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
    if [[ ! -d $aa_env ]]; then
	virtualenv $aa_env -p python3
    fi
}

install_req_pip()
{
    source ${aa_env}/bin/activate
    cat <<REQ > $req
pymetasploit3
docker
REQ

    pip install -r $req
}

check_venv

if [ ! -f "$req" ]; then
    install_req_pip
fi

EOF

    chmod +x $env_sh

    echo -e "\n\033[0;32mPlease run $env_sh as user in order to set up virtual environment.\033[0m"
}

stop()
{
    $dc stop
    $dc down -v
    rm $dcyml
    rm $req
    rm $env_sh
    rm -rf $aa_env
}

usage()
{
    echo "Usage:"
    echo "    $0          Set up test environment."
    echo "    $0 -s       Clean test environment."
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
