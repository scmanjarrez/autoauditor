#!/bin/bash
venv="python3 -m venv"
aa="../autoauditor.py"
aa_venv="autoauditor_venv"
bk_hfc="backup/channel.py"
bk_pym3="backup/msfrpc.py"
green="\033[0;92m[+] "
blue="\033[94m[*] "
yellow="\033[0;33m[-] "
nc="\033[0m"
hlf_sdk="fabric-sdk-py"

echo -e "${blue}Generating virtual environment.$nc"

if [ ! -d $aa_venv ]; then
    $venv $aa_venv > /dev/null
fi

source ${aa_venv}/bin/activate

echo -e "${blue}Updating pip.$nc"
pip install -U pip > /dev/null

echo -e "${blue}Installing requirements.txt.$nc"
pip install -r requirements.txt --no-cache-dir > /dev/null

echo -e "${blue}Installing fabric-sdk-py library.$nc"
cp -r $(pwd)/$hlf_sdk/hfc $aa_venv/lib/python3.*/site-packages

echo -e "${yellow}Using $bk_hfc backup until fabric-sdk-py gets fixed.$nc"
cp $bk_hfc $aa_venv/lib/python3.*/site-packages/hfc/util/

echo -e "${yellow}Using $bk_pym3 backup until pymetasploit3 gets fixed.$nc"
cp $bk_pym3 $aa_venv/lib/python3.*/site-packages/pymetasploit3/

echo -e "${green}Run 'source $aa_venv/bin/activate' and execute $aa.$nc"
