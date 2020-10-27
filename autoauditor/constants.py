from datetime import date
import os


# Error Codes

NOERROR = 240  # All good
EBUILD = 241  # Building problems
ENOBRDGNET = 242  # docker bridge network not found
EACCESS = 243  # Permission denied
EMSCONN = 244  # Metasploit container not connecting, is it running?
EMSPASS = 245  # Authentication, password does not match'
ENOPERM = 246  # User does not belong docker group
EMODNR = 247  # Module not runnable, try with autoauditor.py
EBADREPFMT = 248  # Bad report format
ECONN = 249  # Connection error, can not connect to HLF peer
EBADNETFMT = 250  # Bad network configuration file (format)
EMISSINGARG = 251  # Query missing argument
ENOENT = 252  # No such file or directory
EBADRCFMT = 253  # Bad resources script (format)
EINTR = 254  # Interrupted system call
EDOCKER = 255  # Docker API error
EHLFCONN = 256  # Hyperledger Fabric Error

# Copyright

COPYRIGHT = """
AutoAuditor  Copyright (C) 2020 Sergio Chica Manjarrez @ pervasive.it.uc3m.es.
Universidad Carlos III de Madrid.
This program comes with ABSOLUTELY NO WARRANTY; for details check below.
This is free software, and you are welcome to redistribute it
under certain conditions; check below for details.
"""


# Metasploit

DEFAULT_MSFRPC_PASSWD = 'dummypass'


# Log Messages

MSSTAT = "Metasploit image status:"
MSEXIST = "Metasploit image status: exists."
MSDOWN = "Metasploit image status: does not exist, downloading ..."
MSDONE = "Metasploit image status: does not exist, downloading ... done"
MSCSTAT = "Metasploit container status:"
MSCR = "Metasploit container status: running."
MSCNR = "Metasploit container status: not running."
MSCSTART = "Metasploit container status: not running, starting ..."
MSCDONE = "Metasploit container status: not running, starting ... done"
MSSTOP = "Stopping metasploit container ..."
MSSTOPPED = "Stopping metasploit container ... done"
MSSTOPERR = "Stopping metasploit container ... error"
MSNR = "Stopping metasploit container ... not running"
VPNSTAT = "VPN client image status:"
VPNEXIST = "VPN client image status: exists."
VPNDOWN = "VPN client image status: does not exist, downloading ..."
VPNDONE = "VPN client image status: does not exist, downloading ... done"
VPNCSTAT = "VPN client container status:"
VPNCR = "VPN client container status: running."
VPNCNR = "VPN client container status: not running."
VPNCSTART = "VPN client container status: not running, starting ..."
VPNCDONE = "VPN client container status: not running, starting ... done"
VPNSTOP = "Stopping VPN client container ..."
VPNSTOPPED = "Stopping VPN client container ... done"
VPNSTOPERR = "Stopping VPN client container ... error"
VPNNR = "Stopping VPN client container ... not running"
ATNET = "Removing attacker_network ..."
ATNETRM = "Removing attacker_network ... done"
ATNETNF = "Removing attacker_network ... not found"
ATNETAEND = "Removing attacker_network ... error. Active endpoints."
GENREP = "Generating report ..."
GENREPDONE = "Generating report ... done"
MODULE_TYPES = ['auxiliary', 'encoder', 'exploit', 'nop', 'payload', 'post']
RC_TEMPLATE = '../config/rc.template.json'
NET_TEMPLATE = '../config/network.template.json'
OVPN_TEMPLATE = '../config/client.example.ovpn'


# GUI

WRAP_TEXT_SIZE = 90

ABOUT_NAME = 'AutoAuditor'
ABOUT_YEAR = date.today().strftime('%Y')
ABOUT_AUTHOR = 'Sergio Chica Manjarrez'
ABOUT_LAB = 'Pervasive Computing Laboratory'
ABOUT_DEPARTMENT = "Telematic Engineering Department"
ABOUT_UC3M = 'Universidad Carlos III de Madrid, Leganés'
ABOUT_LOCATION = 'Madrid, Spain'
ABOUT_VERSION = 'v1.0'
ABOUT_LICENSE = 'GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007'
ABOUT_ACKNOWLEDGEMENT = """This work has been supported by National R&D Projects TEC2017-84197-C4-1-R,
TEC2014- 54335-C4-2-R, and by the Comunidad de Madrid project CYNAMON
P2018/TCS-4566 and co-financed by European Structural Funds (ESF and FEDER)."""

FILEPNG = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAgCAYAAAAIXrg4AAAABHNCSVQICAgIfAhki'
           b'AAAAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYX'
           b'BlLm9yZ5vuPBoAAACFSURBVEiJ7dC9DkAwGEbhQ8XghlyZwWgzuN4murCUNJTo3+Q'
           b'7iaGJvE9agBlYgS3wO9LAyEsx4y5wnKcnIGbcB2z2NYoCXiQ3cENKACdSXX4OqXKA'
           b'p8bSgG4ixwFawDiQtzoBGCzyWsoTfSrlBgIIIIAAAgjwM8AU3F8V0AE9oDKPG2DZA'
           b'ZVbdv9fKQUhAAAAAElFTkSuQmCC')
FOLDERPNG = (b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAYCAYAAACbU/80AAAABHNCSVQICAgIfAh'
             b'kiAAAAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3'
             b'NjYXBlLm9yZ5vuPBoAAABtSURBVEiJ7dYxEoAgDETRLwXntgzn4Gww3kILoLESj'
             b'KZJZrah2Ue3ABFIQAXOh9lRPJko/gQx8/N7RAOwWq6GeAtYSenwuPUHq0vWgMMa'
             b'QLAsd4ADHOAABzhgAKphfwlANgRkaLNcaDPp90l2AYuzfIE6Q1SuAAAAAElFTkS'
             b'uQmCCiVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICA'
             b'gIfAhkiAAAAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3L'
             b'mlua3NjYXBlLm9yZ5vuPBoAAAB0SURBVFiF7dYxEoAgDETRLwXntsRzcDYYb6EF'
             b'2FgJgrHYnUmTZl+6gKKABzYgA8fDWUcCQkPxFETL5fcJIwC95cMQbwE9kyrcL3V'
             b'hlc0asFsDcJblAggggAACCHABsmF/ckA0BEQob3mgvEmfv2TTT1R+nxOQcHyB+7'
             b'o6JAAAAABJRU5ErkJggg==')
PLAY = (b'iVBORw0KGgoAAAANSUhEUgAAACoAAAAwCAYAAABnjuimAAAABHNCSVQICAgIfAhkiAAA'
        b'AAlwSFlzAAABYgAAAWIBXyfQUwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9y'
        b'Z5vuPBoAAAGhSURBVFiF1dk/S1ZRHAfwTzXUkAqKY0GzS5M56AvIIXwBUVuCS29AsK2g'
        b'qUWcHV3FsZbQwUCHlpKoIdKlPw4ilH9Ow/XARW5dbzw955wvfIdn+/A8D7/7O+dSZQBP'
        b'8Qk/8QFPMCijDOEtQkP38BCXkulqea4ZWe8bTKQCxnzUDg04wRJG0jA5agGe7zfM4Uq/'
        b'oV2Q9W5jqgRo7CpulgANOFCNs6u5Q2N3MF0CtP53uFUCNOAQz3A9d2jsZzwoARr7CmMl'
        b'QAN+4YV/XHb6CY3dxSNczh0au4k7JUCDatlZxmju0NjveOwvy05q4PluY7IEaMApVnAj'
        b'd2jsPmaozkKh6WvOKMeYKgEKa6VAf3R6MiRMKAW6UcJPf+RsrqYeQW3j6V4Up8YUO/C3'
        b'ZP4IzX4pKWLN28R4GzAldFd1Mu1079pPYBGHu5cyPy5nfwFRxJVO9pdk73G318BeQrO/'
        b'yG1cHnKD/nF5+F/p+vrmK2Z1vODqRXYuCDzGIob7DYxZaAEGvMbtVMCYa1jXDPyC+zJ5'
        b'aUs1VuZVc/AQ784+D6RE1fMb8xrY5j34j0EAAAAASUVORK5CYII=')
STOP = (b'iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAABHNCSVQICAgIfAhkiAAA'
        b'AAlwSFlzAAABYgAAAWIBXyfQUwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9y'
        b'Z5vuPBoAAAObSURBVGiBxdpNb5VVEAfwXxFEaetCiC9tXBJQEQ20XamJxmhM1NLEJYpx'
        b'4caPQFK/ASYoCRuVrrpVlGpQ40ZX6kJjVWCtO0zoG7YU6+Lcm16vd573ezvJbJ47Z2b+'
        b'z8yZM8+cO6R5GsIY9mO49WwV1/FHP4zVpWE8j2fwJA5hXyC7iiv4Ft/gy9azHaEpzGEZ'
        b'WxV5CRcwOUjHJ6U3V9XpiC9jop+O34PzuN0H59t8G+cw2rTzx3Ctj45381U80ZTzM7hZ'
        b'0oE1/IQfWryI9Qo6pus6fwqbBYxt4FOcxGHc0UPXbhzE6/istSZP762WfCWaKeD8Mk7j'
        b'vgr692MWKwVAvFJW+XH5aTMvHVh1aUwqpXnpVHhPjOD3HIVb+AJ3NQCgTW/K3ifXpEqY'
        b'S+cLON/mBextEMRTUssR2Xs/T8GU8nW+aRBPiyOxKZX0kL4q6Xy/0umNDFufR4umMhbN'
        b'S296kJGYy7DVs+WIFixLleJOXMwB0WQkxsQl9sNu4WFxV3m6Q26vwUbincDGkq6WfSYQ'
        b'3PD/Q2qQIA6IT+z/HG7vBUIXA8WDTKfoZb3bKfRjIHQyQ/GgInEq0P19W2BInP+HcpQP'
        b'IhIPB3qXW74bDwTW9O4qu6nfkdgtPtgehMeCH38pYaTfIH4NdB7ZJf582yhhYB0npG+C'
        b'iF7EJ6ql03rwfHRXxqJ/ShrZwKuyQbyAj5UHkZnKUQotljTSpn6k02+BnkeJN/Hf0gba'
        b'aRB7Wr6EmzirjB6sCIDmSmyUIUs6JovRQfZaDQA0E4ncgwzOBkKXagKgfiSiF3CmU+hE'
        b'ILQhTQ/qUtVI3C9NJXrJv9wpOCzlVC/B2QYAVAUxG8jdwN3dBi4Ewmt4qCEQZdJpXPxB'
        b'80Ev5ZMZSucaAkDxSMxn/H48Un45Y9FbDYIoEomIMwvLhHicuC6NPJqiIpHo5k0FJnTn'
        b'MhRc32EQZ4soHRH3HltSWXu7QRBF0+mqgqNFUpjWchTOSZWiLo3L3rBb0kXg0bKKp8WH'
        b'SJtXpNHHgQqOP6D4eP2lCvqRLhfyQGxJJ/aC1Lcc1ruL3YMjLZlLBfXeUr8fMy0/nXpV'
        b'rEXbV0w/K3/FtKrGm++mR1oOVanbVfgKHm/K+TaNSvP5IndmVXlTKpUjTTvfScekEXfT'
        b'zi9o8Gq1CE3gI3EXW4RvSJPmsLfJoyb+7LEPz+FZ23/2iFJgWcrv7/C1dKFys47xJgD0'
        b'ojHcaxvICv7Cn00b+hdnbKCDt3YiiQAAAABJRU5ErkJggg==')
WIZARD = (b'iVBORw0KGgoAAAANSUhEUgAAABIAAAAwCAYAAAAcqipqAAAABHNCSVQICAgIfAhkiA'
          b'AAAAlwSFlzAAABYgAAAWIBXyfQUwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBl'
          b'Lm9yZ5vuPBoAAAFBSURBVEiJ7dfNKgVhGAfw3xEWiiLZsMNRtpZKyscd+LgCF0GxlL'
          b'KRXAsLt0CxxQX42hyOhGJxZmrwzjHnNYuzOP96mmaa93fmnWfm7QzhDGEH53hO6gzb'
          b'GMwZ8yuLeMRnTj1g4S9kFq9NkLTeMJeH9OC6AJLWDXpD0FoLSFor6eCuDLT017wDWQ'
          b'5BoxHQWAh6iYCeQtBFBHQZOjiFD8Vv9Dsm837hqAXooNml9uKkAHIs5xnKphtbqAWA'
          b'GjaTc76l0gTs03jvxpP9G5yK624nSdZxr/jzU8d+CGoFydZ0FunCcORMRn5CpaQ9oX'
          b'pZ0GEZUJoJzGBD8fbPZ4F0ObhOtv2xV9KeXetAHahtoPRdm8QAqi2MrWr8P6rhCvbE'
          b'Lf7Z2q1oLGx98ZMC9Uoi/jvt17VSofsSnDsanw534lt/i9UvqgmwtEFEVrsAAAAASU'
          b'VORK5CYII=')
CBOFF = (b'iVBORw0KGgoAAAANSUhEUgAAABUAAAAYCAYAAAAVibZIAAAABHNCSVQICAgIfAhkiAA'
         b'AAAlwSFlzAAAAsQAAALEBxi1JjQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm'
         b'9yZ5vuPBoAAAB2SURBVDiN7dWxDYMwEAXQR5SamglSpWSAbACLAbNkj5Rp2CBteiTTG'
         b'Co6G4nCX7rS767y54RUcXo8Mngz3jAhZJyxwh81vvglXNngGb19wysBFN8HhFsidJiC'
         b'FrSgBb02etonPcpbJ8NWfB1a3BMuXfARiy97VsCXOZPYbuz2AAAAAElFTkSuQmCC')
CBON = (b'iVBORw0KGgoAAAANSUhEUgAAABUAAAAYCAYAAAAVibZIAAAABHNCSVQICAgIfAhkiAAA'
        b'AAlwSFlzAAAAsQAAALEBxi1JjQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9y'
        b'Z5vuPBoAAAERSURBVDiNtdU9SsRAFADgb2VFbER7CysvoK2whS6ihZ5EBEURBE/gegZP'
        b'oHYeQg9g5wVELFx/EGORZJkNiUk22QdTvMzMl8m8JMMUopO0fay24D3hDq4QtdgGHbxh'
        b'AY94bbDKJawl3ugOvQagZH6EaKYhlBtN0bm20U284Civc5I97WMYzF3RcE/7uMV8kl/g'
        b'uWyls9goALfxEcw5C/p6wfUxtIubJD/PgDv4DMafZvoL0WW856xkNwOe5DxFIUpc1bAI'
        b'1/gK8uMcsBSFrQyct4e10RROi/KLw3/AyihxtYc4KAHH0G7JwHss4rsCOooqL38tsCpa'
        b'O6b2kx5o9zi5TA++PayLP9NJ4wcPkoOv9fgD1GiK6TLKDs8AAAAASUVORK5CYII=')
INFO = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfAhkiAAA'
        b'AAlwSFlzAAAAsQAAALEBxi1JjQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9y'
        b'Z5vuPBoAAAG6SURBVEiJrdY9axRBGAfwX5IzvmFSCB42YqFJIWiMpYpYxEawsRP0C1iK'
        b'2NhY2KQRtAkJaWxFYlJYqPVFP4CF2CdYiG8gd8ihxe7CZG5mdw/8wwO7M/P8n9d5mdCM'
        b'WSxhHt1y7As+4Q1+tuBIYhFbGOBvRgbYxMI4xAexjmENcSxDrOJAE3kXH8YgjmUbx+o8'
        b'z5F/xAPcwBXcUaQvFeV2LpL1xOI/uIeJjFOXsJPQW40XLma8uZsLN8AZ/I70hqLCbyXI'
        b'P0dEJ/AQj3A6mnuS0H9VTc7Kt+JzHMYpe1PxA0cDA9cTun3MdHAN05nwb+MyDtnbHYNo'
        b'XapG+7E0mQg3xsmI/AXO4mswdjWjOwfPtOvxPm4mSC4aLXIlTycbvA/xGC+D/324j3eK'
        b'PZREB7stDbwOvqfRw4UGnZ2O0XbM4VZAON+CXMVd16axfC+lbc2OVJY2WygsY6qU5Rbr'
        b'N8JQzqs/nr+VxBWmGiIZ4lycr7WG1IxjYCUmpzhi3/+HFPUUuziJboORpiL31Fw4YSRr'
        b'xr8yV+o8T2FBceT2a4j7im4ZKWiF3E0VYkbxbJnD8XJsV/FseYtfdcr/ANVRC3ZXH1Bb'
        b'AAAAAElFTkSuQmCC')
ABOUT = (b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAA'
         b'AAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm'
         b'9yZ5vuPBoAAAHfSURBVFiFxdfLThRBFAbgj4YV6LBRZO114cbrK5j4AKIm7kh8BTND4'
         b'pqFT+DCLfo0jpeYiANBTIwxLhC8bHRwUV2ZsZmhu3qa8Ccn6VT6nP+vrjpVf09JxyKu'
         b'4AJm87Gf6KGLLzVqlmIBK3iD/ZJ4jQ5ON0E8h0fYqUBcjB9YRasu+U18qkFcjG3cSCW'
         b'/I6zrpOQxfuNBVfJ76DdIHqOPu2Xk1xqeeTF+CUs7EiekrfkHtPPoJeR9NGjf//A4oc'
         b'h6LjjiZKKIlSL5AnYTCrRHTKCTkP9dfk5kefLDfBaTYCrh3RaWhwfejlE6LnoFwS1sJ'
         b'NboRtWL+Jw4Aznhs/x5GWcT8/dzbrcTlTcZt7IaytcwI3yxGJcTa0SczzCfmLSOv4Wx'
         b'dzUFzGfl7xzARUzXJDyATOjJFNzHn4b4dzJsNlSsDjYIrVDn9isiNb8vnMCoZrWaFvC'
         b'SwVG8VvKphhHbsIgZPE+o82JYwFPhMqqCUW0oH3tfscae/BSNAr7hScXkcW04jUsVa6'
         b'zia3FwTjCQR338bhljSOCqY7RkEUdpSpfKyCOO1ZZHXNfMntgS3HYtzKr/a7Yn7PZJr'
         b'R6CgezglcP3R1+wWm2cqlI41YbBGeH3/JzB7HaFi6VrRH8fhn9QlcxM55dRyAAAAABJ'
         b'RU5ErkJggg==')
CONSOLE_UNHIDE = (b'iVBORw0KGgoAAAANSUhEUgAAAA8AAAAYCAYAAAAlBadpAAAABHNCSVQICA'
                  b'gIfAhkiAAAAAlwSFlzAAAAsQAAALEBxi1JjQAAABl0RVh0U29mdHdhcmUA'
                  b'd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABbSURBVDiN7c0xCoRAEAXRh55NkF'
                  b'1QD+5pFHbVRKNJZJCezGAKOuig6lOpBOjxx1lwP3QNFrSFgy3W9HywBVd3'
                  b'TPdaJHDkxEjgUUx8M4GQmAsUiYkRM4ZSsfI6LsddNmrLM3dAAAAAAElFTk'
                  b'SuQmCC')
CONSOLE_HIDE = (b'iVBORw0KGgoAAAANSUhEUgAAAA8AAAAYCAYAAAAlBadpAAAABHNCSVQICAgI'
                b'fAhkiAAAAAlwSFlzAAAAsQAAALEBxi1JjQAAABl0RVh0U29mdHdhcmUAd3d3'
                b'Lmlua3NjYXBlLm9yZ5vuPBoAAABgSURBVDiN7dChDYAwFAbhT2BogmUyRoDt'
                b'YAVCwkgMAIa6pmkxCLjkd+9OPH6+TosBoVYMWHFiR/dEjCsKpMSiQE7MBkrE'
                b'ZCBgKxTjttszVYpxY4MZfe4ZCQ4sFfc/73IB07s9/4Aha1cAAAAASUVORK5C'
                b'YII=')
ADD = (b'iVBORw0KGgoAAAANSUhEUgAAACoAAAAwCAYAAABnjuimAAAABHNCSVQICAgIfAhkiAAAA'
       b'AlwSFlzAAABYgAAAWIBXyfQUwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5'
       b'vuPBoAAAFVSURBVFiF7Zk/TsMwFIe/pAykgoEDMHEDuEAP0I0FhLgEO+JPd8QluvYWtEP'
       b'FCRohbsCCQEiJYAhDBIqfVf2IU+JP8hI7fp/iF9uJIdJzhsAtkAMF8Bm4FN8uN0BWl1x0'
       b'QK6pzIFsAFwCZ/4Pv3X2gSKhesQHgWUs8oQqHwahTQzKhCoPOk8aWsCXLVE/OTDj9+gkw'
       b'DGid0AxhYwd/Y8VMVRD/7pmnTcbk6NRVE0UVRNF1VhrfQ5cAO9GP4/AS0PdHnBk3D8E7j'
       b'BWMNeKMDECKJm4XKyhL//WzT/WxuRoFFVjibb5ieKMZW2cT4Al8Ga0U0xPp0YbycZ55Oh'
       b'/pIjxb3K0M0RRNVFUTe9Edxx1u4oAql8698Ah8PHj+jZwrggQ/+apSWl3F78uZQo8h7bw'
       b'4CkFpqEtPJhCdY4zJ/wxTVN5oHbWlAHXwIruHIitgKu6ZKSXfAGaqgy+iuM3xwAAAABJR'
       b'U5ErkJggg==')
ADD24 = (b'iVBORw0KGgoAAAANSUhEUgAAABUAAAAYCAYAAAAVibZIAAAABHNCSVQICAgIfAhkiAA'
         b'AAAlwSFlzAAAAsQAAALEBxi1JjQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm'
         b'9yZ5vuPBoAAADRSURBVDiN7dWxagJBEMbx3xlTaqdN6iSdlY0PoJWgT6ZdWp8hkN4XE'
         b'HvxEaxOSwVTuMJ6RO4S9oqAf1iWWXY+ZmeWGWogC2uKtwR6G3zCHOeEa5YhRztBlFfy'
         b'LKgnpVHhzhojDMO+riJclqNF4f6izKdKpL/m/4gWq7/FGKfo7IBdZHfQiuwmvvAaC8d'
         b'JXv4xuKW6C9Us2C94xzE6K3v+c/C74fFP01Is1E/0XJrJ2eVf98ocamt9+8Sa+RO6GC'
         b'QU/bgOvgn6quX4HieshMGXnG9w7FckggmoLQAAAABJRU5ErkJggg==')
EDIT = (b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAA'
        b'AAlwSFlzAAABLQAAAS0B1sg7IAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9y'
        b'Z5vuPBoAAADkSURBVFiF7dcxCsIwFMbx/6DHcnB1dfIGnV0LpW528ByC6OgVvIRb0Ulx'
        b'EUFE0CEGSqltWl8ShDx4UGjp70vS0gZC2asIOAIXIAP6LvEZ8Cr1xlWIKtxZiLgG1722'
        b'GWII3AxCZNJwAoxbhDhL4nrNHy1C5NK4btMQkQSefrn5E5h8rhkA19L5uU28KYQIXvee'
        b'1y1HLIGnhnjVTPxcpiMvd+ITd7rmAQ/4/+OjjvhMAgeYdsBFRq5r4RMHWPnEAXY+cVC/'
        b'Sd5wgHsDLva0F6tXOF6ivt0n1GwcUFurHNgDWxsBQr0BZ6w2bYtcY1sAAAAASUVORK5C'
        b'YII=')
REMOVE = (b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiA'
          b'AAAAlwSFlzAAABDAAAAQwBlqf4UAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBl'
          b'Lm9yZ5vuPBoAAAD6SURBVFiF7ZYxEoIwEEWf2nkJ9B5AgTbewBvoUbimvYUzDLZYmM'
          b'yog8luXEnDn0lFNu+RkBCYkzmrwLMaOABX4JY4/hY4AmvgoilsgcG1DmgS4I2r9eO0'
          b'KXDfeqVE42o+x4lK1CNFWolvcN/KUPE5UCiRiMEH4BQSKHhfN42EBN45RjCVQOIO7F'
          b'9qaqH4LgZPkTCH+0imtBf2SdnGgGwmzN/cSsIEniphCtdKqOBLhcBC0U/aVxzJVgud'
          b'E5PCTSVS4SYSWQ8izfGa8u8wg/uYSWyE8L/9jrNfSKof4FKJ4JUMMl9KxyQmv5b7lD'
          b'zXK/jRRFK4MaLTPidbHqpgYJKLVQy1AAAAAElFTkSuQmCC')

LOADING = '../autoauditor/gui_files/waiting.gif'
FONT = ('../autoauditor/gui_files/font/Hack-Regular.ttf', 12)
FONT_S = ('../autoauditor/gui_files/font/Hack-Regular.ttf', 11)
FONTB = ('../autoauditor/gui_files/font/Hack-Regular.ttf', 12, 'bold')
FONTPAD = 'Any 2'

TEXT_REQ_Y = 'Yes'
TEXT_REQ_N = 'No'
TEXT_LF = 'Log File'
TEXT_LD = 'Log Directory'
TEXT_RC = 'Resources Script File'
TEXT_VPN_CB = 'Enable VPN'
TEXT_VPN_CF = 'OpenVPN Configuration File'
TEXT_BC_CB = 'Enable Blockchain'
TEXT_BC_CF = 'Blockchain Configuration File'
TEXT_BC_LF = 'Blockchain Log File'
TEXT_SC_CB = 'Stop container(s) after execution'
TEXT_START = 'Start'
TEXT_WIZARD = 'Wizard'
TEXT_STOP = 'Stop'
TEXT_MODULE_TYPE = 'Module Type'
TEXT_MODULE_NAME = 'Module Name'
TEXT_MODULE_INFO = 'Module Info'
TEXT_OPTIONS = 'Module Options'
TEXT_OPTION_INFO = 'Option Info'
TEXT_OPT_NAME = 'Option Name'
TEXT_OPT_REQ = 'Required'
TEXT_OPT_VAL = 'Current Setting'
TEXT_OPT_INFO = 'Info'
TEXT_WIZARD_GEN = 'Generate Resources Script'
TEXT_WIZARD_EXIT = 'Exit Wizard'
TEXT_PAYLOAD = 'Add payload ...'
TEXT_PAYLOAD_INFO = 'Payload Info'
TEXT_PAYLOAD_OPTIONS = 'Payload Options'
TEXT_PAYLOAD_OPTION_INFO = 'Payload Info'

TEXT_REQ_SIZE = (8, 1)
TEXT_HEAD_REQ_SIZE = (5, 1)
TEXT_DESC_SIZE = (30, 1)
TEXT_DESC_SIZE_2 = (27, 1)
TEXT_DESC_SIZE_3 = (24, 1)
TEXT_DESC_SIZE_M = (50, 1)
TEXT_DESC_SIZE_L = (79, 1)
TEXT_DESC_SIZE_L2 = (90, 1)
TEXT_DESC_SIZE_XL = (553, 1)
TEXT_DESC_SIZE_XL2 = (566, 1)
TEXT_DESC_SIZE_XL3 = (558, 1)
TEXT_OPT_NAME_SIZE = (25, 1)
TEXT_OPT_VAL_SIZE = (46, 1)

TOOLTIP_LF = ('Absolute path to log file where output should be written. '
              'Click for more details.')
TOOLTIP_LD = ('Absolute path to directory where gathered data '
              'should be collected. Click for more details.')
TOOLTIP_RC = 'Absolute path to resources script file. Click for more details.'
TOOLTIP_VPN_CF = ('Absolute path to openvpn configuration file. '
                  'Click for more details.')
TOOLTIP_BC_CF = ('Absolute path to blockchain network configuration file. '
                 'Click for more details.')
TOOLTIP_BC_LF = ('Absolute path to blockchain log file '
                 'where output should be written. Click for more details.')
TOOLTIP_INFO = 'Information'
TOOLTIP_FILE_BROWSER = 'File Browser'
TOOLTIP_FOLDER_BROWSER = 'Folder Browser'
TOOLTIP_START = 'Run AutoAuditor'
TOOLTIP_STOP = 'Stop Orphan Containers'
TOOLTIP_WIZARD = 'Launch Resources Script Helper'
TOOLTIP_MT = 'Module type. Click for more details'
TOOLTIP_MN = 'Module name. Click for more details'
TOOLTIP_MOD_ADD = 'Add module'
TOOLTIP_MOD_EDIT = 'Edit module'
TOOLTIP_MOD_REMOVE = 'Remove module'
TOOLTIP_MOD_INFO = 'Module info'
TOOLTIP_PAY_ADD = 'Add payload'
TOOLTIP_PAY_EDIT = 'Edit payload'
TOOLTIP_PAY_REMOVE = 'Remove payload'
TOOLTIP_PAY_INFO = 'Payload info'

KEY_LF_I_B = 'lf_i_b'
KEY_LF_T = 'lf_t'
KEY_LF_FB = 'lf_fb'
KEY_LD_I_B = 'ld_i_b'
KEY_LD_T = 'ld_t'
KEY_LD_FB = 'ld_fb'
KEY_RC_I_B = 'rc_i_b'
KEY_RC_T = 'rc_t'
KEY_RC_FB = 'rc_fb'
KEY_VPN_CB = 'vpn_cb'
KEY_VPN_CB_T = 'vpn_cb_t'
KEY_VPN_CF_I_B = 'vpn_cf_i_b'
KEY_VPN_CF_T = 'vpn_cf_t'
KEY_VPN_CF_FB = 'vpn_cf_fb'
KEY_BC_CB = 'bc_cb'
KEY_BC_CB_T = 'bc_cb_t'
KEY_BC_CF_I_B = 'bc_cf_i_b'
KEY_BC_CF_T = 'bc_cf_t'
KEY_BC_CF_FB = 'bc_cf_fb'
KEY_BC_LF_I_B = 'bc_lf_i_b'
KEY_BC_LF_T = 'bc_lf_t'
KEY_BC_LF_FB = 'bc_lf_fb'
KEY_SC_CB = 'sc_cb'
KEY_SC_CB_T = 'sc_cb_t'
KEY_INPUT_LF = 'input_lf'
KEY_INPUT_LD = 'input_ld'
KEY_INPUT_RC = 'input_rc'
KEY_INPUT_VPN_CF = 'input_vpn_cf'
KEY_INPUT_BC_CF = 'input_bc_cf'
KEY_INPUT_BC_LF = 'input_bc_lf'
KEY_START_B = 'start_b'
KEY_START_T = 'start_t'
KEY_STOP_B = 'stop_b'
KEY_STOP_T = 'stop_t'
KEY_WIZARD_B = 'wizard_b'
KEY_WIZARD_T = 'wizard_t'
KEY_CONSOLE = 'console'
KEY_CONSOLE_CB = 'console_cb'
KEY_MODULE_TYPE = 'module_type'
KEY_MODULE_NAME = 'module_name'
KEY_MT_I_B = 'mtype_i_b'
KEY_MN_I_B = 'mname_i_b'
KEY_WIZARD_OPTS_T = 'wizard_options_t'
KEY_WIZARD_OPTS = 'wizard_options'
KEY_WIZARD_EXIT = 'wizard_exit'
KEY_WIZARD_GEN = 'wizard_gen'
KEY_MOD_COL = 'module_col'
KEY_MOD_ADD = 'module_add'
KEY_MOD_EDIT = 'module_edit_'
KEY_MOD_REM = 'module_rem_'
KEY_MOD_INFO = 'module_info_'
KEY_MOD_FRAME = 'module_frame_'
KEY_MOD_NAME = 'module_name_'
KEY_OPT = 'option_'
KEY_OPT_VAL = 'option_value_'
KEY_OPT_HELP = 'option_help_'
KEY_OPT_ACCEPT = 'option_accept'
KEY_OPT_CANCEL = 'option_cancel'
KEY_PAYLOAD = 'payload'
KEY_PAY_ADD = 'payload_add'
KEY_PAY_EDIT = 'payload_edit'
KEY_PAY_REM = 'payload_rem'
KEY_PAY_INFO = 'payload_info'
KEY_PAY_T = 'payload_t'
KEY_PAY_DD = 'payload_dd'
KEY_PAY_HELP = 'payload_help'
KEY_PAY_OPT = 'payload_option_'
KEY_PAY_OPT_VAL = 'payload_option_value_'
KEY_PAY_OPT_HELP = 'payload_option_help_'
KEY_PAY_OPT_ACCEPT = 'payload_option_accept'
KEY_PAY_OPT_CANCEL = 'payload_option_cancel'

MAX_OPTIONS = 100
MAX_MODULES = 50

COLOR_ENABLED = 'black'
COLOR_DISABLED = 'grey'
COLOR_T = 'white'
COLOR_TAB_DISABLED = 'gray90'
BUTTON_COLOR = ('white', 'white')
BUTTON_COLOR_ERR = ('white', 'red')
BUTTON_S_SIZE = (24, 24)
BUTTON_M_SIZE = (32, 32)
BUTTON_L_SIZE = (48, 48)
PAD_EXEC_TEXT = ((10, 10), (10, 0))
PAD_T = ((5, 5), (10, 0))
PAD_IT_T = ((5, 5), (2, 0))
PAD_IT_T2 = ((7, 5), (6, 0))
PAD_IT_T3 = ((7, 5), (2, 2))
PAD_IT_T4 = ((5, 3), (2, 2))
PAD_IT_T5 = ((5, 2), (2, 2))
PAD_IT_T6 = ((2, 2), (2, 2))
PAD_IT_T7 = ((26, 5), (2, 2))
PAD_IT_T7_NS = ((18, 5), (2, 2))
PAD_IT_T_TR = ((5, 23), (6, 0))
PAD_IT_T_TR2 = ((5, 17), (6, 0))
PAD_OPT_HEAD_NAME = ((5, 5), (0, 0))
PAD_OPT_HEAD_VAL = ((6, 4), (0, 0))
PAD_OPT_HEAD_REQ = ((8, 15), (0, 0))
PAD_OPT_HEAD_REQ2 = ((8, 10), (0, 0))
PAD_OPT_HEAD_INFO = ((3, 0), (0, 0))
PAD_NO = ((0, 0), (0, 0))
PAD_NO_TB = ((5, 5), (0, 0))
PAD_NO_L = ((0, 5), (5, 5))
PAD_NO_R = ((5, 0), (5, 5))
PAD_NO_TBR = ((10, 0), (0, 0))
PAD_NO_LRB = ((0, 0), (10, 0))
PAD_NO_LB = ((0, 24), (10, 0))
PAD_NO_LB_NS = ((0, 15), (10, 0))
PAD_MOD = ((28, 0), (0, 0))
CONSOLE_PAD = ((0, 0), (10, 20))
CONSOLE_SIZE = (80, 8)
CONSOLE_CB_SIZE = (110, 1)
EXEC_TEXT_SIZE_S = (10, 1)
EXEC_TEXT_SIZE_XS = (15, 1)
EXEC_TEXT_SIZE_M = (30, 1)
EXEC_TEXT_SIZE_L = (60, 1)
EXEC_TEXT_SIZE_L2 = (49, 1)

OPT_MOD_COLUMN_SIZE = (1128, 495)
def get_exact_column_size(n_elem): return (1128, 33*n_elem)


NO_BORDER = 0
CENTER = 'center'
NO_TEXT = ''
LICENSE_TEXT_SIZE = (105, 675)
LICENSE_COLUMN_SIZE = (950, 280)


DEFAULT_LF = os.path.abspath('output/msf.log')
DEFAULT_LD = os.path.abspath('output')
DEFAULT_RC = os.path.abspath('../config/rc.example.5vuln.json')
DEFAULT_VPN_CF = os.path.abspath('../config/client.example.ovpn')
DEFAULT_BC_CF = os.path.abspath('../config/network.example.json')
DEFAULT_BC_LF = os.path.abspath('output/blockchain.log')
DEFAULT_LICENSE = os.path.abspath('../LICENSE')
