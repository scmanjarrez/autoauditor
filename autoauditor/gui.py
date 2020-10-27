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
import constants as const
import utils
import metasploit
import wizard
import re
import vpn
import json
import blockchain
import os

sg.theme('Reddit')


def browse(text, key, target, image, image_size, color, border,
           disabled=False, tooltip=None, filetype=True, pad=None):
    if filetype:
        bt = sg.FileBrowse(button_text=text, button_color=color,
                           target=target, key=key,
                           tooltip=tooltip, disabled=disabled,
                           pad=pad)
    else:
        bt = sg.FolderBrowse(button_text=text, button_color=color,
                             target=target, key=key,
                             tooltip=tooltip, disabled=disabled,
                             pad=pad)
    bt.ImageData = image
    bt.ImageSize = image_size
    bt.BorderWidth = border
    return bt


def input_text(default, key, disabled=False, font=None,
               pad=None, visible=True):
    it = sg.InputText(default, key=key, disabled=disabled,
                      font=font, pad=pad, visible=visible)
    return it


def button(text, key, image, image_size, color, border,
           tooltip, pad=None, disabled=False, visible=True):
    bt = sg.Button(text, key=key, image_size=image_size,
                   button_color=color, border_width=border,
                   image_data=image, tooltip=tooltip,
                   pad=pad, disabled=disabled, visible=visible)
    return bt


class ImageCheckBox(sg.Button):
    def __init__(self, image_on, image_off, image_size, key,
                 button_color, border_width, enabled, pad=None):
        self.enabled = enabled
        self.image_on = image_on
        self.image_off = image_off
        super().__init__(image_data=image_on if enabled else image_off,
                         image_size=image_size, key=key,
                         button_color=button_color, border_width=border_width,
                         pad=pad)

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


def pay_window(client, parent_window, current_payload):
    pay_name = parent_window[const.KEY_PAY_DD].Get()
    pay = wizard.get_payload(client, pay_name)
    popts, propts = wizard.get_module_options(pay)
    popts_default = popts.copy()

    for popt in current_payload['OPTIONS']:
        popts[popt] = current_payload['OPTIONS'][popt]

    scrollable = len(popts) > 15

    popt_layout = [
        [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB, font=const.FONTPAD)],
        [sg.Text(pay_name, font=const.FONTB)],
        [sg.Frame(const.NO_TEXT, [
            [sg.Text(const.NO_TEXT, font=const.FONTPAD, pad=const.PAD_NO,
                     size=const.TEXT_DESC_SIZE_XL2 if scrollable
                     else const.TEXT_DESC_SIZE_XL3)],
            [sg.Text(const.TEXT_OPT_NAME, font=const.FONTB,
                     size=const.TEXT_OPT_NAME_SIZE,
                     pad=const.PAD_OPT_HEAD_NAME),
             sg.Text(const.TEXT_OPT_VAL, font=const.FONTB,
                     size=const.TEXT_OPT_VAL_SIZE, pad=const.PAD_OPT_HEAD_VAL),
             sg.Text(const.TEXT_OPT_REQ, font=const.FONTB,
                     pad=const.PAD_OPT_HEAD_REQ if scrollable
                     else const.PAD_OPT_HEAD_REQ2, size=const.TEXT_REQ_SIZE),
             sg.Text(const.TEXT_OPT_INFO, font=const.FONTB,
                     pad=const.PAD_OPT_HEAD_INFO)]
        ], border_width=const.NO_BORDER, pad=const.PAD_NO_L)],
        [sg.Column([
            [sg.Frame(const.NO_TEXT, [
                [sg.InputText(popt, size=const.TEXT_DESC_SIZE_2,
                              key=const.KEY_PAY_OPT+str(idx),
                              pad=const.PAD_IT_T2, font=const.FONT,
                              disabled_readonly_background_color=const.COLOR_T,
                              readonly=True, border_width=const.NO_BORDER),
                 sg.InputText(str(popts[popt]), size=const.TEXT_DESC_SIZE_M,
                              key=const.KEY_PAY_OPT_VAL+str(idx),
                              pad=const.PAD_IT_T2, font=const.FONT),
                 sg.Text(const.TEXT_REQ_Y if popt in propts
                         else const.TEXT_REQ_N,
                         size=const.TEXT_REQ_SIZE, font=const.FONT,
                         pad=const.PAD_IT_T_TR if scrollable
                         else const.PAD_IT_T_TR2),
                 button(const.NO_TEXT, const.KEY_PAY_OPT_HELP+str(idx),
                        const.INFO, const.BUTTON_S_SIZE,
                        const.BUTTON_COLOR, const.NO_BORDER,
                        wizard.get_option_desc(pay, popt))]],
                      border_width=const.NO_BORDER, pad=const.PAD_NO)]
            for idx, popt in enumerate(popts)],
                   size=const.OPT_MOD_COLUMN_SIZE if scrollable
                   else const.get_exact_column_size(len(popts)),
                   scrollable=scrollable, vertical_scroll_only=True),
         ],
        [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB)],
        [sg.Button('Accept', key=const.KEY_PAY_OPT_ACCEPT, font=const.FONT),
         sg.Button('Cancel', key=const.KEY_PAY_OPT_CANCEL, font=const.FONT)]]

    pwindow = sg.Window(  # payload options window
        const.TEXT_PAYLOAD_OPTIONS, popt_layout,
        element_justification=const.CENTER, finalize=True)
    help_regex = re.compile(const.KEY_PAY_OPT_HELP+r'\d+')
    while True:
        pevent, _ = pwindow.read()
        if pevent is not None and help_regex.match(pevent):
            popt_n = int(pevent.split('_')[3])  # payload_option_help_xxx
            popt = pwindow[const.KEY_PAY_OPT+str(popt_n)].Get()
            popt_info = wizard.get_option_info(pay, popt)
            pinfo_layout = [
                [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB,
                         font=const.FONTPAD)],
                [sg.Text(popt, font=const.FONTB)],
                [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB,
                         font=const.FONTPAD)]
            ] + [[sg.Frame(const.NO_TEXT,
                           [[sg.Text(el,
                                     font=const.FONTB,
                                     size=const.EXEC_TEXT_SIZE_S),
                             sg.Text(popt_info[el],
                                     font=const.FONT)]
                            for el in popt_info],
                           border_width=const.NO_BORDER)]
                 ] + [[sg.OK(font=const.FONT)]]

            sg.Window(const.TEXT_PAYLOAD_OPTION_INFO, pinfo_layout,
                      element_justification=const.CENTER).read(close=True)

        if pevent == const.KEY_PAY_OPT_ACCEPT:
            current_payload['NAME'] = pay_name
            for idx, popt in enumerate(popts):
                if popts_default[popt] != utils.correct_type(
                        pwindow[const.KEY_PAY_OPT_VAL+str(idx)].Get(),
                        wizard.get_option_info(
                            pay,
                            pwindow[const.KEY_PAY_OPT+str(idx)].Get())):
                    current_payload['OPTIONS'][popt] = utils.correct_type(
                        pwindow[const.KEY_PAY_OPT_VAL+str(idx)].Get(),
                        wizard.get_option_info(
                            pay,
                            pwindow[const.KEY_PAY_OPT+str(idx)].Get()))

            invalid = []
            missing = []
            for cpopt in current_payload['OPTIONS']:
                if current_payload['OPTIONS'][cpopt] == 'Invalid':
                    invalid.append(cpopt)
                elif current_payload['OPTIONS'][cpopt] == 'Missing':
                    missing.append(cpopt)
            if invalid or missing:
                invmislayout = []
                if invalid:
                    invmislayout.extend([
                        [sg.Text("Invalid value in the following options:",
                                 font=const.FONT)],
                        [sg.Text("{}".format(invalid),
                                 font=const.FONT)]])
                if invalid and missing:
                    invmislayout.extend([
                        [sg.Text(const.NO_TEXT, font=const.FONTPAD)]])
                if missing:
                    invmislayout.extend([
                        [sg.Text("Missing value in the following options:",
                                 font=const.FONT)],
                        [sg.Text("{}".format(missing),
                                 font=const.FONT)]])
                invmislayout.extend([
                    [sg.Text(const.NO_TEXT, font=const.FONTPAD)],
                    [sg.OK(button_color=const.BUTTON_COLOR_ERR,
                           font=const.FONT)]])
                sg.Window('Error', invmislayout,
                          element_justification=const.CENTER).read(close=True)
                continue

            parent_window[const.KEY_PAY_ADD](disabled=True)
            parent_window[const.KEY_PAY_EDIT](disabled=False)
            parent_window[const.KEY_PAY_REM](disabled=False)
            break
        if pevent in (sg.WIN_CLOSED, const.KEY_PAY_OPT_CANCEL):
            break
    pwindow.close()


def opt_window(client, parent_window,
               mod_list, mtype, mname, mod_idx,
               edit=False):
    added = False
    mod = None
    tmp_pay_opt = {'NAME': '', 'OPTIONS': {}}

    try:
        mod = wizard.get_module(client, mtype, mname)
    except TypeError:
        sg.Window('Error', [
            [sg.Text("Module name does not match module type.",
                     font=const.FONT)],
            [sg.Text(const.NO_TEXT, font=const.FONTPAD)],
            [sg.OK(button_color=const.BUTTON_COLOR_ERR, font=const.FONT)]
        ], element_justification=const.CENTER,
                  auto_close=True).read(close=True)
        return added
    opts, ropts = wizard.get_module_options(mod)
    opts_default = opts.copy()
    if edit:
        current_opts = mod_list[mtype][mname][mod_idx]
        for copt in current_opts:
            if copt == 'PAYLOAD':
                continue
            opts[copt] = current_opts[copt]
        try:
            tmp_pay_opt = mod_list[mtype][mname][mod_idx]['PAYLOAD']
        except KeyError:
            pass
    scrollable = len(opts) > 15
    opt_layout = [
        [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB, font=const.FONTPAD)],
        [sg.Text("/".join([mtype, mname]), font=const.FONTB)],
        [sg.Frame(const.NO_TEXT, [
            [sg.Text(const.NO_TEXT, font=const.FONTPAD, pad=const.PAD_NO,
                     size=const.TEXT_DESC_SIZE_XL2 if scrollable
                     else const.TEXT_DESC_SIZE_XL3)],
            [sg.Text(const.TEXT_OPT_NAME, font=const.FONTB,
                     size=const.TEXT_OPT_NAME_SIZE,
                     pad=const.PAD_OPT_HEAD_NAME),
             sg.Text(const.TEXT_OPT_VAL, font=const.FONTB,
                     size=const.TEXT_OPT_VAL_SIZE, pad=const.PAD_OPT_HEAD_VAL),
             sg.Text(const.TEXT_OPT_REQ, font=const.FONTB,
                     pad=const.PAD_OPT_HEAD_REQ if scrollable
                     else const.PAD_OPT_HEAD_REQ2, size=const.TEXT_REQ_SIZE),
             sg.Text(const.TEXT_OPT_INFO, font=const.FONTB,
                     pad=const.PAD_OPT_HEAD_INFO)]
        ], border_width=const.NO_BORDER, pad=const.PAD_NO_L)],
        [sg.Column(
            [[sg.Frame(const.NO_TEXT, [
                [sg.InputText(opt, size=const.TEXT_DESC_SIZE_2,
                              key=const.KEY_OPT+str(idx), pad=const.PAD_IT_T2,
                              font=const.FONT,
                              disabled_readonly_background_color=const.COLOR_T,
                              readonly=True, border_width=const.NO_BORDER),
                 sg.InputText(str(opts[opt]), size=const.TEXT_DESC_SIZE_M,
                              key=const.KEY_OPT_VAL+str(idx),
                              pad=const.PAD_IT_T2, font=const.FONT),
                 sg.Text(const.TEXT_REQ_Y if opt in ropts
                         else const.TEXT_REQ_N, size=const.TEXT_REQ_SIZE,
                         font=const.FONT, pad=const.PAD_IT_T_TR if scrollable
                         else const.PAD_IT_T_TR2),
                 button(const.NO_TEXT, const.KEY_OPT_HELP+str(idx), const.INFO,
                        const.BUTTON_S_SIZE, const.BUTTON_COLOR,
                        const.NO_BORDER, wizard.get_option_desc(mod, opt))]
            ], border_width=const.NO_BORDER, pad=const.PAD_NO)]
             for idx, opt in enumerate(opts)],
            size=const.OPT_MOD_COLUMN_SIZE if scrollable
            else const.get_exact_column_size(len(opts)),
            scrollable=scrollable, vertical_scroll_only=True),
         ]]

    if wizard.has_payloads(mod):
        disable = not tmp_pay_opt['OPTIONS']
        opt_layout.extend(
            [
                [sg.Frame(const.NO_TEXT, [
                    [sg.Text(const.TEXT_PAYLOAD, key=const.KEY_PAY_T,
                             size=const.TEXT_DESC_SIZE_2,
                             pad=const.PAD_IT_T3, font=const.FONT),
                     sg.DropDown(wizard.get_module_payloads(mod),
                                 size=const.EXEC_TEXT_SIZE_L2,
                                 font=const.FONT, key=const.KEY_PAY_DD,
                                 readonly=True, pad=const.PAD_IT_T4,
                                 default_value=(mod_list[mtype][mname][mod_idx]
                                                ['PAYLOAD']['NAME'])
                                 if edit and 'PAYLOAD' in (mod_list[mtype]
                                                           [mname][mod_idx])
                                 else ''),
                     button(const.NO_TEXT, const.KEY_PAY_ADD, const.ADD24,
                            const.BUTTON_S_SIZE, const.BUTTON_COLOR,
                            const.NO_BORDER, const.TOOLTIP_PAY_ADD,
                            pad=const.PAD_IT_T5, disabled=not disable),
                     button(const.NO_TEXT, const.KEY_PAY_EDIT, const.EDIT,
                            const.BUTTON_M_SIZE, const.BUTTON_COLOR,
                            const.NO_BORDER, const.TOOLTIP_PAY_EDIT,
                            pad=const.PAD_IT_T6, disabled=disable),
                     button(const.NO_TEXT, const.KEY_PAY_REM, const.REMOVE,
                            const.BUTTON_M_SIZE,
                            const.BUTTON_COLOR, const.NO_BORDER,
                            const.TOOLTIP_PAY_REMOVE, pad=const.PAD_IT_T6,
                            disabled=disable),
                     button(const.NO_TEXT, const.KEY_PAY_INFO, const.INFO,
                            const.BUTTON_S_SIZE, const.BUTTON_COLOR,
                            const.NO_BORDER, const.TOOLTIP_PAY_INFO,
                            pad=const.PAD_IT_T7 if scrollable
                            else const.PAD_IT_T7_NS)]
                ], border_width=const.NO_BORDER,
                          pad=const.PAD_NO_LB if scrollable
                          else const.PAD_NO_LB_NS)]])

    opt_layout.extend(
        [
            [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB)],
            [sg.Button('Accept', key=const.KEY_OPT_ACCEPT, font=const.FONT),
             sg.Button('Cancel', key=const.KEY_OPT_CANCEL, font=const.FONT)]])

    owindow = sg.Window(  # options window
        const.TEXT_OPTIONS, opt_layout,
        element_justification=const.CENTER, finalize=True)

    help_regex = re.compile(const.KEY_OPT_HELP+r'\d+')
    while True:
        oevent, _ = owindow.read()
        if oevent is not None and help_regex.match(oevent):
            opt_n = int(oevent.split('_')[2])  # option_help_xxx
            opt = owindow[const.KEY_OPT+str(opt_n)].Get()
            opt_info = wizard.get_option_info(mod, opt)
            # todo: wrap text when too large
            info_layout = [
                [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB,
                         font=const.FONTPAD)],
                [sg.Text(opt, font=const.FONTB)],
                [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB,
                         font=const.FONTPAD)]] + [
                             [sg.Frame(const.NO_TEXT,
                                       [[sg.Text(el, font=const.FONTB,
                                                 size=const.EXEC_TEXT_SIZE_XS),
                                         sg.Text(opt_info[el],
                                                 font=const.FONT)]
                                        for el in opt_info],
                                       border_width=const.NO_BORDER)]
                         ] + [[sg.OK(font=const.FONT)]]

            sg.Window(const.TEXT_OPTION_INFO, info_layout,
                      element_justification=const.CENTER).read(close=True)

        if oevent == const.KEY_PAY_ADD:
            if not owindow[const.KEY_PAY_DD].Get():
                sg.Window('Error', [
                    [sg.Text(
                        "Payload not selected.", font=const.FONT)],
                    [sg.Text(
                        "Choose a payload from the dropdown.",
                        font=const.FONT)],
                    [sg.OK(button_color=const.BUTTON_COLOR_ERR,
                           font=const.FONT)]
                ], element_justification=const.CENTER,
                          auto_close=True).read(close=True)
            else:
                if tmp_pay_opt['OPTIONS']:
                    sg.Window('Error', [
                        [sg.Text(
                            "Payload already exists.", font=const.FONT)],
                        [sg.Text(
                            "Delete current payload before adding new one.",
                            font=const.FONT)],
                        [sg.OK(button_color=const.BUTTON_COLOR_ERR,
                               font=const.FONT)]
                    ], element_justification=const.CENTER,
                              auto_close=True).read(close=True)
                else:
                    pay_window(
                        client, owindow, tmp_pay_opt)

        if oevent == const.KEY_PAY_EDIT:
            pay_window(
                client, owindow, tmp_pay_opt)

        if oevent == const.KEY_PAY_REM:
            tmp_pay_opt = {'NAME': '', 'OPTIONS': {}}
            owindow[const.KEY_PAY_DD](value='')
            owindow[const.KEY_PAY_ADD](disabled=False)
            owindow[const.KEY_PAY_EDIT](disabled=True)
            owindow[const.KEY_PAY_REM](disabled=True)

        if oevent == const.KEY_PAY_INFO:
            if owindow[const.KEY_PAY_DD].Get():
                pay_n = owindow[const.KEY_PAY_DD].Get()
                pay = wizard.get_payload(client, pay_n)
                pay_info = wizard.get_module_info(pay)
                pay_info_layout = [
                    [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB,
                             font=const.FONTPAD)],
                    [sg.Text(pay_n, font=const.FONTB)],
                    [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB,
                             font=const.FONTPAD)]
                ] + [
                    [sg.Frame(const.NO_TEXT,
                              [[sg.Text(el, font=const.FONTB,
                                        size=const.EXEC_TEXT_SIZE_XS),
                                sg.Text(
                                    TextWrapper(width=const.WRAP_TEXT_SIZE)
                                    .fill(str(pay_info[el])),
                                    font=const.FONT)]
                               for el in pay_info],
                              border_width=const.NO_BORDER)]
                ] + [[sg.OK(font=const.FONT)]]

                sg.Window(const.TEXT_PAYLOAD_INFO, pay_info_layout,
                          element_justification=const.CENTER).read(close=True)

        if oevent == const.KEY_OPT_ACCEPT:
            if mtype not in mod_list:
                mod_list[mtype] = {}
            if mname not in mod_list[mtype]:
                mod_list[mtype][mname] = {}

            opt_l = {
                opt: utils.correct_type(
                    owindow[const.KEY_OPT_VAL+str(idx)].Get(),
                    wizard.get_option_info(mod,
                                           owindow[const.KEY_OPT
                                                   + str(idx)].Get()
                                           )
                )
                for idx, opt in enumerate(opts)
                if opt != 'PAYLOAD'
                and opts_default[opt] != utils.correct_type(
                    owindow[const.KEY_OPT_VAL+str(idx)].Get(),
                    wizard.get_option_info(mod,
                                           owindow[const.KEY_OPT
                                                   + str(idx)].Get()
                                           )
                )
            }

            invalid = []
            missing = []
            for op in opt_l:
                if opt_l[op] == 'Invalid':
                    invalid.append(op)
                elif opt_l[op] == 'Missing':
                    missing.append(op)
            if invalid or missing:
                print(invalid)
                print(missing)
                invmislayout = []
                if invalid:
                    invmislayout.extend([
                        [sg.Text("Invalid value in the following options:",
                                 font=const.FONT)],
                        [sg.Text("{}".format(invalid),
                                 font=const.FONT)]])
                if invalid and missing:
                    invmislayout.extend([
                        [sg.Text(const.NO_TEXT, font=const.FONTPAD)]])
                if missing:
                    invmislayout.extend([
                        [sg.Text("Missing value in the following options:",
                                 font=const.FONT)],
                        [sg.Text("{}".format(missing),
                                 font=const.FONT)]])
                invmislayout.extend([
                    [sg.Text(const.NO_TEXT, font=const.FONTPAD)],
                    [sg.OK(button_color=const.BUTTON_COLOR_ERR,
                           font=const.FONT)]])
                sg.Window('Error', invmislayout,
                          element_justification=const.CENTER).read(close=True)
                continue
            if tmp_pay_opt['OPTIONS']:
                opt_l['PAYLOAD'] = tmp_pay_opt

            mod_list[mtype][mname][mod_idx] = opt_l

            parent_window[const.KEY_MOD_NAME +
                          str(mod_idx)](value=": ".join([mtype, mname]))
            parent_window[const.KEY_MOD_FRAME +
                          str(mod_idx)](visible=True)
            # Update column scrollbar
            parent_window.visibility_changed()
            parent_window[const.KEY_MOD_COL].contents_changed()
            parent_window[const.KEY_MOD_COL].Widget.canvas.yview_moveto(
                999)  # workaround to update column scrollbar
            added = True
            break
        if oevent in (sg.WIN_CLOSED, const.KEY_OPT_CANCEL):
            break
    owindow.close()
    return added


def switch(window, button, *elems):
    for el in elems:
        if isinstance(el, (sg.InputText, sg.Button)):
            el(disabled=button.enabled)
        if isinstance(el, str):
            window[el](
                text_color=const.COLOR_DISABLED if button.enabled
                else const.COLOR_ENABLED)
    button.switch()


def shrink_enlarge_window(window, console, console_cb, cons_size, ncons_size):
    console(visible=not console_cb.enabled)
    console_cb.switch()
    if console_cb.enabled:
        window.size = cons_size
    else:
        window.size = ncons_size
    window.visibility_changed()


def main():
    lf_fb = browse(const.NO_TEXT, const.KEY_LF_FB, const.KEY_INPUT_LF,
                   const.FILEPNG, const.BUTTON_M_SIZE,
                   const.BUTTON_COLOR, const.NO_BORDER,
                   tooltip=const.TOOLTIP_FILE_BROWSER, pad=const.PAD_NO_TB)
    lf_i_b = button(const.NO_TEXT, const.KEY_LF_I_B, const.INFO,
                    const.BUTTON_S_SIZE, const.BUTTON_COLOR,
                    const.NO_BORDER, const.TOOLTIP_LF,
                    pad=const.PAD_NO_TBR)
    ld_fb = browse(const.NO_TEXT, const.KEY_LD_FB, const.KEY_INPUT_LD,
                   const.FOLDERPNG, const.BUTTON_M_SIZE, const.BUTTON_COLOR,
                   const.NO_BORDER, tooltip=const.TOOLTIP_FOLDER_BROWSER,
                   filetype=False, pad=const.PAD_NO_TB)
    ld_i_b = button(const.NO_TEXT, const.KEY_LD_I_B, const.INFO,
                    const.BUTTON_S_SIZE, const.BUTTON_COLOR, const.NO_BORDER,
                    const.TOOLTIP_LD, pad=const.PAD_NO_TBR)
    rc_fb = browse(const.NO_TEXT, const.KEY_RC_FB, const.KEY_INPUT_RC,
                   const.FILEPNG, const.BUTTON_M_SIZE,
                   const.BUTTON_COLOR, const.NO_BORDER,
                   tooltip=const.TOOLTIP_FILE_BROWSER, pad=const.PAD_NO_TB)
    rc_i_b = button(const.NO_TEXT, const.KEY_RC_I_B, const.INFO,
                    const.BUTTON_S_SIZE, const.BUTTON_COLOR,
                    const.NO_BORDER, const.TOOLTIP_RC, pad=const.PAD_NO_TBR)

    vpn_cb = ImageCheckBox(image_on=const.CBON, image_off=const.CBOFF,
                           image_size=const.BUTTON_S_SIZE,
                           key=const.KEY_VPN_CB,
                           button_color=const.BUTTON_COLOR,
                           border_width=const.NO_BORDER, enabled=False)
    vpn_cf_i_b = button(const.NO_TEXT, const.KEY_VPN_CF_I_B,
                        const.INFO, const.BUTTON_S_SIZE,
                        const.BUTTON_COLOR, const.NO_BORDER,
                        const.TOOLTIP_VPN_CF,
                        disabled=True, pad=const.PAD_NO_TBR)
    vpn_cf_it = input_text(const.DEFAULT_VPN_CF, const.KEY_INPUT_VPN_CF,
                           disabled=True, font=const.FONT, pad=const.PAD_IT_T)
    vpn_cf_fb = browse(const.NO_TEXT, const.KEY_VPN_CF_FB,
                       const.KEY_INPUT_VPN_CF, const.FILEPNG,
                       const.BUTTON_M_SIZE, const.BUTTON_COLOR,
                       const.NO_BORDER, disabled=True,
                       tooltip=const.TOOLTIP_FILE_BROWSER, pad=const.PAD_NO_TB)

    bc_cb = ImageCheckBox(image_on=const.CBON, image_off=const.CBOFF,
                          image_size=const.BUTTON_S_SIZE,
                          key=const.KEY_BC_CB, button_color=const.BUTTON_COLOR,
                          border_width=const.NO_BORDER, enabled=False)
    bc_cf_i_b = button(const.NO_TEXT, const.KEY_BC_CF_I_B, const.INFO,
                       const.BUTTON_S_SIZE, const.BUTTON_COLOR,
                       const.NO_BORDER, const.TOOLTIP_BC_CF,
                       disabled=True, pad=const.PAD_NO_TBR)
    bc_cf_it = input_text(const.DEFAULT_BC_CF, const.KEY_INPUT_BC_CF,
                          disabled=True, font=const.FONT, pad=const.PAD_IT_T)
    bc_cf_fb = browse(const.NO_TEXT, const.KEY_BC_CF_FB, const.KEY_INPUT_BC_CF,
                      const.FILEPNG, const.BUTTON_M_SIZE, const.BUTTON_COLOR,
                      const.NO_BORDER, disabled=True,
                      tooltip=const.TOOLTIP_FILE_BROWSER, pad=const.PAD_NO_TB)
    bc_lf_i_b = button(const.NO_TEXT, const.KEY_BC_LF_I_B, const.INFO,
                       const.BUTTON_S_SIZE, const.BUTTON_COLOR,
                       const.NO_BORDER, const.TOOLTIP_BC_LF,
                       disabled=True, pad=const.PAD_NO_TBR)
    bc_lf_it = input_text(const.DEFAULT_BC_LF, const.KEY_INPUT_BC_LF,
                          disabled=True, font=const.FONT, pad=const.PAD_IT_T)
    bc_lf_fb = browse(const.NO_TEXT, const.KEY_BC_LF_FB, const.KEY_INPUT_BC_LF,
                      const.FILEPNG, const.BUTTON_M_SIZE, const.BUTTON_COLOR,
                      const.NO_BORDER, disabled=True,
                      tooltip=const.TOOLTIP_FILE_BROWSER, pad=const.PAD_NO_TB)

    sc_cb = ImageCheckBox(image_on=const.CBON, image_off=const.CBOFF,
                          image_size=const.BUTTON_S_SIZE, key=const.KEY_SC_CB,
                          button_color=const.BUTTON_COLOR,
                          border_width=const.NO_BORDER, enabled=True)

    console_cb = ImageCheckBox(image_on=const.CONSOLE_HIDE,
                               image_off=const.CONSOLE_UNHIDE,
                               image_size=const.BUTTON_S_SIZE,
                               key=const.KEY_CONSOLE_CB,
                               button_color=const.BUTTON_COLOR,
                               border_width=const.NO_BORDER,
                               enabled=False, pad=const.PAD_NO)
    console = sg.Multiline(const.NO_TEXT, key=const.KEY_CONSOLE,
                           size=const.CONSOLE_SIZE, pad=const.CONSOLE_PAD,
                           visible=False, font=const.FONT, autoscroll=True)

    mandatory_layout = [
        [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB, font=const.FONTPAD)],
        [sg.Text(const.TEXT_LF, key=const.KEY_LF_T,
                 size=const.TEXT_DESC_SIZE, font=const.FONTB),
         input_text(const.DEFAULT_LF, const.KEY_INPUT_LF,
                    font=const.FONT, pad=const.PAD_IT_T), lf_fb, lf_i_b],
        [sg.Text(const.TEXT_LD, key=const.KEY_LD_T,
                 size=const.TEXT_DESC_SIZE, font=const.FONTB),
         input_text(const.DEFAULT_LD, const.KEY_INPUT_LD,
                    font=const.FONT, pad=const.PAD_IT_T), ld_fb, ld_i_b],
        [sg.Text(const.TEXT_RC, key=const.KEY_RC_T,
                 size=const.TEXT_DESC_SIZE, font=const.FONTB),
         input_text(const.DEFAULT_RC, const.KEY_INPUT_RC,
                    font=const.FONT, pad=const.PAD_IT_T), rc_fb, rc_i_b],
        [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB, font=const.FONTPAD)]
    ]

    vpn_layout = [
        [vpn_cb, sg.Text(const.TEXT_VPN_CB, key=const.KEY_VPN_CB_T,
                         text_color=const.COLOR_DISABLED, font=const.FONTB,
                         enable_events=True)],
        [sg.Text(const.TEXT_VPN_CF, key=const.KEY_VPN_CF_T,
                 size=const.TEXT_DESC_SIZE, font=const.FONTB,
                 text_color=const.COLOR_DISABLED),
         vpn_cf_it, vpn_cf_fb, vpn_cf_i_b],
        [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB, font=const.FONTPAD)]
    ]

    blockchain_layout = [
        [bc_cb, sg.Text(const.TEXT_BC_CB, key=const.KEY_BC_CB_T,
                        text_color=const.COLOR_DISABLED, font=const.FONTB,
                        enable_events=True)],
        [sg.Text(const.TEXT_BC_CF, key=const.KEY_BC_CF_T,
                 size=const.TEXT_DESC_SIZE, font=const.FONTB,
                 text_color=const.COLOR_DISABLED),
         bc_cf_it, bc_cf_fb, bc_cf_i_b],
        [sg.Text(const.TEXT_BC_LF, key=const.KEY_BC_LF_T,
                 size=const.TEXT_DESC_SIZE, font=const.FONTB,
                 text_color=const.COLOR_DISABLED),
         bc_lf_it, bc_lf_fb, bc_lf_i_b],
        [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB, font=const.FONTPAD)],

        [sc_cb, sg.Text(const.TEXT_SC_CB, key=const.KEY_SC_CB_T,
                        text_color=const.COLOR_ENABLED, font=const.FONTB,
                        enable_events=True)]
    ]

    button_layout = [
        [
            button(const.NO_TEXT, const.KEY_WIZARD_B, const.WIZARD,
                   const.BUTTON_L_SIZE, const.BUTTON_COLOR, const.NO_BORDER,
                   const.TOOLTIP_WIZARD, const.PAD_T),
            sg.Text(const.NO_TEXT, size=const.EXEC_TEXT_SIZE_S,
                    pad=const.PAD_NO),
            button(const.NO_TEXT, const.KEY_START_B, const.PLAY,
                   const.BUTTON_L_SIZE, const.BUTTON_COLOR, const.NO_BORDER,
                   const.TOOLTIP_START, const.PAD_T),
            sg.Text(const.NO_TEXT, size=const.EXEC_TEXT_SIZE_S,
                    pad=const.PAD_NO),
            button(const.NO_TEXT, const.KEY_STOP_B, const.STOP,
                   const.BUTTON_L_SIZE, const.BUTTON_COLOR, const.NO_BORDER,
                   const.TOOLTIP_STOP, const.PAD_T),
        ],
        [
            sg.Text(const.TEXT_WIZARD, key=const.KEY_WIZARD_T,
                    size=const.EXEC_TEXT_SIZE_S, font=const.FONTB,
                    pad=const.PAD_EXEC_TEXT, justification=const.CENTER,
                    enable_events=True),
            sg.Text(const.TEXT_START, key=const.KEY_START_T, font=const.FONTB,
                    size=const.EXEC_TEXT_SIZE_S, pad=const.PAD_EXEC_TEXT,
                    justification=const.CENTER, enable_events=True),
            sg.Text(const.TEXT_STOP, key=const.KEY_STOP_T, font=const.FONTB,
                    size=const.EXEC_TEXT_SIZE_S, pad=const.PAD_EXEC_TEXT,
                    justification=const.CENTER, enable_events=True)
        ],
        [sg.Frame(const.NO_TEXT, [[sg.Text(const.NO_TEXT,
                                           size=const.CONSOLE_CB_SIZE,
                                           pad=const.PAD_NO),
                                   console_cb]],
                  border_width=const.NO_BORDER)],
        [console]
    ]
    autoauditor_layout = [
        [sg.Frame(const.NO_TEXT, mandatory_layout, border_width=0)],
        [sg.Frame(const.NO_TEXT, vpn_layout, border_width=0)],
        [sg.Frame(const.NO_TEXT, blockchain_layout, border_width=0)],
        [sg.Frame(const.NO_TEXT, button_layout, border_width=0,
                  element_justification=const.CENTER)]
    ]

    about_layout = [
        [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB, font=const.FONTPAD)],
        [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB)],
        [sg.Text(const.ABOUT_NAME, font=const.FONTB)],
        [sg.Text(const.ABOUT_VERSION, font=const.FONTB)],
        [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB)],
        [sg.Text(const.ABOUT_AUTHOR, font=const.FONT)],
        [sg.Text(const.ABOUT_LAB, font=const.FONT)],
        [sg.Text(const.ABOUT_DEPARTMENT, font=const.FONT)],
        [sg.Text(const.ABOUT_UC3M, font=const.FONT)],
        [sg.Text(const.ABOUT_LOCATION, font=const.FONT)],
        [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB)],
        [sg.Text(const.ABOUT_ACKNOWLEDGEMENT, font=const.FONT,
                 justification=const.CENTER)],
        [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB)],
        [sg.Text(const.ABOUT_YEAR, font=const.FONT)],
    ]

    with open(const.DEFAULT_LICENSE, 'r') as f:
        gplv3_full = f.read().replace('.  ', '. ').replace('  ', '')

    gplv3_full_layout = [
        [sg.Text(gplv3_full, justification=const.CENTER,
                 size=const.LICENSE_TEXT_SIZE,
                 background_color=const.COLOR_TAB_DISABLED)]
    ]
    license_layout = [
        [sg.Text(const.COPYRIGHT, font=const.FONT,
                 justification=const.CENTER)],
        [sg.Column(gplv3_full_layout,
                   scrollable=True, size=const.LICENSE_COLUMN_SIZE,
                   vertical_scroll_only=True, justification=const.CENTER,
                   background_color=const.COLOR_TAB_DISABLED, pad=const.PAD_T)]
    ]

    layout = [
        [sg.TabGroup(
            [
                [sg.Tab('AutoAuditor', autoauditor_layout,
                        element_justification=const.CENTER)],
                [sg.Tab('About', about_layout,
                        element_justification=const.CENTER)],
                [sg.Tab('License', license_layout,
                        element_justification=const.CENTER)]
            ],
            border_width=const.NO_BORDER,
            tab_background_color=const.COLOR_TAB_DISABLED,
            font=const.FONT
        )]
    ]

    # Event Loop to process "events" and get the "values" of the inputs
    window = sg.Window('AutoAuditor', layout,
                       element_justification=const.CENTER)  # main window
    window_cons_size = None
    window_ncons_size = None

    vpncont = msfcont = None

    while True:
        event, values = window.read()
        if event is not None and window_ncons_size is None:
            window_ncons_size = window.size
        if event is not None \
           and window and console_cb.enabled \
           and window_cons_size is None:
            window_cons_size = window.size

        if event in (const.KEY_VPN_CB, const.KEY_VPN_CB_T):
            switch(window, vpn_cb, vpn_cf_it, vpn_cf_fb,
                   const.KEY_VPN_CF_T, const.KEY_VPN_CB_T, vpn_cf_i_b)

        if event in (const.KEY_BC_CB, const.KEY_BC_CB_T):
            switch(window, bc_cb, bc_cf_it, bc_cf_fb, bc_lf_it, bc_lf_fb,
                   const.KEY_BC_CF_T, const.KEY_BC_LF_T,
                   const.KEY_BC_CB_T, bc_cf_i_b, bc_lf_i_b)

        if event in (const.KEY_SC_CB, const.KEY_SC_CB_T):
            switch(window, sc_cb, const.KEY_SC_CB_T, const.KEY_SC_CB_T)

        if event in (const.KEY_START_B, const.KEY_START_T):
            if not console_cb.enabled:
                shrink_enlarge_window(window, console, console_cb,
                                      window_cons_size,
                                      window_ncons_size)
            utils.console_log(window, console)

            if vpn_cb.enabled:
                vpncf = window[const.KEY_INPUT_VPN_CF].Get()
                if not os.path.isfile(vpncf):
                    sg.Window('Error', [
                        [sg.Text("File {}".format(vpncf), font=const.FONT)],
                        [sg.Text("does not exist.", font=const.FONT)],
                        [sg.Text(const.NO_TEXT, font=const.FONTPAD)],
                        [sg.OK(button_color=const.BUTTON_COLOR_ERR,
                               font=const.FONT)]
                    ], element_justification=const.CENTER,
                              auto_close=True).read(close=True)
                else:
                    vpncont = vpn.setup_vpn(vpncf)

            lf = window[const.KEY_INPUT_LF].Get()
            ld = window[const.KEY_INPUT_LD].Get()

            errcode = utils.check_file_dir(lf, ld)
            if errcode is not None:
                sg.Window('Error', [
                    [sg.Text("Log file/Log directory", font=const.FONT)],
                    [sg.Text("does not exist.", font=const.FONT)],
                    [sg.Text(const.NO_TEXT, font=const.FONTPAD)],
                    [sg.OK(button_color=const.BUTTON_COLOR_ERR,
                           font=const.FONT)]
                ], element_justification=const.CENTER,
                          auto_close=True).read(close=True)
            else:
                msfcont = metasploit.start_msfrpcd(ld, ovpn=vpn_cb.enabled)

            msfclient = metasploit.get_msf_connection(
                const.DEFAULT_MSFRPC_PASSWD)

            rc = window[const.KEY_INPUT_RC].Get()
            if not os.path.isfile(rc):
                sg.Window('Error', [
                    [sg.Text("File {}".format(rc), font=const.FONT)],
                    [sg.Text("does not exist.", font=const.FONT)],
                    [sg.Text(const.NO_TEXT, font=const.FONTPAD)],
                    [sg.OK(button_color=const.BUTTON_COLOR_ERR,
                           font=const.FONT)]
                ], element_justification=const.CENTER,
                          auto_close=True).read(close=True)
            else:
                metasploit.launch_metasploit(msfclient, rc, lf)

            if bc_cb.enabled:
                hc = window[const.KEY_INPUT_BC_CF].Get()
                ho = window[const.KEY_INPUT_BC_LF].Get()
                if not os.path.isfile(hc):
                    sg.Window('Error', [
                        [sg.Text("File {}".format(rc), font=const.FONT)],
                        [sg.Text("does not exist.", font=const.FONT)],
                        [sg.Text(const.NO_TEXT, font=const.FONTPAD)],
                        [sg.OK(button_color=const.BUTTON_COLOR_ERR,
                               font=const.FONT)]
                    ], element_justification=const.CENTER,
                              auto_close=True).read(close=True)
                else:
                    info = blockchain.load_config(hc)
                    errcode = utils.check_file_dir(ho)
                    if errcode is not None:
                        sg.Window('Error', [
                            [sg.Text("Blockchain log file", font=const.FONT)],
                            [sg.Text("does not exist.", font=const.FONT)],
                            [sg.Text(const.NO_TEXT, font=const.FONTPAD)],
                            [sg.OK(button_color=const.BUTTON_COLOR_ERR,
                                   font=const.FONT)]
                        ], element_justification=const.CENTER,
                                  auto_close=True).read(close=True)
                    else:
                        blockchain.store_report(info, lf, ho)
            if sc_cb.enabled:
                errcode = utils.shutdown(msfcont, vpncont)
                if errcode:
                    sg.Window('Success', [
                        [sg.Text("AutoAuditor finished successfully.",
                                 font=const.FONT)],
                        [sg.OK(font=const.FONT)]
                    ], element_justification=const.CENTER,
                              auto_close=True).read(close=True)

        if event in (const.KEY_STOP_B, const.KEY_STOP_T):
            if not console_cb.enabled:
                shrink_enlarge_window(window, console, console_cb,
                                      window_cons_size,
                                      window_ncons_size)
            utils.console_log(window, console)

            if vpn_cb.enabled:
                vpncont = vpn.setup_vpn(
                    window[const.KEY_INPUT_VPN_CF].Get(), stop=True)

            msfcont = metasploit.start_msfrpcd(
                window[const.KEY_INPUT_LD].Get(),
                ovpn=vpn_cb.enabled,
                stop=True)

            errcode = utils.shutdown(msfcont, vpncont)
            if errcode:
                sg.Window('Success', [
                    [sg.Text("Containers stopped successfully.",
                             font=const.FONT)],
                    [sg.OK(font=const.FONT)]
                ], element_justification=const.CENTER,
                          auto_close=True).read(close=True)

        if event == const.KEY_LF_I_B:
            sg.Window(const.TEXT_LF, [
                [sg.Text(
                    "Absolute or relative path where output should be logged.",
                    font=const.FONT)],
                [sg.Text("By default, output/msf.log will be used:",
                         font=const.FONT)],
                [sg.InputText(const.DEFAULT_LF, font=const.FONT, disabled=True,
                              justification=const.CENTER)],
                [sg.OK()]
            ], element_justification=const.CENTER).read(close=True)

        if event == const.KEY_LD_I_B:
            sg.Window(const.TEXT_LD, [
                [sg.Text(
                    ("Absolute or relative path to directory "
                     "where gathered data should be stored."),
                    font=const.FONT)],
                [sg.Text("By default, output will be used:", font=const.FONT)],
                [sg.InputText(const.DEFAULT_LD, font=const.FONT, disabled=True,
                              justification=const.CENTER)],
                [sg.OK()]
            ], element_justification=const.CENTER).read(close=True)

        if event == const.KEY_RC_I_B:
            sg.Window(const.TEXT_RC, [
                [sg.Text(
                    "Absolute or relative path to resource script file.",
                    font=const.FONT)],
                [sg.Text(
                    "Under config, a template and few examples can be found:",
                    font=const.FONT)],
                [sg.InputText(const.DEFAULT_RC, font=const.FONT, disabled=True,
                              justification=const.CENTER)],
                [sg.OK()]
            ], element_justification=const.CENTER).read(close=True)

        if event == const.KEY_VPN_CF_I_B:
            sg.Window(const.TEXT_VPN_CF, [
                [sg.Text(
                    "Absolute or relative path to openvpn configuration file.",
                    font=const.FONT)],
                [sg.Text(
                    "Under config, a template and an example can be found:",
                    font=const.FONT)],
                [sg.InputText(const.DEFAULT_VPN_CF, font=const.FONT,
                              disabled=True, justification=const.CENTER)],
                [sg.OK()]
            ], element_justification=const.CENTER).read(close=True)

        if event == const.KEY_BC_CF_I_B:
            sg.Window(const.TEXT_BC_CF, [
                [sg.Text(
                    ("Absolute or relative path to "
                     "blockchain network configuration."), font=const.FONT)],
                [sg.Text(
                    "Under config, a template and an example can be found:",
                    font=const.FONT)],
                [sg.InputText(const.DEFAULT_BC_CF, font=const.FONT,
                              disabled=True, justification=const.CENTER)],
                [sg.OK()]
            ], element_justification=const.CENTER).read(close=True)

        if event == const.KEY_BC_LF_I_B:
            sg.Window(const.TEXT_BC_LF, [
                [sg.Text(
                    ("Absolute or relative path to "
                     "blockchain log file of uploaded reports."),
                    font=const.FONT)],
                [sg.Text("By default, output/blockchain.log will be used:",
                         font=const.FONT)],
                [sg.InputText(const.DEFAULT_BC_LF, font=const.FONT,
                              disabled=True, justification=const.CENTER)],
                [sg.OK()]
            ], element_justification=const.CENTER).read(close=True)

        if event == sg.WIN_CLOSED:
            break

        if event == const.KEY_CONSOLE_CB:
            shrink_enlarge_window(window, console, console_cb,
                                  window_cons_size,
                                  window_ncons_size)

        if event in (const.KEY_WIZARD_B, const.KEY_WIZARD_T):
            if not console_cb.enabled:
                shrink_enlarge_window(window, console, console_cb,
                                      window_cons_size,
                                      window_ncons_size)
            utils.console_log(window, console)

            msfcont = metasploit.start_msfrpcd(
                window[const.KEY_INPUT_LD].Get())
            msfclient = metasploit.get_msf_connection(
                const.DEFAULT_MSFRPC_PASSWD)
            mtype = None
            mname = None
            mod = None

            # mt_i_b = button(const.NO_TEXT, const.KEY_MT_I_B, const.INFO,
            #                 const.BUTTON_S_SIZE, const.BUTTON_COLOR,
            #                 const.NO_BORDER, const.TOOLTIP_MT)
            # mn_i_b = button(const.NO_TEXT, const.KEY_MN_I_B, const.INFO,
            #                 const.BUTTON_S_SIZE, const.BUTTON_COLOR,
            #                 const.NO_BORDER, const.TOOLTIP_MN)

            mod_layout = [[sg.Frame(const.NO_TEXT, [[
                sg.InputText(str(i), size=const.TEXT_DESC_SIZE_L,
                             pad=const.PAD_NO_TBR,
                             disabled_readonly_background_color=const.COLOR_T,
                             readonly=True, border_width=const.NO_BORDER,
                             font=const.FONT, key=const.KEY_MOD_NAME+str(i)),
                button(const.NO_TEXT, const.KEY_MOD_EDIT+str(i),
                       const.EDIT, const.BUTTON_M_SIZE,
                       const.BUTTON_COLOR, const.NO_BORDER,
                       const.TOOLTIP_MOD_EDIT, pad=const.PAD_MOD),
                button(const.NO_TEXT, const.KEY_MOD_REM+str(i),
                       const.REMOVE, const.BUTTON_M_SIZE,
                       const.BUTTON_COLOR, const.NO_BORDER,
                       const.TOOLTIP_MOD_REMOVE),
                button(const.NO_TEXT, const.KEY_MOD_INFO+str(i),
                       const.INFO, const.BUTTON_S_SIZE,
                       const.BUTTON_COLOR, const.NO_BORDER,
                       const.TOOLTIP_MOD_INFO, pad=const.PAD_MOD)
            ]], visible=False, pad=const.PAD_NO, border_width=const.NO_BORDER,
                                    key=const.KEY_MOD_FRAME+str(i),
                                    element_justification=const.CENTER)]
                          for i in range(const.MAX_MODULES)]

            wizard_layout = [
                [sg.Text(const.NO_TEXT, font=const.FONT, pad=const.PAD_NO_TB)],
                [sg.Text(const.TEXT_MODULE_TYPE, font=const.FONTB,
                         size=const.TEXT_DESC_SIZE),
                 sg.DropDown(const.MODULE_TYPES, size=const.EXEC_TEXT_SIZE_L,
                             font=const.FONT, enable_events=True,
                             key=const.KEY_MODULE_TYPE, readonly=True)],
                [sg.Text(const.TEXT_MODULE_NAME, font=const.FONTB,
                         size=const.TEXT_DESC_SIZE),
                 sg.DropDown(const.NO_TEXT, size=const.EXEC_TEXT_SIZE_L,
                             font=const.FONT, key=const.KEY_MODULE_NAME,
                             readonly=True)],
                [sg.Text(const.NO_TEXT, font=const.FONT, pad=const.PAD_NO)],
                [sg.Column(mod_layout, size=const.OPT_MOD_COLUMN_SIZE,
                           element_justification=const.CENTER,
                           pad=const.PAD_NO, justification=const.CENTER,
                           scrollable=True, vertical_scroll_only=True,
                           key=const.KEY_MOD_COL)],
                [sg.Text(const.NO_TEXT, font=const.FONT, pad=const.PAD_NO)],
                [button(const.NO_TEXT, const.KEY_MOD_ADD, const.ADD,
                        const.BUTTON_L_SIZE, const.BUTTON_COLOR,
                        const.NO_BORDER, const.TOOLTIP_MOD_ADD)],
                [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB,
                         font=const.FONTPAD)],
                [sg.Button(const.TEXT_WIZARD_GEN, key=const.KEY_WIZARD_GEN,
                           font=const.FONT),
                 sg.Button(const.TEXT_WIZARD_EXIT, key=const.KEY_WIZARD_EXIT,
                           font=const.FONT)],
                [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB,
                         font=const.FONTPAD)]
            ]
            wwindow = sg.Window('Wizard', wizard_layout,  # Wizard window
                                element_justification=const.CENTER)

            edit_regex = re.compile(const.KEY_MOD_EDIT+r'\d+')
            rem_regex = re.compile(const.KEY_MOD_REM+r'\d+')
            info_regex = re.compile(const.KEY_MOD_INFO+r'\d+')
            # (const.MAX_MODULES-1) ... 0
            mod_idx = list(range(const.MAX_MODULES-1, -1, -1))
            mod_list = {}
            while True:
                wevent, wvalues = wwindow.read()
                if wevent == const.KEY_MODULE_TYPE:
                    mtype = wvalues[const.KEY_MODULE_TYPE]
                    mods = [''] + wizard.get_modules(msfclient, mtype)
                    wwindow[const.KEY_MODULE_NAME](
                        values=mods)
                    wwindow[const.KEY_MODULE_NAME](
                        value='')

                if wevent == const.KEY_MOD_ADD:
                    mname = wvalues[const.KEY_MODULE_NAME]
                    if mtype and mname:
                        if mod_idx:
                            added = opt_window(
                                msfclient, wwindow, mod_list, mtype, mname,
                                mod_idx[-1])
                            if added:
                                mod_idx.remove(mod_idx[-1])
                        else:
                            sg.Window('Error', [
                                [sg.Text("Maximum modules allowed ({})."
                                         .format(const.MAX_MODULES),
                                         font=const.FONT)],
                                [sg.Text(
                                    ("Limit can be changed in "
                                     "utils.py:const.MAX_MODULES"),
                                    font=const.FONT)],
                                [sg.OK(button_color=const.BUTTON_COLOR_ERR,
                                       font=const.FONT)]
                            ], element_justification=const.CENTER,
                                      auto_close=True).read(close=True)
                    else:
                        sg.Window('Error', [
                            [sg.Text(
                                "Module type or module name not selected.",
                                font=const.FONT)],
                            [sg.Text(
                                ("Choose a module type and module name "
                                 "from the dropdown."), font=const.FONT)],
                            [sg.OK(button_color=const.BUTTON_COLOR_ERR,
                                   font=const.FONT)]
                        ], element_justification=const.CENTER,
                                  auto_close=True).read(close=True)

                if wevent is not None and edit_regex.match(wevent):
                    aux_mod_idx = int(wevent.split("_")[2])  # module_name_xxx
                    aux_mt, aux_mn = wwindow[const.KEY_MOD_NAME +
                                             str(aux_mod_idx)].Get(
                                             ).split(': ')
                    opt_window(
                        msfclient, wwindow, mod_list, aux_mt, aux_mn,
                        aux_mod_idx, edit=True)

                if wevent is not None and rem_regex.match(wevent):
                    aux_mod_idx = int(wevent.split("_")[2])  # module_rem_xxx
                    aux_mt, aux_mn = wwindow[const.KEY_MOD_NAME +
                                             str(aux_mod_idx)].Get(
                                             ).split(': ')
                    wwindow[const.KEY_MOD_FRAME +
                            str(aux_mod_idx)](visible=False)
                    # workaround to hide row after removal
                    wwindow[const.KEY_MOD_FRAME +
                            str(aux_mod_idx)
                            ].ParentRowFrame.config(width=0, height=1)
                    del mod_list[aux_mt][aux_mn][aux_mod_idx]
                    mod_idx.insert(0, aux_mod_idx)  # reuse removed item
                    # Update column scrollbar
                    wwindow.visibility_changed()
                    wwindow[const.KEY_MOD_COL].contents_changed()

                if wevent is not None and info_regex.match(wevent):
                    aux_mod_idx = int(wevent.split("_")[2])  # module_info_xxx
                    aux_mt, aux_mn = wwindow[const.KEY_MOD_NAME +
                                             str(aux_mod_idx)].Get(
                                             ).split(': ')
                    mod = wizard.get_module(msfclient, aux_mt, aux_mn)
                    mod_info = wizard.get_module_info(mod)
                    mod_info_layout = [
                        [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB,
                                 font=const.FONTPAD)],
                        [sg.Text("/".join([aux_mt, aux_mn]),
                                 font=const.FONTB)],
                        [sg.Text(const.NO_TEXT, pad=const.PAD_NO_TB,
                                 font=const.FONTPAD)]
                    ] + [
                        [sg.Frame(const.NO_TEXT,
                                  [[sg.Text(el, font=const.FONTB,
                                            size=const.EXEC_TEXT_SIZE_XS),
                                    sg.Text(
                                        TextWrapper(width=const.WRAP_TEXT_SIZE)
                                        .fill(str(mod_info[el])),
                                        font=const.FONT)]
                                   for el in mod_info],
                                  border_width=const.NO_BORDER)]
                    ] + [[sg.OK(font=const.FONT)]]

                    sg.Window(const.TEXT_PAYLOAD_INFO, mod_info_layout,
                              element_justification=const.CENTER
                              ).read(close=True)

                if wevent in (const.KEY_WIZARD_EXIT, sg.WIN_CLOSED):
                    # while True:
                    #     sg.popup_animated(const.LOADING, no_titlebar=False,
                    #                       background_color='white',
                    #                       time_between_frames=80)
                    errcode = utils.shutdown(msfcont)
                    if errcode:
                        sg.Window('Success', [
                            [sg.Text("Wizard finished successfully.",
                                     font=const.FONT)],
                            [sg.OK(font=const.FONT)]
                        ], element_justification=const.CENTER,
                                  auto_close=True).read(close=True)
                    break

                if wevent == const.KEY_WIZARD_GEN:
                    ev, val = sg.Window("Warning", [
                        [sg.Text("Are you sure you want to",
                                 justification=const.CENTER, font=const.FONT,
                                 pad=const.PAD_NO_R),
                         sg.Text(
                            "overwrite", justification=const.CENTER,
                             font=const.FONTB, pad=const.PAD_NO_L)],
                        [sg.Text("{}?"
                                 .format(window[const.KEY_INPUT_RC].Get()),
                                 justification=const.CENTER, font=const.FONT)],
                        [sg.Text(const.NO_TEXT, justification=const.CENTER,
                                 font=const.FONTPAD)],
                        [sg.Yes(font=const.FONT,
                                button_color=const.BUTTON_COLOR_ERR),
                         sg.No(font=const.FONT)]
                    ], element_justification=const.CENTER).read(close=True)
                    if ev == 'Yes':
                        mod_list_ax = {}
                        for mlt in mod_list:
                            mod_list_ax = deepcopy(mod_list)
                            for mln in mod_list_ax[mlt]:
                                mod_list_ax[mlt][mln] = list(
                                    mod_list_ax[mlt][mln].values())
                        aux_rc = window[const.KEY_INPUT_RC].Get()
                        with open(aux_rc, 'w') as f:
                            json.dump(mod_list_ax, f, indent=2)
                        utils.log(
                            'succg',
                            "Resource script correctly generated in {}"
                            .format(aux_rc))
                        sg.Window('Success', [
                            [sg.Text("Resource script correctly generated in",
                                     font=const.FONT)],
                            [sg.Text("{}".format(aux_rc),
                                     font=const.FONT)],
                            [sg.OK(font=const.FONT)]
                        ], element_justification=const.CENTER,
                                  auto_close=True).read(close=True)
                        sev, sval = sg.Window("Shutdown", [
                            [sg.Text("Shutdown wizard container?",
                                     justification=const.CENTER,
                                     font=const.FONT, pad=const.PAD_NO_R)],
                            [sg.Text(const.NO_TEXT, justification=const.CENTER,
                                     font=const.FONTPAD)],
                            [sg.Yes(font=const.FONT,
                                    button_color=const.BUTTON_COLOR_ERR),
                             sg.No(font=const.FONT)]
                        ], element_justification=const.CENTER).read(close=True)
                        if sev == 'Yes':
                            errcode = utils.shutdown(msfcont)
                            if errcode:
                                sg.Window('Success', [
                                    [sg.Text(
                                        "AutoAuditor finished successfully.",
                                        font=const.FONT)],
                                    [sg.OK(font=const.FONT)]
                                ], element_justification=const.CENTER,
                                          auto_close=True).read(close=True)
                        break
            wwindow.close()
    window.close()


if __name__ == "__main__":
    main()
