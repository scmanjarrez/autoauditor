from distutils.util import strtobool
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

FILEPNG = 'iVBORw0KGgoAAAANSUhEUgAAABgAAAAgCAYAAAAIXrg4AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAACFSURBVEiJ7dC9DkAwGEbhQ8XghlyZwWgzuN4murCUNJTo3+Q7iaGJvE9agBlYgS3wO9LAyEsx4y5wnKcnIGbcB2z2NYoCXiQ3cENKACdSXX4OqXKAp8bSgG4ixwFawDiQtzoBGCzyWsoTfSrlBgIIIIAAAgjwM8AU3F8V0AE9oDKPG2DZAZVbdv9fKQUhAAAAAElFTkSuQmCC'
FOLDERPNG = 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAYCAYAAACbU/80AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABtSURBVEiJ7dYxEoAgDETRLwXntgzn4Gww3kILoLESjKZJZrah2Ue3ABFIQAXOh9lRPJko/gQx8/N7RAOwWq6GeAtYSenwuPUHq0vWgMMaQLAsd4ADHOAABzhgAKphfwlANgRkaLNcaDPp90l2AYuzfIE6Q1SuAAAAAElFTkSuQmCC'
FONT = ('font-awesome/Hack-Regular.ttf', 12)
FONTB = ('font-awesome/Hack-Regular.ttf', 12, 'bold')
PLAY = 'iVBORw0KGgoAAAANSUhEUgAAACoAAAAwCAYAAABnjuimAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAABYgAAAWIBXyfQUwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAK7SURBVFiF1dlPiFVlGMfxz3ub0CxrFUTQopVCBTH33kmyFm7DjYi40qWLbGYCo4QJahUSEeSiRbiISVtYO4dwIQk6Rs09Y0VjMQkTaFSQSPYHS2fO22KQnDvn5p2555x75rs85zm/8+V53gMv5w1g0kbrjWE3HsZl0VEL3rbF7ypAkHgAk3g84/4vOKhuXBDLVVtKDa/KloSH8L7ElGlbytNaTpCYw6Nd1KaiI4IxDVeKFmunhke6rg32YVbiecfdVaDXMoJk1Wvva8GwurO5GnWgF9FbTGC/hkt5CHWilkPGdnyr5XUXrcshL5M8ROFewWuu+UbLczllLiGP0WcxIRrVNJdXYF4dbWe7YEbikAvuyyOwKFG4B6+47jste3sNK2r0WZwWjWiaWc3DRXa0nW2C8xLv+Nz9K324TFG4GyMGzJq2T+z+/WWOPuvtLdGwhi/uVFp2R5cSNfGZaePOe/D/SvsrukhNtEdqVmK002anv6PP5isMa5i8/WIVOtrOkzgjcdzUf1vQKopCwC41M6btWLxQvdG3My94di2IwidVHX07W9eKaLpWRM+thTV6U1r90V8T7DSkVVXRiI+knlB3Agb6LJTFl6JhTeduv1iljl7Fi+Y02yWpRkdTwTHBAYN+7VTUX9GgJfWChqk7lfZL9GfRQXUfdPvftew1ehOHzdusubKfw2V29FOpEUMurObhMkR/FI1pGu8lpEjR66I3/emQbf7uNawo0QkLRjzlh7wC8xb9XjCq7mTOubmJ/iV6ywZveMyNnDKX0KtoxMdSBwy5nIdQJ3oRzdw8FMUA5q1M+IpgzKAjgrQgr2XU6PrLXMC7btik7r0yJVk85DrWRd1ZqYaG/Z52tXCrDILT1tvoFLZm3P9J8LJBH/b70DaAi9b5zUuCPRaPHC+JjvrHYc/4o5+Ct/gXVrq22uLGPS4AAAAASUVORK5CYII='
STOP = 'iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAABbgAAAW4BhFBfJAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAP5SURBVGiBzZrPb1RVFMc/M05xw6JYtTQYBWkphihVEnGLEXVFICQa2duUH5WF0RQSE/4AsJAYF7KDPwOMS1AsbWJCKAhsjS0RaHFj26+L+wba4Z37Y+a+0ZPczZvzvud87znv3nvOnRoZRLAReB/YDWwHXgf6gPWFyiJwH7gL3ASuAj/V4I8c9tsSQZ/gC8E1gdocvwjG5ch2zfFXBGcFjztwvHUsCiYFm6p0vEdwXLCQ0fHW8VhwSvB8bueHBTMVOt46pgXbcjl/sOJZt8YjwYGQf7WA82PAd8BzEVxXgClgGpgB7hTPAHqArcAO4G3g3ZDtQpaBIzX4IUJ3rQjGImdqVnBS8GoC9muCieLdGBujqc4fFCwFQOcFhxUXHctOQ3BUMBewtSTYHws6HJHzfwsG23W8xGav4ELENzEUAlqn+NVmWpk3IMExwbLH5nW578kEmEhcKaogcShA4ivrxU1yO2I7a3ZuEuMeewuCgbKXzgZyvtskLnrsnWlV7pN9tpkXDBZOdo2EYENhu8zW4hpbcqdKy7GxQqdX4ZPnjODFjCR8qXR0taLl2KxWrfNFpLoWCbkD5C3Dzs9NpQHBiqF0ogS0q5EQnDBsrAj6m8uWpbDZAO0aCbljhzXBnyI45w2RDdy1dJKr3MrwJ+u4GrZMrvtAa67G3QP86lEbAX7MEAnLl+E69pnmtxBqDR4AH+OOz5bsBC51GIkbxvMhBPeN8HwYi151Ogk+MjDn6zxtfbTKP7EGupBOli/r656XllMsFOm0Fz+JncDlNkiYNUcd13Qqk+TOQIXfRMN4vlAH/jJ+HE4w8ESKdPoAP4kRXCRiSViFzIM6rvgukzciwZ+RCr6Jt4znt+u4XmWZ7IoANiVzOo0Yz2cRfJZ6lEiRTo8dgaPEJwj6PQoTnRLolITgG88E9zeVrLPGrHxFdBqJ5M1Oru3yu6F7ZTW4r3A4loNAYScpEgG/jrTOjlXQzwl6M5KIjcSgYkvKAnjSA3ghF4EEEr5Gwuky0FBbJVsqJZAoG4/krrRKQb/2vLgsOPQ/IPGlD7BHrn3nIzH+H5KYUmhVFGwrwuQDuijYkJHEYCDnJXio2Iay4IDi2uvjwRnx22nINXSt1aY5lgT7UsFHI8N6S671sTkBe4vcDmttUqvHiuBzCyt0xTQKfE/cJYaAa7grphvAbZ5WUg3cpd2bwDu4a6bYK6bDNTgfoWt6tT/im6hiPExOGw+JIflXp9xjKvqDTSDRkLvorjIazYvudVmdbyEyIPhW7V2GWGNRcEbWDlsRkT65JfCq7HoitLpckbulfKFdP2JWghgyL+Nq4PdwrcotwEus/bvNHHCPtX+3+bNT2/8CfhkCHMpFo58AAAAASUVORK5CYII='
WIZARD = 'iVBORw0KGgoAAAANSUhEUgAAABIAAAAwCAYAAAAcqipqAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAABYgAAAWIBXyfQUwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAFOSURBVEiJ7dexSsNAHMfxb4p2KCgo4qKbtoKroyCC1TfQ+gQ+hIKOIriI+Cw6+AoKuto+gK0uqRFR4eeQBFK9xNw1Q4b84L+E3CeX/C8XAsZoFnQCuge9RXUHOgbNmMf8RdqgV5BS6gW09R+yDvrIQOL6BG2kIZOgbg4krh6oboI6Fkhcu/HoWkLazvkQk9kxQQsO0KIJeneAhibowQF6NBzTCujb4kF/gZopF9CVBXSRMVPVQTc5kOuUNTSCTYCOQL4B8EGH4Tmj8TLABtAGlqIDPeAWPJfuVgmjfdDAYv0EoHMTZIMkazWp1IA5x1uZ/w0VknJCQVHQZRFQFC2D1kAHFu3fTArRduB1I3DKdSrl7FoFVVBpoOhdUxOYBloWY1ugIeCD9wTozHHzT9apF35eaIx5Z4EXiuOnfF0rFBoU4PQh/HXoj9H6Z9DeD1mabwdtWretAAAAAElFTkSuQmCC'
CBOFF = 'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAygAAAMoBawMUsgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABsSURBVEiJ7dahEYNQFETRQ1RaIPGpgxZphYCnjjTycT+CLxgG+XBvZ9beK3fhjQUFNagFM14aPAp87tw12xM/rGIy4IPNwTYGwTVWRX0EQi+TghSkIAUpSAHcPZmFff3vGv2J/Vp8xd+WCf0fuZVmwe+b7gsAAAAASUVORK5CYII='
CBON= 'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAygAAAMoBawMUsgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAEoSURBVEiJ1daxLgRBGMDxH1Hc4QXwChqVRCtatYI3UEiIoLhGo5MrNJKrPIFzGkKCxBN4EQWrW8XuyRq7t3cyV9yXTPN9k/9/dne+nYEl3CJBGmkk6GFRDo8FDkdvKrc18IZXcWINy/hSsLUjweWsFOl0RGhpTISgiSvslhVnIsCvsYFt2YbpxBLMoov1Qq4RTvrvKyqDt3AxrGAFOxW1OVlzFuHHOK1aTdgHq3jPcyfB3Hk8+d2thyXMdqH+R3AeAI4K8OegdlCx6IGCJu4CUAsvQW6/Al4r6EvuA2DZU9UKqj5ygk08BPkUezirEfzEoG3alzwG8JF+inWN9plLOrnochT4MAL4wNao4H5MxN90YIz7yEzITv9xHfpdsqvFjfjXli4WvgFlkbAzkqReWwAAAABJRU5ErkJggg=='

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
TOOLTIP_FILE_BROWSER = 'File Browser'
TOOLTIP_FOLDER_BROWSER = 'Folder Browser'
TOOLTIP_START = 'Run AutoAuditor'
TOOLTIP_STOP = 'Stop Orphan Containers'
TOOLTIP_WIZARD = 'Start AutoAuditor Wizard'

KEY_PY_T = 'py_t'
KEY_PY_FB = 'py_fb'
KEY_AA_T = 'aa_t'
KEY_AA_FB = 'aa_fb'
KEY_LF_T = 'lf_t'
KEY_LF_FB = 'lf_fb'
KEY_LD_T = 'ld_t'
KEY_LD_FB = 'ld_fb'
KEY_RC_T = 'rc_t'
KEY_RC_FB = 'rc_fb'
KEY_VPN_CB = 'vpn_cb'
KEY_VPN_CB_T = 'vpn_cb_t'
KEY_VPN_CF_T = 'vpn_cf_t'
KEY_VPN_CF_FB = 'vpn_cf_fb'
KEY_BC_CB = 'bc_cb'
KEY_BC_CB_T = 'bc_cb_t'
KEY_BC_CF_T = 'bc_cf_t'
KEY_BC_CF_FB = 'bc_cf_fb'
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

TEXT_DESCR_SIZE = (30, 1)
COLOR_ENABLED = 'black'
COLOR_DISABLED = 'grey'
BUTTON_COLOR = ('white', 'white')
BUTTON_SIZE = (32, 32)
BUTTON_BORDER = 0
BUTTON_EXEC_SIZE = (48, 48)

DEFAULT_PY = os.path.abspath('autoauditor_venv/bin/python')
DEFAULT_AA = os.path.abspath('../autoauditor/autoauditor.py')
DEFAULT_LF = os.path.abspath('output/msf.log')
DEFAULT_LD = os.path.abspath('output')
DEFAULT_RC = os.path.abspath('rc2.json')
DEFAULT_VPN_CF = os.path.abspath('client.ovpn')
DEFAULT_BC_CF = os.path.abspath('network.template.json')
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
        'succg' : '{}[+] {}'.format(_GREEN, _CLEANC),
        'succb' : '{}[*] {}'.format(_BLUE, _CLEANC),
        'warn'  : '{}[-] {}'.format(_YELLOW, _CLEANC),
        'error' : '{}[!] {}'.format(_RED, _CLEANC)
    }

    print(level.get(color) + string, end=end, flush=True)

    if errcode is not None:
        sys.exit(errcode)

def check_privileges():
    user = pwd.getpwuid(os.geteuid()).pw_name
    groups = [group.gr_name for group in grp.getgrall() if user in group.gr_mem]

    if 'docker' not in groups:
        log('error', "User '{}' must belong to 'docker' group to communicate with docker API.".format(user), errcode=ENOPERM)

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

        print("\t{}{}: {}".format(sym, opt, exploit[opt] if exploit[opt] is not None else ''))

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
        net.remove()
        log('succg', ATNETRM)

    log('succg', 'Exiting autoauditor.', errcode=NOERROR)

def check_file_dir(outf, outd=None):
    try:
        os.makedirs(os.path.dirname(outf), exist_ok=True)
    except PermissionError:
        log('error', "Insufficient permission to create file path {}.".format(outf), errcode=EACCESS)

    if outd is not None:
        try:
            os.makedirs(outd, exist_ok=True)
        except PermissionError:
            log('error', "Insufficient permission to create directory {}.".format(outd), errcode=EACCESS)

if __name__ == '__main__':
    log('error', "Helper module. Not runnable.", errcode=EMODNR)
