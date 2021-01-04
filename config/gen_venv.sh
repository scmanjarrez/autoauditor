#!/bin/bash

venv="virtualenv"
aa="../autoauditor/autoauditor.py"
aa_venv="autoauditor_venv"
tmp_hfc="backup/channel.py"
tmp_pysg="backup/PySimpleGUI.py"
tmp_pym3="backup/msfrpc.py"
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

echo -e "${yellow}Using $tmp_hfc backup until fabric-sdk-py gets fixed.$nc"
cp $tmp_hfc $aa_venv/lib/python3.*/site-packages/hfc/util/

echo -e "${yellow}Using $tmp_pym3 backup until pymetasploit3 gets fixed.$nc"
cp $tmp_pym3 $aa_venv/lib/python3.*/site-packages/pymetasploit3/

echo -e "${green}Virtual environment ready. Enable $aa_venv and execute $aa.$nc"
