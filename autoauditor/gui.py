#!/usr/bin/env python3
import PySimpleGUI as sg
import subprocess
import sys
from utils import *

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

class ImageCheckBox(sg.Button):
    def __init__(self, image_on, image_off, key, button_color, border_width, enabled):
        self.enabled = enabled
        self.image_on = image_on
        self.image_off = image_off
        super().__init__(image_data=image_on if enabled else image_off, key=key, button_color=button_color, border_width=border_width)

    @property
    def enabled(self):
        return self.__enabled

    @enabled.setter
    def enabled(self, enabled):
        self.__enabled = enabled

    def switch(self):
        if self.enabled:
            self(image_data=self.image_off)
            self.enabled = False
        else:
            self(image_data=self.image_on)
            self.enabled = True

py_fb = browse('', KEY_PY_FB, KEY_INPUT_PY, FILEPNG, BUTTON_SIZE, BUTTON_COLOR, BUTTON_BORDER, tooltip=TOOLTIP_FILE_BROWSER)
aa_fb = browse('', KEY_AA_FB, KEY_INPUT_AA, FILEPNG, BUTTON_SIZE, BUTTON_COLOR, BUTTON_BORDER, tooltip=TOOLTIP_FILE_BROWSER)
lf_fb = browse('', KEY_LF_FB, KEY_INPUT_LF, FILEPNG, BUTTON_SIZE, BUTTON_COLOR, BUTTON_BORDER, tooltip=TOOLTIP_FILE_BROWSER)
ld_fb = browse('', KEY_LD_FB, KEY_INPUT_LD, FOLDERPNG, BUTTON_SIZE, BUTTON_COLOR, BUTTON_BORDER, tooltip=TOOLTIP_FOLDER_BROWSER, filetype=False)
rc_fb = browse('', KEY_RC_FB, KEY_INPUT_RC, FILEPNG, BUTTON_SIZE, BUTTON_COLOR, BUTTON_BORDER, tooltip=TOOLTIP_FILE_BROWSER)

vpn_cb = ImageCheckBox(image_on=CBON, image_off=CBOFF, key=KEY_VPN_CB, button_color=BUTTON_COLOR, border_width=BUTTON_BORDER, enabled=False)
vpn_cf_it = input_text(DEFAULT_VPN_CF, KEY_INPUT_VPN_CF, True, FONT)
vpn_cf_fb = browse('', KEY_VPN_CF_FB, KEY_INPUT_VPN_CF, FILEPNG, BUTTON_SIZE, BUTTON_COLOR, BUTTON_BORDER, disabled=True, tooltip=TOOLTIP_FILE_BROWSER)

bc_cb = ImageCheckBox(image_on=CBON, image_off=CBOFF, key=KEY_BC_CB, button_color=BUTTON_COLOR, border_width=BUTTON_BORDER, enabled=False)
bc_cf_it = input_text(DEFAULT_BC_CF, KEY_INPUT_BC_CF, True, FONT)
bc_cf_fb = browse('', KEY_BC_CF_FB, KEY_INPUT_BC_CF, FILEPNG, BUTTON_SIZE, BUTTON_COLOR, BUTTON_BORDER, disabled=True, tooltip=TOOLTIP_FILE_BROWSER)

bc_lf_it = input_text(DEFAULT_BC_LF, KEY_INPUT_BC_LF, True, FONT)
bc_lf_fb = browse('', KEY_BC_LF_FB, KEY_INPUT_BC_LF, FILEPNG, BUTTON_SIZE, BUTTON_COLOR, BUTTON_BORDER, disabled=True, tooltip=TOOLTIP_FILE_BROWSER)

sc_cb = ImageCheckBox(image_on=CBON, image_off=CBOFF, key=KEY_SC_CB, button_color=BUTTON_COLOR, border_width=BUTTON_BORDER, enabled=True)

console = sg.Multiline('', key=KEY_CONSOLE, size=(79, 8), pad=(20, 30), visible=False, font=FONT, autoscroll=True)

layout = [
    [sg.Text('')],
    [sg.Text(TEXT_PY, key=KEY_PY_T, size=TEXT_DESCR_SIZE, font=FONTB), input_text(DEFAULT_PY, KEY_INPUT_PY, font=FONT), py_fb],
    [sg.Text(TEXT_AA, key=KEY_AA_T, size=TEXT_DESCR_SIZE, font=FONTB), input_text(DEFAULT_AA, KEY_INPUT_AA, font=FONT), aa_fb],
    [sg.Text('')],
    [sg.Text(TEXT_LF, key=KEY_LF_T, size=TEXT_DESCR_SIZE, font=FONTB), input_text(DEFAULT_LF, KEY_INPUT_LF, font=FONT), lf_fb],
    [sg.Text(TEXT_LD, key=KEY_LD_T, size=TEXT_DESCR_SIZE, font=FONTB), input_text(DEFAULT_LD, KEY_INPUT_LD, font=FONT), ld_fb],
    [sg.Text(TEXT_RC, key=KEY_RC_T, size=TEXT_DESCR_SIZE, font=FONTB), input_text(DEFAULT_RC, KEY_INPUT_RC, font=FONT), rc_fb],
    [sg.Text('')],

    [vpn_cb, sg.Text(TEXT_VPN_CB, key=KEY_VPN_CB_T, text_color=COLOR_DISABLED, font=FONTB, enable_events=True)],
    [sg.Text(TEXT_VPN_CF, key=KEY_VPN_CF_T, size=TEXT_DESCR_SIZE, font=FONTB, text_color=COLOR_DISABLED), vpn_cf_it, vpn_cf_fb],
    [sg.Text('')],

    [bc_cb, sg.Text(TEXT_BC_CB, key=KEY_BC_CB_T, text_color=COLOR_DISABLED, font=FONTB, enable_events=True)],
    [sg.Text(TEXT_BC_CF, key=KEY_BC_CF_T, size=TEXT_DESCR_SIZE, font=FONTB, text_color=COLOR_DISABLED), bc_cf_it, bc_cf_fb],
    [sg.Text(TEXT_BC_LF, key=KEY_BC_LF_T, size=TEXT_DESCR_SIZE, font=FONTB, text_color=COLOR_DISABLED), bc_lf_it, bc_lf_fb],
    [sg.Text('')],

    [sc_cb, sg.Text(TEXT_SC_CB, key=KEY_SC_CB_T, text_color=COLOR_ENABLED, font=FONTB,  enable_events=True)],
    [sg.Text('')],

    [
        sg.Text('', size=(14, 1), pad=(5, 0)), button('', KEY_START_B, PLAY, BUTTON_EXEC_SIZE, BUTTON_COLOR, 0, TOOLTIP_START),
        sg.Text('', size=(26, 1), pad=(0, 0)), button('', KEY_WIZARD_B, WIZARD, BUTTON_EXEC_SIZE, BUTTON_COLOR, 0, TOOLTIP_WIZARD),
        sg.Text('', size=(28, 1), pad=(3, 0)), button('', KEY_STOP_B, STOP, BUTTON_EXEC_SIZE, BUTTON_COLOR, 0, TOOLTIP_STOP)
    ],
    [
        sg.Text('', size=(2, 1)),
        sg.Text('', size=(4, 1), pad=(0, 0)), sg.Text(TOOLTIP_START, key=KEY_START_T, font=FONTB),
        sg.Text('', size=(4, 1), pad=(5, 0)), sg.Text(TOOLTIP_WIZARD, key=KEY_WIZARD_T, font=FONTB),
        sg.Text('', size=(4, 1), pad=(0, 0)), sg.Text(TOOLTIP_STOP, key=KEY_STOP_T, font=FONTB),
        sg.Text('', size=(4, 1), pad=(0, 0))
    ],
    [console]
]

def switch(button, *elems):
    for el in elems:
        if isinstance(el, sg.InputText) or isinstance(el, sg.Button):
            el(disabled=button.enabled)
        if isinstance(el, str):
            window[el](text_color=COLOR_DISABLED if button.enabled else COLOR_ENABLED)
    button.switch()

def run_command(console, cmd, timeout=None, window=None):
    nop = None
    """ run shell command
    @param cmd: command to execute
    @param timeout: timeout for command execution
    @param window: the PySimpleGUI window that the output is going to (needed to do refresh on)
    @return: (return code from command, command output)
    """
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = ''
    for line in p.stdout:
        line = line.decode(errors='replace' if (sys.version_info) < (3, 5) else 'backslashreplace').replace('\r', '\n').rstrip()
        output += line
        print(line)
        console.print(line)
        window.refresh() if window else nop        # yes, a 1-line if, so shoot me

    retval = p.wait(timeout)
    return (retval, output)

# Create the Window
window = sg.Window('AutoAuditor', layout)
# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event == KEY_VPN_CB or event == KEY_VPN_CB_T:
        switch(vpn_cb, vpn_cf_it, vpn_cf_fb,KEY_VPN_CF_T, KEY_VPN_CB_T)

    if event == KEY_BC_CB or event == KEY_BC_CB_T:
        switch(bc_cb, bc_cf_it, bc_cf_fb, bc_lf_it, bc_lf_fb, KEY_BC_CF_T, KEY_BC_LF_T, KEY_BC_CB_T)

    if event == KEY_SC_CB or event == KEY_SC_CB_T:
        switch(sc_cb, KEY_SC_CB_T, KEY_SC_CB_T)

    if event == KEY_START_B:
        cmd = [
            window[KEY_INPUT_PY].Get(),
            window[KEY_INPUT_AA].Get(),
            '-r', window[KEY_INPUT_RC].Get(),
            '-o', window[KEY_INPUT_LF].Get(),
            '-d', window[KEY_INPUT_LD].Get(),
            '--no-color'
        ]
        if vpn_cb.enabled:
            cmd.extend(
                [
                    '-v', window[KEY_INPUT_VPN_CF].Get()
                ]
            )
        if bc_cb.enabled:
            cmd.extend(
                [
                    '-hc', window[KEY_INPUT_BC_CF].Get(),
                    '-ho', window[KEY_INPUT_BC_LF].Get()
                ]
            )
        if not sc_cb.enabled:
            cmd.extend(
                [
                    '-b'
                ]
            )
        console(visible=True)
        run_command(console, cmd=" ".join(cmd), window=window)

    if event == KEY_STOP_B:
        cmd = [
            window[KEY_INPUT_PY].Get(),
            window[KEY_INPUT_AA].Get(),
            '-s',
            '--no-color'
        ]
        if vpn_cb.enabled:
            cmd.extend(
                [
                    '-v', window[KEY_INPUT_VPN_CF].Get()
                ]
            )
        console(visible=True)
        run_command(console, cmd=" ".join(cmd), window=window)
    if event == sg.WIN_CLOSED:  # if user closes window or clicks cancel
        break

window.close()
