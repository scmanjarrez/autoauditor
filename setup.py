#!/usr/bin/env python3

# SPDX-License-Identifier: GPL-3.0-or-later

# setup - package setup.

# Copyright (C) 2022 Sergio Chica Manjarrez @ pervasive.it.uc3m.es.
# Universidad Carlos III de Madrid.

# This file is part of AutoAuditor.

# AutoAuditor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# AutoAuditor is distributed in the hope that it will be useful,
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
    version='1.0.0',
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
        'Programming Language :: Python :: 3.8'
    ],
    packages=['autoauditor'],
    python_requires='>= 3.6',
    install_requires=[
        'opentimestamps-client',
        'docker',
        'bs4',
        'PySimpleGUI',
        # Compiled from fork, check third_party/pymetasploit3/README.md
        (f'pymetasploit3 @ '
         f'file://localhost/{os.getcwd()}/'
         f'third_party/pymetasploit3/pymetasploit3-1.0-py3-none-any.whl'),
        # Compiled from fork, check third_party/fabric_sdk/README.md
        (f'fabric-sdk-py @ '
         f'file://localhost/{os.getcwd()}/'
         f'third_party/fabric_sdk/fabric_sdk_py-0.9.0-py3-none-any.whl')
    ],
    entry_points={
        'console_scripts': [
            'autoauditor=autoauditor.__main__:main',
            'query=autoauditor.query:main'
        ]
    }
)
