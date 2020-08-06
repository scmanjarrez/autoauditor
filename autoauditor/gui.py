#!/usr/bin/env python3

# gui - Graphic User Interface module.

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

from utils import *
import PySimpleGUI as sg
import subprocess
import metasploit
import wizard
import sys
import re
import vpn
import blockchain

sg.theme('Reddit')  # Add a touch of color
# All the stuff inside your window.


def browse(text, key, target, image, image_size, color, border, disabled=False, tooltip=None, filetype=True, pad=None):
    if filetype:
        bt = sg.FileBrowse(button_text=text, button_color=color, target=target,
                           key=key, tooltip=tooltip, disabled=disabled, pad=None)
    else:
        bt = sg.FolderBrowse(button_text=text, button_color=color, target=target,
                             key=key, tooltip=tooltip, disabled=disabled, pad=None)
    bt.ImageData = image
    bt.ImageSize = image_size
    bt.BorderWidth = border
    return bt


def input_text(default, key, disabled=False, font=None, pad=None, visible=True):
    it = sg.InputText(default, key=key, disabled=disabled,
                      font=font, pad=pad, visible=visible)
    return it


def button(text, key, image, image_size, color, border, tooltip, pad=None, disabled=False, visible=True):
    bt = sg.Button(text, key=key, image_size=image_size, button_color=color,
                   border_width=border, image_data=image, tooltip=tooltip, pad=pad, disabled=disabled, visible=visible)
    return bt


class ImageCheckBox(sg.Button):
    def __init__(self, image_on, image_off, image_size, key, button_color, border_width, enabled, pad=None):
        self.enabled = enabled
        self.image_on = image_on
        self.image_off = image_off
        super().__init__(image_data=image_on if enabled else image_off, image_size=image_size,
                         key=key, button_color=button_color, border_width=border_width, pad=pad)

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
            window[el](
                text_color=COLOR_DISABLED if button.enabled else COLOR_ENABLED)
    button.switch()


def run_command(console, cmd, timeout=None, window=None):
    nop = None
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in p.stdout:
        line = line.decode(errors='replace' if (sys.version_info) < (
            3, 5) else 'backslashreplace').replace('\r', '\n').rstrip()
        console.print(line)
        window.refresh() if window else nop        # yes, a 1-line if, so shoot me
    exitcode = p.wait(timeout)
    return exitcode


py_fb = browse(NO_TEXT, KEY_PY_FB, KEY_INPUT_PY, FILEPNG, BUTTON_M_SIZE,
               BUTTON_COLOR, NO_BORDER, tooltip=TOOLTIP_FILE_BROWSER, pad=PAD_NO_TB)
py_i_b = button(NO_TEXT, KEY_PY_I_B, INFO, BUTTON_S_SIZE,
                BUTTON_COLOR, NO_BORDER, TOOLTIP_PY)
aa_fb = browse(NO_TEXT, KEY_AA_FB, KEY_INPUT_AA, FILEPNG, BUTTON_M_SIZE,
               BUTTON_COLOR, NO_BORDER, tooltip=TOOLTIP_FILE_BROWSER, pad=PAD_NO_TB)
aa_i_b = button(NO_TEXT, KEY_AA_I_B, INFO, BUTTON_S_SIZE,
                BUTTON_COLOR, NO_BORDER, TOOLTIP_AA)
lf_fb = browse(NO_TEXT, KEY_LF_FB, KEY_INPUT_LF, FILEPNG, BUTTON_M_SIZE,
               BUTTON_COLOR, NO_BORDER, tooltip=TOOLTIP_FILE_BROWSER, pad=PAD_NO_TB)
lf_i_b = button(NO_TEXT, KEY_LF_I_B, INFO, BUTTON_S_SIZE,
                BUTTON_COLOR, NO_BORDER, TOOLTIP_LF)
ld_fb = browse(NO_TEXT, KEY_LD_FB, KEY_INPUT_LD, FOLDERPNG, BUTTON_M_SIZE, BUTTON_COLOR,
               NO_BORDER, tooltip=TOOLTIP_FOLDER_BROWSER, filetype=False, pad=PAD_NO_TB)
ld_i_b = button(NO_TEXT, KEY_LD_I_B, INFO, BUTTON_S_SIZE,
                BUTTON_COLOR, NO_BORDER, TOOLTIP_LD)
rc_fb = browse(NO_TEXT, KEY_RC_FB, KEY_INPUT_RC, FILEPNG, BUTTON_M_SIZE,
               BUTTON_COLOR, NO_BORDER, tooltip=TOOLTIP_FILE_BROWSER, pad=PAD_NO_TB)
rc_i_b = button(NO_TEXT, KEY_RC_I_B, INFO, BUTTON_S_SIZE,
                BUTTON_COLOR, NO_BORDER, TOOLTIP_RC)

vpn_cb = ImageCheckBox(image_on=CBON, image_off=CBOFF, image_size=BUTTON_S_SIZE,
                       key=KEY_VPN_CB, button_color=BUTTON_COLOR, border_width=NO_BORDER, enabled=False)
vpn_cf_i_b = button(NO_TEXT, KEY_VPN_CF_I_B, INFO, BUTTON_S_SIZE,
                    BUTTON_COLOR, NO_BORDER, TOOLTIP_VPN_CF, disabled=True)
vpn_cf_it = input_text(DEFAULT_VPN_CF, KEY_INPUT_VPN_CF,
                       disabled=True, font=FONT, pad=PAD_IT_T)
vpn_cf_fb = browse(NO_TEXT, KEY_VPN_CF_FB, KEY_INPUT_VPN_CF, FILEPNG, BUTTON_M_SIZE,
                   BUTTON_COLOR, NO_BORDER, disabled=True, tooltip=TOOLTIP_FILE_BROWSER, pad=PAD_NO_TB)

bc_cb = ImageCheckBox(image_on=CBON, image_off=CBOFF, image_size=BUTTON_S_SIZE,
                      key=KEY_BC_CB, button_color=BUTTON_COLOR, border_width=NO_BORDER, enabled=False)
bc_cf_i_b = button(NO_TEXT, KEY_BC_CF_I_B, INFO, BUTTON_S_SIZE,
                   BUTTON_COLOR, NO_BORDER, TOOLTIP_BC_CF, disabled=True)
bc_cf_it = input_text(DEFAULT_BC_CF, KEY_INPUT_BC_CF,
                      disabled=True, font=FONT, pad=PAD_IT_T)
bc_cf_fb = browse(NO_TEXT, KEY_BC_CF_FB, KEY_INPUT_BC_CF, FILEPNG, BUTTON_M_SIZE,
                  BUTTON_COLOR, NO_BORDER, disabled=True, tooltip=TOOLTIP_FILE_BROWSER, pad=PAD_NO_TB)
bc_lf_i_b = button(NO_TEXT, KEY_BC_LF_I_B, INFO, BUTTON_S_SIZE,
                   BUTTON_COLOR, NO_BORDER, TOOLTIP_BC_LF, disabled=True)
bc_lf_it = input_text(DEFAULT_BC_LF, KEY_INPUT_BC_LF,
                      disabled=True, font=FONT, pad=PAD_IT_T)
bc_lf_fb = browse(NO_TEXT, KEY_BC_LF_FB, KEY_INPUT_BC_LF, FILEPNG, BUTTON_M_SIZE,
                  BUTTON_COLOR, NO_BORDER, disabled=True, tooltip=TOOLTIP_FILE_BROWSER, pad=PAD_NO_TB)

sc_cb = ImageCheckBox(image_on=CBON, image_off=CBOFF, image_size=BUTTON_S_SIZE,
                      key=KEY_SC_CB, button_color=BUTTON_COLOR, border_width=NO_BORDER, enabled=True)

console_cb = ImageCheckBox(image_on=CONSOLE_HIDE, image_off=CONSOLE_UNHIDE, image_size=BUTTON_S_SIZE,
                           key=KEY_CONSOLE_CB, button_color=BUTTON_COLOR, border_width=NO_BORDER, enabled=False, pad=PAD_NO)
console = sg.Multiline(NO_TEXT, key=KEY_CONSOLE, size=CONSOLE_SIZE,
                       pad=CONSOLE_PAD, visible=False, font=FONT, autoscroll=True)

mandatory_layout = [
    [sg.Text(NO_TEXT, pad=PAD_NO_TB)],
    [sg.Text(TEXT_PY, key=KEY_PY_T, size=TEXT_DESC_SIZE, font=FONTB), py_i_b,
     input_text(DEFAULT_PY, KEY_INPUT_PY, font=FONT, pad=PAD_IT_T), py_fb],
    [sg.Text(TEXT_AA, key=KEY_AA_T, size=TEXT_DESC_SIZE, font=FONTB), aa_i_b,
     input_text(DEFAULT_AA, KEY_INPUT_AA, font=FONT, pad=PAD_IT_T), aa_fb],
    [sg.Text(NO_TEXT, pad=PAD_NO_TB)],
    [sg.Text(TEXT_LF, key=KEY_LF_T, size=TEXT_DESC_SIZE, font=FONTB), lf_i_b,
     input_text(DEFAULT_LF, KEY_INPUT_LF, font=FONT, pad=PAD_IT_T), lf_fb],
    [sg.Text(TEXT_LD, key=KEY_LD_T, size=TEXT_DESC_SIZE, font=FONTB), ld_i_b,
     input_text(DEFAULT_LD, KEY_INPUT_LD, font=FONT, pad=PAD_IT_T), ld_fb],
    [sg.Text(TEXT_RC, key=KEY_RC_T, size=TEXT_DESC_SIZE, font=FONTB), rc_i_b,
     input_text(DEFAULT_RC, KEY_INPUT_RC, font=FONT, pad=PAD_IT_T), rc_fb],
    [sg.Text(NO_TEXT, pad=PAD_NO_TB)]
]

vpn_layout = [
    [vpn_cb, sg.Text(TEXT_VPN_CB, key=KEY_VPN_CB_T,
                     text_color=COLOR_DISABLED, font=FONTB, enable_events=True)],
    [sg.Text(TEXT_VPN_CF, key=KEY_VPN_CF_T, size=TEXT_DESC_SIZE, font=FONTB,
             text_color=COLOR_DISABLED), vpn_cf_i_b, vpn_cf_it, vpn_cf_fb],
    [sg.Text(NO_TEXT, pad=PAD_NO_TB)]
]

blockchain_layout = [
    [bc_cb, sg.Text(TEXT_BC_CB, key=KEY_BC_CB_T,
                    text_color=COLOR_DISABLED, font=FONTB, enable_events=True)],
    [sg.Text(TEXT_BC_CF, key=KEY_BC_CF_T, size=TEXT_DESC_SIZE, font=FONTB,
             text_color=COLOR_DISABLED), bc_cf_i_b, bc_cf_it, bc_cf_fb],
    [sg.Text(TEXT_BC_LF, key=KEY_BC_LF_T, size=TEXT_DESC_SIZE, font=FONTB,
             text_color=COLOR_DISABLED), bc_lf_i_b, bc_lf_it, bc_lf_fb],
    [sg.Text(NO_TEXT, pad=PAD_NO_TB)],

    [sc_cb, sg.Text(TEXT_SC_CB, key=KEY_SC_CB_T,
                    text_color=COLOR_ENABLED, font=FONTB,  enable_events=True)]
]

button_layout = [
    [
        button(NO_TEXT, KEY_WIZARD_B, WIZARD, BUTTON_L_SIZE,
               BUTTON_COLOR, NO_BORDER, TOOLTIP_WIZARD, PAD_T),
        sg.Text(NO_TEXT, size=EXEC_TEXT_SIZE_S, pad=PAD_NO),
        button(NO_TEXT, KEY_START_B, PLAY, BUTTON_L_SIZE,
               BUTTON_COLOR, NO_BORDER, TOOLTIP_START, PAD_T),
        sg.Text(NO_TEXT, size=EXEC_TEXT_SIZE_S, pad=PAD_NO),
        button(NO_TEXT, KEY_STOP_B, STOP, BUTTON_L_SIZE,
               BUTTON_COLOR, NO_BORDER, TOOLTIP_STOP, PAD_T),
    ],
    [
        sg.Text(TEXT_WIZARD, key=KEY_WIZARD_T, size=EXEC_TEXT_SIZE_S,
                font=FONTB, pad=PAD_EXEC_TEXT, justification=CENTER, enable_events=True),
        sg.Text(TEXT_START, key=KEY_START_T, font=FONTB,
                size=EXEC_TEXT_SIZE_S, pad=PAD_EXEC_TEXT, justification=CENTER, enable_events=True),
        sg.Text(TEXT_STOP, key=KEY_STOP_T, font=FONTB,
                size=EXEC_TEXT_SIZE_S, pad=PAD_EXEC_TEXT, justification=CENTER, enable_events=True)
    ],
    [sg.Frame(NO_TEXT, [[sg.Text(NO_TEXT, size=(110, 1), pad=PAD_NO),
                         console_cb]], border_width=NO_BORDER)],
    [console]
]
autoauditor_layout = [
    [sg.Frame(NO_TEXT, mandatory_layout, border_width=0)],
    [sg.Frame(NO_TEXT, vpn_layout, border_width=0)],
    [sg.Frame(NO_TEXT, blockchain_layout, border_width=0)],
    [sg.Frame(NO_TEXT, button_layout, border_width=0,
              element_justification=CENTER)]
]

about_layout = [
    [sg.Text(NO_TEXT, pad=PAD_NO_TB)],
    [sg.Text(NO_TEXT, pad=PAD_NO_TB)],
    [sg.Text(NO_TEXT, pad=PAD_NO_TB)],
    [sg.Text(ABOUT_NAME, font=FONTB)],
    [sg.Text(ABOUT_VERSION, font=FONTB)],
    [sg.Text(NO_TEXT)],
    [sg.Text(NO_TEXT, pad=PAD_NO_TB)],
    [sg.Text(ABOUT_AUTHOR, font=FONT)],
    [sg.Text(ABOUT_LAB, font=FONT)],
    [sg.Text(ABOUT_DEPARTMENT, font=FONT)],
    [sg.Text(ABOUT_UC3M, font=FONT)],
    [sg.Text(ABOUT_LOCATION, font=FONT)],
    [sg.Text(NO_TEXT)],
    [sg.Text(NO_TEXT, pad=PAD_NO_TB)],
    [sg.Text(ABOUT_ACKNOWLEDGEMENT, font=FONT, justification=CENTER)],
    [sg.Text(NO_TEXT)],
    [sg.Text(NO_TEXT, pad=PAD_NO_TB)],
    [sg.Text(ABOUT_YEAR, font=FONT)],
]

gplv3 = """
AutoAuditor  Copyright (C) 2020  Sergio Chica Manjarrez
This program comes with ABSOLUTELY NO WARRANTY; for details check below.
This is free software, and you are welcome to redistribute it
under certain conditions; check below for details.
"""

with open(DEFAULT_LICENSE, 'r') as f:
    gplv3_full = f.read().replace('.  ', '. ').replace('  ', '')

gplv3_full_layout = [
    [sg.Text(gplv3_full, justification=CENTER, size=LICENSE_TEXT_SIZE,
             background_color=COLOR_TAB_DISABLED)]
]
license_layout = [
    [sg.Text(gplv3, font=FONT, justification=CENTER)],
    [sg.Column(gplv3_full_layout,
               scrollable=True, size=LICENSE_COLUMN_SIZE, vertical_scroll_only=True, justification=CENTER, background_color=COLOR_TAB_DISABLED, pad=PAD_T)]
]


layout = [
    [sg.TabGroup(
        [
            [sg.Tab('AutoAuditor', autoauditor_layout,
                    element_justification=CENTER)],
            [sg.Tab('About', about_layout, element_justification=CENTER)],
            [sg.Tab('License', license_layout, element_justification=CENTER)]
        ],
        border_width=NO_BORDER,
        tab_background_color=COLOR_TAB_DISABLED,
        font=FONT
    )]
]

# Create the Window
window = sg.Window('AutoAuditor', layout, element_justification=CENTER)
window_no_console_size = None
window_console_size = None


def shrink_enlarge_window():
    console(visible=not console_cb.enabled)
    console_cb.switch()
    if console_cb.enabled:
        window.size = window_console_size
    else:
        window.size = window_no_console_size
    window.refresh()


def opt_window(msfclient, mtype, mname, mod_idx, current_opts=[]):
    added = False
    mod = wizard._get_module(msfclient, mtype, mname)
    opts, ropts = wizard._get_module_options(mod)
    if current_opts:
        for cp in current_opts:
            opts[cp] = current_opts[cp]
    scrollable = len(opts) > 18
    opt_layout = [
        [sg.Text(NO_TEXT, pad=PAD_NO_TB, font=FONTPAD)],
        [sg.Text("/".join([mtype, mname]), font=FONTB)],
        [sg.Frame(NO_TEXT, [[sg.Text(NO_TEXT, font=FONTPAD, pad=PAD_NO, size=TEXT_DESC_SIZE_XL2)],
                            [sg.Text(TEXT_OPT_NAME, font=FONTB, size=TEXT_OPT_NAME_SIZE, pad=PAD_OPT_HEAD), sg.Text(TEXT_OPT_REQ, font=FONTB, pad=PAD_OPT_HEAD2, size=TEXT_REQ_SIZE), sg.Text(TEXT_OPT_VAL, font=FONTB, size=TEXT_OPT_VAL_SIZE, pad=PAD_OPT_HEAD3)]], border_width=NO_BORDER)],
        [sg.Column(
            [[sg.Frame(NO_TEXT, [
                [sg.InputText(opt, size=TEXT_DESC_SIZE_2, key=KEY_OPT+str(idx), pad=PAD_IT_T, font=FONT, disabled_readonly_background_color=COLOR_IT_AS_T, readonly=True, border_width=NO_BORDER),
                 sg.Text(TEXT_REQ_Y if opt in ropts else TEXT_REQ_N,
                         size=TEXT_REQ_SIZE, justification=CENTER, font=FONT),
                 button(NO_TEXT, KEY_OPT_HELP+str(idx), INFO, BUTTON_S_SIZE,
                        BUTTON_COLOR, NO_BORDER, wizard._get_option_desc(mod, opt)),
                 sg.InputText(str(opts[opt]), size=TEXT_DESC_SIZE_M, key=KEY_OPT_VAL+str(idx), pad=PAD_IT_T, font=FONT)]], border_width=NO_BORDER, pad=PAD_NO)] for idx, opt in enumerate(opts)], size=OPT_MOD_COLUMN_SIZE, scrollable=scrollable, vertical_scroll_only=True)],
        [sg.Text(NO_TEXT, pad=PAD_NO_TB)],
        [sg.Button('Accept', key=KEY_OPT_ACCEPT),
         sg.Button('Cancel', key=KEY_OPT_CANCEL)]
    ]

    owindow = sg.Window(
        TEXT_OPTIONS, opt_layout, element_justification=CENTER, finalize=True)
    help_regex = re.compile(KEY_OPT_HELP+'\d+')
    while True:
        oevent, ovalue = owindow.read()
        if oevent is not None and help_regex.match(oevent):
            opt_n = int(oevent.split('_')[2])  # option_help_xxx
            opt = owindow[KEY_OPT+str(opt_n)].Get()
            opt_info = wizard._get_option_info(mod, opt)
            info_layout = [
                [sg.Text(NO_TEXT, pad=PAD_NO_TB, font=FONTPAD)],
                [sg.Text(opt, font=FONTB)],
                [sg.Text(NO_TEXT, pad=PAD_NO_TB, font=FONTPAD)]] +\
                [[sg.Frame(NO_TEXT, [[sg.Text(el, font=FONTB, size=EXEC_TEXT_SIZE_S), sg.Text(opt_info[el], font=FONT)]
                                     for el in opt_info], border_width=NO_BORDER)]] +\
                [[sg.OK(font=FONT)]]

            sg.Window(TEXT_OPTION_INFO, info_layout,
                      element_justification=CENTER).read(close=True)

        if oevent == KEY_OPT_ACCEPT:
            if mtype not in mod_list:
                mod_list[mtype] = {}
            if mname not in mod_list[mtype]:
                mod_list[mtype][mname] = {}

            opt_l = {opt: correct_type(owindow[KEY_OPT_VAL+str(idx)].Get())
                     for idx, opt in enumerate(opts)
                     if opts[opt] != correct_type(owindow[KEY_OPT_VAL+str(idx)].Get())}

            mod_list[mtype][mname][mod_idx] = opt_l

            wwindow[KEY_MOD_NAME +
                    str(mod_idx)](value=": ".join([mtype, mname]))

            # wwindow[KEY_MOD_FRAME +
            #         str(mod_idx)].unhide_row()
            wwindow[KEY_MOD_FRAME +
                    str(mod_idx)](visible=True)
            wwindow.refresh()  # trick to show last element inmediately
            wwindow[KEY_MOD_COL].Widget.canvas.config(
                scrollregion=wwindow[KEY_MOD_COL].Widget.canvas.bbox('all'))
            wwindow[KEY_MOD_COL].Widget.canvas.yview_moveto(
                999)
            added = True
            break
        if oevent == KEY_OPT_CANCEL:
            break
    owindow.close()
    return added


# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event is not None and window_no_console_size is None:
        window_no_console_size = window.size
    if event is not None and window and console_cb.enabled and window_console_size is None:
        window_console_size = window.size

    if event == KEY_VPN_CB or event == KEY_VPN_CB_T:
        switch(vpn_cb, vpn_cf_it, vpn_cf_fb,
               KEY_VPN_CF_T, KEY_VPN_CB_T, vpn_cf_i_b)

    if event == KEY_BC_CB or event == KEY_BC_CB_T:
        switch(bc_cb, bc_cf_it, bc_cf_fb, bc_lf_it, bc_lf_fb,
               KEY_BC_CF_T, KEY_BC_LF_T, KEY_BC_CB_T, bc_cf_i_b, bc_lf_i_b)

    if event == KEY_SC_CB or event == KEY_SC_CB_T:
        switch(sc_cb, KEY_SC_CB_T, KEY_SC_CB_T)

    if event == KEY_START_B or event == KEY_START_T:
        if not console_cb.enabled:
            shrink_enlarge_window()
        console_log(window, console)

        vpncont = msfcont = None

        if vpn_cb.enabled:
            vpncf = window[KEY_INPUT_VPN_CF].Get()
            if not os.path.isfile(vpncf):
                sg.Window('Error', [
                    [sg.Text('File {}'.format(vpncf), font=FONT)],
                    [sg.Text('does not exist.', font=FONT)],
                    [sg.Text(NO_TEXT, font=FONTPAD)],
                    [sg.OK(button_color=BUTTON_COLOR_ERR)]
                ], element_justification=CENTER, auto_close=True).read(close=True)
            else:
                vpncont = vpn.setup_vpn(vpncf)

        lf = window[KEY_INPUT_LF].Get()
        ld = window[KEY_INPUT_LD].Get()

        errcode = check_file_dir(lf, ld)
        if errcode is not None:
            sg.Window('Error', [
                [sg.Text('Log file/Log directory', font=FONT)],
                [sg.Text('does not exist.', font=FONT)],
                [sg.Text(NO_TEXT, font=FONTPAD)],
                [sg.OK(button_color=BUTTON_COLOR_ERR)]
            ], element_justification=CENTER, auto_close=True).read(close=True)
        else:
            msfcont = metasploit.start_msfrpcd(ld, ovpn=vpn_cb.enabled)

        msfclient = metasploit.get_msf_connection(DEFAULT_MSFRPC_PASSWD)

        rc = window[KEY_INPUT_RC].Get()
        if not os.path.isfile(rc):
            sg.Window('Error', [
                [sg.Text('File {}'.format(rc), font=FONT)],
                [sg.Text('does not exist.', font=FONT)],
                [sg.Text(NO_TEXT, font=FONTPAD)],
                [sg.OK(button_color=BUTTON_COLOR_ERR)]
            ], element_justification=CENTER, auto_close=True).read(close=True)
        else:
            metasploit.launch_metasploit(msfclient, rc, lf)

        if bc_cb.enabled:
            hc = window[KEY_INPUT_BC_CF].Get()
            ho = window[KEY_INPUT_BC_LF].Get()
            if not os.path.isfile(hc):
                sg.Window('Error', [
                    [sg.Text('File {}'.format(rc), font=FONT)],
                    [sg.Text('does not exist.', font=FONT)],
                    [sg.Text(NO_TEXT, font=FONTPAD)],
                    [sg.OK(button_color=BUTTON_COLOR_ERR)]
                ], element_justification=CENTER, auto_close=True).read(close=True)
            else:
                info = blockchain.load_config(hc)
                errcode = check_file_dir(ho)
                if errcode is not None:
                    sg.Window('Error', [
                        [sg.Text('Blockchain log file', font=FONT)],
                        [sg.Text('does not exist.', font=FONT)],
                        [sg.Text(NO_TEXT, font=FONTPAD)],
                        [sg.OK(button_color=BUTTON_COLOR_ERR)]
                    ], element_justification=CENTER, auto_close=True).read(close=True)
                else:
                    blockchain.store_report(info, lf, ho)
        if sc_cb.enabled:
            shutdown(msfcont, vpncont)

    if event == KEY_STOP_B or event == KEY_STOP_T:
        if not console_cb.enabled:
            shrink_enlarge_window()
        console_log(window, console)

        if vpn_cb.enabled:
            vpncont = vpn.setup_vpn(window[KEY_INPUT_VPN_CF].Get(), stop=True)

        msfcont = metasploit.start_msfrpcd(
                    window[KEY_INPUT_LD].Get(), ovpn=vpn_cb.enabled, stop=True)

        shutdown(msfcont, vpncont)

    if event == KEY_PY_I_B:
        sg.Window(TEXT_PY, [
            [sg.Text('Absolute or relative path to python executable.', font=FONT)],
            [sg.Text(
                'A virtual environment can be generated using gen_venv.sh script.', font=FONT)],
            [sg.Text(
                'After the generation, the python executable is located in:', font=FONT)],
            [sg.InputText(DEFAULT_PY, font=FONT, disabled=True,
                          justification=CENTER)],
            [sg.OK()]
        ], element_justification=CENTER).read(close=True)

    if event == KEY_AA_I_B:
        sg.Window(TEXT_AA, [
            [sg.Text('Absolute or relative path to autoauditor script.', font=FONT)],
            [sg.Text('Autoauditor script is under autoauditor directory:', font=FONT)],
            [sg.InputText(DEFAULT_AA, font=FONT, disabled=True,
                          justification=CENTER)],
            [sg.OK()]
        ], element_justification=CENTER).read(close=True)

    if event == KEY_LF_I_B:
        sg.Window(TEXT_LF, [
            [sg.Text(
                'Absolute or relative path where output should be logged.', font=FONT)],
            [sg.Text('By default, output/msf.log will be used:', font=FONT)],
            [sg.InputText(DEFAULT_LF, font=FONT, disabled=True,
                          justification=CENTER)],
            [sg.OK()]
        ], element_justification=CENTER).read(close=True)

    if event == KEY_LD_I_B:
        sg.Window(TEXT_LD, [
            [sg.Text(
                'Absolute or relative path to directory where gathered data should be stored.', font=FONT)],
            [sg.Text('By default, output will be used:', font=FONT)],
            [sg.InputText(DEFAULT_LD, font=FONT, disabled=True,
                          justification=CENTER)],
            [sg.OK()]
        ], element_justification=CENTER).read(close=True)

    if event == KEY_RC_I_B:
        sg.Window(TEXT_RC, [
            [sg.Text('Absolute or relative path to resource script file.', font=FONT)],
            [sg.Text(
                'Under config, a template and few examples can be found:', font=FONT)],
            [sg.InputText(DEFAULT_RC, font=FONT, disabled=True,
                          justification=CENTER)],
            [sg.OK()]
        ], element_justification=CENTER).read(close=True)

    if event == KEY_VPN_CF_I_B:
        sg.Window(TEXT_VPN_CF, [
            [sg.Text(
                'Absolute or relative path to openvpn configuration file.', font=FONT)],
            [sg.Text('Under config, a template and an example can be found:', font=FONT)],
            [sg.InputText(DEFAULT_VPN_CF, font=FONT,
                          disabled=True, justification=CENTER)],
            [sg.OK()]
        ], element_justification=CENTER).read(close=True)

    if event == KEY_BC_CF_I_B:
        sg.Window(TEXT_BC_CF, [
            [sg.Text(
                'Absolute or relative path to blockchain network configuration.', font=FONT)],
            [sg.Text('Under config, a template and an example can be found:', font=FONT)],
            [sg.InputText(DEFAULT_BC_CF, font=FONT,
                          disabled=True, justification=CENTER)],
            [sg.OK()]
        ], element_justification=CENTER).read(close=True)

    if event == KEY_BC_LF_I_B:
        sg.Window(TEXT_BC_LF, [
            [sg.Text(
                'Absolute or relative path to blockchain log file of uploaded reports.', font=FONT)],
            [sg.Text('By default, output/blockchain.log will be used:', font=FONT)],
            [sg.InputText(DEFAULT_BC_LF, font=FONT,
                          disabled=True, justification=CENTER)],
            [sg.OK()]
        ], element_justification=CENTER).read(close=True)

    if event == sg.WIN_CLOSED:
        break

    if event == KEY_CONSOLE_CB:
        shrink_enlarge_window()

    if event == KEY_WIZARD_B or event == KEY_WIZARD_T:
        if not console_cb.enabled:
            shrink_enlarge_window()
        console_log(window, console)

        msfcont = metasploit.start_msfrpcd(window[KEY_INPUT_LD].Get())
        msfclient = metasploit.get_msf_connection(DEFAULT_MSFRPC_PASSWD)
        mtype = None
        mname = None
        mod = None

        mt_i_b = button(NO_TEXT, KEY_MT_I_B, INFO, BUTTON_S_SIZE,
                        BUTTON_COLOR, NO_BORDER, TOOLTIP_MT)
        mn_i_b = button(NO_TEXT, KEY_MN_I_B, INFO, BUTTON_S_SIZE,
                        BUTTON_COLOR, NO_BORDER, TOOLTIP_MN)

        mod_layout = [[sg.Frame(NO_TEXT, [[
            sg.InputText(str(i), size=TEXT_DESC_SIZE_L, pad=PAD_NO_TBR, disabled_readonly_background_color=COLOR_IT_AS_T,
                         readonly=True, border_width=NO_BORDER, font=FONT, key=KEY_MOD_NAME+str(i)),
            button(NO_TEXT, KEY_MOD_EDIT+str(i), EDIT, BUTTON_M_SIZE,
                   BUTTON_COLOR, NO_BORDER, TOOLTIP_MOD_EDIT, pad=PAD_MOD),
            button(NO_TEXT, KEY_MOD_REM+str(i), REMOVE, BUTTON_M_SIZE,
                   BUTTON_COLOR, NO_BORDER, TOOLTIP_MOD_REMOVE)
        ]], visible=False, pad=PAD_NO, border_width=NO_BORDER, key=KEY_MOD_FRAME+str(i), element_justification=CENTER)] for i in range(MAX_MODULES)]

        wizard_layout = [
            [sg.Text(NO_TEXT, font=FONT, pad=PAD_NO_TB)],
            [sg.Text(TEXT_MODULE_TYPE, font=FONTB, size=TEXT_DESC_SIZE), sg.DropDown(
                MODULE_TYPES, size=EXEC_TEXT_SIZE_L, font=FONT, enable_events=True, key=KEY_MODULE_TYPE, readonly=True)],
            [sg.Text(TEXT_MODULE_NAME, font=FONTB, size=TEXT_DESC_SIZE), sg.DropDown(
                NO_TEXT, size=EXEC_TEXT_SIZE_L, font=FONT, key=KEY_MODULE_NAME, readonly=True)],
            [sg.Text(NO_TEXT, font=FONT, pad=PAD_NO)],
            [sg.Column(mod_layout, size=OPT_MOD_COLUMN_SIZE, element_justification=CENTER, pad=PAD_NO,
                       justification=CENTER, scrollable=True, vertical_scroll_only=True, key=KEY_MOD_COL)],
            [sg.Text(NO_TEXT, font=FONT, pad=PAD_NO)],
            [button(NO_TEXT, KEY_MOD_ADD, ADD, BUTTON_L_SIZE,
                    BUTTON_COLOR, NO_BORDER, TOOLTIP_MOD_ADD)],
            [sg.Text(NO_TEXT, pad=PAD_NO_TB, font=FONTPAD)],
            [sg.Button(TEXT_WIZARD_GEN, key=KEY_WIZARD_GEN, font=FONT),
             sg.Button(TEXT_WIZARD_EXIT, key=KEY_WIZARD_EXIT, font=FONT)],
            [sg.Text(NO_TEXT, pad=PAD_NO_TB, font=FONTPAD)]
        ]
        wwindow = sg.Window('Helper', wizard_layout,
                            element_justification=CENTER)

        edit_regex = re.compile(KEY_MOD_EDIT+'\d+')
        rem_regex = re.compile(KEY_MOD_REM+'\d+')
        # (MAX_MODULES-1) ... 0
        mod_idx = [idx for idx in range(MAX_MODULES-1, -1, -1)]
        mod_list = {}
        while True:
            wevent, wvalues = wwindow.read()
            if wevent == KEY_MODULE_TYPE:
                mtype = wvalues[KEY_MODULE_TYPE]
                mods = [''] + wizard._get_modules(msfclient, mtype)
                wwindow[KEY_MODULE_NAME](
                    values=mods)

            if wevent == KEY_MOD_ADD:
                mname = wvalues[KEY_MODULE_NAME]
                if mtype and mname:
                    if mod_idx:
                        added = opt_window(
                            msfclient, mtype, mname, mod_idx[-1])
                        if added:
                            mod_idx.remove(mod_idx[-1])
                    else:
                        sg.Window('Error', [
                            [sg.Text('Maximum modules allowed ({}).'.format(
                                MAX_MODULES), font=FONT)],
                            [sg.Text(
                                'Limit can be changed in utils.py:MAX_MODULES', font=FONT)],
                            [sg.OK(button_color=BUTTON_COLOR_ERR, font=FONT)]
                        ], element_justification=CENTER, auto_close=True).read(close=True)
                else:
                    sg.Window('Error', [
                        [sg.Text(
                            'Empty module type/name.'.format(MAX_MODULES), font=FONT)],
                        [sg.Text(
                            'Choose a module type and module name from the dropdown.', font=FONT)],
                        [sg.OK(button_color=BUTTON_COLOR_ERR, font=FONT)]
                    ], element_justification=CENTER, auto_close=True, auto_close_duration=2).read(close=True)

            if wevent is not None and edit_regex.match(wevent):
                aux_mod_idx = int(wevent.split("_")[2])  # module_name_xxx
                aux_mt, aux_mn = wwindow[KEY_MOD_NAME +
                                         str(aux_mod_idx)].Get().split(': ')
                opt_window(
                    msfclient, aux_mt, aux_mn, aux_mod_idx, mod_list[aux_mt][aux_mn][aux_mod_idx])

            if wevent is not None and rem_regex.match(wevent):
                aux_mod_idx = int(wevent.split("_")[2])  # module_rem_xxx
                aux_mt, aux_mn = wwindow[KEY_MOD_NAME +
                                         str(aux_mod_idx)].Get().split(': ')
                wwindow[KEY_MOD_FRAME+str(aux_mod_idx)](visible=False)
                wwindow[KEY_MOD_FRAME+str(aux_mod_idx)
                        ].ParentRowFrame.config(width=0, height=1)
                del mod_list[aux_mt][aux_mn][aux_mod_idx]
                mod_idx.insert(0, aux_mod_idx)  # reuse removed item

            if wevent in (KEY_WIZARD_EXIT, sg.WIN_CLOSED):
                shutdown(msfcont)
                break

            if wevent == KEY_WIZARD_GEN:
                ev, val = sg.Window('Are you sure?', [
                    [sg.Text('Are you sure you want to', justification=CENTER, font=FONT, pad=PAD_NO_R), sg.Text(
                        'overwrite', justification=CENTER, font=FONTB, pad=PAD_NO_L)],
                    [sg.Text('{}?'.format(window[KEY_INPUT_RC].Get()),
                             justification=CENTER, font=FONT)],
                    [sg.Text(NO_TEXT, justification=CENTER, font=FONTPAD)],
                    [sg.Yes(font=FONT, button_color=BUTTON_COLOR_ERR),
                     sg.No(font=FONT)]
                ], element_justification=CENTER).read(close=True)
                if ev == 'Yes':
                    for mlt in mod_list:
                        for mln in mod_list[mlt]:
                            mod_list[mlt][mln] = list(
                                mod_list[mlt][mln].values())
                    with open(window[KEY_INPUT_RC].Get(), 'w') as f:
                        json.dump(rc_file, f, indent=2)
                        utils.log(
                            'succg', "Resource script file generated at {}".format(rc_out))
        wwindow.close()
window.close()
