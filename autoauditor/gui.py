#!/usr/bin/env python3
import PySimpleGUI as sg
import subprocess
import sys
from utils import *

sg.theme('Reddit')	# Add a touch of color
# All the stuff inside your window.

def browse(text, key, target, image, image_size, color, border, disabled=False, tooltip=None, filetype=True, pad=None):
    if filetype:
        bt =  sg.FileBrowse(button_text=text, button_color=color, target=target, key=key, tooltip=tooltip, disabled=disabled, pad=None)
    else:
        bt =  sg.FolderBrowse(button_text=text, button_color=color, target=target, key=key, tooltip=tooltip, disabled=disabled, pad=None)
    bt.ImageData = image
    bt.ImageSize = image_size
    bt.BorderWidth = border
    return bt

def input_text(default, key, disabled=False, font=None, pad=None):
    it = sg.InputText(default, key=key, disabled=disabled, font=font, pad=pad)
    return it

def button(text, key, image, image_size, color, border, tooltip, pad=None, disabled=False):
    bt = sg.Button(text, key=key, image_size=image_size, button_color=color, border_width=border, image_data=image, tooltip=tooltip, pad=pad, disabled=disabled)
    return bt

class ImageCheckBox(sg.Button):
    def __init__(self, image_on, image_off, image_size, key, button_color, border_width, enabled, pad=None):
        self.enabled = enabled
        self.image_on = image_on
        self.image_off = image_off
        super().__init__(image_data=image_on if enabled else image_off, image_size=image_size, key=key, button_color=button_color, border_width=border_width, pad=pad)

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

def switch(button, *elems):
    for el in elems:
        if isinstance(el, sg.InputText) or isinstance(el, sg.Button):
            el(disabled=button.enabled)
        if isinstance(el, str):
            window[el](text_color=COLOR_DISABLED if button.enabled else COLOR_ENABLED)
    button.switch()

def run_command(console, cmd, timeout=None, window=None):
    nop = None
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in p.stdout:
        line = line.decode(errors='replace' if (sys.version_info) < (3, 5) else 'backslashreplace').replace('\r', '\n').rstrip()
        console.print(line)
        window.refresh() if window else nop        # yes, a 1-line if, so shoot me
    exitcode = p.wait(timeout)
    return exitcode

py_fb = browse(NO_TEXT, KEY_PY_FB, KEY_INPUT_PY, FILEPNG, BUTTON_M_SIZE, BUTTON_COLOR, NO_BORDER, tooltip=TOOLTIP_FILE_BROWSER, pad=PAD_NO_TOPBOT)
py_i_b = button(NO_TEXT, KEY_PY_I_B, INFO, BUTTON_S_SIZE, BUTTON_COLOR, NO_BORDER, TOOLTIP_PY)
aa_fb = browse(NO_TEXT, KEY_AA_FB, KEY_INPUT_AA, FILEPNG, BUTTON_M_SIZE, BUTTON_COLOR, NO_BORDER, tooltip=TOOLTIP_FILE_BROWSER, pad=PAD_NO_TOPBOT)
aa_i_b = button(NO_TEXT, KEY_AA_I_B, INFO, BUTTON_S_SIZE, BUTTON_COLOR, NO_BORDER, TOOLTIP_AA)
lf_fb = browse(NO_TEXT, KEY_LF_FB, KEY_INPUT_LF, FILEPNG, BUTTON_M_SIZE, BUTTON_COLOR, NO_BORDER, tooltip=TOOLTIP_FILE_BROWSER, pad=PAD_NO_TOPBOT)
lf_i_b = button(NO_TEXT, KEY_LF_I_B, INFO, BUTTON_S_SIZE, BUTTON_COLOR, NO_BORDER, TOOLTIP_LF)
ld_fb = browse(NO_TEXT, KEY_LD_FB, KEY_INPUT_LD, FOLDERPNG, BUTTON_M_SIZE, BUTTON_COLOR, NO_BORDER, tooltip=TOOLTIP_FOLDER_BROWSER, filetype=False, pad=PAD_NO_TOPBOT)
ld_i_b = button(NO_TEXT, KEY_LD_I_B, INFO, BUTTON_S_SIZE, BUTTON_COLOR, NO_BORDER, TOOLTIP_LD)
rc_fb = browse(NO_TEXT, KEY_RC_FB, KEY_INPUT_RC, FILEPNG, BUTTON_M_SIZE, BUTTON_COLOR, NO_BORDER, tooltip=TOOLTIP_FILE_BROWSER, pad=PAD_NO_TOPBOT)
rc_i_b = button(NO_TEXT, KEY_RC_I_B, INFO, BUTTON_S_SIZE, BUTTON_COLOR, NO_BORDER, TOOLTIP_RC)

vpn_cb = ImageCheckBox(image_on=CBON, image_off=CBOFF, image_size=BUTTON_S_SIZE, key=KEY_VPN_CB, button_color=BUTTON_COLOR, border_width=NO_BORDER, enabled=False)
vpn_cf_i_b = button(NO_TEXT, KEY_VPN_CF_I_B, INFO, BUTTON_S_SIZE, BUTTON_COLOR, NO_BORDER, TOOLTIP_VPN_CF, disabled=True)
vpn_cf_it = input_text(DEFAULT_VPN_CF, KEY_INPUT_VPN_CF, disabled=True, font=FONT, pad=PAD_IT_TOP)
vpn_cf_fb = browse(NO_TEXT, KEY_VPN_CF_FB, KEY_INPUT_VPN_CF, FILEPNG, BUTTON_M_SIZE, BUTTON_COLOR, NO_BORDER, disabled=True, tooltip=TOOLTIP_FILE_BROWSER, pad=PAD_NO_TOPBOT)

bc_cb = ImageCheckBox(image_on=CBON, image_off=CBOFF, image_size=BUTTON_S_SIZE, key=KEY_BC_CB, button_color=BUTTON_COLOR, border_width=NO_BORDER, enabled=False)
bc_cf_i_b = button(NO_TEXT, KEY_BC_CF_I_B, INFO, BUTTON_S_SIZE, BUTTON_COLOR, NO_BORDER, TOOLTIP_BC_CF, disabled=True)
bc_cf_it = input_text(DEFAULT_BC_CF, KEY_INPUT_BC_CF, disabled=True, font=FONT, pad=PAD_IT_TOP)
bc_cf_fb = browse(NO_TEXT, KEY_BC_CF_FB, KEY_INPUT_BC_CF, FILEPNG, BUTTON_M_SIZE, BUTTON_COLOR, NO_BORDER, disabled=True, tooltip=TOOLTIP_FILE_BROWSER, pad=PAD_NO_TOPBOT)
bc_lf_i_b = button(NO_TEXT, KEY_BC_LF_I_B, INFO, BUTTON_S_SIZE, BUTTON_COLOR, NO_BORDER, TOOLTIP_BC_LF, disabled=True)
bc_lf_it = input_text(DEFAULT_BC_LF, KEY_INPUT_BC_LF, disabled=True, font=FONT, pad=PAD_IT_TOP)
bc_lf_fb = browse(NO_TEXT, KEY_BC_LF_FB, KEY_INPUT_BC_LF, FILEPNG, BUTTON_M_SIZE, BUTTON_COLOR, NO_BORDER, disabled=True, tooltip=TOOLTIP_FILE_BROWSER, pad=PAD_NO_TOPBOT)

sc_cb = ImageCheckBox(image_on=CBON, image_off=CBOFF, image_size=BUTTON_S_SIZE, key=KEY_SC_CB, button_color=BUTTON_COLOR, border_width=NO_BORDER, enabled=True)

console = sg.Multiline(NO_TEXT, key=KEY_CONSOLE, size=CONSOLE_SIZE, pad=CONSOLE_PAD, visible=False, font=FONT, autoscroll=True)

mandatory_layout = [
    [sg.Text(TEXT_PY, key=KEY_PY_T, size=TEXT_DESCR_SIZE, font=FONTB), py_i_b, input_text(DEFAULT_PY, KEY_INPUT_PY, font=FONT, pad=PAD_IT_TOP), py_fb],
    [sg.Text(TEXT_AA, key=KEY_AA_T, size=TEXT_DESCR_SIZE, font=FONTB), aa_i_b, input_text(DEFAULT_AA, KEY_INPUT_AA, font=FONT, pad=PAD_IT_TOP), aa_fb],
    [sg.Text(NO_TEXT, pad=PAD_NO_TOPBOT)],
    [sg.Text(TEXT_LF, key=KEY_LF_T, size=TEXT_DESCR_SIZE, font=FONTB), lf_i_b, input_text(DEFAULT_LF, KEY_INPUT_LF, font=FONT, pad=PAD_IT_TOP), lf_fb],
    [sg.Text(TEXT_LD, key=KEY_LD_T, size=TEXT_DESCR_SIZE, font=FONTB), ld_i_b, input_text(DEFAULT_LD, KEY_INPUT_LD, font=FONT, pad=PAD_IT_TOP), ld_fb],
    [sg.Text(TEXT_RC, key=KEY_RC_T, size=TEXT_DESCR_SIZE, font=FONTB), rc_i_b, input_text(DEFAULT_RC, KEY_INPUT_RC, font=FONT, pad=PAD_IT_TOP), rc_fb],
    [sg.Text(NO_TEXT, pad=PAD_NO_TOPBOT)]
]

vpn_layout = [
    [vpn_cb, sg.Text(TEXT_VPN_CB, key=KEY_VPN_CB_T, text_color=COLOR_DISABLED, font=FONTB, enable_events=True)],
    [sg.Text(TEXT_VPN_CF, key=KEY_VPN_CF_T, size=TEXT_DESCR_SIZE, font=FONTB, text_color=COLOR_DISABLED), vpn_cf_i_b, vpn_cf_it, vpn_cf_fb],
    [sg.Text(NO_TEXT, pad=PAD_NO_TOPBOT)]
]

blockchain_layout = [
    [bc_cb, sg.Text(TEXT_BC_CB, key=KEY_BC_CB_T, text_color=COLOR_DISABLED, font=FONTB, enable_events=True)],
    [sg.Text(TEXT_BC_CF, key=KEY_BC_CF_T, size=TEXT_DESCR_SIZE, font=FONTB, text_color=COLOR_DISABLED), bc_cf_i_b, bc_cf_it, bc_cf_fb],
    [sg.Text(TEXT_BC_LF, key=KEY_BC_LF_T, size=TEXT_DESCR_SIZE, font=FONTB, text_color=COLOR_DISABLED), bc_lf_i_b, bc_lf_it, bc_lf_fb],
    [sg.Text(NO_TEXT, pad=PAD_NO_TOPBOT)],

    [sc_cb, sg.Text(TEXT_SC_CB, key=KEY_SC_CB_T, text_color=COLOR_ENABLED, font=FONTB,  enable_events=True)]
]

button_layout = [
    [
        button(NO_TEXT, KEY_WIZARD_B, WIZARD, BUTTON_B_SIZE, BUTTON_COLOR, NO_BORDER, TOOLTIP_WIZARD, PAD_TOP),
        sg.Text(NO_TEXT, size=EXEC_TEXT_SIZE, pad=PAD_NO),
        button(NO_TEXT, KEY_START_B, PLAY, BUTTON_B_SIZE, BUTTON_COLOR, NO_BORDER, TOOLTIP_START, PAD_TOP),
        sg.Text(NO_TEXT, size=EXEC_TEXT_SIZE, pad=PAD_NO),
        button(NO_TEXT, KEY_STOP_B, STOP, BUTTON_B_SIZE, BUTTON_COLOR, NO_BORDER, TOOLTIP_STOP, PAD_TOP),
    ],
    [
        sg.Text(TEXT_WIZARD, key=KEY_WIZARD_T, size=EXEC_TEXT_SIZE, font=FONTB, pad=PAD_EXEC_TEXT, justification=CENTER),
        sg.Text(TEXT_START, key=KEY_START_T, font=FONTB, size=EXEC_TEXT_SIZE, pad=PAD_EXEC_TEXT, justification=CENTER),
        sg.Text(TEXT_STOP, key=KEY_STOP_T, font=FONTB, size=EXEC_TEXT_SIZE, pad=PAD_EXEC_TEXT, justification=CENTER)
    ],
    [console]
]
autoauditor_layout = [
    [sg.Frame(NO_TEXT, mandatory_layout, border_width=0)],
    [sg.Frame(NO_TEXT, vpn_layout, border_width=0)],
    [sg.Frame(NO_TEXT, blockchain_layout, border_width=0)],
    [sg.Frame(NO_TEXT, button_layout, border_width=0, element_justification="center")]
]

about_layout = [
    [sg.Text(NO_TEXT, pad=PAD_TOP)],
    [sg.Text(ABOUT_NAME, font=FONTB)],
    [sg.Text(ABOUT_VERSION, font=FONTB)],
    [sg.Text(NO_TEXT)],
    [sg.Text(ABOUT_AUTHOR, font=FONT)],
    [sg.Text(ABOUT_LAB, font=FONT)],
    [sg.Text(ABOUT_DEPARTMENT, font=FONT)],
    [sg.Text(ABOUT_UC3M, font=FONT)],
    [sg.Text(ABOUT_LOCATION, font=FONT)],
    [sg.Text(NO_TEXT)],
    [sg.Text(ABOUT_ACKNOWLEDGEMENT, font=FONT)],
    [sg.Text(NO_TEXT)],
    [sg.Text(ABOUT_LICENSE, font=FONT)],
    [sg.Text(NO_TEXT)],
    [sg.Text(ABOUT_YEAR, font=FONT)],
]

layout = [
    [sg.TabGroup(
        [
            [sg.Tab('AutoAuditor', autoauditor_layout, element_justification='center')],
            [sg.Tab('About', about_layout, element_justification='center')]
        ],
        border_width=NO_BORDER,
        tab_background_color=COLOR_TAB_DISABLED,
        font=FONT
    )]
]

# Create the Window
window = sg.Window('AutoAuditor', layout, element_justification="center")
# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event == KEY_VPN_CB or event == KEY_VPN_CB_T:
        switch(vpn_cb, vpn_cf_it, vpn_cf_fb,KEY_VPN_CF_T, KEY_VPN_CB_T, vpn_cf_i_b)

    if event == KEY_BC_CB or event == KEY_BC_CB_T:
        switch(bc_cb, bc_cf_it, bc_cf_fb, bc_lf_it, bc_lf_fb, KEY_BC_CF_T, KEY_BC_LF_T, KEY_BC_CB_T, bc_cf_i_b, bc_lf_i_b)

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
        errcode = run_command(console, cmd=" ".join(cmd), window=window)
        if errcode == 0:
            sg.Popup('AutoAuditor finished without errors.', title='Success')

    if event == KEY_WIZARD_B:
        sg.Popup('Wizard GUI not implemented yet!', title='Error')

    if event == KEY_PY_I_B:
        help_layout = [
            [sg.Text('Absolute or relative path to python executable.', font=FONT)],
            [sg.Text('A virtual environment can be generated using gen_venv.sh script.', font=FONT)],
            [sg.Text('After the generation, the python executable is located in:', font=FONT)],
            [sg.InputText(DEFAULT_PY, font=FONT, disabled=True, justification=CENTER)],
            [sg.OK()]
        ]
        sg.Window(TEXT_PY, help_layout, element_justification=CENTER).read(close=True)

    if event == KEY_AA_I_B:
        help_layout = [
            [sg.Text('Absolute or relative path to autoauditor script.', font=FONT)],
            [sg.Text('Autoauditor script is under autoauditor directory:', font=FONT)],
            [sg.InputText(DEFAULT_AA, font=FONT, disabled=True, justification=CENTER)],
            [sg.OK()]
        ]
        sg.Window(TEXT_AA, help_layout, element_justification=CENTER).read(close=True)

    if event == KEY_LF_I_B:
        help_layout = [
            [sg.Text('Absolute or relative path where output should be logged.', font=FONT)],
            [sg.Text('By default, output/msf.log will be used:', font=FONT)],
            [sg.InputText(DEFAULT_LF, font=FONT, disabled=True, justification=CENTER)],
            [sg.OK()]
        ]
        sg.Window(TEXT_LF, help_layout, element_justification=CENTER).read(close=True)

    if event == KEY_LD_I_B:
        help_layout = [
            [sg.Text('Absolute or relative path to directory where gathered data should be stored.', font=FONT)],
            [sg.Text('By default, output will be used:', font=FONT)],
            [sg.InputText(DEFAULT_LD, font=FONT, disabled=True, justification=CENTER)],
            [sg.OK()]
        ]
        sg.Window(TEXT_LD, help_layout, element_justification=CENTER).read(close=True)

    if event == KEY_RC_I_B:
        help_layout = [
            [sg.Text('Absolute or relative path to resource script file.', font=FONT)],
            [sg.Text('Under config, a template and few samples can be found:', font=FONT)],
            [sg.InputText(DEFAULT_RC, font=FONT, disabled=True, justification=CENTER)],
            [sg.OK()]
        ]
        sg.Window(TEXT_RC, help_layout, element_justification=CENTER).read(close=True)

    if event == KEY_VPN_CF_I_B:
        help_layout = [
            [sg.Text('Absolute or relative path to openvpn configuration file.', font=FONT)],
            [sg.Text('Under config, a sample can be found:', font=FONT)],
            [sg.InputText(DEFAULT_VPN_CF, font=FONT, disabled=True, justification=CENTER)],
            [sg.OK()]
        ]
        sg.Window(TEXT_VPN_CF, help_layout, element_justification=CENTER).read(close=True)

    if event == KEY_BC_CF_I_B:
        help_layout = [
            [sg.Text('Absolute or relative path to blockchain network configuration.', font=FONT)],
            [sg.Text('Under config, a template and a sample can be found:', font=FONT)],
            [sg.InputText(DEFAULT_BC_CF, font=FONT, disabled=True, justification=CENTER)],
            [sg.OK()]
        ]
        sg.Window(TEXT_BC_CF, help_layout, element_justification=CENTER).read(close=True)

    if event == KEY_BC_LF_I_B:
        help_layout = [
            [sg.Text('Absolute or relative path to blockchain log file of uploaded reports.', font=FONT)],
            [sg.Text('By default, output/blockchain.log will be used:', font=FONT)],
            [sg.InputText(DEFAULT_BC_LF, font=FONT, disabled=True, justification=CENTER)],
            [sg.OK()]
        ]
        sg.Window(TEXT_BC_LF, help_layout, element_justification=CENTER).read(close=True)

    if event == sg.WIN_CLOSED:  # if user closes window or clicks cancel
        break

window.close()
