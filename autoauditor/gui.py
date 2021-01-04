#!/usr/bin/env python3

# gui - Graphic User Interface module.

# Copyright (C) 2020 Sergio Chica Manjarrez @ pervasive.it.uc3m.es.
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

from copy import deepcopy
import PySimpleGUI as sg
import constants as cst
import asyncio as _asyncio
import utils
import metasploit
import wizard
import re
import vpn
import json
import blockchain
import os
import queue
import threading
import time

sg.theme('Reddit')

sg.theme_input_background_color(cst.C['lightblue'])
sg.set_options(font=cst.FNT)

MN = 'MAIN'
WZ = 'WIZ'
MO = 'MOPTS'
PO = 'POPTS'
POP = 'POPUP'

WIN = {
    'MAIN': None,
    'WIZ': None,
    'MOPTS': {},
    'POPTS': {},
    'POPUP': {
        MN: [],
        WZ: [],
        MO: {},
        PO: {}
    }
}


class Button(sg.Button):
    def __init__(self, key, tooltip=None, image_data=cst.ICO_INFO,
                 image_size=cst.B_SZ24, button_color=cst.B_C,
                 pad=cst.P_N_TB, border_width=cst.N_WDTH, disabled=False,
                 target=(None, None), button_type=sg.BUTTON_TYPE_READ_FORM,
                 visible=True):
        super().__init__(key=key, tooltip=tooltip,
                         image_data=image_data, image_size=image_size,
                         button_color=button_color, pad=pad,
                         border_width=border_width, disabled=disabled,
                         target=target, button_type=button_type,
                         visible=visible)


class Browser(Button):
    def __init__(self, key, tooltip, target,
                 folder=False, disabled=False):
        super().__init__(key=key, tooltip=tooltip,
                         image_data=cst.ICO_FOLDER if folder else cst.ICO_FILE,
                         image_size=cst.B_SZ32, pad=cst.P_N_TB,
                         disabled=disabled, target=target,
                         button_type=sg.BUTTON_TYPE_BROWSE_FILE if folder
                         else sg.BUTTON_TYPE_BROWSE_FILE)


class ImageCheckBox(Button):
    def __init__(self, key, image_on=cst.ICO_CBNCHK, image_off=cst.ICO_CBCHK,
                 image_size=cst.B_SZ24, pad=cst.P_N, enabled=False):
        self.enabled = enabled
        self.image_on = image_on
        self.image_off = image_off
        super().__init__(key=key,
                         image_data=image_on if enabled else image_off,
                         image_size=image_size, pad=pad, border_width=0)

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, enabled):
        self._enabled = enabled

    def switch(self):
        if self.enabled:
            self(image_data=self.image_off)
            self.enabled = False
        else:
            self(image_data=self.image_on)
            self.enabled = True


class Window(sg.Window):
    def __init__(self, *text, title="Error", button_color=cst.B_C_ERR,
                 auto_close_duration=4):
        layout = [
            [sg.Text(font=cst.FNT_P, pad=cst.P_N_TB)],
            [sg.OK(button_color=button_color)]
        ]
        for t in text[::-1]:
            layout.insert(0, [sg.Text(t)])

        super().__init__(title, layout, element_justification=cst.J_C,
                         icon=cst.ICO, auto_close=True, keep_on_top=True,
                         auto_close_duration=auto_close_duration)
        self.read(close=True)


class Module():
    def __init__(self, client, mtype, mname, ticket):
        self.client = client
        self._ticket = ticket
        self.mod = wizard.get_module(self.client, mtype, mname)
        self._mopts = {}
        self._payload = None

    def ticket(self):
        return self._ticket

    def mtype(self):
        return self.mod.moduletype

    def mname(self):
        return self.mod.modulename

    def info(self):
        return wizard.get_module_info(self.mod)

    def options(self):
        return wizard.get_module_options(self.mod)

    def mopts(self):
        return self._mopts

    def has_payloads(self):
        return wizard.has_payloads(self.mod)

    def payloads(self):
        return wizard.get_module_payloads(self.mod)

    def opt_info(self, opt):
        return wizard.get_option_info(self.mod, opt)

    def opt_desc(self, opt):
        return wizard.get_option_desc(self.mod, opt)

    @property
    def payload(self):
        return self._payload

    @payload.setter
    def payload(self, pname):
        self._payload = Module(self.client, 'payload', pname, self.ticket)

    @payload.deleter
    def payload(self):
        self._payload = None

    def gen_dict(self):
        axm = deepcopy(self._mopts)
        if self.payload is not None:
            axm['PAYLOAD'] = {}
            axm['PAYLOAD']['NAME'] = self.payload.mname()
            axm['PAYLOAD']['OPTIONS'] = deepcopy(self.payload.mopts())
        return axm


class TicketSystem():
    def __init__(self, total):
        self.tickets = list(range(total))[::-1]

    def get_ticket(self):
        return self.tickets.pop()

    def return_ticket(self, ticket):
        self.tickets.append(ticket)

    def available_ticket(self):
        return bool(self.tickets)


class LoadingGif(sg.Window):
    def __init__(self, start_gif=False):
        self.start_gif = start_gif
        self.message = ('Starting\ncontainers' if start_gif
                        else 'Stopping\ncontainers')
        self.layout = [
            [sg.Image(filename=cst.LOADING,
                      background_color=cst.C['white'],
                      key=cst.K_GIF)],
            [sg.Text(font=cst.FNT_P, pad=cst.P_N_LR)],
            [sg.Text(self.message, background_color=cst.C['white'],
                     justification=cst.J_C)]]

        super().__init__('Loading', self.layout,
                         element_justification=cst.J_C,
                         element_padding=(0, 0), margins=(10, 10),
                         icon=cst.ICO, finalize=True)

    def update(self):
        self[cst.K_GIF].UpdateAnimation(cst.LOADING,
                                        time_between_frames=100)
        self.refresh()

    def stop(self):
        self.close()


class LoadingThread(threading.Thread):
    def __init__(self, event, window, start_gif=False):
        threading.Thread.__init__(self)
        self.stopped = event
        self.window = window
        self.daemon = True
        self.start_gif = start_gif

    def run(self):
        while not self.stopped.wait(0.1):
            self.window.write_event_value('GIF', self.start_gif)
        self.window.write_event_value('GIFSTOP', self.start_gif)


class AutoauditorThread(threading.Thread):
    def __init__(self, window, cmd_queue, stopped):
        threading.Thread.__init__(self)
        self.daemon = True
        self.window = window
        self.queue = cmd_queue
        self.stopped = stopped
        self.vpncnt = None
        self.msfcnt = None
        self.msfcl = None
        self.cfg = None
        self.async_loop = _asyncio.new_event_loop()
        self.sgif_flag = None
        self.stop = False

    def run(self):
        while not self.stopped.is_set():
            cmd, params = self.queue.get()
            getattr(self, cmd)(*params)

    def vpnstart(self, vpncfg, stop):
        self.vpncnt = vpn.setup_vpn(vpncfg, stop=stop)

    def msfstart(self, ldir, ovpn, stop):
        self.stop = stop
        if not stop:
            self.sgif_flag = threading.Event()
            sgif_thread = LoadingThread(self.sgif_flag, self.window,
                                        start_gif=True)
            sgif_thread.start()
        self.msfcnt = metasploit.start_msfrpcd(ldir, ovpn, stop)
        self.window.write_event_value('START', (self.msfcnt, stop))

    def msfconnect(self, passwd, is_wizard):
        self.msfcl = metasploit.get_msf_connection(passwd)
        err = cst.EMSCONN
        if self.msfcl is not None:
            err = cst.NOERROR
        if not self.stop:
            self.sgif_flag.set()
            time.sleep(0.1)  # avoid race condition
        self.window.write_event_value('CONNECT', (err, is_wizard, self.msfcl))

    def msfrun(self, rc, log):
        metasploit.launch_metasploit(self.msfcl, rc, log)

    def hlfloadconfig(self, cfg):
        _asyncio.set_event_loop(self.async_loop)
        self.cfg = blockchain.load_config(cfg, loop=self.async_loop)

    def hlfstore(self, report, log):
        if self.cfg is not None:
            blockchain.store_report(self.cfg,
                                    report, log, loop=self.async_loop)

    def msfstop(self, stop):
        if stop:
            sgif = self.msfcnt is not None or self.vpncnt is not None
            if sgif:
                sgif_flag = threading.Event()
                sgif_thread = LoadingThread(sgif_flag, self.window,
                                            start_gif=False)
                sgif_thread.start()
            err = utils.shutdown(self.msfcnt, self.vpncnt)
            if sgif:
                sgif_flag.set()
                time.sleep(0.1)  # avoid race condition
            self.window.write_event_value('STOP', err)
        else:
            self.window.write_event_value('STOP', cst.NOERROR)
        self.msfcnt = None
        self.vpncnt = None


def color_scrollbar(window, *key, disable=False):
    abg = cst.C['lightblue']
    bg = cst.C['white']
    ebw = 1
    tc = cst.C['blue']
    rel = sg.RELIEF_SUNKEN
    if disable:
        abg = cst.C['white']
        ebw = 0
        tc = cst.C['white']
        rel = sg.RELIEF_FLAT
    for k in key:
        attr = 'vbar'
        if isinstance(window[k].Widget,
                      sg.PySimpleGUI.TkScrollableFrame):
            attr = 'vscrollbar'

        getattr(window[k].Widget, attr).configure(
            activebackground=abg, bg=bg,
            elementborderwidth=ebw, troughcolor=tc,
            relief=rel)

        if isinstance(window[k].Widget, sg.tk.scrolledtext.ScrolledText):
            window[k].Widget.configure(
                selectbackground=cst.C['darkblue'],
                inactiveselectbackground=cst.C['darkblue'])


def color_select_input(window, *args, bg=True):
    for wdgt in args:
        if type(window[wdgt].Widget) is sg.tk.Entry:
            window[wdgt].Widget.configure(selectbackground=cst.C['darkblue'],
                                          readonlybackground=cst.C['greyblue']
                                          if bg else None)


def autoauditor_window():
    mandatory_layout = [
        [sg.Text(font=cst.FNT_P, pad=cst.P_N_TB)],
        [sg.Text(cst.T_MAIN_LF, size=cst.T_DESC_SZ2, font=cst.FNT_B),
         sg.InputText(cst.DEF_MAIN_LF, key=cst.K_MAIN_IT_LF,
                      pad=cst.P_IT),
         Browser(key=cst.K_MAIN_LF_FB, tooltip=cst.TT_MAIN_FB,
                 target=cst.K_MAIN_IT_LF),
         Button(key=cst.K_MAIN_LFINFO, tooltip=cst.TT_MAIN_LF)],
        [sg.Text(cst.T_MAIN_LD, size=cst.T_DESC_SZ2, font=cst.FNT_B),
         sg.InputText(cst.DEF_MAIN_LD, key=cst.K_MAIN_IT_LD,
                      pad=cst.P_IT),
         Browser(key=cst.K_MAIN_LD_FB, tooltip=cst.TT_MAIN_DB,
                 target=cst.K_MAIN_IT_LD, folder=True),
         Button(key=cst.K_MAIN_LDINFO, tooltip=cst.TT_MAIN_LD)],
        [sg.Text(cst.T_MAIN_RC, size=cst.T_DESC_SZ2, font=cst.FNT_B),
         sg.InputText(cst.DEF_MAIN_RC, key=cst.K_MAIN_IT_RC,
                      pad=cst.P_IT),
         Browser(key=cst.K_MAIN_RC_FB, tooltip=cst.TT_MAIN_FB,
                 target=cst.K_MAIN_IT_RC),
         Button(key=cst.K_MAIN_RCINFO, tooltip=cst.TT_MAIN_RC)],
        [ImageCheckBox(key=cst.K_MAIN_RC_CB, pad=cst.P_N_R2),
         sg.Text(cst.T_MAIN_RC_CB, key=cst.K_MAIN_RC_CB_T,
                 font=cst.FNT_B, pad=cst.P_N_R3, enable_events=True)],
        [sg.Text(font=cst.FNT_P, pad=cst.P_N_TB)]
    ]

    vpn_layout = [
        [ImageCheckBox(key=cst.K_MAIN_VPN_CB, pad=cst.P_N_R2),
         sg.Text(cst.T_MAIN_VPN_CB, key=cst.K_MAIN_VPN_CB_T,
                 font=cst.FNT_B, pad=cst.P_N_R3, enable_events=True)],
        [sg.Text(cst.T_MAIN_VPN_CF, key=cst.K_MAIN_VPN_CF_T,
                 size=cst.T_DESC_SZ2, font=cst.FNT_B,
                 text_color=cst.C['grey']),
         sg.InputText(cst.DEF_MAIN_VPN_CF, key=cst.K_MAIN_IT_VPN_CF,
                      pad=cst.P_IT, disabled=True),
         Browser(key=cst.K_MAIN_VPN_CF_FB, tooltip=cst.TT_MAIN_FB,
                 target=cst.K_MAIN_IT_VPN_CF, disabled=True),
         Button(key=cst.K_MAIN_VPN_CFINFO,
                tooltip=cst.TT_MAIN_VPN_CF, disabled=True)],
        [sg.Text(font=cst.FNT_P, pad=cst.P_N_TB)]
    ]

    blockchain_layout = [
        [ImageCheckBox(key=cst.K_MAIN_BC_CB, pad=cst.P_N_R2),
         sg.Text(cst.T_MAIN_BC_CB, key=cst.K_MAIN_BC_CB_T,
                 font=cst.FNT_B, pad=cst.P_N_R3, enable_events=True)],
        [sg.Text(cst.T_MAIN_BC_CF, key=cst.K_MAIN_BC_CF_T,
                 size=cst.T_DESC_SZ2, font=cst.FNT_B,
                 text_color=cst.C['grey']),
         sg.InputText(cst.DEF_MAIN_BC_CF, key=cst.K_MAIN_IT_BC_CF,
                      pad=cst.P_IT, disabled=True),
         Browser(key=cst.K_MAIN_BC_CF_FB, tooltip=cst.TT_MAIN_FB,
                 target=cst.K_MAIN_IT_BC_CF, disabled=True),
         Button(key=cst.K_MAIN_BC_CFINFO,
                tooltip=cst.TT_MAIN_BC_CF, disabled=True)],
        [sg.Text(cst.T_MAIN_BC_LF, key=cst.K_MAIN_BC_LF_T,
                 size=cst.T_DESC_SZ2, font=cst.FNT_B,
                 text_color=cst.C['grey']),
         sg.InputText(cst.DEF_MAIN_BC_LF, key=cst.K_MAIN_IT_BC_LF,
                      pad=cst.P_IT, disabled=True),
         Browser(key=cst.K_MAIN_BC_LF_FB, tooltip=cst.TT_MAIN_FB,
                 target=cst.K_MAIN_IT_BC_LF, disabled=True),
         Button(key=cst.K_MAIN_BC_LFINFO,
                tooltip=cst.TT_MAIN_BC_LF, disabled=True)],
        [sg.Text(font=cst.FNT_P, pad=cst.P_N_TB)],
        [ImageCheckBox(key=cst.K_MAIN_SC_CB, pad=cst.P_N_R2, enabled=True),
         sg.Text(cst.T_MAIN_SC_CB, key=cst.K_MAIN_SC_CB_T,
                 font=cst.FNT_B, pad=cst.P_N_R3, enable_events=True)]
    ]

    button_layout = [
        [Button(key=cst.K_MAIN_RAA_B, tooltip=cst.TT_MAIN_RAA,
                image_data=cst.ICO_PLAY, image_size=cst.B_SZ48,
                pad=cst.P_T),
         sg.Text(size=cst.T_ACTION_SZ, pad=cst.P_N),
         Button(key=cst.K_MAIN_RBC_B, tooltip=cst.TT_MAIN_RBC,
                image_data=cst.ICO_BCKCHN, image_size=cst.B_SZ48,
                pad=cst.P_T),
         sg.Text(size=cst.T_ACTION_SZ, pad=cst.P_N),
         Button(key=cst.K_MAIN_WIZ_B, tooltip=cst.TT_MAIN_WIZ,
                image_data=cst.ICO_WIZ, image_size=cst.B_SZ48,
                pad=cst.P_T),
         sg.Text(size=cst.T_ACTION_SZ, pad=cst.P_N),
         Button(cst.K_MAIN_STP_B, tooltip=cst.TT_MAIN_STP,
                image_data=cst.ICO_STOP, image_size=cst.B_SZ48,
                pad=cst.P_T),
         ],
        [sg.Text(cst.T_MAIN_RAA, key=cst.K_MAIN_RAA_T,
                 size=cst.T_ACTION_SZ2, font=cst.FNT_B,
                 pad=cst.P_ACTION, justification=cst.J_C,
                 enable_events=True),
         sg.Text(cst.T_MAIN_RBC, key=cst.K_MAIN_RBC_T,
                 size=cst.T_ACTION_SZ2, font=cst.FNT_B,
                 pad=cst.P_ACTION, justification=cst.J_C,
                 enable_events=True),
         sg.Text(cst.T_MAIN_WIZ, key=cst.K_MAIN_WIZ_T,
                 size=cst.T_ACTION_SZ2, font=cst.FNT_B,
                 pad=cst.P_ACTION, justification=cst.J_C,
                 enable_events=True),
         sg.Text(cst.T_MAIN_STP, key=cst.K_MAIN_STP_T,
                 size=cst.T_ACTION_SZ2, font=cst.FNT_B,
                 pad=cst.P_ACTION, justification=cst.J_C,
                 enable_events=True)
         ],
        [sg.Frame(cst.T_N, [
            [sg.Text(size=cst.C_TLOG_SZ, pad=cst.P_N),
             ImageCheckBox(key=cst.K_MAIN_LOG_CB, image_on=cst.ICO_C_H,
                           image_off=cst.ICO_C_S, image_size=cst.B_SZ16)]
        ], border_width=cst.N_WDTH)],
        [sg.Multiline(key=cst.K_MAIN_LOG, size=cst.C_LOG_SZ,
                      font=cst.FNT_F, pad=cst.P_LOG,
                      background_color=cst.C['lightblue'], autoscroll=True,
                      visible=False, disabled=True)]
    ]
    autoauditor_layout = [
        [sg.Frame(cst.T_N, mandatory_layout, border_width=cst.N_WDTH)],
        [sg.Frame(cst.T_N, vpn_layout, border_width=cst.N_WDTH)],
        [sg.Frame(cst.T_N, blockchain_layout, border_width=cst.N_WDTH)],
        [sg.Frame(cst.T_N, button_layout, border_width=0,
                  element_justification=cst.J_C)]
    ]

    about_layout = [
        [sg.Text(key=cst.K_MAIN_ABOUT_P, font=cst.FNT_P, pad=cst.P_AB)],
        [sg.Text(cst.MAIN_ABOUT_NAME, font=cst.FNT_B)],
        [sg.Text(cst.MAIN_ABOUT_VER, font=cst.FNT_B)],
        [sg.Text(pad=cst.P_N_TB)],
        [sg.Text(cst.MAIN_ABOUT_AUTHOR)],
        [sg.Text(cst.MAIN_ABOUT_LAB)],
        [sg.Text(cst.MAIN_ABOUT_DEPT)],
        [sg.Text(cst.MAIN_ABOUT_UC3M)],
        [sg.Text(cst.MAIN_ABOUT_LOC)],
        [sg.Text(pad=cst.P_N_TB)],
        [sg.Text(cst.MAIN_ABOUT_ACK, justification=cst.J_C)],
        [sg.Text(pad=cst.P_N_TB)],
        [sg.Text(cst.MAIN_ABOUT_YEAR)],
    ]

    with open(cst.DEF_MAIN_LIC, 'r') as f:
        # fix double spaces in GNU LICENSE text
        gplv3_full = f.read().replace('.  ', '. ').replace('  ', '')

    license_layout = [
        [sg.Text(cst.COPYRIGHT, justification=cst.J_C)],
        [sg.Multiline(gplv3_full, key=cst.K_MAIN_LIC, size=cst.MAIN_LIC_C_SZ,
                      font=cst.FNT2, background_color=cst.C['lightblue'],
                      justification=cst.J_C)]
    ]

    layout = [
        [sg.TabGroup([
            [sg.Tab("AutoAuditor", autoauditor_layout,
                    element_justification=cst.J_C)],
            [sg.Tab("About", about_layout,
                    element_justification=cst.J_C)],
            [sg.Tab("License", license_layout,
                    element_justification=cst.J_C)]
        ], key=cst.K_MAIN_TAB, border_width=cst.N_WDTH,
                     enable_events=True,
                     tab_background_color=cst.C['lightblue'])]
    ]

    WIN[MN] = sg.Window("AutoAuditor", layout,
                        element_justification=cst.J_C,
                        icon=cst.ICO_M, finalize=True)

    # remove click animation
    def rem_click_anim(*key):
        for k in key:
            WIN[MN][k].Widget.configure(
                relief=sg.RELIEF_SUNKEN)

    rem_click_anim(cst.K_MAIN_RC_CB, cst.K_MAIN_VPN_CB,
                   cst.K_MAIN_BC_CB, cst.K_MAIN_SC_CB, cst.K_MAIN_LOG_CB)
    color_scrollbar(WIN[MN], cst.K_MAIN_LIC)
    color_scrollbar(WIN[MN], cst.K_MAIN_LOG, disable=True)

    WIN[MN].TKroot.option_add('*TCombobox*Listbox*selectBackground',
                              cst.C['lightblue'])
    cstm_s = sg.ttk.Style()
    cstm_s.map('TCombobox', background=[('hover', cst.C['lightblue']),
                                        ('disabled', cst.C['greyblue'])])
    # fix combo color other desktop environments
    cstm_s.configure('TCombobox', arrowcolor=cst.C['white'],
                     background=cst.C['blue'])
    cstm_s.map('Vertical.TScrollbar',
               background=[('active', cst.C['lightblue'])])
    cstm_s.configure('Vertical.TScrollbar',
                     troughcolor=cst.C['white'], background=cst.C['blue'],
                     arrowcolor=cst.C['white'])
    color_select_input(WIN[MN], cst.K_MAIN_IT_LF, cst.K_MAIN_IT_LD,
                       cst.K_MAIN_IT_RC, cst.K_MAIN_IT_VPN_CF,
                       cst.K_MAIN_IT_BC_CF, cst.K_MAIN_IT_BC_LF)


def wizard_window(cur_modules):
    mod_layout = [
        [sg.Frame(cst.T_N, [
            [sg.InputText(f"Module {i}", key=f'{cst.K_WIZ_MNAME}{i}',
                          size=cst.T_DESC_SZ5, font=cst.FNT_B,
                          disabled_readonly_background_color=cst.C['white'],
                          readonly=True, border_width=cst.N_WDTH),
             Button(key=f'{cst.K_WIZ_MEDIT}{i}', tooltip=cst.TT_WIZ_MEDIT,
                    image_data=cst.ICO_EDIT, pad=cst.P_MOD),
             Button(key=f'{cst.K_WIZ_MREM}{i}', tooltip=cst.TT_WIZ_MREM,
                    image_data=cst.ICO_REM),
             Button(key=f'{cst.K_WIZ_MINFO}{i}', tooltip=cst.TT_WIZ_MINFO,
                    image_data=cst.ICO_INFO, pad=cst.P_MOD2)
             ]], key=f'{cst.K_WIZ_MFRAME}{i}', pad=cst.P_N_LRT,
                  border_width=cst.N_WDTH, element_justification=cst.J_C,
                  visible=False)]
        for i in range(cst.MAX_MODS)]

    wizard_layout = [
        [sg.Text(pad=cst.P_N_TB)],
        [sg.Frame(cst.T_N, [
            [sg.Text(cst.T_WIZ_MTYPE, size=cst.T_DESC_SZ, font=cst.FNT_B),
             sg.DropDown(cst.MOD_TYPES, key=cst.K_WIZ_MODT,
                         size=cst.T_MODDD_SZ, pad=cst.P_DD,
                         enable_events=True, readonly=True),
             Button(key=cst.T_N, pad=cst.P_MN, disabled=True, visible=False)],
            [sg.Text(cst.T_WIZ_MNAME, size=cst.T_DESC_SZ, font=cst.FNT_B),
             sg.DropDown(cst.T_N, key=cst.K_WIZ_MODN,
                         size=cst.T_MODDD_SZ, pad=cst.P_DD,
                         enable_events=True, readonly=True),
             Button(key=cst.K_WIZ_MODN_INFO, tooltip=cst.TT_WIZ_MNAME,
                    disabled=True, pad=cst.P_MN)]], border_width=cst.N_WDTH)],
        [sg.Text(pad=cst.P_N)],
        [sg.Column(mod_layout, key=cst.K_WIZ_MCOL, size=cst.C_SZ,
                   pad=cst.P_N_RTB, justification=cst.J_C,
                   scrollable=True, vertical_scroll_only=True,
                   element_justification=cst.J_C)],
        [sg.Text(font=cst.FNT_P, pad=cst.P_N)],
        [Button(key=cst.K_WIZ_MADD, tooltip=cst.TT_WIZ_MADD,
                image_data=cst.ICO_ADD, image_size=cst.B_SZ48)],
        [sg.Text(font=cst.FNT_P, pad=cst.P_N_TB)],
        [sg.Button(cst.T_WIZ_GEN, key=cst.K_WIZ_GEN),
         sg.Button(cst.T_WIZ_EXIT, key=cst.K_WIZ_EXIT)],
        [sg.Text(font=cst.FNT_P, pad=cst.P_N_TB)]
    ]

    if WIN[WZ] is not None:
        WIN[WZ].close()

    WIN[WZ] = sg.Window(cst.T_WIZ_TIT, wizard_layout,
                        element_justification=cst.J_C,
                        icon=cst.ICO_W, finalize=True)

    for i in range(cst.MAX_MODS):
        WIN[WZ][f'{cst.K_WIZ_MFRAME}{i}'].hide_row()

    color_select_input(WIN[WZ], *[f'{cst.K_WIZ_MNAME}{i}'
                                  for i in range(cst.MAX_MODS)], bg=False)

    if cur_modules:
        for cm in cur_modules.values():
            WIN[WZ][f'{cst.K_WIZ_MNAME}{cm.ticket()}'](
                value=f"Module {cm.mtype()}/{cm.mname()}")
            WIN[WZ][f'{cst.K_WIZ_MFRAME}{cm.ticket()}'](visible=True)
            WIN[WZ][f'{cst.K_WIZ_MFRAME}{cm.ticket()}'].unhide_row()
        # Update column scrollbar
        WIN[WZ].visibility_changed()
        WIN[WZ][cst.K_WIZ_MCOL].contents_changed()
        WIN[WZ][cst.K_WIZ_MCOL].Widget.canvas.yview_moveto(
            999)  # set scrollbar to last element

    if len(cur_modules) <= cst.C_EL:
        color_scrollbar(WIN[WZ], cst.K_WIZ_MCOL, disable=True)
    else:
        color_scrollbar(WIN[WZ], cst.K_WIZ_MCOL)


def mopts_window(module, edit=False):
    opts, ropts = module.options()

    current_opts = module.mopts()
    if current_opts:
        for kcopt, vcopt in current_opts.items():
            opts[kcopt] = vcopt

    scrollable = len(opts) > cst.C_OPTS
    hidden = f"{module.ticket()}:{'new' if not edit else 'edit'}"
    opt_layout = [
        [sg.Text(hidden, key=cst.K_MOPTS_ID,
                 font=cst.FNT_P, text_color=cst.C['white'],
                 pad=cst.P_N_TB)],
        [sg.Text(f"{module.mtype()}/{module.mname()}",
                 key=cst.K_MOPTS_TIT,
                 font=cst.FNT_B)],
        [sg.Frame(cst.T_N, [
            [sg.Text(size=cst.T_DESC_SZ6, font=cst.FNT_P, pad=cst.P_N)],
            [sg.Text(cst.T_MOPTS_HNAME, size=cst.T_HEAD_ONAME_SZ,
                     font=cst.FNT_B, pad=cst.P_HEAD_ONAME),
             sg.Text(cst.T_MOPTS_HVAL, size=cst.T_HEAD_OVAL_SZ,
                     font=cst.FNT_B, pad=cst.P_HEAD_OVAL),
             sg.Text(cst.T_MOPTS_HREQ, size=cst.T_HEAD_OREQ_SZ,
                     font=cst.FNT_B, pad=cst.P_HEAD_OREQ),
             sg.Text(cst.T_MOPTS_HINFO, font=cst.FNT_B,
                     pad=cst.P_HEAD_OINFO)]
        ], pad=cst.P_N_L, border_width=cst.N_WDTH)],
        [sg.Column([
            [sg.Frame(cst.T_N, [
                [sg.InputText(opt, key=f'{cst.K_MOPTS}{idx}',
                              size=cst.T_DESC_SZ, pad=cst.P_IT2,
                              border_width=cst.N_WDTH,
                              disabled_readonly_background_color=(
                                  cst.C['white']),
                              readonly=True),
                 sg.InputText(str(opts[opt]), key=f'{cst.K_MOPTS_VAL}{idx}',
                              size=cst.T_DESC_SZ4,
                              pad=cst.P_IT2) if (opt != 'ACTION' and
                                                 module.opt_info(
                                                     opt)['type'] != 'enum')
                 else sg.DropDown(module.opt_info(opt)['enums'],
                                  key=f'{cst.K_MOPTS_VAL}{idx}',
                                  default_value=opts[opt],
                                  size=cst.T_DESC_SZ3, pad=cst.P_IT2DD,
                                  readonly=True) if opt != 'ACTION'
                 else sg.DropDown(list(module.opt_info(opt).values()),
                                  key=f'{cst.K_MOPTS_VAL}{idx}',
                                  default_value=opts[opt],
                                  size=cst.T_DESC_SZ3, pad=cst.P_IT2DD,
                                  readonly=True),
                 sg.Text(cst.T_MOPTS_RY if opt in ropts
                         else cst.T_MOPTS_RN,
                         size=cst.T_HEAD_OREQ_SZ, pad=cst.P_IT8),
                 Button(key=f'{cst.K_MOPTS_INFO}{idx}',
                        tooltip=module.opt_desc(opt), pad=cst.P_IT7)]
            ], pad=cst.P_N_TB3, border_width=cst.N_WDTH)]
            for idx, opt in enumerate(opts)],
                   key=cst.K_MOPTS_COL,
                   size=cst.C_SZ2 if scrollable
                   else cst.column_size(len(opts)),
                   scrollable=scrollable, vertical_scroll_only=True),
         ]]

    if module.has_payloads():
        pay_exist = module.payload is not None
        opt_layout.extend(
            [
                [sg.Frame(cst.T_N, [
                    [sg.Text(size=cst.T_DESC_SZ6,
                             font=cst.FNT_P, pad=cst.P_N)],
                    [sg.Text(cst.T_MOPTS_PAY, size=cst.T_DESC_SZ,
                             pad=cst.P_IT3),
                     sg.DropDown([''] + module.payloads(), key=cst.K_MOPTS_PDD,
                                 default_value=(module.payload.mname()
                                                if pay_exist else ''),
                                 size=cst.T_DESC_SZ3, pad=cst.P_IT4,
                                 readonly=True, disabled=pay_exist,
                                 enable_events=True),
                     Button(key=cst.K_MOPTS_PADD, image_data=cst.ICO_ADD_S,
                            tooltip=cst.TT_MOPTS_PADD, pad=cst.P_IT5,
                            disabled=pay_exist),
                     Button(key=cst.K_MOPTS_PEDIT, tooltip=cst.TT_MOPTS_PEDIT,
                            image_data=cst.ICO_EDIT, pad=cst.P_IT5,
                            disabled=not pay_exist),
                     Button(key=cst.K_MOPTS_PREM, tooltip=cst.TT_MOPTS_PREM,
                            image_data=cst.ICO_REM, pad=cst.P_IT5,
                            disabled=not pay_exist),
                     Button(key=cst.K_MOPTS_PINFO, tooltip=cst.TT_MOPTS_PINFO,
                            pad=cst.P_IT6, disabled=not pay_exist)]
                ], pad=cst.P_N_LRB, border_width=cst.N_WDTH)]])

    opt_layout.extend([
        [sg.Text(font=cst.FNT_P, pad=cst.P_N_TB)],
        [sg.Button('Accept', key=cst.K_MOPTS_ACPT),
         sg.Button('Cancel', key=cst.K_MOPTS_CNCL)]])

    WIN[MO][module.ticket()] = sg.Window(
        cst.T_MOPTS_TIT, opt_layout,
        element_justification=cst.J_C,
        icon=cst.ICO_MO, finalize=True)

    color_select_input(WIN[MO][module.ticket()],
                       *[f'{cst.K_MOPTS_VAL}{it}'
                         for it in range(len(opts))])

    color_select_input(WIN[MO][module.ticket()],
                       *[f'{cst.K_MOPTS}{it}'
                         for it in range(len(opts))], bg=False)

    if scrollable:
        color_scrollbar(WIN[MO][module.ticket()], cst.K_MOPTS_COL)


def popts_window(module, mstate, pname=''):
    if pname:
        module.payload = pname
    popts, propts = module.payload.options()

    current_opts = module.payload.mopts()
    if current_opts:
        for kcopt, vcopt in current_opts.items():
            popts[kcopt] = vcopt

    scrollable = len(popts) > cst.C_OPTS

    hidden = f"{module.ticket()}:{mstate}:{'new' if pname else 'edit'}"

    popt_layout = [
        [sg.Text(hidden, key=cst.K_POPTS_ID,
                 font=cst.FNT_P, text_color=cst.C['white'], pad=cst.P_N_TB)],
        [sg.Text(f"{module.mtype()}/{module.mname()}",
                 key=cst.K_MOPTS_TIT,
                 font=cst.FNT_B)],
        [sg.Text(module.payload.mname(),
                 key=cst.K_POPTS_TITLE)],
        [sg.Frame(cst.T_N, [
            [sg.Text(size=cst.T_DESC_SZ6, font=cst.FNT_P, pad=cst.P_N)],
            [sg.Text(cst.T_MOPTS_HNAME, size=cst.T_HEAD_ONAME_SZ,
                     font=cst.FNT_B, pad=cst.P_HEAD_ONAME),
             sg.Text(cst.T_MOPTS_HVAL, size=cst.T_HEAD_OVAL_SZ,
                     font=cst.FNT_B, pad=cst.P_HEAD_OVAL),
             sg.Text(cst.T_MOPTS_HREQ, size=cst.T_HEAD_OREQ_SZ,
                     font=cst.FNT_B, pad=cst.P_HEAD_OREQ),
             sg.Text(cst.T_MOPTS_HINFO, font=cst.FNT_B,
                     pad=cst.P_HEAD_OINFO)]
        ], border_width=cst.N_WDTH, pad=cst.P_N_L)],
        [sg.Column([
            [sg.Frame(cst.T_N, [
                [sg.InputText(popt, key=f'{cst.K_POPTS}{idx}',
                              size=cst.T_DESC_SZ, pad=cst.P_IT2,
                              border_width=cst.N_WDTH,
                              disabled_readonly_background_color=(
                                  cst.C['white']),
                              readonly=True),
                 sg.InputText(str(popts[popt]), key=f'{cst.K_POPTS_VAL}{idx}',
                              size=cst.T_DESC_SZ4, pad=cst.P_IT2),
                 sg.Text(cst.T_MOPTS_RY if popt in propts
                         else cst.T_MOPTS_RN,
                         size=cst.T_HEAD_OREQ_SZ, pad=cst.P_IT8),
                 Button(key=f'{cst.K_POPTS_INFO}{idx}',
                        tooltip=module.payload.opt_desc(popt), pad=cst.P_IT7)]
            ], pad=cst.P_N_TB3, border_width=cst.N_WDTH)]
            for idx, popt in enumerate(popts)],
                   key=cst.K_POPTS_COL,
                   size=cst.C_SZ2 if scrollable
                   else cst.column_size(len(popts)),
                   scrollable=scrollable, vertical_scroll_only=True),
         ],
        [sg.Text(pad=cst.P_N_TB)],
        [sg.Button('Accept', key=cst.K_POPTS_ACPT),
         sg.Button('Cancel', key=cst.K_POPTS_CNCL)]]

    WIN[PO][module.ticket()] = sg.Window(
        cst.T_POPTS_TIT, popt_layout,
        element_justification=cst.J_C,
        icon=cst.ICO_PO, finalize=True)

    color_select_input(WIN[PO][module.ticket()],
                       *[f'{cst.K_POPTS_VAL}{it}'
                         for it in range(len(popts))])

    color_select_input(WIN[PO][module.ticket()],
                       *[f'{cst.K_POPTS}{it}'
                         for it in range(len(popts))], bg=False)

    if scrollable:
        color_scrollbar(WIN[PO][module.ticket()], cst.K_POPTS_COL)


def info_window(module, ticket=None):
    if isinstance(module, Module):
        minfo = module.info()
        absname = f"{module.mtype()}/{module.mname()}"
    else:
        minfo = wizard.get_module_info(module)
        absname = f"{module.moduletype}/{module.modulename}"

    minfo_lay = [
        [sg.Text(font=cst.FNT_P, pad=cst.P_N_TB)],
        [sg.Text(absname,
                 font=cst.FNT_B)],
        [sg.Text(font=cst.FNT_P, pad=cst.P_N_TB)]
    ] + [
        [sg.Column([
            [sg.Frame(cst.T_N, [
                [sg.Multiline(mi,
                              key=f'{cst.K_O_ML}{idx}',
                              size=cst.T_INFO_SZ, font=cst.FNT_B,
                              border_width=cst.N_WDTH,
                              background_color=cst.C['white'],
                              disabled=True),
                 sg.Multiline(str(minfo[mi]),
                              key=f'{cst.K_OINFO_ML}{idx}',
                              size=cst.T_INFO_SZ4,
                              background_color=cst.C['lightblue'],
                              disabled=True)]
                for idx, mi in enumerate(minfo)],
                      border_width=cst.N_WDTH)]
        ], key=cst.K_MINFO_COL, size=cst.C_SZ3,
                   element_justification=cst.J_C,
                   scrollable=True, vertical_scroll_only=True)]
    ] + [[sg.OK()]]

    win = WIN[POP][WZ]
    if ticket is not None:
        if ticket not in WIN[POP][MO]:
            WIN[POP][MO][ticket] = []
        win = WIN[POP][MO][ticket]

    win.append(
        sg.Window(cst.T_MOPTS_PINFO_TIT if ticket is not None
                  else cst.T_WIZ_MINFO_TIT,
                  minfo_lay, element_justification=cst.J_C,
                  icon=cst.ICO_PI if ticket is not None else cst.ICO_MI,
                  finalize=True))
    color_scrollbar(win[-1], cst.K_MINFO_COL)
    color_scrollbar(win[-1],
                    *[f'{cst.K_O_ML}{idx}' for idx in range(len(minfo))],
                    disable=True)
    color_scrollbar(win[-1],
                    *[f'{cst.K_OINFO_ML}{idx}' for idx in range(len(minfo))])
    for idx in range(len(minfo)):
        win[-1][f'{cst.K_O_ML}{idx}'].Widget.config(
            highlightbackground=cst.C['white'], highlightcolor=cst.C['white'])
        win[-1][f'{cst.K_OINFO_ML}{idx}'].Widget.config(
            highlightbackground=cst.C['white'], highlightcolor=cst.C['white'])


def oinfo_window(module, option, payload=False):
    if payload:
        info = module.payload.opt_info(option)
        win = WIN[POP][PO]
        tckt = module.payload.ticket()
    else:
        info = module.opt_info(option)
        win = WIN[POP][MO]
        tckt = module.ticket()

    info_lay = [
        [sg.Text(font=cst.FNT_P, pad=cst.P_N_TB)],
        [sg.Text(option, font=cst.FNT_B)],
        [sg.Text(font=cst.FNT_P, pad=cst.P_N_TB)]
    ] + [[sg.Frame(cst.T_N,
                   [[sg.Multiline(opt,
                                  key=f'{cst.K_O_ML}{idx}',
                                  size=cst.T_INFO_SZ2, font=cst.FNT_B,
                                  border_width=cst.N_WDTH,
                                  background_color=cst.C['white'],
                                  disabled=True),
                     sg.Multiline(str(info[opt]),
                                  key=f'{cst.K_OINFO_ML}{idx}',
                                  size=cst.T_INFO_SZ3,
                                  background_color=cst.C['lightblue'],
                                  disabled=True)]
                    for idx, opt in enumerate(info)],
                   border_width=cst.N_WDTH)]
         ] + [[sg.OK()]]

    if tckt not in win:
        win[tckt] = []
    win[tckt].append(
        sg.Window(cst.T_POPTS_INFO_TIT if payload else cst.T_MOPTS_INFO_TIT,
                  info_lay, element_justification=cst.J_C,
                  icon=cst.ICO_POI if payload else cst.ICO_MOI,
                  finalize=True))

    color_scrollbar(win[tckt][-1],
                    *[f'{cst.K_O_ML}{idx}' for idx in range(len(info))],
                    disable=True)
    color_scrollbar(win[tckt][-1],
                    *[f'{cst.K_OINFO_ML}{idx}' for idx in range(len(info))])
    for idx in range(len(info)):
        win[tckt][-1][f'{cst.K_O_ML}{idx}'].Widget.config(
            highlightbackground=cst.C['white'], highlightcolor=cst.C['white'])
        win[tckt][-1][f'{cst.K_OINFO_ML}{idx}'].Widget.config(
            highlightbackground=cst.C['white'], highlightcolor=cst.C['white'])


def oerror_window(opt_window, invalid_missing, payload=False):
    invmis_lay = []
    if invalid_missing['inv']:
        invmis_lay.extend([
            [sg.Text("Invalid", font=cst.FNT_B)],
            [sg.Multiline(
                "\n".join(
                    [f"{opt}: {val}"
                     for opt, val in invalid_missing['inv'].values()]),
                key=f'{cst.K_OINV_ML}',
                size=cst.T_INFO_SZ5, font=cst.FNT_F,
                background_color=cst.C['lightblue'],
                disabled=True)]])
    if invalid_missing['inv'] and invalid_missing['mis']:
        invmis_lay.extend([
            [sg.Text(font=cst.FNT_P)]])
    if invalid_missing['mis']:
        invmis_lay.extend([
            [sg.Text("Missing", font=cst.FNT_B)],
            [sg.Multiline(
                "\n".join(
                    [f"{opt}: {val}"
                     for opt, val in invalid_missing['mis'].values()]),
                key=f'{cst.K_OMIS_ML}',
                size=cst.T_INFO_SZ5, font=cst.FNT_F,
                background_color=cst.C['lightblue'],
                disabled=True)]])
    invmis_lay.extend([
        [sg.Text(font=cst.FNT_P)],
        [sg.OK(button_color=cst.B_C_ERR)]])

    for idx in invalid_missing['inv']:
        opt_window[f'{cst.K_POPTS if payload else cst.K_MOPTS}{idx}'](
            text_color=cst.C['red'])

    for idx in invalid_missing['mis']:
        opt_window[f'{cst.K_POPTS if payload else cst.K_MOPTS}{idx}'](
            text_color=cst.C['red'])

    tmpw = sg.Window("Error", invmis_lay,
                     element_justification=cst.J_C,
                     keep_on_top=True,
                     icon=cst.ICO, finalize=True)
    if invalid_missing['inv']:
        color_scrollbar(tmpw, cst.K_OINV_ML)
        color_select_input(tmpw, cst.K_OINV_ML)
    if invalid_missing['mis']:
        color_scrollbar(tmpw, cst.K_OMIS_ML)
        color_select_input(tmpw, cst.K_OMIS_ML)
    tmpw.read(close=True)


def help_window(title, text, path):
    hw = sg.Window(title, [
        [sg.Text(text)],
        [sg.Text(font=cst.FNT_P, pad=cst.P_N_TB)],
        [sg.Text("Default:", font=cst.FNT_B),
         sg.InputText(path, key=cst.K_MAIN_INFO_DEF, disabled=True)],
        [sg.Text(font=cst.FNT_P, pad=cst.P_N_TB)],
        [sg.OK()]
    ], element_justification=cst.J_C, icon=cst.ICO_I, finalize=True)
    color_select_input(hw, cst.K_MAIN_INFO_DEF)
    return hw


def main():
    def switch_state(win, checkbox, *elems):
        for el in elems:
            if isinstance(win[el], (sg.InputText, sg.Button)):
                win[el](disabled=win[checkbox].enabled)
            else:
                win[el](
                    text_color=cst.C['grey'] if win[checkbox].enabled
                    else cst.C['black'])
        win[checkbox].switch()

    def shrink_enlarge_window(console, console_cb, cons_size, ncons_size):
        console(visible=not console_cb.enabled)
        console_cb.switch()
        if console_cb.enabled:
            WIN[MN].size = cons_size
        else:
            WIN[MN].size = ncons_size
        WIN[MN].visibility_changed()

    def is_popup(window):
        return (window in WIN[POP][MN] or window in WIN[POP][WZ] or
                window in [win for wtckt in WIN[POP][MO]
                           for win in WIN[POP][MO][wtckt]] or
                window in [win for wtckt in WIN[POP][PO]
                           for win in WIN[POP][PO][wtckt]])

    def close_popups(ticket, *wtype):
        for wt in wtype:
            if isinstance(WIN[POP][wt], list):
                for win in WIN[POP][wt]:
                    win.close()
                WIN[POP][wt] = []
            else:
                if ticket is None:
                    for wtckt in WIN[POP][wt]:
                        for win in WIN[POP][wt][wtckt]:
                            win.close()
                    WIN[POP][wt] = {}
                else:
                    if ticket in WIN[POP][wt]:
                        for win in WIN[POP][wt][ticket]:
                            win.close()
                        WIN[POP][wt][ticket] = []

    def close_wizard():
        close_popups(None, WZ, MO, PO)

        for win in WIN[PO]:
            WIN[PO][win].close()
        WIN[PO] = {}

        for win in WIN[MO]:
            WIN[MO][win].close()
        WIN[MO] = {}

        if WIN[WZ] is not None:
            WIN[WZ].close()
            WIN[WZ] = None

    def parse_rc_file(rcfile, client, ticket_system):
        with open(rcfile, 'r') as f:
            rc = json.load(f)
        modules = {}
        for mtype in rc:
            for mname in rc[mtype]:
                for rcmod in rc[mtype][mname]:
                    ticket = ticket_system.get_ticket()
                    mod = Module(client, mtype, mname, ticket)
                    mopts = mod.mopts()
                    for rcmopt in rcmod:
                        if rcmopt == 'PAYLOAD':
                            mod.payload = rcmod['PAYLOAD']['NAME']
                            popts = mod.payload.mopts()
                            for popt in rcmod['PAYLOAD']['OPTIONS']:
                                popts[popt] = rcmod['PAYLOAD']['OPTIONS'][popt]
                        else:
                            mopts[rcmopt] = rcmod[rcmopt]
                    modules[ticket] = mod
        return modules

    def dump_modules(mod_list):
        mod_dict = {}
        for mod in mod_list.values():
            mtype = mod.mtype()
            mname = mod.mname()
            if mtype not in mod_dict:
                mod_dict[mtype] = {}
            if mname not in mod_dict[mtype]:
                mod_dict[mtype][mname] = []
            mod_dict[mtype][mname].append(mod.gen_dict())
        return mod_dict

    def gen_tmp_opts(window, module, payload=False):
        if payload:
            options, _ = module.payload.options()
        else:
            options, _ = module.options()

        tmp_opts = {}
        for idx, opt in enumerate(options):
            opt_val = utils.correct_type(
                window[(f'{cst.K_POPTS_VAL if payload else cst.K_MOPTS_VAL}'
                       f'{idx}')].Get(),
                module.payload.opt_info(
                    window[(f'{cst.K_POPTS}{idx}')].Get()
                ) if payload else
                module.opt_info(
                    window[(f'{cst.K_MOPTS}{idx}')].Get())
            )

            if options[opt] != opt_val:
                tmp_opts[idx] = (opt, opt_val)

        inv_miss = {'inv': {}, 'mis': {}}
        for kidx, vopt in tmp_opts.items():
            if isinstance(vopt[1], str):
                if vopt[1].startswith('Invalid'):
                    inv_miss['inv'][kidx] = (vopt[0], vopt[1].split('. ')[1])
                elif vopt[1].startswith('Missing'):
                    inv_miss['mis'][kidx] = (vopt[0], vopt[1].split('. ')[1])

        return tmp_opts, inv_miss

    autoauditor_window()

    win_out_sz = None
    win_out_sz_hidden = None

    mtype = None
    mname = None

    modules = {}
    tmp_modules = {}

    msfcl = None

    def get_module(ticket, modtype):
        search = modules
        if modtype == 'new':
            search = tmp_modules
        try:
            mod = search[ticket]
        except KeyError:
            print((f"Error, could not find ticket in "
                   f"{'' if modtype == 'edit' else 'tmp_'}modules dict: "
                   f"{search}."))
        else:
            return mod

    def rm_cancel_mod(ticket, remove=False):
        ts.return_ticket(ticket)
        search = tmp_modules
        if remove:
            search = modules
        try:
            del search[ticket]
        except KeyError:
            print((f"Error: Could not find module "
                   f"in {'' if remove else 'tmp_'}modules dict."))

    wiz_medit_re = re.compile(cst.K_WIZ_MEDIT+r'\d+')
    wiz_mrem_re = re.compile(cst.K_WIZ_MREM+r'\d+')
    wiz_minfo_re = re.compile(cst.K_WIZ_MINFO+r'\d+')
    mopts_info_re = re.compile(cst.K_MOPTS_INFO + r'\d+')
    popts_info_re = re.compile(cst.K_POPTS_INFO + r'\d+')

    ts = TicketSystem(cst.MAX_MODS)

    cmd_queue = queue.Queue()
    cmd_event = threading.Event()
    cmd_thread = AutoauditorThread(WIN[MN], cmd_queue, cmd_event)
    cmd_thread.start()

    gif = None
    job_run = False

    while True:
        window, event, values = sg.read_all_windows()
        # print(window.Title, event)

        if window == sg.WIN_CLOSED:
            cmd_event.set()
            break

        if is_popup(window):
            window.close()

        if window == WIN[MN]:
            if event == sg.WIN_CLOSED:
                break

            if not window[cst.K_MAIN_LOG_CB].enabled and \
               win_out_sz_hidden is None:
                win_out_sz_hidden = window.size

            if window[cst.K_MAIN_LOG_CB].enabled and \
               win_out_sz is None:
                win_out_sz = window.size

            if event == cst.K_MAIN_TAB:
                if values[cst.K_MAIN_TAB] == 'License':
                    lic_sz = cst.MAIN_LIC_C_H
                    if window[cst.K_MAIN_LOG_CB].enabled:
                        lic_sz = cst.MAIN_LIC_C_H2
                    window[cst.K_MAIN_LIC].Widget.configure(
                        height=lic_sz)

                elif values[cst.K_MAIN_TAB] == 'About':
                    fontp = cst.FNT_P
                    if window[cst.K_MAIN_LOG_CB].enabled:
                        fontp = cst.FNT_P2
                    window[cst.K_MAIN_ABOUT_P](font=fontp)
                else:
                    window[cst.K_MAIN_IT_LF].Widget.select_clear()

            if event in (cst.K_MAIN_RC_CB, cst.K_MAIN_RC_CB_T):
                switch_state(window, cst.K_MAIN_RC_CB)

            if event in (cst.K_MAIN_VPN_CB, cst.K_MAIN_VPN_CB_T):
                switch_state(window, cst.K_MAIN_VPN_CB,
                             cst.K_MAIN_VPN_CF_T, cst.K_MAIN_IT_VPN_CF,
                             cst.K_MAIN_VPN_CF_FB, cst.K_MAIN_VPN_CFINFO)

            if event in (cst.K_MAIN_BC_CB, cst.K_MAIN_BC_CB_T):
                switch_state(window, cst.K_MAIN_BC_CB,
                             cst.K_MAIN_BC_CF_T, cst.K_MAIN_IT_BC_CF,
                             cst.K_MAIN_BC_CF_FB, cst.K_MAIN_BC_CFINFO,
                             cst.K_MAIN_BC_LF_T, cst.K_MAIN_IT_BC_LF,
                             cst.K_MAIN_BC_LF_FB, cst.K_MAIN_BC_LFINFO)

            if event in (cst.K_MAIN_SC_CB, cst.K_MAIN_SC_CB_T):
                switch_state(window, cst.K_MAIN_SC_CB)

            if event == cst.K_MAIN_LFINFO:
                WIN[POP][MN].append(
                    help_window(cst.T_MAIN_LF,
                                "Absolute/Relative path to "
                                "autoauditor log output file.",
                                cst.DEF_MAIN_LF))

            if event == cst.K_MAIN_LDINFO:
                WIN[POP][MN].append(
                    help_window(cst.T_MAIN_LD,
                                "Absolute/Relative path to "
                                "gathered data output directory.",
                                cst.DEF_MAIN_LD))

            if event == cst.K_MAIN_RCINFO:
                WIN[POP][MN].append(
                    help_window(cst.T_MAIN_RC,
                                "Absolute/Relative path to "
                                "resource script file.",
                                cst.DEF_MAIN_RC))

            if event == cst.K_MAIN_VPN_CFINFO:
                WIN[POP][MN].append(
                    help_window(cst.T_MAIN_VPN_CF,
                                "Absolute/Relative path to "
                                "OpenVPN configuration file.",
                                cst.DEF_MAIN_VPN_CF))

            if event == cst.K_MAIN_BC_CFINFO:
                WIN[POP][MN].append(
                    help_window(cst.T_MAIN_BC_CF,
                                "Absolute/Relative path to "
                                "blockchain network configuration file.",
                                cst.DEF_MAIN_BC_CF))

            if event == cst.K_MAIN_BC_LFINFO:
                WIN[POP][MN].append(
                    help_window(cst.T_MAIN_BC_LF,
                                "Absolute/Relative path to "
                                "blockchain log output file.",
                                cst.DEF_MAIN_BC_LF))

            if event == cst.K_MAIN_LOG_CB:
                shrink_enlarge_window(window[cst.K_MAIN_LOG],
                                      window[cst.K_MAIN_LOG_CB],
                                      win_out_sz,
                                      win_out_sz_hidden)

            if event in (cst.K_MAIN_RAA_B, cst.K_MAIN_RAA_T):
                if not job_run:
                    error = False
                    utils.set_logger(window)

                    lf = window[cst.K_MAIN_IT_LF].Get()
                    ld = window[cst.K_MAIN_IT_LD].Get()

                    errcode = utils.check_file_dir(lf, ld)
                    if errcode is not None:
                        Window(f"Log file/directory path "
                               f"cannot be created: {errcode}.")
                        error = True

                    rc = window[cst.K_MAIN_IT_RC].Get()
                    if not os.path.isfile(rc):
                        Window(f"File {rc} does not exist.")
                        error = True

                    if window[cst.K_MAIN_VPN_CB].enabled:
                        vpncf = window[cst.K_MAIN_IT_VPN_CF].Get()
                        if not os.path.isfile(vpncf):
                            Window(f"File {vpncf} does not exist.")
                            error = True

                    if window[cst.K_MAIN_BC_CB].enabled:
                        hc = window[cst.K_MAIN_IT_BC_CF].Get()
                        if not os.path.isfile(hc):
                            Window(f"File {hc} does not exist.")
                            error = True

                        ho = window[cst.K_MAIN_IT_BC_LF].Get()
                        errcode = utils.check_file_dir(ho)
                        if errcode is not None:
                            Window(f"File path {ho} "
                                   f"cannot be created: {errcode}.")
                            error = True

                    if not error:
                        if not window[cst.K_MAIN_LOG_CB].enabled:
                            shrink_enlarge_window(
                                window[cst.K_MAIN_LOG],
                                window[cst.K_MAIN_LOG_CB],
                                win_out_sz,
                                win_out_sz_hidden)

                        if window[cst.K_MAIN_VPN_CB].enabled:
                            cmd_queue.put(('vpnstart',
                                           (vpncf,
                                            False)))  # stop

                        cmd_queue.put(('msfstart',
                                       (ld,
                                        window[cst.K_MAIN_VPN_CB].enabled,
                                        False)))  # stop
                        cmd_queue.put(('msfconnect',
                                       (cst.DEF_MSFRPC_PWD,
                                        False)))  # wizard
                        cmd_queue.put(('msfrun', (rc, lf)))

                        if window[cst.K_MAIN_BC_CB].enabled:
                            cmd_queue.put(('hlfloadconfig', (hc,)))
                            cmd_queue.put(('hlfstore', (lf, ho)))

                        cmd_queue.put(('msfstop',
                                       (window[cst.K_MAIN_SC_CB].enabled,)
                                       ))

                        job_run = True

            if event in (cst.K_MAIN_RBC_B, cst.K_MAIN_RBC_T):
                if not job_run:
                    error = False
                    utils.set_logger(window)

                    ld = window[cst.K_MAIN_IT_LD].Get()
                    lf = window[cst.K_MAIN_IT_LF].Get()

                    if not os.path.isfile(lf):
                        Window("Autoauditor log does not exist.")
                        error = True

                    errcode = utils.check_file_dir(lf, ld)
                    if errcode is not None:
                        Window(f"Log file/directory path "
                               f"cannot be created: {errcode}.")
                        error = True

                    if window[cst.K_MAIN_VPN_CB].enabled:
                        vpncf = window[cst.K_MAIN_IT_VPN_CF].Get()
                        if not os.path.isfile(vpncf):
                            Window(f"File {vpncf} does not exist.")
                            error = True

                    if not window[cst.K_MAIN_BC_CB].enabled:
                        Window("Blockchain must be enabled.")
                        error = True
                    else:
                        hc = window[cst.K_MAIN_IT_BC_CF].Get()
                        if not os.path.isfile(hc):
                            Window(f"File {hc} does not exist.")
                            error = True

                        ho = window[cst.K_MAIN_IT_BC_LF].Get()
                        errcode = utils.check_file_dir(ho)
                        if errcode is not None:
                            Window(f"File path {ho} "
                                   f"cannot be created: {errcode}.")
                            error = True

                    if not error:
                        if not window[cst.K_MAIN_LOG_CB].enabled:
                            shrink_enlarge_window(
                                window[cst.K_MAIN_LOG],
                                window[cst.K_MAIN_LOG_CB],
                                win_out_sz,
                                win_out_sz_hidden)

                        if window[cst.K_MAIN_VPN_CB].enabled:
                            cmd_queue.put(('vpnstart',
                                           (vpncf,
                                            False)))  # stop

                        cmd_queue.put(('msfstart',
                                       (ld,
                                        window[cst.K_MAIN_VPN_CB].enabled,
                                        False)))  # stop
                        cmd_queue.put(('msfconnect',
                                       (cst.DEF_MSFRPC_PWD,
                                        False)))  # wizard
                        cmd_queue.put(('hlfloadconfig', (hc,)))
                        cmd_queue.put(('hlfstore', (lf, ho)))

                        cmd_queue.put(('msfstop',
                                       (window[cst.K_MAIN_SC_CB].enabled,)
                                       ))

                        job_run = True

            if event in (cst.K_MAIN_WIZ_B, cst.K_MAIN_WIZ_T):
                if WIN[WZ] is None and not job_run:
                    if not window[cst.K_MAIN_LOG_CB].enabled:
                        shrink_enlarge_window(window[cst.K_MAIN_LOG],
                                              window[cst.K_MAIN_LOG_CB],
                                              win_out_sz,
                                              win_out_sz_hidden)
                    error = False
                    utils.set_logger(window)

                    lf = window[cst.K_MAIN_IT_LF].Get()
                    ld = window[cst.K_MAIN_IT_LD].Get()

                    errcode = utils.check_file_dir(lf, ld)
                    if errcode is not None:
                        Window("Log file/directory "
                               "creation permission error.")
                        error = True

                    if window[cst.K_MAIN_RC_CB].enabled:
                        rc = window[cst.K_MAIN_IT_RC].Get()
                        if not os.path.isfile(rc):
                            Window(f"File {rc} does not exist.")
                            error = True

                    if window[cst.K_MAIN_VPN_CB].enabled:
                        vpncf = window[cst.K_MAIN_IT_VPN_CF].Get()
                        if not os.path.isfile(vpncf):
                            Window(f"File {vpncf} does not exist.")
                            error = True

                    if not error:
                        if not window[cst.K_MAIN_LOG_CB].enabled:
                            shrink_enlarge_window(
                                window[cst.K_MAIN_LOG],
                                window[cst.K_MAIN_LOG_CB],
                                win_out_sz,
                                win_out_sz_hidden)

                        if window[cst.K_MAIN_VPN_CB].enabled:
                            cmd_queue.put(('vpnstart',
                                           (vpncf,
                                            False)))  # stop
                        cmd_queue.put(
                            ('msfstart',
                             (ld,
                              window[cst.K_MAIN_VPN_CB].enabled,  # ovpn
                              False)))  # stop
                        cmd_queue.put(('msfconnect',
                                       (cst.DEF_MSFRPC_PWD,
                                        True)))  # wizard
                        job_run = True

            if event in (cst.K_MAIN_STP_B, cst.K_MAIN_STP_T):
                if not window[cst.K_MAIN_LOG_CB].enabled:
                    shrink_enlarge_window(window[cst.K_MAIN_LOG],
                                          window[cst.K_MAIN_LOG_CB],
                                          win_out_sz,
                                          win_out_sz_hidden)
                utils.set_logger(window)

                if window[cst.K_MAIN_VPN_CB].enabled:
                    vpncf = window[cst.K_MAIN_IT_VPN_CF].Get()
                    cmd_queue.put(('vpnstart',
                                   (vpncf,
                                    True)))  # stop

                ld = window[cst.K_MAIN_IT_LD].Get()
                cmd_queue.put(('msfstart',
                               (ld,
                                window[cst.K_MAIN_VPN_CB].enabled,
                                True)))  # stop

                cmd_queue.put(('msfstop', (True,)))
                close_wizard()

            if event == 'LOG':
                window[cst.K_MAIN_LOG].print(values[event])
                if float(window[cst.K_MAIN_LOG].Widget.index('end-2l')
                         ) >= cst.C_EL - 1:
                    color_scrollbar(window, cst.K_MAIN_LOG)

            if event == 'GIF':
                if gif is None:
                    gif = LoadingGif(start_gif=values[event])
                gif.update()

            if event == 'GIFSTOP':
                if gif is not None:
                    gif.stop()
                gif = None

            if event == 'START':
                msfcnt, stop = values[event]
                if msfcnt is None and not stop:
                    Window("Containers could not be started")

            if event == 'STOP':
                if values[event] == cst.NOERROR:
                    Window("AutoAuditor finished successfully.",
                           title="Success", button_color=None,
                           auto_close_duration=1)
                else:
                    Window(f"AutoAuditor finished with error: "
                           f"{values[event]}")
                job_run = False

            if event == 'CONNECT':
                error, is_wizard, msfcl = values[event]
                if error == cst.NOERROR:
                    if is_wizard:
                        if window[cst.K_MAIN_RC_CB].enabled:
                            modules = parse_rc_file(
                                window[cst.K_MAIN_IT_RC].Get(),
                                msfcl,
                                ts)
                        wizard_window(modules)
                else:
                    Window(f"Error connecting with metasploit container: "
                           f"{values[event]}")

        if window == WIN[WZ]:
            if event == sg.WIN_CLOSED:
                window.close()
                WIN[WZ] = None
                job_run = False
                close_wizard()
            else:
                if event == cst.K_WIZ_MODT:
                    mtype = values[cst.K_WIZ_MODT]
                    if msfcl is not None:
                        mods = [''] + wizard.get_modules(msfcl, mtype)
                    else:
                        mods = ['Error loading list. '
                                'Wait until metasploit container starts.']
                    window[cst.K_WIZ_MODN](
                        values=mods)
                    window[cst.K_WIZ_MODN](
                        value='')
                    window[cst.K_WIZ_MODN_INFO](disabled=True)

                if event == cst.K_WIZ_MODN:
                    if window[cst.K_WIZ_MODN].Get():
                        window[cst.K_WIZ_MODN_INFO](disabled=False)
                    else:
                        window[cst.K_WIZ_MODN_INFO](disabled=True)

                if event == cst.K_WIZ_MODN_INFO:
                    if window[cst.K_WIZ_MODN].Get():
                        tmp_mod = wizard.get_module(
                            msfcl,
                            window[cst.K_WIZ_MODT].Get(),
                            window[cst.K_WIZ_MODN].Get())
                        info_window(tmp_mod)

                if event == cst.K_WIZ_MADD:
                    mname = values[cst.K_WIZ_MODN]
                    if mtype and mname:
                        if mname.startswith('Error'):
                            Window("Choose module type again "
                                   "to reload module names list.")
                        else:
                            if ts.available_ticket():
                                ticket = ts.get_ticket()
                                tmp_mod = Module(msfcl,
                                                 mtype, mname, ticket)
                                tmp_modules[ticket] = tmp_mod

                                mopts_window(tmp_mod)
                            else:
                                Window(f"Maximum modules allowed "
                                       f"({cst.MAX_MODS}).",
                                       "Limit can be changed in "
                                       "utils.py:cst.MAX_MODS")
                    else:
                        Window("Module type/name not selected.",
                               "Choose module type and module name "
                               "from dropdown list.")

                if event == 'MOD_NEW':
                    ticket, modstate = values[event]
                    if ticket not in tmp_modules and ticket not in modules:
                        Window("Error processing module. Try again.")
                    elif ticket in tmp_modules:
                        modules[ticket] = tmp_modules[ticket]
                        del tmp_modules[ticket]

                if wiz_medit_re.match(event):
                    ticket = int(event.split('_')[2])  # kwiz_mname_xxx
                    if ticket in WIN[MO]:
                        Window("Module window already open.")
                    else:
                        mopts_window(modules[ticket], edit=True)

                if wiz_mrem_re.match(event):
                    ticket = int(event.split('_')[2])  # kwiz_mrem_xxx
                    window[f'{cst.K_WIZ_MFRAME}{ticket}'](visible=False)
                    window[f'{cst.K_WIZ_MFRAME}{ticket}'].hide_row()
                    rm_cancel_mod(ticket, remove=True)
                    # Update column scrollbar
                    window.visibility_changed()
                    window[cst.K_WIZ_MCOL].contents_changed()
                    if len(modules) <= cst.C_EL:
                        color_scrollbar(WIN[WZ], cst.K_WIZ_MCOL, disable=True)

                if wiz_minfo_re.match(event):
                    ticket = int(event.split('_')[2])  # kwiz_minfo_xxx
                    mod = get_module(ticket, 'edit')
                    info_window(mod)

                if event == cst.K_WIZ_EXIT:
                    cmd_queue.put(('msfstop', (True,)))
                    window.close()
                    WIN[WZ] = None
                    modules = {}
                    tmp_modules = {}
                    job_run = False
                    close_wizard()

                if event == cst.K_WIZ_GEN:
                    ev, _ = sg.Window("Warning", [
                        [sg.Text(f"You are going to override "
                                 f"{WIN[MN][cst.K_MAIN_IT_RC].Get()}.",
                                 pad=cst.P_N_R,
                                 justification=cst.J_C)],
                        [sg.Text("Are you sure?",
                                 font=cst.FNT_B, pad=cst.P_N_L,
                                 justification=cst.J_C)],
                        [sg.Text(font=cst.FNT_P,
                                 justification=cst.J_C)],
                        [sg.Ok(button_color=cst.B_C_ERR),
                         sg.Cancel()]
                    ], element_justification=cst.J_C,
                                      icon=cst.ICO).read(close=True)
                    if ev == 'Ok':
                        rc_dict = dump_modules(modules)
                        rc_out = WIN[MN][cst.K_MAIN_IT_RC].Get()
                        with open(rc_out, 'w') as f:
                            json.dump(rc_dict, f, indent=2)
                        utils.log(
                            'succg',
                            f"Resources script generated in {rc_out}")
                        sg.Window('Success', [
                            [sg.Text("Resources script generated in")],
                            [sg.Text(f"{rc_out}")],
                            [sg.OK()]
                        ], element_justification=cst.J_C,
                                  auto_close=True, auto_close_duration=1,
                                  keep_on_top=True,
                                  icon=cst.ICO).read(close=True)
                        sev, _ = sg.Window("Shutdown", [
                            [sg.Text("Close wizard and shutdown containers?",
                                     pad=cst.P_N_R, justification=cst.J_C)],
                            [sg.Text(cst.T_N, font=cst.FNT_P,
                                     justification=cst.J_C)],
                            [sg.Ok(button_color=cst.B_C_ERR),
                             sg.Cancel()]
                        ], element_justification=cst.J_C,
                                           icon=cst.ICO).read(close=True)
                        if sev == 'Ok':
                            cmd_queue.put(('msfstop', (True,)))
                            close_wizard()
                            modules = {}
                            tmp_modules = {}

        if window in WIN[MO].values():
            ax = window[cst.K_MOPTS_ID].Get().split(':')
            ticket, modstate = int(ax[0]), ax[1]

            if event in (sg.WIN_CLOSED, cst.K_MOPTS_CNCL):
                window.close()
                del WIN[MO][ticket]
                if ticket in WIN[PO]:
                    WIN[PO][ticket].close()
                    del WIN[PO][ticket]
                close_popups(ticket, MO, PO)
                if modstate == 'new':
                    rm_cancel_mod(ticket)
            else:
                module = get_module(ticket, modstate)
                if module is not None:
                    if mopts_info_re.match(event):
                        idx = int(event.split('_')[2])  # kmopts_info_xxx
                        opt = window[cst.K_MOPTS+str(idx)].Get()
                        oinfo_window(module, opt)

                    if event == cst.K_MOPTS_PDD:
                        if window[cst.K_MOPTS_PDD].Get():
                            window[cst.K_MOPTS_PINFO](disabled=False)
                        else:
                            window[cst.K_MOPTS_PINFO](disabled=True)
                    if event == cst.K_MOPTS_PADD:
                        if not window[cst.K_MOPTS_PDD].Get():
                            Window("Payload not selected. "
                                   "Choose payload from dropdown list.")
                        else:
                            if ticket in WIN[PO]:
                                Window("Payload window already open.")
                            else:
                                popts_window(module,
                                             modstate,
                                             window[cst.K_MOPTS_PDD].Get())

                    if event == cst.K_MOPTS_PEDIT:
                        if ticket in WIN[PO]:
                            Window("Payload window already open.")
                        else:
                            popts_window(module, modstate)

                    if event == cst.K_MOPTS_PREM:
                        del module.payload
                        window[cst.K_MOPTS_PDD](disabled=False)
                        window[cst.K_MOPTS_PDD](value='')
                        window[cst.K_MOPTS_PADD](disabled=False)
                        window[cst.K_MOPTS_PEDIT](disabled=True)
                        window[cst.K_MOPTS_PREM](disabled=True)

                    if event == cst.K_MOPTS_PINFO:
                        if window[cst.K_MOPTS_PDD].Get():
                            tmp_pay = wizard.get_payload(
                                msfcl, window[cst.K_MOPTS_PDD].Get())
                            info_window(tmp_pay, ticket=ticket)

                    if event == cst.K_MOPTS_ACPT:
                        tmp_opts, inv_miss = gen_tmp_opts(window, module)

                        if inv_miss['inv'] or inv_miss['mis']:
                            oerror_window(window, inv_miss)
                        else:
                            cur_opts = module.mopts()
                            for topt in tmp_opts.values():
                                cur_opts[topt[0]] = topt[1]

                            WIN[WZ][f'{cst.K_WIZ_MNAME}{ticket}'](
                                value=(f"Module "
                                       f"{module.mtype()}/{module.mname()}"))
                            WIN[WZ][f'{cst.K_WIZ_MFRAME}{ticket}'](
                                visible=True)
                            WIN[WZ][f'{cst.K_WIZ_MFRAME}{ticket}'].unhide_row()
                            # Update column scrollbar
                            WIN[WZ].visibility_changed()
                            WIN[WZ][cst.K_WIZ_MCOL].contents_changed()
                            WIN[WZ][cst.K_WIZ_MCOL].Widget.canvas.yview_moveto(
                                999)  # set scrollbar to last element
                            if len(modules) >= cst.C_EL:
                                color_scrollbar(WIN[WZ], cst.K_WIZ_MCOL)

                            WIN[WZ].write_event_value('MOD_NEW',
                                                      (ticket, modstate))
                            window.close()
                            del WIN[MO][ticket]
                            close_popups(ticket, MO, PO)
                else:
                    Window("Error processing module. Try again.")
                    window.close()
                    del WIN[MO][ticket]
                    close_popups(ticket, MO)
                    if ticket in WIN[PO]:
                        WIN[PO][ticket].close()
                        del WIN[PO][ticket]
                        close_popups(ticket, PO)

        if window in WIN[PO].values():
            ax = window[cst.K_POPTS_ID].Get().split(':')
            ticket, modstate, paystate = int(ax[0]), ax[1], ax[2]
            module = get_module(ticket, modstate)

            if module is not None:
                if event in (sg.WIN_CLOSED, cst.K_POPTS_CNCL):
                    window.close()
                    del WIN[PO][ticket]
                    close_popups(ticket, PO)
                    if paystate == 'new':
                        del module.payload
                else:
                    if popts_info_re.match(event):
                        idx = int(event.split('_')[2])  # kpopts_info_xxx
                        popt = window[cst.K_POPTS+str(idx)].Get()
                        oinfo_window(module, popt, payload=True)

                    if event == cst.K_POPTS_ACPT:
                        if module.payload is None:
                            Window("Missing payload in module.")
                            window.close()
                            del WIN[PO][ticket]
                            close_popups(ticket, PO)
                        else:
                            tmp_popts, pinv_miss = gen_tmp_opts(window, module,
                                                                payload=True)
                            if pinv_miss['inv'] or pinv_miss['mis']:
                                oerror_window(window, pinv_miss, payload=True)
                            else:
                                cur_popts = module.payload.mopts()
                                for tpopt in tmp_popts.values():
                                    cur_popts[tpopt[0]] = tpopt[1]

                                WIN[MO][ticket][cst.K_MOPTS_PDD](
                                    disabled=True)
                                WIN[MO][ticket][cst.K_MOPTS_PADD](
                                    disabled=True)
                                WIN[MO][ticket][cst.K_MOPTS_PEDIT](
                                    disabled=False)
                                WIN[MO][ticket][cst.K_MOPTS_PREM](
                                    disabled=False)
                                window.close()
                                del WIN[PO][ticket]
                                close_popups(ticket, PO)
            else:
                Window("Error processing payload. Try again.")
                window.close()
                del WIN[PO][ticket]
                close_popups(ticket, PO)
                if ticket in WIN[MO]:
                    WIN[MO][ticket].close()
                    del WIN[MO][ticket]
                    close_popups(ticket, MO)


if __name__ == "__main__":
    main()
