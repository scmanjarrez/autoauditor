#!/usr/bin/env python3
import PySimpleGUI as sg
import fontawesome as fa

FILEPNG = 'iVBORw0KGgoAAAANSUhEUgAAABgAAAAgCAYAAAAIXrg4AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAACFSURBVEiJ7dC9DkAwGEbhQ8XghlyZwWgzuN4murCUNJTo3+Q7iaGJvE9agBlYgS3wO9LAyEsx4y5wnKcnIGbcB2z2NYoCXiQ3cENKACdSXX4OqXKAp8bSgG4ixwFawDiQtzoBGCzyWsoTfSrlBgIIIIAAAgjwM8AU3F8V0AE9oDKPG2DZAZVbdv9fKQUhAAAAAElFTkSuQmCC'
FOLDERPNG = 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAYCAYAAACbU/80AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABtSURBVEiJ7dYxEoAgDETRLwXntgzn4Gww3kILoLESjKZJZrah2Ue3ABFIQAXOh9lRPJko/gQx8/N7RAOwWq6GeAtYSenwuPUHq0vWgMMaQLAsd4ADHOAABzhgAKphfwlANgRkaLNcaDPp90l2AYuzfIE6Q1SuAAAAAElFTkSuQmCC'
FONT = ('font-awesome/Hack-Regular.ttf', 12)
FONTB = ('font-awesome/Hack-Regular.ttf', 12, 'bold')
PLAY = 'iVBORw0KGgoAAAANSUhEUgAAACoAAAAwCAYAAABnjuimAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAABYgAAAWIBXyfQUwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAK7SURBVFiF1dlPiFVlGMfxz3ub0CxrFUTQopVCBTH33kmyFm7DjYi40qWLbGYCo4QJahUSEeSiRbiISVtYO4dwIQk6Rs09Y0VjMQkTaFSQSPYHS2fO22KQnDvn5p2555x75rs85zm/8+V53gMv5w1g0kbrjWE3HsZl0VEL3rbF7ypAkHgAk3g84/4vOKhuXBDLVVtKDa/KloSH8L7ElGlbytNaTpCYw6Nd1KaiI4IxDVeKFmunhke6rg32YVbiecfdVaDXMoJk1Wvva8GwurO5GnWgF9FbTGC/hkt5CHWilkPGdnyr5XUXrcshL5M8ROFewWuu+UbLczllLiGP0WcxIRrVNJdXYF4dbWe7YEbikAvuyyOwKFG4B6+47jste3sNK2r0WZwWjWiaWc3DRXa0nW2C8xLv+Nz9K324TFG4GyMGzJq2T+z+/WWOPuvtLdGwhi/uVFp2R5cSNfGZaePOe/D/SvsrukhNtEdqVmK002anv6PP5isMa5i8/WIVOtrOkzgjcdzUf1vQKopCwC41M6btWLxQvdG3My94di2IwidVHX07W9eKaLpWRM+thTV6U1r90V8T7DSkVVXRiI+knlB3Agb6LJTFl6JhTeduv1iljl7Fi+Y02yWpRkdTwTHBAYN+7VTUX9GgJfWChqk7lfZL9GfRQXUfdPvftew1ehOHzdusubKfw2V29FOpEUMurObhMkR/FI1pGu8lpEjR66I3/emQbf7uNawo0QkLRjzlh7wC8xb9XjCq7mTOubmJ/iV6ywZveMyNnDKX0KtoxMdSBwy5nIdQJ3oRzdw8FMUA5q1M+IpgzKAjgrQgr2XU6PrLXMC7btik7r0yJVk85DrWRd1ZqYaG/Z52tXCrDILT1tvoFLZm3P9J8LJBH/b70DaAi9b5zUuCPRaPHC+JjvrHYc/4o5+Ct/gXVrq22uLGPS4AAAAASUVORK5CYII='
STOP = 'iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAABbgAAAW4BhFBfJAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAP5SURBVGiBzZrPb1RVFMc/M05xw6JYtTQYBWkphihVEnGLEXVFICQa2duUH5WF0RQSE/4AsJAYF7KDPwOMS1AsbWJCKAhsjS0RaHFj26+L+wba4Z37Y+a+0ZPczZvzvud87znv3nvOnRoZRLAReB/YDWwHXgf6gPWFyiJwH7gL3ASuAj/V4I8c9tsSQZ/gC8E1gdocvwjG5ch2zfFXBGcFjztwvHUsCiYFm6p0vEdwXLCQ0fHW8VhwSvB8bueHBTMVOt46pgXbcjl/sOJZt8YjwYGQf7WA82PAd8BzEVxXgClgGpgB7hTPAHqArcAO4G3g3ZDtQpaBIzX4IUJ3rQjGImdqVnBS8GoC9muCieLdGBujqc4fFCwFQOcFhxUXHctOQ3BUMBewtSTYHws6HJHzfwsG23W8xGav4ELENzEUAlqn+NVmWpk3IMExwbLH5nW578kEmEhcKaogcShA4ivrxU1yO2I7a3ZuEuMeewuCgbKXzgZyvtskLnrsnWlV7pN9tpkXDBZOdo2EYENhu8zW4hpbcqdKy7GxQqdX4ZPnjODFjCR8qXR0taLl2KxWrfNFpLoWCbkD5C3Dzs9NpQHBiqF0ogS0q5EQnDBsrAj6m8uWpbDZAO0aCbljhzXBnyI45w2RDdy1dJKr3MrwJ+u4GrZMrvtAa67G3QP86lEbAX7MEAnLl+E69pnmtxBqDR4AH+OOz5bsBC51GIkbxvMhBPeN8HwYi151Ogk+MjDn6zxtfbTKP7EGupBOli/r656XllMsFOm0Fz+JncDlNkiYNUcd13Qqk+TOQIXfRMN4vlAH/jJ+HE4w8ESKdPoAP4kRXCRiSViFzIM6rvgukzciwZ+RCr6Jt4znt+u4XmWZ7IoANiVzOo0Yz2cRfJZ6lEiRTo8dgaPEJwj6PQoTnRLolITgG88E9zeVrLPGrHxFdBqJ5M1Oru3yu6F7ZTW4r3A4loNAYScpEgG/jrTOjlXQzwl6M5KIjcSgYkvKAnjSA3ghF4EEEr5Gwuky0FBbJVsqJZAoG4/krrRKQb/2vLgsOPQ/IPGlD7BHrn3nIzH+H5KYUmhVFGwrwuQDuijYkJHEYCDnJXio2Iay4IDi2uvjwRnx22nINXSt1aY5lgT7UsFHI8N6S671sTkBe4vcDmttUqvHiuBzCyt0xTQKfE/cJYaAa7grphvAbZ5WUg3cpd2bwDu4a6bYK6bDNTgfoWt6tT/im6hiPExOGw+JIflXp9xjKvqDTSDRkLvorjIazYvudVmdbyEyIPhW7V2GWGNRcEbWDlsRkT65JfCq7HoitLpckbulfKFdP2JWghgyL+Nq4PdwrcotwEus/bvNHHCPtX+3+bNT2/8CfhkCHMpFo58AAAAASUVORK5CYII='
WIZARD = 'iVBORw0KGgoAAAANSUhEUgAAABIAAAAwCAYAAAAcqipqAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAABYgAAAWIBXyfQUwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAFOSURBVEiJ7dexSsNAHMfxb4p2KCgo4qKbtoKroyCC1TfQ+gQ+hIKOIriI+Cw6+AoKuto+gK0uqRFR4eeQBFK9xNw1Q4b84L+E3CeX/C8XAsZoFnQCuge9RXUHOgbNmMf8RdqgV5BS6gW09R+yDvrIQOL6BG2kIZOgbg4krh6oboI6Fkhcu/HoWkLazvkQk9kxQQsO0KIJeneAhibowQF6NBzTCujb4kF/gZopF9CVBXSRMVPVQTc5kOuUNTSCTYCOQL4B8EGH4Tmj8TLABtAGlqIDPeAWPJfuVgmjfdDAYv0EoHMTZIMkazWp1IA5x1uZ/w0VknJCQVHQZRFQFC2D1kAHFu3fTArRduB1I3DKdSrl7FoFVVBpoOhdUxOYBloWY1ugIeCD9wTozHHzT9apF35eaIx5Z4EXiuOnfF0rFBoU4PQh/HXoj9H6Z9DeD1mabwdtWretAAAAAElFTkSuQmCC'
CBOFF = 'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAygAAAMoBawMUsgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABsSURBVEiJ7dahEYNQFETRQ1RaIPGpgxZphYCnjjTycT+CLxgG+XBvZ9beK3fhjQUFNagFM14aPAp87tw12xM/rGIy4IPNwTYGwTVWRX0EQi+TghSkIAUpSAHcPZmFff3vGv2J/Vp8xd+WCf0fuZVmwe+b7gsAAAAASUVORK5CYII='
CBON= 'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAygAAAMoBawMUsgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAEoSURBVEiJ1daxLgRBGMDxH1Hc4QXwChqVRCtatYI3UEiIoLhGo5MrNJKrPIFzGkKCxBN4EQWrW8XuyRq7t3cyV9yXTPN9k/9/dne+nYEl3CJBGmkk6GFRDo8FDkdvKrc18IZXcWINy/hSsLUjweWsFOl0RGhpTISgiSvslhVnIsCvsYFt2YbpxBLMoov1Qq4RTvrvKyqDt3AxrGAFOxW1OVlzFuHHOK1aTdgHq3jPcyfB3Hk8+d2thyXMdqH+R3AeAI4K8OegdlCx6IGCJu4CUAsvQW6/Al4r6EvuA2DZU9UKqj5ygk08BPkUezirEfzEoG3alzwG8JF+inWN9plLOrnochT4MAL4wNao4H5MxN90YIz7yEzITv9xHfpdsqvFjfjXli4WvgFlkbAzkqReWwAAAABJRU5ErkJggg=='

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
KEY_INPUT_LF = 'input_lf'
KEY_INPUT_LD = 'input_ld'
KEY_INPUT_RC = 'input_rc'
KEY_INPUT_VPN_CF = 'input_vpn_cf'
KEY_INPUT_BC_CF = 'input_bc_cf'
KEY_INPUT_BC_LF = 'input_bc_lf'
KEY_START_B = 'start_b'
KEY_STOP_B = 'stop_b'
KEY_WIZARD_B = 'wizard_b'

TEXT_DESCR_SIZE = (30, 1)
COLOR_ENABLED = 'black'
COLOR_DISABLED = 'grey'
COLOR_BUTTON = ('white', 'white')
BUTTON_SIZE = (32, 32)
BUTTON_BORDER = 0

DEFAULT_LF = 'output/msf.log'
DEFAULT_LD = 'output'
DEFAULT_RC = 'rc5.json'
DEFAULT_VPN_CF = 'client.ovpn'
DEFAULT_BC_CF = 'network.template.json'
DEFAULT_BC_LF = 'output/blockchain.log'


sg.theme('Reddit')	# Add a touch of color
# All the stuff inside your window.


def browse(text, key, target, image, image_size, color, border, disabled=False, tooltip=None, filetype=True):
    if filetype:
        bt =  sg.FileBrowse(button_text=text, button_color=color, target=target, key=key, tooltip=tooltip, disabled=disabled)
    else:
        bt =  sg.FolderBrowse(button_text=text, button_color=color, target=target, key=key, tooltip=tooltip, disabled=disabled)
    bt.ImageData = image
    bt.ImageSize = image_size
    bt.BorderWidth = border
    return bt

def input_text(default, key, disabled=False, font=None):
    it = sg.InputText(default, key=key, disabled=disabled, font=font)
    return it

def button(text, key, image, image_size, color, border, tooltip):
    bt = sg.Button(text, key=key, image_size=image_size, button_color=color, border_width=border, image_data=image, tooltip=tooltip)
    return bt

lf_fb = browse('', KEY_LF_FB, KEY_INPUT_LF, FILEPNG, BUTTON_SIZE, COLOR_BUTTON, BUTTON_BORDER, tooltip=TOOLTIP_FILE_BROWSER)
ld_fb = browse('', KEY_LD_FB, KEY_INPUT_LD, FOLDERPNG, BUTTON_SIZE, COLOR_BUTTON, BUTTON_BORDER, tooltip=TOOLTIP_FOLDER_BROWSER, filetype=False)
rc_fb = browse('', KEY_RC_FB, KEY_INPUT_RC, FILEPNG, BUTTON_SIZE, COLOR_BUTTON, BUTTON_BORDER, tooltip=TOOLTIP_FILE_BROWSER)

vpn_cb = sg.Button('', image_data=CBOFF, key=KEY_VPN_CB, button_color=COLOR_BUTTON, border_width=BUTTON_BORDER)
vpn_cb_enabled = False
vpn_cf_it = input_text(DEFAULT_VPN_CF, KEY_INPUT_VPN_CF, True, FONT)
vpn_cf_fb = browse('', KEY_VPN_CF_FB, KEY_INPUT_VPN_CF, FILEPNG, BUTTON_SIZE, COLOR_BUTTON, BUTTON_BORDER, disabled=True, tooltip=TOOLTIP_FILE_BROWSER)

bc_cb = sg.Button('', image_data=CBOFF, key=KEY_BC_CB, button_color=COLOR_BUTTON, border_width=BUTTON_BORDER)
bc_cb_enabled = False
bc_cf_it = input_text(DEFAULT_BC_CF, KEY_INPUT_BC_CF, True, FONT)
bc_cf_fb = browse('', KEY_BC_CF_FB, KEY_INPUT_BC_CF, FILEPNG, BUTTON_SIZE, COLOR_BUTTON, BUTTON_BORDER, disabled=True, tooltip=TOOLTIP_FILE_BROWSER)

bc_lf_it = input_text(DEFAULT_BC_LF, KEY_INPUT_BC_LF, True, FONT)
bc_lf_fb = browse('', KEY_BC_LF_FB, KEY_INPUT_BC_LF, FILEPNG, BUTTON_SIZE, COLOR_BUTTON, BUTTON_BORDER, disabled=True, tooltip=TOOLTIP_FILE_BROWSER)

sc_cb = sg.Button('', image_data=CBON, key=KEY_SC_CB, button_color=COLOR_BUTTON, border_width=BUTTON_BORDER)
sc_cb_enabled = True

layout = [
    [sg.Text('')],
    [sg.Text(TEXT_LF, size=TEXT_DESCR_SIZE, font=FONTB), input_text(DEFAULT_LF, KEY_INPUT_LF, font=FONT), lf_fb],
    [sg.Text(TEXT_LD, size=TEXT_DESCR_SIZE, font=FONTB), input_text(DEFAULT_LD, KEY_INPUT_LD, font=FONT), ld_fb],
    [sg.Text(TEXT_RC, size=TEXT_DESCR_SIZE, font=FONTB), input_text(DEFAULT_RC, KEY_INPUT_RC, font=FONT), rc_fb],
    [sg.Text('')],

    [vpn_cb, sg.Text(TEXT_VPN_CB, text_color=COLOR_DISABLED, font=FONTB, key=KEY_VPN_CB_T, enable_events=True)],
    [sg.Text(TEXT_VPN_CF, size=TEXT_DESCR_SIZE, font=FONTB, text_color=COLOR_DISABLED, key=KEY_VPN_CF_T), vpn_cf_it, vpn_cf_fb],
    [sg.Text('')],

    [bc_cb, sg.Text(TEXT_BC_CB, text_color=COLOR_DISABLED, font=FONTB, key=KEY_BC_CB_T, enable_events=True)],
    [sg.Text(TEXT_BC_CF, size=TEXT_DESCR_SIZE, font=FONTB, text_color=COLOR_DISABLED, key=KEY_BC_CF_T), bc_cf_it, bc_cf_fb],
    [sg.Text(TEXT_BC_LF, size=TEXT_DESCR_SIZE, font=FONTB, text_color=COLOR_DISABLED, key=KEY_BC_LF_T), bc_lf_it, bc_lf_fb],
    [sg.Text('')],

    [sc_cb, sg.Text(TEXT_SC_CB, text_color=COLOR_ENABLED, font=FONTB, key=KEY_SC_CB_T, enable_events=True)],
    [sg.Text('')],
    [sg.Text('')],

    [
        sg.Text('', size=(13, 1)), button('', KEY_START_B, PLAY, (100, 50), COLOR_BUTTON, 0, TOOLTIP_START),
        sg.Text('', size=(17, 1)), button('', KEY_WIZARD_B, WIZARD, (100, 50), COLOR_BUTTON, 0, TOOLTIP_WIZARD),
        sg.Text('', size=(20, 1)), button('', KEY_STOP_B, STOP, (100, 50), COLOR_BUTTON, 0, TOOLTIP_STOP)
    ],
    [
        sg.Text('', size=(8, 1)), sg.Text(TOOLTIP_START, font=FONTB),
        sg.Text('', size=(2, 1)), sg.Text(TOOLTIP_WIZARD, font=FONTB),
        sg.Text('', size=(2, 1)), sg.Text(TOOLTIP_STOP, font=FONTB),
    ],
    [sg.Text('')]
]

def switch(disabled=True, *elems):
    for el in elems:
        el(disabled=disabled)

# Create the Window
window = sg.Window('AutoAuditor', layout)
# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    print(event)
    print(values)
    if event == KEY_VPN_CB or event == KEY_VPN_CB_T:
        if vpn_cb_enabled:
            switch(True, vpn_cf_it, vpn_cf_fb)
            window[KEY_VPN_CF_T](text_color=COLOR_DISABLED)
            window[KEY_VPN_CB](image_data=CBOFF)
            window[KEY_VPN_CB_T](text_color=COLOR_DISABLED)
            vpn_cb_enabled = False
        else:
            switch(False, vpn_cf_it, vpn_cf_fb)
            window[KEY_VPN_CF_T](text_color=COLOR_ENABLED)
            window[KEY_VPN_CB](image_data=CBON)
            window[KEY_VPN_CB_T](text_color=COLOR_ENABLED)
            vpn_cb_enabled = True

    if event == KEY_BC_CB or event == KEY_BC_CB_T:
        if bc_cb_enabled:
            switch(True, bc_cf_it, bc_cf_fb, bc_lf_it, bc_lf_fb)
            window[KEY_BC_CF_T](text_color=COLOR_DISABLED)
            window[KEY_BC_LF_T](text_color=COLOR_DISABLED)
            window[KEY_BC_CB](image_data=CBOFF)
            window[KEY_BC_CB_T](text_color=COLOR_DISABLED)
            bc_cb_enabled = False
        else:
            switch(False, bc_cf_it, bc_cf_fb, bc_lf_it, bc_lf_fb)
            window[KEY_BC_CF_T](text_color=COLOR_ENABLED)
            window[KEY_BC_LF_T](text_color=COLOR_ENABLED)
            window[KEY_BC_CB](image_data=CBON)
            window[KEY_BC_CB_T](text_color=COLOR_ENABLED)
            bc_cb_enabled = True

    if event == KEY_SC_CB or event == KEY_SC_CB_T:
        if sc_cb_enabled:
            window[KEY_SC_CB_T](text_color=COLOR_DISABLED)
            window[KEY_SC_CB](image_data=CBOFF)
            window[KEY_SC_CB_T](text_color=COLOR_DISABLED)
            sc_cb_enabled = False
        else:
            window[KEY_SC_CB_T](text_color=COLOR_ENABLED)
            window[KEY_SC_CB](image_data=CBON)
            window[KEY_SC_CB_T](text_color=COLOR_ENABLED)
            sc_cb_enabled = True

    if event == sg.WIN_CLOSED:	# if user closes window or clicks cancel
        break

window.close()
