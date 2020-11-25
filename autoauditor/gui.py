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
from textwrap import TextWrapper
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

sg.theme('Reddit')

WIN = {
    'MAIN': None,
    'WIZ': None,
    'MOPTS': {},
    'POPTS': {},
    'POPUP': []
}

MN = 'MAIN'
WZ = 'WIZ'
MO = 'MOPTS'
PO = 'POPTS'
POP = 'POPUP'

shared_msfcl = None


class Button(sg.Button):
    def __init__(self, key, tooltip=None, image_data=cst.ICO_INFO,
                 image_size=cst.B_SZ_S, button_color=cst.B_C,
                 pad=cst.N_P_TBR, border_width=cst.N_WDTH, disabled=False,
                 target=(None, None), button_type=sg.BUTTON_TYPE_READ_FORM):
        super().__init__(key=key, tooltip=tooltip,
                         image_data=image_data, image_size=image_size,
                         button_color=button_color, pad=pad,
                         border_width=border_width, disabled=disabled,
                         target=target, button_type=button_type)


class Browser(Button):
    def __init__(self, key, tooltip, target,
                 folder=False, disabled=False):
        super().__init__(key=key, tooltip=tooltip,
                         image_data=cst.ICO_FOLDER if folder else cst.ICO_FILE,
                         image_size=cst.B_SZ_M, pad=cst.N_P_TB,
                         disabled=disabled, target=target,
                         button_type=sg.BUTTON_TYPE_BROWSE_FILE if folder
                         else sg.BUTTON_TYPE_BROWSE_FILE)


class ImageCheckBox(Button):
    def __init__(self, key, image_on=cst.ICO_CBON, image_off=cst.ICO_CBOFF,
                 enabled=False):
        self.enabled = enabled
        self.image_on = image_on
        self.image_off = image_off
        super().__init__(key=key,
                         image_data=image_on if enabled else image_off,
                         pad=cst.N_P)

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


class Module():
    def __init__(self, client, mtype, mname, ticket):
        self.client = client
        self.ticket = ticket
        self.mod = wizard.get_module(self.client, mtype, mname)
        self._mopts = {}
        self._payload = None

    def ticket(self):
        return self.ticket

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
    def __init__(self, starting_gif=False):
        self.starting_gif = starting_gif
        self.message = ('Starting\ncontainers' if starting_gif
                        else 'Stopping\ncontainers')
        self.layout = [
            [sg.Image(filename=cst.LOADING,
                      background_color=cst.C_W,
                      key=cst.K_GIF)],
            [sg.Text(pad=cst.N_P_LR,
                     font=cst.FONTP)],
            [sg.Text(self.message,
                     background_color=cst.C_W,
                     font=cst.FONT,
                     justification=cst.J_C)]]

        super().__init__('Loading', self.layout,
                         element_justification=cst.J_C,
                         element_padding=(0, 0), margins=(10, 10),
                         finalize=True)

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


def autoauditor_thread(stopped, queue, window):
    vpncont = None
    msfcont = None
    msfclient = None
    config = None
    async_loop = _asyncio.new_event_loop()
    while not stopped.is_set():
        queuedata = queue.get()
        # print(f"thread_queue: {queuedata}")
        cmd, params = queuedata
        if cmd == 'vpn':
            vpncf, stop = params
            vpncont = vpn.setup_vpn(vpncf, stop=stop)
        if cmd == 'msfstart':
            log_dir, ovpn, stop, wizard = params
            if not stop:
                startAnim = threading.Event()
                starting_thread = LoadingThread(
                    startAnim, window, start_gif=True)
                starting_thread.start()
            msfcont = metasploit.start_msfrpcd(log_dir, ovpn, stop)
            if not stop:
                startAnim.set()
            window.write_event_value('START', (msfcont, wizard, stop))
        if cmd == 'msfconn':
            passwd, = params
            msfclient = metasploit.get_msf_connection(passwd)
            if msfclient is not None:
                window.write_event_value('CONNECT', cst.NOERROR)
                global shared_msfcl
                shared_msfcl = msfclient
            else:
                window.write_event_value('CONNECT', cst.EMSCONN)

        if cmd == 'msfrun':
            res_scpt, log_file = params
            metasploit.launch_metasploit(msfclient, res_scpt, log_file)

        if cmd == 'hlfloadconfig':
            _asyncio.set_event_loop(async_loop)
            config_file, = params
            config = blockchain.load_config(config_file, loop=async_loop)

        if cmd == 'hlfstore':
            report, log_file = params
            if config is not None:
                blockchain.store_report(config, report, log_file,
                                        loop=async_loop)

        if cmd == 'stop':
            stopAnim = threading.Event()
            stopping_thread = LoadingThread(stopAnim, window, start_gif=False)
            stopping_thread.start()
            errcode = utils.shutdown(msfcont, vpncont)
            stopAnim.set()
            window.write_event_value('STOP', errcode)


def autoauditor_window():
    mandatory_layout = [
        [sg.Text(font=cst.FONTP, pad=cst.N_P_TB)],
        [sg.Text(cst.T_MAIN_LF, size=cst.T_DESC_SZ_S2, font=cst.FONTB),
         sg.InputText(cst.DEF_MAIN_LF, key=cst.K_MAIN_IT_LF,
                      font=cst.FONT, pad=cst.P_IT),
         Browser(key=cst.K_MAIN_LF_FB, tooltip=cst.TT_MAIN_FB,
                 target=cst.K_MAIN_IT_LF),
         Button(key=cst.K_MAIN_LFINFO, tooltip=cst.TT_MAIN_LF)],
        [sg.Text(cst.T_MAIN_LD, size=cst.T_DESC_SZ_S2, font=cst.FONTB),
         sg.InputText(cst.DEF_MAIN_LD, key=cst.K_MAIN_IT_LD,
                      font=cst.FONT, pad=cst.P_IT),
         Browser(key=cst.K_MAIN_LD_FB, tooltip=cst.TT_MAIN_DB,
                 target=cst.K_MAIN_IT_LD, folder=True),
         Button(key=cst.K_MAIN_LDINFO, tooltip=cst.TT_MAIN_LD)],
        [sg.Text(cst.T_MAIN_RC, size=cst.T_DESC_SZ_S2, font=cst.FONTB),
         sg.InputText(cst.DEF_MAIN_RC, key=cst.K_MAIN_IT_RC,
                      font=cst.FONT, pad=cst.P_IT),
         Browser(key=cst.K_MAIN_RC_FB, tooltip=cst.TT_MAIN_FB,
                 target=cst.K_MAIN_IT_RC),
         Button(key=cst.K_MAIN_RCINFO, tooltip=cst.TT_MAIN_RC)],
        [sg.Text(font=cst.FONTP, pad=cst.N_P_TB)]
    ]

    vpn_layout = [
        [ImageCheckBox(key=cst.K_MAIN_VPN_CB),
         sg.Text(cst.T_MAIN_VPN_CB, key=cst.K_MAIN_VPN_CB_T,
                 font=cst.FONTB, text_color=cst.C_DIS,
                 enable_events=True)],
        [sg.Text(cst.T_MAIN_VPN_CF, key=cst.K_MAIN_VPN_CF_T,
                 size=cst.T_DESC_SZ_S2, font=cst.FONTB,
                 text_color=cst.C_DIS),
         sg.InputText(cst.DEF_MAIN_VPN_CF, key=cst.K_MAIN_IT_VPN_CF,
                      font=cst.FONT, pad=cst.P_IT, disabled=True),
         Browser(key=cst.K_MAIN_VPN_CF_FB, tooltip=cst.TT_MAIN_FB,
                 target=cst.K_MAIN_IT_VPN_CF, disabled=True),
         Button(key=cst.K_MAIN_VPN_CFINFO,
                tooltip=cst.TT_MAIN_VPN_CF, disabled=True)],
        [sg.Text(font=cst.FONTP, pad=cst.N_P_TB)]
    ]

    blockchain_layout = [
        [ImageCheckBox(key=cst.K_MAIN_BC_CB),
         sg.Text(cst.T_MAIN_BC_CB, key=cst.K_MAIN_BC_CB_T,
                 font=cst.FONTB, text_color=cst.C_DIS,
                 enable_events=True)],
        [sg.Text(cst.T_MAIN_BC_CF, key=cst.K_MAIN_BC_CF_T,
                 size=cst.T_DESC_SZ_S2, font=cst.FONTB,
                 text_color=cst.C_DIS),
         sg.InputText(cst.DEF_MAIN_BC_CF, key=cst.K_MAIN_IT_BC_CF,
                      font=cst.FONT, pad=cst.P_IT, disabled=True),
         Browser(key=cst.K_MAIN_BC_CF_FB, tooltip=cst.TT_MAIN_FB,
                 target=cst.K_MAIN_IT_BC_CF, disabled=True),
         Button(key=cst.K_MAIN_BC_CFINFO,
                tooltip=cst.TT_MAIN_BC_CF, disabled=True)],
        [sg.Text(cst.T_MAIN_BC_LF, key=cst.K_MAIN_BC_LF_T,
                 size=cst.T_DESC_SZ_S2, font=cst.FONTB,
                 text_color=cst.C_DIS),
         sg.InputText(cst.DEF_MAIN_BC_LF, key=cst.K_MAIN_IT_BC_LF,
                      font=cst.FONT, pad=cst.P_IT, disabled=True),
         Browser(key=cst.K_MAIN_BC_LF_FB, tooltip=cst.TT_MAIN_FB,
                 target=cst.K_MAIN_IT_BC_LF, disabled=True),
         Button(key=cst.K_MAIN_BC_LFINFO,
                tooltip=cst.TT_MAIN_BC_LF, disabled=True)],
        [sg.Text(font=cst.FONTP, pad=cst.N_P_TB)],
        [ImageCheckBox(key=cst.K_MAIN_SC_CB, enabled=True),
         sg.Text(cst.T_MAIN_SC_CB, key=cst.K_MAIN_SC_CB_T,
                 font=cst.FONTB, text_color=cst.C_EN,
                 enable_events=True)]
    ]

    button_layout = [
        [Button(key=cst.K_MAIN_RAA_B, tooltip=cst.TT_MAIN_RAA,
                image_data=cst.ICO_PLAY, image_size=cst.B_SZ_L,
                pad=cst.P_T),
         sg.Text(size=cst.EXEC_T_SZ_S, pad=cst.N_P),
         Button(key=cst.K_MAIN_RBC_B, tooltip=cst.TT_MAIN_RBC,
                image_data=cst.ICO_BCKCHN, image_size=cst.B_SZ_L,
                pad=cst.P_T),
         sg.Text(size=cst.EXEC_T_SZ_S, pad=cst.N_P),
         Button(key=cst.K_MAIN_WIZ_B, tooltip=cst.TT_MAIN_WIZ,
                image_data=cst.ICO_WIZ, image_size=cst.B_SZ_L,
                pad=cst.P_T),
         sg.Text(size=cst.EXEC_T_SZ_S, pad=cst.N_P),
         Button(cst.K_MAIN_STP_B, tooltip=cst.TT_MAIN_STP,
                image_data=cst.ICO_STOP, image_size=cst.B_SZ_L,
                pad=cst.P_T),
         ],
        [sg.Text(cst.T_MAIN_RAA, key=cst.K_MAIN_RAA_T,
                 size=cst.EXEC_T_SZ_S, font=cst.FONTB,
                 pad=cst.P_EXEC_T, justification=cst.J_C,
                 enable_events=True),
         sg.Text(cst.T_MAIN_RBC, key=cst.K_MAIN_RBC_T,
                 size=cst.EXEC_T_SZ_S, font=cst.FONTB,
                 pad=cst.P_EXEC_T, justification=cst.J_C,
                 enable_events=True),
         sg.Text(cst.T_MAIN_WIZ, key=cst.K_MAIN_WIZ_T,
                 size=cst.EXEC_T_SZ_S, font=cst.FONTB,
                 pad=cst.P_EXEC_T, justification=cst.J_C,
                 enable_events=True),
         sg.Text(cst.T_MAIN_STP, key=cst.K_MAIN_STP_T,
                 size=cst.EXEC_T_SZ_S, font=cst.FONTB,
                 pad=cst.P_EXEC_T, justification=cst.J_C,
                 enable_events=True)
         ],
        [sg.Frame(cst.N_T, [
            [sg.Text(size=cst.LOG_CB_P_SZ, pad=cst.N_P),
             ImageCheckBox(key=cst.K_MAIN_LOG_CB, image_on=cst.ICO_C_H,
                           image_off=cst.ICO_C_S)]
        ], border_width=cst.N_WDTH)],
        [sg.Multiline(key=cst.K_MAIN_LOG, size=cst.LOG_SZ,
                      font=cst.FONT, pad=cst.LOG_P,
                      autoscroll=True, visible=False)]
    ]
    autoauditor_layout = [
        [sg.Frame(cst.N_T, mandatory_layout, border_width=cst.N_WDTH)],
        [sg.Frame(cst.N_T, vpn_layout, border_width=cst.N_WDTH)],
        [sg.Frame(cst.N_T, blockchain_layout, border_width=cst.N_WDTH)],
        [sg.Frame(cst.N_T, button_layout, border_width=0,
                  element_justification=cst.J_C)]
    ]

    about_layout = [
        [sg.Text(font=cst.FONTP, pad=cst.N_P_TB)],
        [sg.Text(pad=cst.N_P_TB)],
        [sg.Text(cst.MAIN_ABOUT_NAME, font=cst.FONTB)],
        [sg.Text(cst.MAIN_ABOUT_VER, font=cst.FONTB)],
        [sg.Text(pad=cst.N_P_TB)],
        [sg.Text(cst.MAIN_ABOUT_AUTHOR, font=cst.FONT)],
        [sg.Text(cst.MAIN_ABOUT_LAB, font=cst.FONT)],
        [sg.Text(cst.MAIN_ABOUT_DEPT, font=cst.FONT)],
        [sg.Text(cst.MAIN_ABOUT_UC3M, font=cst.FONT)],
        [sg.Text(cst.MAIN_ABOUT_LOC, font=cst.FONT)],
        [sg.Text(pad=cst.N_P_TB)],
        [sg.Text(cst.MAIN_ABOUT_ACK, font=cst.FONT,
                 justification=cst.J_C)],
        [sg.Text(pad=cst.N_P_TB)],
        [sg.Text(cst.MAIN_ABOUT_YEAR, font=cst.FONT)],
    ]

    with open(cst.DEF_MAIN_LIC, 'r') as f:
        # fix double spaces in GNU LICENSE text
        gplv3_full = f.read().replace('.  ', '. ').replace('  ', '')

    gplv3_full_layout = [
        [sg.Text(gplv3_full, size=cst.MAIN_LIC_T_SZ,
                 justification=cst.J_C, background_color=cst.C_TAB_DIS)]
    ]
    license_layout = [
        [sg.Text(cst.COPYRIGHT, font=cst.FONT,
                 justification=cst.J_C)],
        [sg.Column(gplv3_full_layout,
                   size=cst.MAIN_LIC_C_SZ, pad=cst.P_T, justification=cst.J_C,
                   scrollable=True, vertical_scroll_only=True,
                   background_color=cst.C_TAB_DIS, )]
    ]

    layout = [
        [sg.TabGroup([
            [sg.Tab('AutoAuditor', autoauditor_layout,
                    element_justification=cst.J_C)],
            [sg.Tab('About', about_layout,
                    element_justification=cst.J_C)],
            [sg.Tab('License', license_layout,
                    element_justification=cst.J_C)]
        ], font=cst.FONT, border_width=cst.N_WDTH,
                     tab_background_color=cst.C_TAB_DIS)]
    ]

    WIN[MN] = sg.Window('AutoAuditor', layout,
                        element_justification=cst.J_C,
                        finalize=True)

    # remove extra pixel displacement on click
    WIN[MN][cst.K_MAIN_VPN_CB].Widget.config(
        relief=sg.RELIEF_SUNKEN, borderwidth=0)
    WIN[MN][cst.K_MAIN_BC_CB].Widget.config(
        relief=sg.RELIEF_SUNKEN, borderwidth=0)
    WIN[MN][cst.K_MAIN_SC_CB].Widget.config(
        relief=sg.RELIEF_SUNKEN, borderwidth=0)


def wizard_window():
    mod_layout = [
        [sg.Frame(cst.N_T, [
            [sg.InputText(str(i), key=f"{cst.K_WIZ_MNAME}{i}",
                          size=cst.T_DESC_SZ_M2, font=cst.FONT,
                          pad=cst.N_P_TBR, border_width=cst.N_WDTH,
                          disabled_readonly_background_color=cst.C_W,
                          readonly=True),
             Button(key=f"{cst.K_WIZ_MEDIT}{i}", tooltip=cst.TT_WIZ_MEDIT,
                    image_data=cst.ICO_EDIT, image_size=cst.B_SZ_M,
                    pad=cst.P_MOD),
             Button(key=f"{cst.K_WIZ_MREM}{i}", tooltip=cst.TT_WIZ_MREM,
                    image_data=cst.ICO_REM, image_size=cst.B_SZ_M),
             Button(key=f"{cst.K_WIZ_MINFO}{i}", tooltip=cst.TT_WIZ_MINFO,
                    image_data=cst.ICO_INFO, pad=cst.P_MOD)
             ]], visible=False, pad=cst.N_P,
                  border_width=cst.N_WDTH,
                  key=f"{cst.K_WIZ_MFRAME}{i}",
                  element_justification=cst.J_C)]
        for i in range(cst.MAX_MODS)]

    wizard_layout = [
        [sg.Text(font=cst.FONT, pad=cst.N_P_TB)],
        [sg.Text(cst.T_WIZ_MTYPE, size=cst.T_DESC_SZ_S2, font=cst.FONTB),
         sg.DropDown(cst.MOD_TYPES, key=cst.K_WIZ_MODT,
                     size=cst.EXEC_T_SZ_L, font=cst.FONT,
                     enable_events=True, readonly=True)],
        [sg.Text(cst.T_WIZ_MNAME, size=cst.T_DESC_SZ_S2, font=cst.FONTB),
         sg.DropDown(cst.N_T, key=cst.K_WIZ_MODN,
                     size=cst.EXEC_T_SZ_L, font=cst.FONT,
                     readonly=True)],
        [sg.Text(font=cst.FONT, pad=cst.N_P)],
        [sg.Column(mod_layout, key=cst.K_WIZ_MCOL, size=cst.C_SZ,
                   pad=cst.N_P, justification=cst.J_C,
                   scrollable=True, vertical_scroll_only=True,
                   element_justification=cst.J_C)],
        [sg.Text(font=cst.FONT, pad=cst.N_P)],
        [Button(key=cst.K_WIZ_MADD, tooltip=cst.TT_WIZ_MADD,
                image_data=cst.ICO_ADD, image_size=cst.B_SZ_L,)],
        [sg.Text(font=cst.FONTP, pad=cst.N_P_TB)],
        [sg.Button(cst.T_WIZ_GEN, key=cst.K_WIZ_GEN, font=cst.FONT),
         sg.Button(cst.T_WIZ_EXIT, key=cst.K_WIZ_EXIT, font=cst.FONT)],
        [sg.Text(font=cst.FONTP, pad=cst.N_P_TB)]
    ]
    WIN[WZ] = sg.Window(cst.T_WIZ_TIT, wizard_layout,
                        element_justification=cst.J_C,
                        finalize=True)


def mopts_window(module, edit=False):
    opts, ropts = module.options()

    current_opts = module.mopts()
    if current_opts:
        for copt in current_opts:
            opts[copt] = current_opts[copt]

    scrollable = len(opts) > 15
    hidden = f"{module.ticket}:{'new' if not edit else 'edit'}"
    opt_layout = [
        [sg.Text(hidden, key=cst.K_MOPTS_ID,
                 font=cst.FONTP, text_color=cst.C_W,
                 pad=cst.N_P_TB)],
        [sg.Text(f"{module.mtype()}/{module.mname()}",
                 key=cst.K_MOPTS_TIT,
                 font=cst.FONTB)],
        [sg.Frame(cst.N_T, [
            [sg.Text(size=cst.T_DESC_SZ_XL2 if scrollable
                     else cst.T_DESC_SZ_XL,
                     font=cst.FONTP, pad=cst.N_P)],
            [sg.Text(cst.T_MOPTS_HNAME, size=cst.T_OPT_NAME_SZ,
                     font=cst.FONTB, pad=cst.P_OPT_HEAD_NAME),
             sg.Text(cst.T_MOPTS_HVAL, size=cst.T_OPT_VAL_SZ,
                     font=cst.FONTB, pad=cst.P_OPT_HEAD_VAL),
             sg.Text(cst.T_MOPTS_HREQ, size=cst.T_REQ_SZ,
                     font=cst.FONTB,
                     pad=cst.P_OPT_HEAD_REQ if scrollable
                     else cst.P_OPT_HEAD_REQ2),
             sg.Text(cst.T_MOPTS_HINFO, font=cst.FONTB,
                     pad=cst.P_OPT_HEAD_INFO)]
        ], pad=cst.N_P_L, border_width=cst.N_WDTH)],
        [sg.Column([
            [sg.Frame(cst.N_T, [
                [sg.InputText(opt, key=f"{cst.K_MOPTS}{idx}",
                              size=cst.T_DESC_SZ_S, font=cst.FONT,
                              pad=cst.P_IT2, border_width=cst.N_WDTH,
                              disabled_readonly_background_color=cst.C_W,
                              readonly=True),
                 sg.InputText(opts[opt], key=f"{cst.K_MOPTS_VAL}{idx}",
                              size=cst.T_DESC_SZ_M, font=cst.FONT,
                              pad=cst.P_IT2),
                 sg.Text(cst.T_MOPTS_RY if opt in ropts
                         else cst.T_MOPTS_RN,
                         size=cst.T_REQ_SZ, font=cst.FONT,
                         pad=cst.P_IT_TR if scrollable
                         else cst.P_IT_TR2),
                 Button(key=f"{cst.K_MOPTS_INFO}{idx}",
                        tooltip=module.opt_desc(opt))]
            ], pad=cst.N_P, border_width=cst.N_WDTH)]
            for idx, opt in enumerate(opts)],
            size=cst.C_SZ if scrollable
            else cst.column_size(len(opts)),
            scrollable=scrollable, vertical_scroll_only=True),
         ]]

    if module.has_payloads():
        pay_exist = module.payload is not None
        opt_layout.extend(
            [
                [sg.Frame(cst.N_T, [
                    [sg.Text(cst.T_MOPTS_PAY, size=cst.T_DESC_SZ_S,
                             font=cst.FONT, pad=cst.P_IT3),
                     sg.DropDown(module.payloads(), key=cst.K_MOPTS_PDD,
                                 default_value=(module.payload.mname()
                                                if pay_exist else ''),
                                 size=cst.EXEC_T_SZ_L2, font=cst.FONT,
                                 readonly=True, pad=cst.P_IT4,
                                 disabled=pay_exist),
                     Button(key=cst.K_MOPTS_PADD, image_data=cst.ICO_ADD_S,
                            tooltip=cst.TT_MOPTS_PADD, pad=cst.P_IT5,
                            disabled=pay_exist),
                     Button(key=cst.K_MOPTS_PEDIT, tooltip=cst.TT_MOPTS_PEDIT,
                            image_data=cst.ICO_EDIT, image_size=cst.B_SZ_M,
                            pad=cst.P_IT6, disabled=not pay_exist),
                     Button(key=cst.K_MOPTS_PREM, tooltip=cst.TT_MOPTS_PREM,
                            image_data=cst.ICO_REM, image_size=cst.B_SZ_M,
                            pad=cst.P_IT6, disabled=not pay_exist),
                     Button(key=cst.K_MOPTS_PINFO, tooltip=cst.TT_MOPTS_PINFO,
                            pad=cst.P_IT7 if scrollable
                            else cst.P_IT7_NS)]
                ], pad=cst.N_P_LB if scrollable
                          else cst.N_P_LB_NS,
                          border_width=cst.N_WDTH)]])

    opt_layout.extend([
        [sg.Text(pad=cst.N_P_TB)],
        [sg.Button('Accept', key=cst.K_MOPTS_ACPT, font=cst.FONT),
         sg.Button('Cancel', key=cst.K_MOPTS_CNCL, font=cst.FONT)]])

    WIN[MO][module.ticket] = sg.Window(
        cst.T_MOPTS_TIT, opt_layout,
        element_justification=cst.J_C,
        finalize=True)


def popts_window(module, mstate, pname=''):
    if pname:
        module.payload = pname
    popts, propts = module.payload.options()

    current_opts = module.payload.mopts()
    if current_opts:
        for copt in current_opts:
            popts[copt] = current_opts[copt]

    scrollable = len(popts) > 15

    hidden = f"{module.ticket}:{mstate}:{'new' if pname else 'edit'}"

    popt_layout = [
        [sg.Text(hidden, key=cst.K_POPTS_ID,
                 font=cst.FONTP, text_color=cst.C_W, pad=cst.N_P_TB,)],
        [sg.Text(f"{module.mtype()}/{module.mname()}",
                 key=cst.K_MOPTS_TIT,
                 font=cst.FONTB)],
        [sg.Text(module.payload.mname(),
                 key=cst.K_POPTS_TITLE,
                 font=cst.FONT)],
        [sg.Frame(cst.N_T, [
            [sg.Text(font=cst.FONTP, pad=cst.N_P,
                     size=cst.T_DESC_SZ_XL2 if scrollable
                     else cst.T_DESC_SZ_XL)],
            [sg.Text(cst.T_MOPTS_HNAME, size=cst.T_OPT_NAME_SZ,
                     font=cst.FONTB, pad=cst.P_OPT_HEAD_NAME),
             sg.Text(cst.T_MOPTS_HVAL, size=cst.T_OPT_VAL_SZ,
                     font=cst.FONTB, pad=cst.P_OPT_HEAD_VAL),
             sg.Text(cst.T_MOPTS_HREQ, size=cst.T_REQ_SZ,
                     font=cst.FONTB,
                     pad=cst.P_OPT_HEAD_REQ if scrollable
                     else cst.P_OPT_HEAD_REQ2, ),
             sg.Text(cst.T_MOPTS_HINFO, font=cst.FONTB,
                     pad=cst.P_OPT_HEAD_INFO)]
        ], border_width=cst.N_WDTH, pad=cst.N_P_L)],
        [sg.Column([
            [sg.Frame(cst.N_T, [
                [sg.InputText(popt, key=f"{cst.K_POPTS}{idx}",
                              size=cst.T_DESC_SZ_S, font=cst.FONT,
                              pad=cst.P_IT2, border_width=cst.N_WDTH,
                              disabled_readonly_background_color=cst.C_W,
                              readonly=True),
                 sg.InputText(popts[popt], key=f"{cst.K_POPTS_VAL}{idx}",
                              size=cst.T_DESC_SZ_M, font=cst.FONT,
                              pad=cst.P_IT2),
                 sg.Text(cst.T_MOPTS_RY if popt in propts
                         else cst.T_MOPTS_RN,
                         size=cst.T_REQ_SZ, font=cst.FONT,
                         pad=cst.P_IT_TR if scrollable
                         else cst.P_IT_TR2),
                 Button(key=f"{cst.K_POPTS_INFO}{idx}",
                        tooltip=module.opt_desc(popt))]
            ], pad=cst.N_P, border_width=cst.N_WDTH)]
            for idx, popt in enumerate(popts)],
                   size=cst.C_SZ if scrollable
                   else cst.column_size(len(popts)),
                   scrollable=scrollable, vertical_scroll_only=True),
         ],
        [sg.Text(pad=cst.N_P_TB)],
        [sg.Button('Accept', key=cst.K_POPTS_ACPT, font=cst.FONT),
         sg.Button('Cancel', key=cst.K_POPTS_CNCL, font=cst.FONT)]]

    WIN[PO][module.ticket] = sg.Window(
        cst.T_POPTS_TIT, popt_layout,
        element_justification=cst.J_C,
        finalize=True)


def switch(target_button, *elems):
    for el in elems:
        if isinstance(el, (sg.InputText, sg.Button)):
            el(disabled=target_button.enabled)
        if isinstance(el, str):
            WIN[MN][el](
                text_color=cst.C_DIS if target_button.enabled
                else cst.C_EN)
    target_button.switch()


def shrink_enlarge_window(console, console_cb, cons_size, ncons_size):
    console(visible=not console_cb.enabled)
    console_cb.switch()
    if console_cb.enabled:
        WIN[MN].size = cons_size
    else:
        WIN[MN].size = ncons_size
    WIN[MN].visibility_changed()


def close_all_windows(stop=False):
    for win in WIN[POP]:
        win.close()
    for win in WIN[PO]:
        WIN[PO][win].close()
    for win in WIN[MO]:
        WIN[MO][win].close()
    if WIN[WZ] is not None:
        WIN[WZ].close()
        WIN[WZ] = None
    if not stop:
        if WIN[MN] is not None:
            WIN[MN].close()
            WIN[MN] = None


def main():
    autoauditor_window()

    win_out_sz = None
    win_out_sz_hidden = None

    mtype = None
    mname = None

    modules = {}
    tmp_modules = {}

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
    cmd_thread = threading.Thread(target=autoauditor_thread,
                                  args=(cmd_event, cmd_queue, WIN[MN]),
                                  daemon=True)
    cmd_thread.start()

    gif = None
    job_run = False

    while True:
        window, event, values = sg.read_all_windows()
        # print(window.Title, event)

        if window == sg.WIN_CLOSED:
            cmd_event.set()
            break

        if window in WIN[POP]:
            window.close()
            WIN[POP].remove(window)

        if window == WIN[MN]:
            if event == sg.WIN_CLOSED:
                close_all_windows()
                break
            else:
                if not window[cst.K_MAIN_LOG_CB].enabled and \
                   win_out_sz_hidden is None:
                    win_out_sz_hidden = window.size

                if window[cst.K_MAIN_LOG_CB].enabled and \
                   win_out_sz is None:
                    win_out_sz = window.size

                if event in (cst.K_MAIN_VPN_CB, cst.K_MAIN_VPN_CB_T):
                    switch(window[cst.K_MAIN_VPN_CB],
                           window[cst.K_MAIN_IT_VPN_CF],
                           window[cst.K_MAIN_VPN_CF_FB],
                           cst.K_MAIN_VPN_CF_T, cst.K_MAIN_VPN_CB_T,
                           window[cst.K_MAIN_VPN_CFINFO])

                if event in (cst.K_MAIN_BC_CB, cst.K_MAIN_BC_CB_T):
                    switch(window[cst.K_MAIN_BC_CB],
                           window[cst.K_MAIN_IT_BC_CF],
                           window[cst.K_MAIN_BC_CF_FB],
                           window[cst.K_MAIN_IT_BC_LF],
                           window[cst.K_MAIN_BC_LF_FB],
                           cst.K_MAIN_BC_CF_T, cst.K_MAIN_BC_LF_T,
                           cst.K_MAIN_BC_CB_T,
                           window[cst.K_MAIN_BC_CFINFO],
                           window[cst.K_MAIN_BC_LFINFO])

                if event in (cst.K_MAIN_SC_CB, cst.K_MAIN_SC_CB_T):
                    switch(window[cst.K_MAIN_SC_CB], cst.K_MAIN_SC_CB_T,
                           cst.K_MAIN_SC_CB_T)

                if event == cst.K_MAIN_LFINFO:
                    WIN[POP].append(
                        sg.Window(cst.T_MAIN_LF, [
                            [sg.Text(
                                ("Absolute or relative path "
                                 "where output should be logged."),
                                font=cst.FONT)],
                            [sg.Text("Default:",
                                     font=cst.FONT)],
                            [sg.InputText(cst.DEF_MAIN_LF, font=cst.FONT,
                                          disabled=True,
                                          justification=cst.J_C)],
                            [sg.OK()]
                        ], element_justification=cst.J_C, finalize=True))

                if event == cst.K_MAIN_LDINFO:
                    WIN[POP].append(
                        sg.Window(cst.T_MAIN_LD, [
                            [sg.Text(
                                ("Absolute or relative path to directory "
                                 "where gathered data should be stored."),
                                font=cst.FONT)],
                            [sg.Text("Default:",
                                     font=cst.FONT)],
                            [sg.InputText(cst.DEF_MAIN_LD, font=cst.FONT,
                                          disabled=True,
                                          justification=cst.J_C)],
                            [sg.OK()]
                        ], element_justification=cst.J_C, finalize=True))

                if event == cst.K_MAIN_RCINFO:
                    WIN[POP].append(
                        sg.Window(cst.T_MAIN_RC, [
                            [sg.Text(
                                ("Absolute or relative path "
                                 "to resource script file."),
                                font=cst.FONT)],
                            [sg.Text(
                                ("Template and examples in config folder. "
                                 "Default:"),
                                font=cst.FONT)],
                            [sg.InputText(cst.DEF_MAIN_RC, font=cst.FONT,
                                          disabled=True,
                                          justification=cst.J_C)],
                            [sg.OK()]
                        ], element_justification=cst.J_C, finalize=True))

                if event == cst.K_MAIN_VPN_CFINFO:
                    WIN[POP].append(
                        sg.Window(cst.T_MAIN_VPN_CF, [
                            [sg.Text(
                                ("Absolute or relative path "
                                 "to OpenVPN configuration file."),
                                font=cst.FONT)],
                            [sg.Text(
                                ("Template and example in config folder. "
                                 "Default:"),
                                font=cst.FONT)],
                            [sg.InputText(cst.DEF_MAIN_VPN_CF, font=cst.FONT,
                                          disabled=True,
                                          justification=cst.J_C)],
                            [sg.OK()]
                        ], element_justification=cst.J_C, finalize=True))

                if event == cst.K_MAIN_BC_CFINFO:
                    WIN[POP].append(
                        sg.Window(cst.T_MAIN_BC_CF, [
                            [sg.Text(
                                ("Absolute or relative path to "
                                 "blockchain network configuration."),
                                font=cst.FONT)],
                            [sg.Text(
                                ("Template and example in config folder. "
                                 "Default:"),
                                font=cst.FONT)],
                            [sg.InputText(cst.DEF_MAIN_BC_CF, font=cst.FONT,
                                          disabled=True,
                                          justification=cst.J_C)],
                            [sg.OK()]
                        ], element_justification=cst.J_C, finalize=True))

                if event == cst.K_MAIN_BC_LFINFO:
                    WIN[POP].append(
                        sg.Window(cst.T_MAIN_BC_LF, [
                            [sg.Text(
                                ("Absolute or relative path to "
                                 "blockchain log file of uploaded reports."),
                                font=cst.FONT)],
                            [sg.Text(("Default:"),
                                     font=cst.FONT)],
                            [sg.InputText(cst.DEF_MAIN_BC_LF, font=cst.FONT,
                                          disabled=True,
                                          justification=cst.J_C)],
                            [sg.OK()]
                        ], element_justification=cst.J_C, finalize=True))

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
                            sg.Window('Error', [
                                [sg.Text((f"Log file/directory path "
                                          f"cannot be created: {errcode}."),
                                         font=cst.FONT)],
                                [sg.Text(font=cst.FONTP)],
                                [sg.OK(button_color=cst.B_C_ERR,
                                       font=cst.FONT)]
                            ], element_justification=cst.J_C,
                                      auto_close=True, keep_on_top=True
                                      ).read(close=True)
                            error = True

                        rc = window[cst.K_MAIN_IT_RC].Get()
                        if not os.path.isfile(rc):
                            sg.Window('Error', [
                                [sg.Text(f"File {rc} does not exist.",
                                         font=cst.FONT)],
                                [sg.Text(font=cst.FONTP)],
                                [sg.OK(button_color=cst.B_C_ERR,
                                       font=cst.FONT)]
                            ], element_justification=cst.J_C,
                                      auto_close=True, keep_on_top=True
                                      ).read(close=True)
                            error = True

                        if window[cst.K_MAIN_VPN_CB].enabled:
                            vpncf = window[cst.K_MAIN_IT_VPN_CF].Get()
                            if not os.path.isfile(vpncf):
                                sg.Window('Error', [
                                    [sg.Text(f"File {vpncf} does not exist.",
                                             font=cst.FONT)],
                                    [sg.Text(font=cst.FONTP)],
                                    [sg.OK(button_color=cst.B_C_ERR,
                                           font=cst.FONT)]
                                ], element_justification=cst.J_C,
                                          auto_close=True, keep_on_top=True
                                          ).read(close=True)
                                error = True

                        if window[cst.K_MAIN_BC_CB].enabled:
                            hc = window[cst.K_MAIN_IT_BC_CF].Get()
                            if not os.path.isfile(hc):
                                sg.Window('Error', [
                                    [sg.Text(f"File {hc} does not exist.",
                                             font=cst.FONT)],
                                    [sg.Text(font=cst.FONTP)],
                                    [sg.OK(button_color=cst.B_C_ERR,
                                           font=cst.FONT)]
                                ], element_justification=cst.J_C,
                                          auto_close=True, keep_on_top=True
                                          ).read(close=True)
                                error = True

                            ho = window[cst.K_MAIN_IT_BC_LF].Get()
                            errcode = utils.check_file_dir(ho)
                            if errcode is not None:
                                sg.Window('Error', [
                                    [sg.Text((f"File path {ho} cannot "
                                              f"be created: {errcode}."),
                                             font=cst.FONT)],
                                    [sg.Text(font=cst.FONTP)],
                                    [sg.OK(button_color=cst.B_C_ERR,
                                           font=cst.FONT)]
                                ], element_justification=cst.J_C,
                                          auto_close=True, keep_on_top=True
                                          ).read(close=True)
                                error = True

                        if not error:
                            if not window[cst.K_MAIN_LOG_CB].enabled:
                                shrink_enlarge_window(
                                    window[cst.K_MAIN_LOG],
                                    window[cst.K_MAIN_LOG_CB],
                                    win_out_sz,
                                    win_out_sz_hidden)
                            if window[cst.K_MAIN_VPN_CB].enabled:
                                cmd_queue.put(('vpn', (vpncf, False)))

                            cmd_queue.put(('msfstart',
                                           (ld,
                                            window[cst.K_MAIN_VPN_CB].enabled,
                                            False,    # stop
                                            False)))  # wizard
                            cmd_queue.put(('msfconn', (cst.DEF_MSFRPC_PWD,)))
                            cmd_queue.put(('msfrun', (rc, lf)))

                            if window[cst.K_MAIN_BC_CB].enabled:
                                cmd_queue.put(('hlfloadconfig', (hc,)))
                                cmd_queue.put(('hlfstore', (lf, ho)))

                            if window[cst.K_MAIN_SC_CB].enabled:
                                cmd_queue.put(('stop', ()))

                            job_run = True

                if event in (cst.K_MAIN_RBC_B, cst.K_MAIN_RBC_T):
                    error = False
                    utils.set_logger(window)

                    lf = window[cst.K_MAIN_IT_LF].Get()
                    if not os.path.isfile(lf):
                        sg.Window('Error', [
                            [sg.Text("Autoauditor log does not exist.",
                                     font=cst.FONT)],
                            [sg.Text(font=cst.FONTP)],
                            [sg.OK(button_color=cst.B_C_ERR,
                                   font=cst.FONT)]
                        ], element_justification=cst.J_C,
                                  auto_close=True, keep_on_top=True
                                  ).read(close=True)
                        error = True

                    if not window[cst.K_MAIN_BC_CB].enabled:
                        sg.Window('Error', [
                            [sg.Text("Blockchain must be enabled.",
                                     font=cst.FONT)],
                            [sg.Text(font=cst.FONTP)],
                            [sg.OK(button_color=cst.B_C_ERR,
                                   font=cst.FONT)]
                            ], element_justification=cst.J_C,
                                  auto_close=True, keep_on_top=True
                                  ).read(close=True)
                        error = True
                    else:
                        hc = window[cst.K_MAIN_IT_BC_CF].Get()
                        if not os.path.isfile(hc):
                            sg.Window('Error', [
                                [sg.Text(f"File {hc} does not exist.",
                                         font=cst.FONT)],
                                [sg.Text(font=cst.FONTP)],
                                [sg.OK(button_color=cst.B_C_ERR,
                                       font=cst.FONT)]
                            ], element_justification=cst.J_C,
                                      auto_close=True, keep_on_top=True
                                      ).read(close=True)
                            error = True

                        ho = window[cst.K_MAIN_IT_BC_LF].Get()
                        errcode = utils.check_file_dir(ho)
                        if errcode is not None:
                            sg.Window('Error', [
                                [sg.Text((f"File path {ho} cannot "
                                          f"be created: {errcode}."),
                                         font=cst.FONT)],
                                [sg.Text(font=cst.FONTP)],
                                [sg.OK(button_color=cst.B_C_ERR,
                                       font=cst.FONT)]
                            ], element_justification=cst.J_C,
                                      auto_close=True, keep_on_top=True
                                      ).read(close=True)
                            error = True

                    if not error:
                        if not window[cst.K_MAIN_LOG_CB].enabled:
                            shrink_enlarge_window(
                                window[cst.K_MAIN_LOG],
                                window[cst.K_MAIN_LOG_CB],
                                win_out_sz,
                                win_out_sz_hidden)
                        cmd_queue.put(('hlfloadconfig', (hc,)))
                        cmd_queue.put(('hlfstore', (lf, ho)))

                if event in (cst.K_MAIN_WIZ_B, cst.K_MAIN_WIZ_T):
                    if WIN[WZ] is None and not job_run:
                        if not window[cst.K_MAIN_LOG_CB].enabled:
                            shrink_enlarge_window(window[cst.K_MAIN_LOG],
                                                  window[cst.K_MAIN_LOG_CB],
                                                  win_out_sz,
                                                  win_out_sz_hidden)
                        utils.set_logger(window)

                        lf = window[cst.K_MAIN_IT_LF].Get()
                        ld = window[cst.K_MAIN_IT_LD].Get()

                        errcode = utils.check_file_dir(lf, ld)
                        if errcode is not None:
                            sg.Window('Error', [
                                [sg.Text("Log file/Log directory",
                                         font=cst.FONT)],
                                [sg.Text("creation permission error.",
                                         font=cst.FONT)],
                                [sg.Text(font=cst.FONTP)],
                                [sg.OK(button_color=cst.B_C_ERR,
                                       font=cst.FONT)]
                            ], element_justification=cst.J_C,
                                      auto_close=True, keep_on_top=True
                                      ).read(close=True)

                        cmd_queue.put(('msfstart', (ld,
                                                    False,   # ovpn
                                                    False,   # stop
                                                    True)))  # wizard
                        cmd_queue.put(('msfconn', (cst.DEF_MSFRPC_PWD,)))
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
                        cmd_queue.put(('vpn', (vpncf, True)))

                    ld = window[cst.K_MAIN_IT_LD].Get()
                    cmd_queue.put(('msfstart',
                                   (ld,
                                    window[cst.K_MAIN_VPN_CB].enabled,
                                    True,     # stop
                                    False)))  # wizard

                    cmd_queue.put(('stop', ()))
                    close_all_windows(stop=True)

                if event == 'LOG':
                    window[cst.K_MAIN_LOG].print(values[event])

                if event == 'GIF':
                    if gif is None:
                        gif = LoadingGif(starting_gif=values[event])
                    gif.update()

                if event == 'GIFSTOP':
                    if gif is not None:
                        gif.stop()
                    gif = None

                if event == 'START':
                    msfcl, is_wizard, stop = values[event]
                    if msfcl is not None:
                        if is_wizard:
                            wizard_window()
                    else:
                        if not stop:
                            sg.Window('Error', [
                                [sg.Text("Containers could not be started",
                                         font=cst.FONT)],
                                [sg.OK(font=cst.FONT,
                                       button_color=cst.B_C_ERR)]
                            ], element_justification=cst.J_C,
                                      auto_close=True, keep_on_top=True
                                      ).read(close=True)

                if event == 'STOP':
                    if values[event] == cst.NOERROR:
                        sg.Window('Success', [
                            [sg.Text("AutoAuditor finished successfully.",
                                     font=cst.FONT)],
                            [sg.OK(font=cst.FONT)]
                        ], element_justification=cst.J_C,
                                  auto_close=True, auto_close_duration=1,
                                  keep_on_top=True).read(close=True)
                    else:
                        sg.Window('Error', [
                            [sg.Text((f"AutoAuditor finished with error: "
                                      f"{values[event]}"),
                                     font=cst.FONT)],
                            [sg.OK(font=cst.FONT,
                                   button_color=cst.B_C_ERR)]
                        ], element_justification=cst.J_C,
                                  keep_on_top=True).read(close=True)
                    job_run = False

                if event == 'CONNECT':
                    if values[event] != cst.NOERROR:
                        sg.Window('Error', [
                            [sg.Text((f"Error establishing connection "
                                      f"with metasploit container: "
                                      f"{values[event]}"),
                                     font=cst.FONT,
                                     button_color=cst.B_C_ERR)],
                            [sg.OK(font=cst.FONT)]
                        ], element_justification=cst.J_C,
                                  auto_close=True, keep_on_top=True
                                  ).read(close=True)

        if window == WIN[WZ]:
            if event == sg.WIN_CLOSED:
                window.close()
                WIN[WZ] = None
                job_run = False
            else:
                if event == cst.K_WIZ_MODT:
                    mtype = values[cst.K_WIZ_MODT]
                    if shared_msfcl is not None:
                        mods = [''] + wizard.get_modules(shared_msfcl, mtype)
                    else:
                        mods = ['Error loading list. '
                                'Wait until metasploit container starts.']
                    window[cst.K_WIZ_MODN](
                        values=mods)
                    window[cst.K_WIZ_MODN](
                        value='')

                if event == cst.K_WIZ_MADD:
                    mname = values[cst.K_WIZ_MODN]
                    if mtype and mname:
                        if mname.startswith('Error'):
                            sg.Window('Error', [
                                    [sg.Text(("Choose module type again "
                                              "to reload module names list."),
                                             font=cst.FONT)],
                                    [sg.OK(button_color=cst.B_C_ERR,
                                           font=cst.FONT)]
                                ], element_justification=cst.J_C,
                                          auto_close=True, keep_on_top=True
                                      ).read(close=True)
                        else:
                            if ts.available_ticket():
                                ticket = ts.get_ticket()
                                tmp_mod = Module(shared_msfcl,
                                                 mtype, mname, ticket)
                                tmp_modules[ticket] = tmp_mod

                                mopts_window(tmp_mod)
                            else:
                                sg.Window('Error', [
                                    [sg.Text((f"Maximum modules allowed "
                                              f"({cst.MAX_MODS})."),
                                             font=cst.FONT)],
                                    [sg.Text(
                                        ("Limit can be changed in "
                                         "utils.py:cst.MAX_MODS"),
                                        font=cst.FONT)],
                                    [sg.OK(button_color=cst.B_C_ERR,
                                           font=cst.FONT)]
                                ], element_justification=cst.J_C,
                                          auto_close=True, keep_on_top=True
                                          ).read(close=True)
                    else:
                        sg.Window('Error', [
                            [sg.Text(
                                "Module type/name not selected.",
                                font=cst.FONT)],
                            [sg.Text(
                                ("Choose a module type and module name "
                                 "from dropdown list."), font=cst.FONT)],
                            [sg.OK(button_color=cst.B_C_ERR,
                                   font=cst.FONT)]
                        ], element_justification=cst.J_C,
                                  auto_close=True, keep_on_top=True
                                  ).read(close=True)

                if event == 'MOD_NEW':
                    ticket, modstate = values[event]
                    if ticket not in tmp_modules and ticket not in modules:
                        sg.Window('Error', [
                            [sg.Text(
                                "Error processing module. Try again.",
                                font=cst.FONT)],
                            [sg.OK(button_color=cst.B_C_ERR,
                                   font=cst.FONT)]
                        ], element_justification=cst.J_C,
                                  auto_close=True, keep_on_top=True
                                  ).read(close=True)
                    elif ticket in tmp_modules:
                        modules[ticket] = tmp_modules[ticket]
                        del tmp_modules[ticket]

                if wiz_medit_re.match(event):
                    ticket = int(event.split("_")[2])  # kwiz_mname_xxx
                    if ticket in WIN[MO]:
                        sg.Window('Error', [
                            [sg.Text("Payload window already open.",
                                     font=cst.FONT)],
                            [sg.Text(font=cst.FONTP)],
                            [sg.OK(button_color=cst.B_C_ERR,
                                   font=cst.FONT)]
                        ], element_justification=cst.J_C
                                  ).read(close=True)
                    else:
                        mopts_window(modules[ticket], edit=True)
                if wiz_mrem_re.match(event):
                    ticket = int(event.split("_")[2])  # kwiz_mrem_xxx
                    window[f"{cst.K_WIZ_MFRAME}{ticket}"](visible=False)
                    # workaround to hide row after removal
                    window[f"{cst.K_WIZ_MFRAME}{ticket}"
                           ].ParentRowFrame.config(width=0, height=1)
                    rm_cancel_mod(ticket, remove=True)
                    # Update column scrollbar
                    window.visibility_changed()
                    window[cst.K_WIZ_MCOL].contents_changed()

                if wiz_minfo_re.match(event):
                    ticket = int(event.split("_")[2])  # kwiz_minfo_xxx
                    mod = get_module(ticket, 'edit')
                    oinfo = mod.info()
                    minfo_lay = [
                        [sg.Text(pad=cst.N_P_TB,
                                 font=cst.FONTP)],
                        [sg.Text(f"{mod.mtype()}/{mod.mname()}",
                                 font=cst.FONTB)],
                        [sg.Text(pad=cst.N_P_TB,
                                 font=cst.FONTP)]
                    ] + [
                        [sg.Frame(cst.N_T, [
                            [sg.Text(el, font=cst.FONTB,
                                     size=cst.EXEC_T_SZ_XS),
                             sg.Text(
                                 TextWrapper(width=cst.WRAP_T_SZ)
                                 .fill(str(oinfo[el])),
                                 font=cst.FONT)
                             ] for el in oinfo],
                                  border_width=cst.N_WDTH)]
                    ] + [[sg.OK(font=cst.FONT)]]

                    WIN[POP].append(
                        sg.Window(cst.T_WIZ_MINFO_TIT, minfo_lay,
                                  element_justification=cst.J_C,
                                  finalize=True))

                if event == cst.K_WIZ_EXIT:
                    cmd_queue.put(('stop', ()))
                    window.close()
                    WIN[WZ] = None
                    job_run = False

                if event == cst.K_WIZ_GEN:
                    ev, _ = sg.Window("Warning", [
                        [sg.Text((f"You are overwriting "
                                  f"{WIN[MN][cst.K_MAIN_IT_RC].Get()}."),
                                 justification=cst.J_C,
                                 font=cst.FONT, pad=cst.N_P_R)],
                        [sg.Text("Do you want to continue?",
                                 justification=cst.J_C,
                                 font=cst.FONTB, pad=cst.N_P_L)],
                        [sg.Text(justification=cst.J_C,
                                 font=cst.FONTP)],
                        [sg.Ok(font=cst.FONT,
                               button_color=cst.B_C_ERR),
                         sg.Cancel(font=cst.FONT)]
                    ], element_justification=cst.J_C).read(close=True)
                    if ev == 'Ok':
                        rc_dict = dump_modules(modules)
                        rc_out = WIN[MN][cst.K_MAIN_IT_RC].Get()
                        with open(rc_out, 'w') as f:
                            json.dump(rc_dict, f, indent=2)
                        utils.log(
                            'succg',
                            f"Resources script generated in {rc_out}")
                        sg.Window('Success', [
                            [sg.Text(
                                "Resources script generated in",
                                font=cst.FONT)],
                            [sg.Text(f"{rc_out}",
                                     font=cst.FONT)],
                            [sg.OK(font=cst.FONT)]
                        ], element_justification=cst.J_C,
                                  auto_close=True, keep_on_top=True
                                  ).read(close=True)
                        sev, _ = sg.Window("Shutdown", [
                            [sg.Text("Close wizard and shutdown containers?",
                                     justification=cst.J_C,
                                     font=cst.FONT, pad=cst.N_P_R)],
                            [sg.Text(cst.N_T,
                                     justification=cst.J_C,
                                     font=cst.FONTP)],
                            [sg.Ok(font=cst.FONT,
                                   button_color=cst.B_C_ERR),
                             sg.Cancel(font=cst.FONT)]
                        ], element_justification=cst.J_C).read(
                            close=True)
                        if sev == 'Ok':
                            cmd_queue.put(('stop', ()))
                            close_all_windows(stop=True)

        if window in WIN[MO].values():
            ax = window[cst.K_MOPTS_ID].Get().split(':')
            ticket, modstate = int(ax[0]), ax[1]

            if event in (sg.WIN_CLOSED, cst.K_MOPTS_CNCL):
                window.close()
                del WIN[MO][ticket]
                if modstate == 'new':
                    rm_cancel_mod(ticket)
            else:
                module = get_module(ticket, modstate)
                if module is not None:
                    if mopts_info_re.match(event):
                        idx = int(event.split('_')[2])  # kmopts_info_xxx
                        opt = window[cst.K_MOPTS+str(idx)].Get()
                        oinfo = module.opt_info(opt)
                        oinfo_lay = [
                            [sg.Text(pad=cst.N_P_TB,
                                     font=cst.FONTP)],
                            [sg.Text(opt, font=cst.FONTB)],
                            [sg.Text(pad=cst.N_P_TB, font=cst.FONTP)]
                        ] + [
                            [sg.Frame(cst.N_T, [
                                [sg.Text(el, font=cst.FONTB,
                                         size=cst.EXEC_T_SZ_XS),
                                 sg.Text(oinfo[el],
                                         font=cst.FONT)
                                 ] for el in oinfo],
                                      border_width=cst.N_WDTH)]
                        ] + [[sg.OK(font=cst.FONT)]]

                        WIN[POP].append(
                            sg.Window(cst.T_MOPTS_HINFO, oinfo_lay,
                                      element_justification=cst.J_C,
                                      finalize=True))

                    if event == cst.K_MOPTS_PADD:
                        if not window[cst.K_MOPTS_PDD].Get():
                            sg.Window('Error', [
                                [sg.Text(
                                    "Payload not selected.", font=cst.FONT)],
                                [sg.Text(
                                    "Choose payload from dropdown list.",
                                    font=cst.FONT)],
                                [sg.OK(button_color=cst.B_C_ERR,
                                       font=cst.FONT)]
                            ], element_justification=cst.J_C
                                      ).read(close=True)
                        else:
                            if ticket in WIN[PO]:
                                sg.Window('Error', [
                                    [sg.Text("Payload window already open.",
                                             font=cst.FONT)],
                                    [sg.Text(font=cst.FONTP)],
                                    [sg.OK(button_color=cst.B_C_ERR,
                                           font=cst.FONT)]
                                ], element_justification=cst.J_C
                                          ).read(close=True)
                            else:
                                popts_window(module,
                                             modstate,
                                             window[cst.K_MOPTS_PDD].Get())

                    if event == cst.K_MOPTS_PEDIT:
                        if ticket in WIN[PO]:
                            sg.Window('Error', [
                                [sg.Text("Payload window already open.",
                                         font=cst.FONT)],
                                [sg.Text(font=cst.FONTP)],
                                [sg.OK(button_color=cst.B_C_ERR,
                                       font=cst.FONT)]
                            ], element_justification=cst.J_C
                                      ).read(close=True)
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
                            tmp_pname = window[cst.K_MOPTS_PDD].Get()
                            tmp_pay = wizard.get_payload(
                                shared_msfcl, tmp_pname)
                            tmp_pinfo = wizard.get_module_info(tmp_pay)
                            tmp_pinfo_lay = [
                                [sg.Text(pad=cst.N_P_TB,
                                         font=cst.FONTP)],
                                [sg.Text(tmp_pname, font=cst.FONTB)],
                                [sg.Text(pad=cst.N_P_TB,
                                         font=cst.FONTP)]
                            ] + [
                                [sg.Frame(cst.N_T, [
                                    [sg.Text(el, font=cst.FONTB,
                                             size=cst.EXEC_T_SZ_XS),
                                     sg.Text(
                                         TextWrapper(width=cst.WRAP_T_SZ)
                                         .fill(str(tmp_pinfo[el])),
                                         font=cst.FONT)]
                                    for el in tmp_pinfo],
                                          border_width=cst.N_WDTH)]
                            ] + [[sg.OK(font=cst.FONT)]]

                            WIN[POP].append(
                                sg.Window(cst.T_MOPTS_PINFO_TIT,
                                          tmp_pinfo_lay,
                                          element_justification=cst.J_C,
                                          finalize=True)
                            )

                    if event == cst.K_MOPTS_ACPT:
                        ax_opts, _ = module.options()

                        tmp_opts = {}
                        for idx, opt in enumerate(ax_opts):
                            opt_val = utils.correct_type(
                                window[f"{cst.K_MOPTS_VAL}{idx}"].Get(),
                                module.opt_info(
                                    window[f"{cst.K_MOPTS}{idx}"].Get())
                            )
                            if ax_opts[opt] != opt_val:
                                tmp_opts[opt] = opt_val

                        invalid = []
                        missing = []
                        for opt in tmp_opts:
                            if isinstance(tmp_opts[opt], str):
                                if tmp_opts[opt].startswith('Invalid'):
                                    invalid.append(
                                        (opt, tmp_opts[opt].split('. ')[1]))
                                elif tmp_opts[opt].startswith('Missing'):
                                    missing.append(opt)
                        if invalid or missing:
                            invmis_lay = []
                            if invalid:
                                invmis_lay.extend([
                                    [sg.Text("Invalid value in options:",
                                             font=cst.FONT)],
                                    [sg.Text(f"{invalid}",
                                             font=cst.FONT)]])
                            if invalid and missing:
                                invmis_lay.extend([
                                    [sg.Text(font=cst.FONTP)]])
                            if missing:
                                invmis_lay.extend([
                                    [sg.Text("Missing value in options:",
                                             font=cst.FONT)],
                                    [sg.Text(f"{missing}",
                                             font=cst.FONT)]])
                            invmis_lay.extend([
                                [sg.Text(font=cst.FONTP)],
                                [sg.OK(button_color=cst.B_C_ERR,
                                       font=cst.FONT)]])
                            sg.Window('Error', invmis_lay,
                                      element_justification=cst.J_C,
                                      keep_on_top=True).read(close=True)
                        else:
                            cur_opts = module.mopts()

                            for opt in tmp_opts:
                                cur_opts[opt] = tmp_opts[opt]

                            WIN[WZ][cst.K_WIZ_MNAME+str(ticket)](
                                value=f"{module.mtype()}: {module.mname()}")
                            WIN[WZ][cst.K_WIZ_MFRAME+str(ticket)](
                                visible=True)
                            # Update column scrollbar
                            WIN[WZ].visibility_changed()
                            WIN[WZ][cst.K_WIZ_MCOL].contents_changed()
                            WIN[WZ][cst.K_WIZ_MCOL].Widget.canvas.yview_moveto(
                                999)  # set scrollbar to last element
                            WIN[WZ].write_event_value('MOD_NEW',
                                                      (ticket, modstate))
                            window.close()
                            del WIN[MO][ticket]
                else:
                    sg.Window('Error', [
                        [sg.Text(
                            "Error processing module. Add module again.",
                            font=cst.FONT)],
                        [sg.OK(button_color=cst.B_C_ERR,
                               font=cst.FONT)]
                    ], element_justification=cst.J_C,
                              auto_close=True).read(close=True)
                    window.close()
                    del WIN[MO][ticket]
                    if ticket in WIN[PO]:
                        WIN[PO][ticket].close()
                        del WIN[PO][ticket]

        if window in WIN[PO].values():
            ax = window[cst.K_POPTS_ID].Get().split(':')
            ticket, modstate, paystate = int(ax[0]), ax[1], ax[2]
            module = get_module(ticket, modstate)

            if module is not None:
                if event in (sg.WIN_CLOSED, cst.K_POPTS_CNCL):
                    window.close()
                    del WIN[PO][ticket]
                    if paystate == 'new':
                        del module.payload
                else:
                    if popts_info_re.match(event):
                        idx = int(event.split('_')[2])  # kpopts_info_xxx
                        popt = window[cst.K_POPTS+str(idx)].Get()
                        pinfo = module.payload.opt_info(popt)
                        pinfo_lay = [
                            [sg.Text(pad=cst.N_P_TB,
                                     font=cst.FONTP)],
                            [sg.Text(popt, font=cst.FONTB)],
                            [sg.Text(pad=cst.N_P_TB,
                                     font=cst.FONTP)]
                        ] + [[sg.Frame(cst.N_T,
                                       [[sg.Text(el,
                                                 font=cst.FONTB,
                                                 size=cst.EXEC_T_SZ_S),
                                         sg.Text(pinfo[el],
                                                 font=cst.FONT)]
                                        for el in pinfo],
                                       border_width=cst.N_WDTH)]
                             ] + [[sg.OK(font=cst.FONT)]]

                        WIN[POP].append(
                            sg.Window(cst.T_POPTS_INFO_TIT, pinfo_lay,
                                      element_justification=cst.J_C,
                                      finalize=True))

                    if event == cst.K_POPTS_ACPT:
                        ax_popts, _ = module.payload.options()
                        tmp_popts = {}
                        for idx, popt in enumerate(ax_popts):
                            popt_val = utils.correct_type(
                                    window[cst.K_POPTS_VAL+str(idx)].Get(),
                                    module.payload.opt_info(
                                        window[cst.K_POPTS+str(idx)].Get()))
                            if ax_popts[popt] != popt_val:
                                tmp_popts[popt] = popt_val

                        invalid = []
                        missing = []
                        for popt in tmp_popts:
                            if isinstance(tmp_popts[popt], str):
                                if tmp_popts[popt].startswith('Invalid'):
                                    invalid.append(popt)
                                elif tmp_popts[popt].startswith('Missing'):
                                    missing.append(popt)
                        if invalid or missing:
                            invmis_lay = []
                            if invalid:
                                invmis_lay.extend([
                                    [sg.Text("Invalid value in options:",
                                             font=cst.FONT)],
                                    [sg.Text(f"{invalid}",
                                             font=cst.FONT)]])
                            if invalid and missing:
                                invmis_lay.extend([
                                    [sg.Text(font=cst.FONTP)]])
                            if missing:
                                invmis_lay.extend([
                                    [sg.Text("Missing value in options:",
                                             font=cst.FONT)],
                                    [sg.Text(f"{missing}",
                                             font=cst.FONT)]])
                            invmis_lay.extend([
                                [sg.Text(font=cst.FONTP)],
                                [sg.OK(button_color=cst.B_C_ERR,
                                       font=cst.FONT)]])
                            sg.Window('Error', invmis_lay,
                                      element_justification=cst.J_C,
                                      keep_on_top=True).read(close=True)
                        else:
                            cur_popts = module.payload.mopts()
                            for popt in tmp_popts:
                                cur_popts[popt] = tmp_popts[popt]

                            WIN[MO][ticket][cst.K_MOPTS_PDD](disabled=True)
                            WIN[MO][ticket][cst.K_MOPTS_PADD](disabled=True)
                            WIN[MO][ticket][cst.K_MOPTS_PEDIT](disabled=False)
                            WIN[MO][ticket][cst.K_MOPTS_PREM](disabled=False)
                            window.close()
                            del WIN[PO][ticket]
            else:
                sg.Window('Error', [
                    [sg.Text(
                        "Error processing module. Add module again.",
                        font=cst.FONT)],
                    [sg.OK(button_color=cst.B_C_ERR,
                           font=cst.FONT)]
                ], element_justification=cst.J_C,
                          auto_close=True).read(close=True)
                window.close()
                del WIN[PO][ticket]
                if ticket in WIN[MO]:
                    WIN[MO][ticket].close()
                    del WIN[MO][ticket]


if __name__ == "__main__":
    main()
