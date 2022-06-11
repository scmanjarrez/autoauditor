#!/usr/bin/env python3

# SPDX-License-Identifier: GPL-3.0-or-later

# gui - gui module.

# Copyright (C) 2020-2022 Sergio Chica Manjarrez @ pervasive.it.uc3m.es.
# Universidad Carlos III de Madrid.

# This file is part of autoauditor.

# autoauditor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# autoauditor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with GNU Emacs.  If not, see <https://www.gnu.org/licenses/>.

from PySide6.QtCore import (Property, QAbstractListModel, QFile, QModelIndex,
                            QObject, Qt, QTextStream, QThread, Signal, Slot)
from PySide6.QtQml import (QQmlApplicationEngine, qmlRegisterType)
from PySide6.QtGui import QGuiApplication, QIcon
from autoauditor.gui import resources  # noqa
from autoauditor import blockchain as bc
from autoauditor import metasploit as ms
from autoauditor import constants as ct
from autoauditor import wizard as wz
from autoauditor import utils as ut
from autoauditor import vpn

import asyncio as _asyncio
import json
import sys


class Module(QObject):
    wrongType = Signal(str)

    def __init__(self, client, mtype, mname):
        QObject.__init__(self)
        self._module = wz.Module(client, mtype, mname)
        self._client = client
        self._mopts = {}
        self._payload = {'tmp': True, 'mod': None}

    @Property(int)
    def wid(self): return self._id

    @wid.setter
    def wid(self, newid): self._id = newid

    @Property(str)
    def mtype(self): return self._module.mod.moduletype

    @Property(str)
    def mname(self): return self._module.mod.modulename

    @Property('QVariant')
    def info(self):
        items = dict(sorted(self._module.info().items()))
        for i in items:
            if not isinstance(items[i], bool) and not items[i]:
                items[i] = "-"
            else:
                if isinstance(items[i], list):
                    items[i] = ", ".join([": ".join(subl)
                                         if isinstance(subl, list)
                                         else subl
                                         for subl in items[i]])
                else:
                    items[i] = str(items[i])
        return items

    @Property('QVariantList')
    def options(self): return sorted(self._module.options())

    @Slot(QObject, result=bool)
    def missing_required(self, window):
        mis = self._module.missing()
        window.showError.emit(f"Following options required: {', '.join(mis)}")
        return len(mis)

    @Slot(str, result='QVariant')
    def opt_info(self, opt):
        res = {}
        if opt != 'ACTION':
            for k, v in sorted(self._module.opt_info(opt).items()):
                res[k] = str(v)
                if isinstance(v, list):
                    res[k] = ", ".join(v)
        else:
            res['Actions'] = ", ".join(list(
                self._module.opt_info(opt).values()))
            res['Default'] = self._module.info()['default_action']
            res['Desc'] = self._module.opt_desc('ACTION')
            res['Required'] = "True"
            res['Type'] = "enum"
        return res

    @Slot(str, result='QVariantList')
    def opt_value(self, opt):
        if opt != 'ACTION':
            value = self._module.mod[opt]
            vinfo = self._module.opt_info(opt)
            vreq = "Yes" if vinfo['required'] else "No"
            ret = [False, '', [], vreq]
            if value is not None:
                ret[1] = str(value)
                if vinfo['type'] in ('bool', 'enum'):
                    values = ['True', 'False']
                    if vinfo['type'] == 'enum':
                        values = vinfo['enums']
                    ret[0] = True
                    ret[2] = [str(
                        [t.lower() for t in values].index(ret[1].lower()))
                              ] + values
        else:
            values = list(self._module.opt_info(opt).values())
            value = self._module.mod.action
            ret = [True, value,
                   [str(values.index(value))] + values, "Yes"]
        return ret

    @Slot(QObject, str, str, bool)
    def set_mopt(self, window, label, value, payload, as_popup=True):
        if value:
            mod = self
            if payload:
                mod = self._payload['mod']
            vinfo = mod._module.opt_info(label)
            correct, res = ut.correct_type(value, vinfo)
            if not correct:
                if as_popup:
                    window.showError.emit(res)
                else:
                    return False, res
            else:
                if label == 'ACTION':
                    mod._module.mod.action = res
                else:
                    mod._module.mod[label] = res
                mod._mopts[label] = res

    @Property(bool)
    def has_payloads(self): return self._module.has_payloads()

    @Property('QVariantList')
    def payloads(self): return self._module.payloads()

    @Property(QObject)
    def payload(self):
        return self._payload['mod']

    @Slot(str)
    def payload_load(self, pname):
        self._payload['mod'] = Module(self._client, 'payload', pname)
        self._payload['mod'].wid = self.wid

    @Slot()
    def payload_set(self):
        self._payload['tmp'] = False

    @Slot()
    def payload_unset(self):
        self._payload['tmp'] = True

    @Slot(result='QVariant')
    def payload_info(self):
        return self._payload['mod'].info

    @Slot(result=int)
    def payload_metadata(self):
        if not self._payload['tmp']:
            return self._module.payloads().index(self._payload['mod'].mname)
        return -1

    def gen_dict(self):
        dct = dict(sorted(self._mopts.items()))
        if not self._payload['tmp']:
            dct['PAYLOAD'] = {}
            dct['PAYLOAD']['NAME'] = self._payload['mod'].mname
            dct['PAYLOAD']['OPTIONS'] = self._payload['mod']._mopts
        return {'mtype': self.mtype, 'mname': self.mname, 'opts': dct}


class OptionsModel(QAbstractListModel):
    KeyRole = Qt.UserRole + 1
    IsComboRole = Qt.UserRole + 2
    ValueRole = Qt.UserRole + 3
    ValueListRole = Qt.UserRole + 4
    ReqRole = Qt.UserRole + 5
    match = {
        KeyRole: b'key',
        IsComboRole: b'isCombo',
        ValueRole: b'value',
        ValueListRole: b'valueList',
        ReqRole: b'req'
    }

    def __init__(self):
        QAbstractListModel.__init__(self)
        self.elements = []

    def data(self, index, role=Qt.DisplayRole):
        return self.elements[index.row()][self.match[role].decode()]

    def rowCount(self, parent=QModelIndex()):
        return len(self.elements)

    def roleNames(self):
        return self.match

    def setElements(self, elements):
        self.beginInsertRows(QModelIndex(), 0, len(elements) - 1)
        self.elements = elements
        self.endInsertRows()

    def addElement(self, key, is_combo, value, value_list, req):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.elements.append({'key': key, 'isCombo': is_combo,
                              'value': value, 'valueList': value_list,
                              'req': req})
        self.endInsertRows()


class Backend(QObject):
    taskCompleted = Signal(str)
    dockerCompleted = Signal()
    setupMsfClient = Signal()

    def __init__(self, root):
        QObject.__init__(self)
        self.root = root
        self.async_loop = _asyncio.new_event_loop()
        self.msf = None
        self.msfcl = None
        self.tmp = None
        self.cwid = 0
        self._modules = {}

    def _property(self, obj_id, prop):
        return self.root.findChild(QObject, obj_id).property(prop)

    def containers_start(self, action):
        ready = False
        errors = []
        self.log = self._property('tfLog', 'text')
        self.loot = self._property('tfLoot', 'text')
        rc = self._property('tfRc', 'text')
        erc = self._property('sErc', 'checked')
        self.vpn = self._property('sVpn', 'checked')
        self.vcfg = self._property('tfVcfg', 'text')
        sbc = self._property('sBc', 'checked')
        bcfg = self._property('tfBcfg', 'text')
        blog = self._property('tfBlog', 'text')
        if ut.check_writef(self.log) is not None:
            errors.append(["Log not writable"])
        if ut.check_writed(self.loot) is not None:
            errors.append(["Loot not writable"])
        if ((action == 'pbRun' or action == 'pbWizard' and erc)
            and ut.check_readf(rc) is not None):  # noqa
            errors.append(["Resources script not readable"])
        if self.vpn and ut.check_readf(self.vcfg) is not None:
            errors.append(["Vpn configuration not readable"])
        if sbc:
            if ut.check_readf(bcfg) is not None:
                errors.append(["Blockchain configuration not readable"])
            if ut.check_writef(blog) is not None:
                errors.append(["Blockchain log not writable"])
        if not errors:
            self.root.openConsole.emit()
            if self.vpn:
                vpn.start_vpn(self.vcfg)
            self.msf = ms.start_msf(self.loot, self.vpn)
            if self.msf is not None:
                self.dockerCompleted.emit()
                self.msfcl = ms.get_msf_connection(ct.DEF_MSFRPC_PWD)
                if self.msfcl is not None:
                    ready = True
                else:
                    self.root.errorSignal.emit(
                        ['Error connecting to msfrpc server'],
                        action)
            else:
                self.root.errorSignal.emit(
                    ['Error starting containers'], action)
        else:
            self.root.errorSignal.emit(errors, action)
        return ready

    def backend_ready(self, action):
        ready = False
        if self.msf is None:
            self.root.errorSignal.emit(
                ['Metasploit container not running'], action)
        elif self.msfcl is None:
            self.root.errorSignal.emit(
                ['Backend not ready'], action)
        else:
            ready = True
        return ready

    @Slot()
    def button_run(self):
        pbar = 'pbRun'
        if self.containers_start(pbar) and self.backend_ready(pbar):
            ms.launch_metasploit(self.msfcl,
                                 self._property('tfRc', 'text'),
                                 self.log)
            if self._property('sBc', 'checked'):
                self.store()
            if self._property('cStop', 'checked'):
                self.stop(pbar)
            else:
                self.taskCompleted.emit(pbar)

    @Slot()
    def button_store(self):
        pbar = 'pbStore'
        if self.containers_start(pbar) and self.backend_ready(pbar):
            self.store()
            if self._property('cStop', 'checked'):
                self.stop(pbar)
            else:
                self.taskCompleted.emit(pbar)

    def store(self):
        _asyncio.set_event_loop(self.async_loop)
        cfg = bc.load_config(self._property('tfBcfg', 'text'),
                             loop=self.async_loop)
        if cfg is not None:
            bc.store_report(cfg, self.log,
                            self._property('tfBlog', 'text'),
                            ct.DEF_EPEERS,
                            loop=self.async_loop)

    @Slot()
    def button_wizard(self):
        pbar = 'pbWizard'
        if self.containers_start(pbar) and self.backend_ready(pbar):
            if self._property('sErc', 'checked') and not self._modules:
                self.parse_rc()
            self.taskCompleted.emit(pbar)
            self.root.openWizard.emit()

    @Slot()
    def request_wizard(self):
        if self.msf is not None and self.msfcl is not None:
            self.root.openWizard.emit()
        else:
            self.button_wizard()

    def parse_rc(self):
        with open(self._property('tfRc', 'text')) as f:
            try:
                rc = json.load(f)
            except json.decoder.JSONDecodeError:
                self.root.errorSignal.emit(["Error parsing RC"], 'pbWizard')
        for mtype in rc:
            for mname in rc[mtype]:
                for mod in rc[mtype][mname]:
                    tmp = Module(self.msfcl, mtype, mname)
                    tmp.wid = self.cwid
                    self._modules[self.cwid] = {'tmp': False, 'mod': tmp}
                    self.root.addModule.emit(tmp)
                    self.cwid += 1
                    errors = []
                    for opt in mod:
                        if opt == 'PAYLOAD':
                            tmp.payload_load(mod['PAYLOAD']['NAME'])
                            tmp.payload_set()
                            for popt in mod['PAYLOAD']['OPTIONS']:
                                res = tmp.set_mopt(
                                    self.root, popt,
                                    mod['PAYLOAD']['OPTIONS'][popt],
                                    True, as_popup=False)
                                if res is not None:
                                    errors.append(res[1])
                        else:
                            res = tmp.set_mopt(
                                self.root, opt, mod[opt],
                                False, as_popup=False)
                            if res is not None:
                                errors.append(res[1])
                    if errors:
                        self.root.showError.emit(errors)

    @Slot()
    def button_stop(self):
        self.stop('pbStop')

    def stop(self, bar_id):
        ut.shutdown()
        self._modules = {}
        self.dockerCompleted.emit()
        self.taskCompleted.emit(bar_id)

    @Slot(str)
    def modules(self, mtype):
        mnames = wz.mnames(self.msfcl, mtype)
        self.root.setModuleNames.emit(mnames)

    @Slot(str, str)
    def module_load(self, mtype, mname):
        self.tmp = Module(self.msfcl, mtype, mname)

    @Slot(int)
    def module_info(self, wid):
        if wid == -1:
            self.root.openModuleInfo.emit(self.tmp.info)
        else:
            self.root.openModuleInfo.emit(self._modules[wid]['mod'].info)

    @Slot(int)
    def module_open(self, wid):
        if wid == -1:
            new = Module(self.msfcl, self.tmp.mtype, self.tmp.mname)
            new.wid = self.cwid
            self._modules[self.cwid] = {'tmp': True, 'mod': new}
            self.root.openModuleOptions.emit(
                self._modules[self.cwid]['mod'],
                self._modules[self.cwid]['mod'].has_payloads,
                True)
            self.cwid += 1
        else:
            self.root.openModuleOptions.emit(
                self._modules[wid]['mod'],
                self._modules[wid]['mod'].has_payloads,
                False)

    @Slot(QObject, QObject)
    def module_fill_options(self, model, module):
        rows = []
        for opt in module.options:
            opt_val = module.opt_value(opt)
            rows.append({'key': opt, 'isCombo': opt_val[0],
                         'value': opt_val[1],
                         'valueList': opt_val[2],
                         'req': opt_val[3]})
        model.setElements(rows)

    @Slot(int)
    def module_added(self, wid):
        self._modules[wid]['tmp'] = False

    @Slot(int)
    def module_remove(self, wid):
        del self._modules[wid]

    @Slot(int)
    def tmp_remove(self, wid):
        if wid in self._modules and self._modules[wid]['tmp']:
            del self._modules[wid]

    @Slot()
    def check_save(self):
        if ut.check_existf(self._property('tfRc', 'text')):
            self.root.warnSave.emit()
        else:
            self.generate_rc()

    @Slot()
    def generate_rc(self):
        rc = {}
        for mod in self._modules.values():
            if not mod['tmp']:
                dct = mod['mod'].gen_dict()
                if dct['mtype'] not in rc:
                    rc[dct['mtype']] = {}
                if dct['mname'] not in rc[dct['mtype']]:
                    rc[dct['mtype']][dct['mname']] = []
                rc[dct['mtype']][dct['mname']].append(dct['opts'])

        with open(self._property('tfRc', 'text'), 'w') as f:
            json.dump(rc, f, indent=2)


class BackendThread(QThread):
    def __init__(self, root):
        QThread.__init__(self)
        self.backend = Backend(root)
        self.backend.moveToThread(self)


def main():
    def _status(containers, container_id):
        if container_id in containers:
            return 'on'
        return 'off'

    @Slot()
    def containers_status():
        cnts = ut.running_containers()
        root.containerStatus.emit('vpnStatus',
                                  _status(cnts, 'autoauditor_vpn_client'))
        msf = _status(cnts, 'autoauditor_msf')
        root.containerStatus.emit('msfStatus', msf)

    @Slot(str)
    def pbar_hide(pbar):
        root.hidePBar.emit(pbar)
        root.endConsole.emit()

    def create_connections():
        root.closing.connect(backend_thread.quit)
        root.requestRun.connect(backend_thread.backend.button_run)
        root.requestStore.connect(backend_thread.backend.button_store)
        root.requestWizard.connect(backend_thread.backend.button_wizard)
        root.openOrRequestWizard.connect(
            backend_thread.backend.request_wizard)
        root.requestStop.connect(backend_thread.backend.button_stop)
        root.moduleTypeSelected.connect(backend_thread.backend.modules)
        root.moduleNameSelected.connect(backend_thread.backend.module_load)
        root.moduleInfo.connect(backend_thread.backend.module_info)
        root.requestModule.connect(backend_thread.backend.module_open)
        root.fillModuleOptions.connect(
            backend_thread.backend.module_fill_options)
        root.addedModule.connect(backend_thread.backend.module_added)
        root.removeModule.connect(backend_thread.backend.module_remove)
        root.tmpRemoveModule.connect(backend_thread.backend.tmp_remove)
        root.checkSave.connect(backend_thread.backend.check_save)
        root.generateRc.connect(backend_thread.backend.generate_rc)
        backend_thread.backend.dockerCompleted.connect(
            containers_status)
        backend_thread.backend.taskCompleted.connect(pbar_hide)
        ut.set_logger(root.newLineConsole)

    app = QGuiApplication(sys.argv)
    app.setWindowIcon(QIcon(':/icon'))
    qmlRegisterType(OptionsModel, "OptionsModel", 1, 0, "OptionsModel")

    engine = QQmlApplicationEngine()
    engine.quit.connect(app.quit)
    engine.load('autoauditor/gui/main.qml')
    root = engine.rootObjects()[0]
    backend_thread = BackendThread(root)
    create_connections()
    backend_thread.start()

    obj = root.findChild(QObject, 'taLicense')
    lic = QFile(':/license')
    if lic.open(QFile.ReadOnly):
        t_lic = QTextStream(lic).readAll()
        lic.close()
        obj.setProperty('text', t_lic.replace('.  ', '. ').replace('  ', ''))
    containers_status()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
