#!/usr/bin/env python3

# SPDX-License-Identifier: GPL-3.0-or-later

# setup - package setup.

# Copyright (C) 2020-2022 Sergio Chica Manjarrez @ pervasive.it.uc3m.es.
# Universidad Carlos III de Madrid.

# This file is part of autoauditor.

# autoauditor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# autoauditor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with GNU Emacs.  If not, see <https://www.gnu.org/licenses/>.

from setuptools import setup
from pathlib import Path

import os

_parent = Path(__file__).parent.resolve()
readme = (_parent / 'README.md').read_text(encoding='utf-8')

setup(
    name='autoauditor',
    version='3.1',
    description='Semi-automatic scanner and vulnerability exploiter',
    author='Sergio Chica',
    author_email='sergio.chica@uc3m.es',
    long_description=readme,
    long_description_content_type='text/markdown',
    keywords=[
        'vulnerability',
        'metasploit',
        'exploit',
        'scanner',
        'nmap',
        'cve'
    ],
    url='https://gitlab.gast.it.uc3m.es/schica/autoauditor',
    license='GPLv3+',
    license_files=['LICENSE'],
    classifiers=[
        ('License :: OI Approved :: '
         'GNU General Public License v3 or later (GPLv3+)'),
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7'
    ],
    packages=['autoauditor', 'autoauditor.gui'],
    python_requires='>= 3.7',
    install_requires=[
        'aiogrpc==1.8',
        'appdirs==1.4.4',
        'beautifulsoup4==4.11.1',
        'bs4==0.0.1',
        'certifi==2022.5.18.1',
        'cffi==1.15.0',
        'chardet==3.0.4',
        'click==8.1.3',
        'CouchDB==1.2',
        'cryptography==37.0.2',
        'decorator==5.1.1',
        'docker==5.0.3',
        # Compiled from fork, check third_party/fabric_sdk/README.md
        (f'fabric-sdk-py @ '
         f'file://localhost/{os.getcwd()}/'
         f'third_party/fabric_sdk/fabric_sdk_py-0.9.0-py3-none-any.whl'),
        'Flask==2.1.2',
        'gitdb==4.0.9',
        'GitPython==3.1.27',
        'grpcio==1.46.3',
        'hkdf==0.0.3',
        'idna==2.7',
        'importlib-metadata==4.11.4',
        'itsdangerous==2.1.2',
        'Jinja2==3.1.2',
        'lark-parser==0.7.1',
        'MarkupSafe==2.1.1',
        'msgpack==1.0.4',
        'opentimestamps==0.4.1',
        'opentimestamps-client==0.7.0',
        'path==16.4.0',
        'path.py==12.5.0',
        'protobuf==3.20.1',
        'py==1.11.0',
        'pycparser==2.21',
        'pycryptodomex==3.14.1',
        # Compiled from fork, check third_party/pymetasploit3/README.md
        (f'pymetasploit3 @ '
         f'file://localhost/{os.getcwd()}/'
         f'third_party/pymetasploit3/pymetasploit3-1.0-py3-none-any.whl'),
        'pyOpenSSL==22.0.0',
        'pysha3==1.0.2',
        'PySide6==6.3.0',
        'PySide6-Addons==6.3.0',
        'PySide6-Essentials==6.3.0',
        'PySocks==1.7.1',
        'python-bitcoinlib==0.10.2',
        'requests==2.20.0',
        'retry==0.9.2',
        'Rx==3.2.0',
        'shiboken6==6.3.0',
        'six==1.16.0',
        'smmap==5.0.0',
        'soupsieve==2.3.2.post1',
        'urllib3==1.24.3',
        'websocket-client==1.3.2',
        'Werkzeug==2.1.2',
        'zipp==3.8.0'],
    entry_points={
        'console_scripts': [
            'autoauditor=autoauditor.__main__:main',
            'query=autoauditor.query:main'
        ]
    }
)
