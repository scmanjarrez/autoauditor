# utils - Utilities module.

# Copyright (C) 2020 Sergio Chica Manjarrez.

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

from distutils.util import strtobool
from datetime import date
import sys
import pwd
import grp
import docker
import os

############### AutoAuditor Variables ###############

NOERROR = 0
EBUILD = 241
ENOBRDGNET = 242
EACCESS = 243
EMSCONN = 244
EMSPASS = 245
ENOPERM = 246
EMODNR = 247
EBADREPFMT = 248
ECONN = 249
EBADNETFMT = 250
EMISSINGARG = 251

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
VPNNR = "Stopping VPN client container ... not running"

ATNET = "Removing attacker_network ..."
ATNETRM = "Removing attacker_network ... done"
ATNETNF = "Removing attacker_network ... not found"

GENREP = "Generating report ..."
GENREPDONE = "Generating report ... done"


############### GUI Variables ###############
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

FILEPNG = 'iVBORw0KGgoAAAANSUhEUgAAABgAAAAgCAYAAAAIXrg4AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAACFSURBVEiJ7dC9DkAwGEbhQ8XghlyZwWgzuN4murCUNJTo3+Q7iaGJvE9agBlYgS3wO9LAyEsx4y5wnKcnIGbcB2z2NYoCXiQ3cENKACdSXX4OqXKAp8bSgG4ixwFawDiQtzoBGCzyWsoTfSrlBgIIIIAAAgjwM8AU3F8V0AE9oDKPG2DZAZVbdv9fKQUhAAAAAElFTkSuQmCC'
FOLDERPNG = 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAYCAYAAACbU/80AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABtSURBVEiJ7dYxEoAgDETRLwXntgzn4Gww3kILoLESjKZJZrah2Ue3ABFIQAXOh9lRPJko/gQx8/N7RAOwWq6GeAtYSenwuPUHq0vWgMMaQLAsd4ADHOAABzhgAKphfwlANgRkaLNcaDPp90l2AYuzfIE6Q1SuAAAAAElFTkSuQmCCiVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAB0SURBVFiF7dYxEoAgDETRLwXntsRzcDYYb6EF2FgJgrHYnUmTZl+6gKKABzYgA8fDWUcCQkPxFETL5fcJIwC95cMQbwE9kyrcL3Vhlc0asFsDcJblAggggAACCHABsmF/ckA0BEQob3mgvEmfv2TTT1R+nxOQcHyB+7o6JAAAAABJRU5ErkJggg=='
PLAY = 'iVBORw0KGgoAAAANSUhEUgAAACoAAAAwCAYAAABnjuimAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAABYgAAAWIBXyfQUwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAGhSURBVFiF1dk/S1ZRHAfwTzXUkAqKY0GzS5M56AvIIXwBUVuCS29AsK2gqUWcHV3FsZbQwUCHlpKoIdKlPw4ilH9Ow/XARW5dbzw955wvfIdn+/A8D7/7O+dSZQBP8Qk/8QFPMCijDOEtQkP38BCXkulqea4ZWe8bTKQCxnzUDg04wRJG0jA5agGe7zfM4Uq/oV2Q9W5jqgRo7CpulgANOFCNs6u5Q2N3MF0CtP53uFUCNOAQz3A9d2jsZzwoARr7CmMlQAN+4YV/XHb6CY3dxSNczh0au4k7JUCDatlZxmju0NjveOwvy05q4PluY7IEaMApVnAjd2jsPmaozkKh6WvOKMeYKgEKa6VAf3R6MiRMKAW6UcJPf+RsrqYeQW3j6V4Up8YUO/C3ZP4IzX4pKWLN28R4GzAldFd1Mu1079pPYBGHu5cyPy5nfwFRxJVO9pdk73G318BeQrO/yG1cHnKD/nF5+F/p+vrmK2Z1vODqRXYuCDzGIob7DYxZaAEGvMbtVMCYa1jXDPyC+zJ5aUs1VuZVc/AQ784+D6RE1fMb8xrY5j34j0EAAAAASUVORK5CYII='
STOP = 'iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAABYgAAAWIBXyfQUwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAObSURBVGiBxdpNb5VVEAfwXxFEaetCiC9tXBJQEQ20XamJxmhM1NLEJYpx4caPQFK/ASYoCRuVrrpVlGpQ40ZX6kJjVWCtO0zoG7YU6+Lcm16vd573ezvJbJ47Z2b+z8yZM8+cO6R5GsIY9mO49WwV1/FHP4zVpWE8j2fwJA5hXyC7iiv4Ft/gy9azHaEpzGEZWxV5CRcwOUjHJ6U3V9XpiC9jop+O34PzuN0H59t8G+cw2rTzx3Ctj45381U80ZTzM7hZ0oE1/IQfWryI9Qo6pus6fwqbBYxt4FOcxGHc0UPXbhzE6/istSZP762WfCWaKeD8Mk7jvgr692MWKwVAvFJW+XH5aTMvHVh1aUwqpXnpVHhPjOD3HIVb+AJ3NQCgTW/K3ifXpEqYS+cLON/mBextEMRTUssR2Xs/T8GU8nW+aRBPiyOxKZX0kL4q6Xy/0umNDFufR4umMhbNS296kJGYy7DVs+WIFixLleJOXMwB0WQkxsQl9sNu4WFxV3m6Q26vwUbincDGkq6WfSYQ3PD/Q2qQIA6IT+z/HG7vBUIXA8WDTKfoZb3bKfRjIHQyQ/GgInEq0P19W2BInP+HcpQPIhIPB3qXW74bDwTW9O4qu6nfkdgtPtgehMeCH38pYaTfIH4NdB7ZJf582yhhYB0npG+CiF7EJ6ql03rwfHRXxqJ/ShrZwKuyQbyAj5UHkZnKUQotljTSpn6k02+BnkeJN/Hf0gbaaRB7Wr6EmzirjB6sCIDmSmyUIUs6JovRQfZaDQA0E4ncgwzOBkKXagKgfiSiF3CmU+hEILQhTQ/qUtVI3C9NJXrJv9wpOCzlVC/B2QYAVAUxG8jdwN3dBi4Ewmt4qCEQZdJpXPxB80Ev5ZMZSucaAkDxSMxn/H48Un45Y9FbDYIoEomIMwvLhHicuC6NPJqiIpHo5k0FJnTnMhRc32EQZ4soHRH3HltSWXu7QRBF0+mqgqNFUpjWchTOSZWiLo3L3rBb0kXg0bKKp8WHSJtXpNHHgQqOP6D4eP2lCvqRLhfyQGxJJ/aC1Lcc1ruL3YMjLZlLBfXeUr8fMy0/nXpVrEXbV0w/K3/FtKrGm++mR1oOVanbVfgKHm/K+TaNSvP5IndmVXlTKpUjTTvfScekEXfTzi9o8Gq1CE3gI3EXW4RvSJPmsLfJoyb+7LEPz+FZ23/2iFJgWcrv7/C1dKFys47xJgD0ojHcaxvICv7Cn00b+hdnbKCDt3YiiQAAAABJRU5ErkJggg=='
WIZARD = 'iVBORw0KGgoAAAANSUhEUgAAABIAAAAwCAYAAAAcqipqAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAABYgAAAWIBXyfQUwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAFBSURBVEiJ7dfNKgVhGAfw3xEWiiLZsMNRtpZKyscd+LgCF0GxlLKRXAsLt0CxxQX42hyOhGJxZmrwzjHnNYuzOP96mmaa93fmnWfm7QzhDGEH53hO6gzbGMwZ8yuLeMRnTj1g4S9kFq9NkLTeMJeH9OC6AJLWDXpD0FoLSFor6eCuDLT017wDWQ5BoxHQWAh6iYCeQtBFBHQZOjiFD8Vv9Dsm837hqAXooNml9uKkAHIs5xnKphtbqAWAGjaTc76l0gTs03jvxpP9G5yK624nSdZxr/jzU8d+CGoFydZ0FunCcORMRn5CpaQ9oXpZ0GEZUJoJzGBD8fbPZ4F0ObhOtv2xV9KeXetAHahtoPRdm8QAqi2MrWr8P6rhCvbELf7Z2q1oLGx98ZMC9Uoi/jvt17VSofsSnDsanw534lt/i9UvqgmwtEFEVrsAAAAASUVORK5CYII='
CBOFF = 'iVBORw0KGgoAAAANSUhEUgAAABUAAAAYCAYAAAAVibZIAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAsQAAALEBxi1JjQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAB2SURBVDiN7dWxDYMwEAXQR5SamglSpWSAbACLAbNkj5Rp2CBteiTTGCo6G4nCX7rS767y54RUcXo8Mngz3jAhZJyxwh81vvglXNngGb19wysBFN8HhFsidJiCFrSgBb02etonPcpbJ8NWfB1a3BMuXfARiy97VsCXOZPYbuz2AAAAAElFTkSuQmCC'
CBON = 'iVBORw0KGgoAAAANSUhEUgAAABUAAAAYCAYAAAAVibZIAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAsQAAALEBxi1JjQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAERSURBVDiNtdU9SsRAFADgb2VFbER7CysvoK2whS6ihZ5EBEURBE/gegZPoHYeQg9g5wVELFx/EGORZJkNiUk22QdTvMzMl8m8JMMUopO0fay24D3hDq4QtdgGHbxhAY94bbDKJawl3ugOvQagZH6EaKYhlBtN0bm20U284Civc5I97WMYzF3RcE/7uMV8kl/guWyls9goALfxEcw5C/p6wfUxtIubJD/PgDv4DMafZvoL0WW856xkNwOe5DxFIUpc1bAI1/gK8uMcsBSFrQyct4e10RROi/KLw3/AyihxtYc4KAHH0G7JwHss4rsCOooqL38tsCpaO6b2kx5o9zi5TA++PayLP9NJ4wcPkoOv9fgD1GiK6TLKDs8AAAAASUVORK5CYII='
INFO = 'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAsQAAALEBxi1JjQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAG6SURBVEiJrdY9axRBGAfwX5IzvmFSCB42YqFJIWiMpYpYxEawsRP0C1iK2NhY2KQRtAkJaWxFYlJYqPVFP4CF2CdYiG8gd8ihxe7CZG5mdw/8wwO7M/P8n9d5mdCMWSxhHt1y7As+4Q1+tuBIYhFbGOBvRgbYxMI4xAexjmENcSxDrOJAE3kXH8YgjmUbx+o8z5F/xAPcwBXcUaQvFeV2LpL1xOI/uIeJjFOXsJPQW40XLma8uZsLN8AZ/I70hqLCbyXIP0dEJ/AQj3A6mnuS0H9VTc7Kt+JzHMYpe1PxA0cDA9cTun3MdHAN05nwb+MyDtnbHYNoXapG+7E0mQg3xsmI/AXO4mswdjWjOwfPtOvxPm4mSC4aLXIlTycbvA/xGC+D/324j3eKPZREB7stDbwOvqfRw4UGnZ2O0XbM4VZAON+CXMVd16axfC+lbc2OVJY2WygsY6qU5RbrN8JQzqs/nr+VxBWmGiIZ4lycr7WG1IxjYCUmpzhi3/+HFPUUuziJboORpiL31Fw4YSRrxr8yV+o8T2FBceT2a4j7im4ZKWiF3E0VYkbxbJnD8XJsV/FseYtfdcr/ANVRC3ZXH1BbAAAAAElFTkSuQmCC'
ABOUT = 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAHfSURBVFiFxdfLThRBFAbgj4YV6LBRZO114cbrK5j4AKIm7kh8BTND4pqFT+DCLfo0jpeYiANBTIwxLhC8bHRwUV2ZsZmhu3qa8Ccn6VT6nP+vrjpVf09JxyKu4AJm87Gf6KGLLzVqlmIBK3iD/ZJ4jQ5ON0E8h0fYqUBcjB9YRasu+U18qkFcjG3cSCW/I6zrpOQxfuNBVfJ76DdIHqOPu2Xk1xqeeTF+CUs7EiekrfkHtPPoJeR9NGjf//A4och6LjjiZKKIlSL5AnYTCrRHTKCTkP9dfk5kefLDfBaTYCrh3RaWhwfejlE6LnoFwS1sJNboRtWL+Jw4Aznhs/x5GWcT8/dzbrcTlTcZt7IaytcwI3yxGJcTa0SczzCfmLSOv4WxdzUFzGfl7xzARUzXJDyATOjJFNzHn4b4dzJsNlSsDjYIrVDn9isiNb8vnMCoZrWaFvCSwVG8VvKphhHbsIgZPE+o82JYwFPhMqqCUW0oH3tfscae/BSNAr7hScXkcW04jUsVa6zia3FwTjCQR338bhljSOCqY7RkEUdpSpfKyCOO1ZZHXNfMntgS3HYtzKr/a7Yn7PZJrR6CgezglcP3R1+wWm2cqlI41YbBGeH3/JzB7HaFi6VrRH8fhn9QlcxM55dRyAAAAABJRU5ErkJggg=='
CONSOLE_UNHIDE = 'iVBORw0KGgoAAAANSUhEUgAAAA8AAAAYCAYAAAAlBadpAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAsQAAALEBxi1JjQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABbSURBVDiN7c0xCoRAEAXRh55NkF1QD+5pFHbVRKNJZJCezGAKOuig6lOpBOjxx1lwP3QNFrSFgy3W9HywBVd3TPdaJHDkxEjgUUx8M4GQmAsUiYkRM4ZSsfI6LsddNmrLM3dAAAAAAElFTkSuQmCC'
CONSOLE_HIDE = 'iVBORw0KGgoAAAANSUhEUgAAAA8AAAAYCAYAAAAlBadpAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAsQAAALEBxi1JjQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABgSURBVDiN7dChDYAwFAbhT2BogmUyRoDtYAVCwkgMAIa6pmkxCLjkd+9OPH6+TosBoVYMWHFiR/dEjCsKpMSiQE7MBkrEZCBgKxTjttszVYpxY4MZfe4ZCQ4sFfc/73IB07s9/4Aha1cAAAAASUVORK5CYII='

FONT = ('../autoauditor/gui_files/font/Hack-Regular.ttf', 12)
FONT_S = ('../autoauditor/gui_files/font/Hack-Regular.ttf', 11)
FONTB = ('../autoauditor/gui_files/font/Hack-Regular.ttf', 12, 'bold')
TEXT_DESCR_SIZE = (30, 1)
TEXT_PY = 'Python Executable Path'
TEXT_AA = 'AutoAuditor Path'
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
TOOLTIP_PY = 'Absolute path to python executable present in autoauditor_venv. Click for more details.'
TOOLTIP_AA = 'Absolute path to autoauditor tool. Click for more details.'
TOOLTIP_LF = 'Absolute path to log file where output should be written. Click for more details.'
TOOLTIP_LD = 'Absolute path to directory where gathered data should be collected. Click for more details.'
TOOLTIP_RC = 'Absolute path to resources script file. Click for more details.'
TOOLTIP_VPN_CF = 'Absolute path to openvpn configuration file. Click for more details.'
TOOLTIP_BC_CF = 'Absolute path to blockchain network configuration file. Click for more details.'
TOOLTIP_BC_LF = 'Absolute path to blockchain log file where output should be written. Click for more details.'
TOOLTIP_INFO = 'Information'
TOOLTIP_FILE_BROWSER = 'File Browser'
TOOLTIP_FOLDER_BROWSER = 'Folder Browser'
TOOLTIP_START = 'Run AutoAuditor'
TOOLTIP_STOP = 'Stop Orphan Containers'
TOOLTIP_WIZARD = 'Launch Resources Script Helper'

KEY_PY_I_B = 'py_i_b'
KEY_PY_T = 'py_t'
KEY_PY_FB = 'py_fb'
KEY_AA_I_B = 'aa_i_b'
KEY_AA_T = 'aa_t'
KEY_AA_FB = 'aa_fb'
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
KEY_INPUT_PY = 'input_py'
KEY_INPUT_AA = 'input_aa'
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

COLOR_ENABLED = 'black'
COLOR_DISABLED = 'grey'
COLOR_TAB_DISABLED = 'gray90'
BUTTON_COLOR = ('white', 'white')
BUTTON_S_SIZE = (24, 24)
BUTTON_M_SIZE = (32, 32)
BUTTON_B_SIZE = (48, 48)
PAD_EXEC_TEXT = ((10, 10), (10, 0))
PAD_TOP = ((5, 5), (20, 0))
PAD_IT_TOP = ((5, 5), (2, 0))
PAD_NO = ((0, 0), (0, 0))
PAD_NO_TOPBOT = ((5, 5), (0, 0))
CONSOLE_PAD = ((0, 0), (10, 20))
CONSOLE_SIZE = (80, 8)
EXEC_TEXT_SIZE = (10, 1)
NO_BORDER = 0
CENTER = 'center'
NO_TEXT = ''
LICENSE_TEXT_SIZE = (105, 675)
LICENSE_COLUMN_SIZE = (950, 500)


DEFAULT_PY = os.path.abspath('../config/autoauditor_venv/bin/python')
DEFAULT_AA = os.path.abspath('../autoauditor/autoauditor.py')
DEFAULT_LF = os.path.abspath('output/msf.log')
DEFAULT_LD = os.path.abspath('output')
DEFAULT_RC = os.path.abspath('../config/rc.example.5vuln.json')
DEFAULT_VPN_CF = os.path.abspath('../config/client.example.ovpn')
DEFAULT_BC_CF = os.path.abspath('../config/network.example.json')
DEFAULT_BC_LF = os.path.abspath('output/blockchain.log')

_RED = '\033[91m'
_YELLOW = '\033[93m'
_BLUE = '\033[94m'
_GREEN = '\033[92m'
_CLEANC = '\033[0m'
_NC = ''


def log(color, string, end='\n', errcode=None):
    level = {
        'normal': '',
        'succg': '{}[+] {}'.format(_GREEN, _CLEANC),
        'succb': '{}[*] {}'.format(_BLUE, _CLEANC),
        'warn': '{}[-] {}'.format(_YELLOW, _CLEANC),
        'error': '{}[!] {}'.format(_RED, _CLEANC)
    }

    print(level.get(color) + string, end=end, flush=True)

    if errcode is not None:
        sys.exit(errcode)


def check_privileges():
    user = pwd.getpwuid(os.geteuid()).pw_name
    groups = [group.gr_name for group in grp.getgrall()
              if user in group.gr_mem]

    if 'docker' not in groups:
        log('error', "User '{}' must belong to 'docker' group to communicate with docker API.".format(
            user), errcode=ENOPERM)


def print_options(exploit, adv=False):
    opt_l = exploit.options
    if not adv:
        opt_l = [opt for opt in opt_l if opt not in exploit.advanced]

    for opt in opt_l:
        sym = ''
        if opt in exploit.required:
            sym = '{}- {}'.format(_YELLOW, _CLEANC)
            if opt in exploit.missing_required:
                sym = '{}* {}'.format(_RED, _CLEANC)

        print("\t{}{}: {}".format(
            sym, opt, exploit[opt] if exploit[opt] is not None else ''))


def correct_type(value):
    if value.isdigit():
        return int(value)
    if value.lower() in ('true', 'false'):
        return bool(strtobool(value))
    return value


def shutdown(vpncont, msfcont):
    client = docker.from_env()

    log('succb', MSSTOP, end='\r')
    if msfcont is not None:
        msfcont.stop()
        log('succg', MSSTOPPED)
    else:
        log('succg', MSNR)

    log('succb', VPNSTOP, end='\r')
    if vpncont is not None:
        vpncont.stop()
        log('succg', VPNSTOPPED)
    else:
        log('succg', VPNNR)

    log('succb', ATNET, end='\r')
    try:
        net = client.networks.get('attacker_network')
    except docker.errors.NotFound:
        log('succg', ATNETNF)
    else:
        try:
            net.remove()
        except docker.errors.APIError:
            log('warn', "Can not remove attacker_network. There are active endpoints.")
        else:
            log('succg', ATNETRM)

    log('succg', 'Exiting autoauditor.', errcode=NOERROR)


def check_file_dir(outf, outd=None):
    dirname = os.path.dirname(outf)
    if dirname:
        try:
            os.makedirs(dirname, exist_ok=True)
        except PermissionError:
            log('error', "Insufficient permission to create file path {}.".format(
                outf), errcode=EACCESS)

    if outd is not None:
        try:
            os.makedirs(outd, exist_ok=True)
        except PermissionError:
            log('error', "Insufficient permission to create directory {}.".format(
                outd), errcode=EACCESS)


if __name__ == '__main__':
    log('error', "Not standalone module. Run again from autoauditor.py.", errcode=EMODNR)
