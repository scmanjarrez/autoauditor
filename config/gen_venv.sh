#!/bin/bash

venv="virtualenv"
aa_venv="autoauditor_venv"
tmp_msfrpc="backup/msfrpc.py"
tmp_hfc="backup/channel.py"
green="\033[0;92m[+] "
blue="\033[94m[*] "
nc="\033[0m"
hfc_sdk_py="fabric-sdk-py"

echo -e "${blue}Generating virtual environment.$nc"

if [ ! -d $aa_venv ]; then
    $venv $aa_venv -p python3 > /dev/null
fi

source ${aa_venv}/bin/activate

pip install -r requirements.txt > /dev/null

echo -e "${blue}Installing fabric-sdk-py library.$nc"
cp -r $(pwd)/$hfc_sdk_py/hfc $aa_venv/lib/python3.*/site-packages

echo -e "${yellow}Using backup/channel.py backup until fabric-sdk-py gets updated.$nc"
cp $tmp_hfc $aa_venv/lib/python3.*/site-packages/hfc/util/

echo -e "${green}Virtual environment ready. Enable $aa_venv and execute $aa.$nc"
