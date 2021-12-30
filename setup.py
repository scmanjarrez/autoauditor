from setuptools import setup

import pathlib
import os

_parent = pathlib.Path(__file__).parent.resolve()
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
    packages=[
        'autoauditor',
        'autoauditor.tools'
    ],
    package_dir={
        'autoauditor.tools': 'tools'
    },
    package_data={
        'autoauditor.tools': ['tools/*']
    },
    include_package_data=True,
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
            'autoauditor=autoauditor.__main__:main'
        ]
    }
)
