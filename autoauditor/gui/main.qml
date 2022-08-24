import Qt.labs.platform as Labs
import QtQuick.Controls 6.2
import QtQuick.Dialogs 6.2
import QtQuick.Layouts 6.2
import QtQuick.Window 6.2
import QtQuick 6.2

ApplicationWindow {
    id: mainWindow
    title: "autoauditor"
    minimumWidth: 720
    minimumHeight: 560
    visible: true
    Material.theme: cTheme.checked ? Material.Light : Material.Dark

    property font fLabel: Qt.font({
        family: roboto.name,
        weight: Font.Bold,
        pixelSize: 18
    })
    property font fSwitch: Qt.font({
        family: roboto.name,
        weight: Font.Medium,
        pixelSize: 15
    })
    property font fInput: Qt.font({
        family: roboto.name,
        weight: Font.Light,
        pixelSize: 18
    })
    property font fTooltip: Qt.font({
        family: roboto.name,
        weight: Font.Light,
        pixelSize: 12
    })
    property font fMenubar: Qt.font({
        family: roboto.name,
        pixelSize: 11
    })
    property int sLPad: 30
    property int sMPad: sLPad - 12
    property int sSPad: 10
    property int sMenuBar: 15
    property int sTextField: 350
    function debugObj(obj) {
        for (var p in obj)
            console.log(p + ": " + obj[p])
    }
    property var idMap: ({
        'vpnStatus': vpnStatus,
        'msfStatus': msfStatus,
        'pbRun': pbRun,
        'pbStore': pbStore,
        'pbWizard': pbWizard,
        'pbStop': pbStop
    })
    property var openedModules: ({})
    signal requestRun()
    signal requestStore()
    signal requestWizard()
    signal openWizard()
    signal openOrRequestWizard()
    onOpenWizard: {
        wizardLoader.item.show();
        cWizard.checked = true
    }
    signal requestStop()
    signal hidePBar(barId: string)
    onHidePBar: (barId) => {
        idMap[barId].visible = false
    }
    signal containerStatus(buttonId: string, status: string)
    onContainerStatus: (buttonId, status) => {
        idMap[buttonId].icon.source = 'qrc:/' + status
        if (buttonId === 'msfStatus') {
            if (status === 'on') {
                cWizard.enabled = true
            } else {
                cWizard.enabled = false;
                wizardLoader.item.hide();
                for (var ow in openedModules) {
                    openedModules[ow].close();
                    delete openedModules[ow]
                }
                cWizard.checked = false
            }
        }
    }
    signal openConsole()
    onOpenConsole: {
        consoleLoader.item.show();
        cConsole.checked = true
    }
    signal endConsole()
    onEndConsole: consoleLoader.item.text = consoleLoader.item.text + '---\n'
    signal newLineConsole(line: string)
    onNewLineConsole: line => consoleLoader.item.text = consoleLoader.item.text + line + '\n'
    signal showError(errors: var)
    onShowError: errors => {
        errorDialogText.text = errors.join('\n');
        errorDialog.open()
    }
    signal errorSignal(errors: var, barId: string)
    onErrorSignal: (errors, barId) => {
        errorDialogText.text = errors.join('\n');
        errorDialog.open();
        idMap[barId].visible = false
    }
    signal checkSave()
    signal warnSave()
    onWarnSave: {
        wizardLoader.item.idMap['warnDialog'].open()
    }
    signal moduleTypeSelected(mtype: string)
    signal setModuleNames(mnames: var)
    onSetModuleNames: mnames => wizardLoader.item.idMap['mName'].model = mnames
    signal moduleInfo(wid: int)
    signal openModuleInfo(minfo: var)
    onOpenModuleInfo: minfo => {
        wizardLoader.item.idMap['mInfo'].clear()
        for (var k in minfo) {
            wizardLoader.item.idMap['mInfo'].append(
                {key: k[0].toUpperCase() + k.substring(1),
                 value: minfo[k]})
        }
        wizardLoader.item.idMap['mInfoDialog'].open()
    }
    signal moduleNameSelected(mtype: string, mname: string)
    signal requestModule(wid: int)
    signal fillModuleOptions(model: var, mod: var)
    signal openModuleOptions(mod: var, pay: bool, newMod: bool)
    onOpenModuleOptions: (mod, pay, newMod) => {
        if (!(mod.wid in openedModules)) {
            var window = Qt.createComponent('module.qml').createObject(mainWindow);
            openedModules[mod.wid] = window;
            window.title = mod.mtype + "/" + mod.mname;
            window.newModule = newMod;
            window.module = mod;
            window.wid = mod.wid;
            fillModuleOptions(window.idMap['mOpts'], mod);
            if (!pay) {
                window.idMap['mPayload'].visible = false
            } else {
                window.idMap['mPayloads'].model = mod.payloads;
                var index = mod.payload_metadata()
                if (index != -1) {
                    window.idMap['cbPayload'].enabled = false;
                    window.idMap['bPayAdd'].enabled = false;
                    window.idMap['bPayload'].enabled = true;
                    window.idMap['bPayEdit'].enabled = true;
                    window.idMap['bPayRemove'].enabled = true
                }
                window.idMap['mPayloads'].currentIndex = index
            }
        }
    }
    signal addedModule(wid: int)
    signal addModule(mod: var)
    onAddModule: mod => {
        wizardLoader.item.idMap['mList'].append(
            {hidden: mod.wid,
             name: mod.mtype + "/" + mod.mname});
        wizardLoader.item.idMap['bSave'].enabled = true;
        addedModule(mod.wid)
    }
    signal removeModule(wid: int)
    signal tmpRemoveModule(wid: int)
    signal deleteModule(wid: int)
    onDeleteModule: wid => {
        for (var i=0; i < wizardLoader.item.idMap['mList'].count; i++) {
            if (wizardLoader.item.idMap['mList'].get(i)['hidden'] === wid) {
                wizardLoader.item.idMap['mList'].remove(i);
                break
            }
        }
        if (wizardLoader.item.idMap['mList'].count == 0) {
            wizardLoader.item.idMap['bSave'].enabled = false
        }
        removeModule(wid)
    }
    signal generateRc()
    Labs.FileDialog {
        id: fileBrowser
        title: "Please choose file"
        onAccepted: target.text = file.toString().replace('file://', '')
        property var target
    }
    Labs.FolderDialog {
        id: folderBrowser
        title: "Please choose directory"
        onAccepted: target.text = folder.toString().replace('file://', '')
        property var target
    }
    ToolTip {
        id: tooltip
        font: fTooltip
    }
    Timer {
        id: tooltipTimer
        onTriggered: {
            tooltip.x = map.x;
            tooltip.y = map.y + sSPad;
            tooltip.show(text)
        }
        property string text
        property var map
    }
    Dialog {
        id: errorDialog
        anchors.centerIn: parent
        ColumnLayout {
            Label {
                id: errorDialogText
                font: fInput
            }
            DialogButtonBox {
                standardButtons: DialogButtonBox.Ok
                onAccepted: errorDialog.close()
            }
        }
    }
    Loader {
        id: wizardLoader
        source: 'wizard.qml'
        property alias item: wizardLoader.item
    }
    Loader {
        id: consoleLoader
        source: 'console.qml'
        property alias item: consoleLoader.item
    }
    FontLoader {
        id: roboto
        source: 'qrc:/font'
    }
    menuBar: RowLayout {
        spacing: 0
        MenuBar {
            id: mainMenuBar
            font: fMenubar
            Layout.fillWidth: true
            Menu {
                id: menu
                title: "&Windows"
                font: fTooltip
                MenuItem {
                    id: cWizard
                    text: "Wi&zard"
                    checkable: true
                    onToggled: {
                        if (checked) {
                            openOrRequestWizard()
                        } else {
                            wizardLoader.item.hide()
                        }
                    }
                }
                MenuItem {
                    id: cConsole
                    text: "&Console"
                    checkable: true
                    onToggled: {
                        if (checked) {
                            consoleLoader.item.show()
                        } else {
                            consoleLoader.item.hide()
                        }
                    }
                }
            }
            Menu {
                title: "&Settings"
                font: fTooltip
                MenuItem {
                    id: cStop
                    objectName: 'cStop'
                    text: "S&top containers after run"
                    checkable: true
                    checked: true
                }
                MenuItem {
                    id: cTheme
                    text: "&Light theme"
                    checkable: true
                    Component.onCompleted: checked = Material.theme === Material.Light
                }
            }
        }
        Rectangle {
            width: containersStatus.width
            height: mainMenuBar.height
            color: Material.dialogColor
            RowLayout {
                id: containersStatus
                height: parent.height
                spacing: -2
                Label {
                    text: "vpn"
                    font: fTooltip
                    topPadding: -3
                }
                ToolButton {
                    id: vpnStatus
                    icon.source: 'qrc:/off'
                    icon.width: 12
                    icon.height: 12
                    background: null
                }
                Item { implicitWidth: sSPad }
                Label {
                    text: "msf"
                    font: fTooltip
                    topPadding: -3
                }
                ToolButton {
                    id: msfStatus
                    icon.source: 'qrc:/off'
                    icon.width: 12
                    icon.height: 12
                    background: null
                }
                Item { implicitWidth: 5 }
            }
        }
    }
    TabBar {
        id: tabbar
        width: parent.width
        TabButton {
            text: "Main"
        }
        TabButton {
            text: "About"
        }
        TabButton {
            text: "License"
        }
    }
    StackLayout {
        id: tabLayouts
        anchors.top: tabbar.bottom
        width: parent.width
        height: parent.height - tabbar.height
        currentIndex: tabbar.currentIndex
        Item {
            id: boxMain
            width: parent.width
            height: parent.height
            Item {
                id: mainTopPadding
                implicitHeight: sSPad
                implicitWidth: parent.width
            }
            RowLayout {
                id: mainLayout
                width: parent.width
                height: parent.height - mainTopPadding.height - mainBottomPadding.height
                anchors.top: mainTopPadding.bottom
                Item { implicitWidth: sLPad }
                ColumnLayout {
                    spacing: -sSPad
                    RowLayout {
                        id: rowLog
                        Label {
                            id: lLog
                            Layout.fillWidth: true
                            text: "Log"
                            font: fLabel
                            MouseArea {
                                id: mouseLog
                                anchors.fill: parent
                                hoverEnabled: true
                                onEntered: {
                                    tooltipTimer.map = mapToItem(mainWindow.contentItem, lLog.x, lLog.y);
                                    tooltipTimer.text = "Autoauditor exploit execution trace";
                                    tooltipTimer.start()
                                }
                                onExited: {
                                    tooltipTimer.stop();
                                    tooltip.hide()
                                }
                            }
                        }
                        TextField {
                            id: tfLog
                            objectName: 'tfLog'
                            Layout.preferredWidth: sTextField
                            text: "output/msf.log"
                            placeholderText: "Log path..."
                            font: fInput
                            selectByMouse: true
                        }
                        ToolButton {
                            id: bLog
                            icon.source: 'qrc:/file'
                            onClicked: {
                                fileBrowser.nameFilters = ["LOG files (*.log)", "All files (*)"];
                                fileBrowser.target = tfLog;
                                fileBrowser.fileMode = Labs.FileDialog.SaveFile;
                                fileBrowser.open()
                            }
                        }
                    }
                    RowLayout {
                        id: rowLoot
                        Label {
                            id: lLoot
                            Layout.fillWidth: true
                            text: "Loot"
                            font: fLabel
                            MouseArea {
                                id: mouseLoot
                                anchors.fill: parent
                                hoverEnabled: true
                                onEntered: {
                                    tooltipTimer.map = mapToItem(mainWindow.contentItem, lLoot.x, lLoot.y);
                                    tooltipTimer.text = "Metasploit-framework loot storage";
                                    tooltipTimer.start()
                                }
                                onExited: {
                                    tooltipTimer.stop();
                                    tooltip.hide()
                                }
                            }
                        }
                        TextField {
                            id: tfLoot
                            objectName: 'tfLoot'
                            Layout.preferredWidth: sTextField
                            text: "output"
                            placeholderText: "Loot path..."
                            font: fInput
                            selectByMouse: true
                        }
                        ToolButton {
                            id: bLoot
                            icon.source: 'qrc:/folder'
                            onClicked: {
                                folderBrowser.target = tfLoot;
                                folderBrowser.open()
                            }
                        }
                    }
                    RowLayout {
                        id: rowRc
                        Label {
                            id: lRc
                            Layout.fillWidth: true
                            text: "Resources script"
                            font: fLabel
                            MouseArea {
                                id: mouseRc
                                anchors.fill: parent
                                hoverEnabled: true
                                onEntered: {
                                    tooltipTimer.map = mapToItem(mainWindow.contentItem, lRc.x, lRc.y);
                                    tooltipTimer.text = "Exploits to be run in metasploit-framework";
                                    tooltipTimer.start()
                                }
                                onExited: {
                                    tooltipTimer.stop();
                                    tooltip.hide()
                                }
                            }
                        }
                        TextField {
                            id: tfRc
                            objectName: 'tfRc'
                            Layout.preferredWidth: sTextField
                            text: "tools/vulnerable_net/examples/rc.example5v.json"
                            placeholderText: "Resources script path..."
                            font: fInput
                            selectByMouse: true
                        }
                        ToolButton {
                            id: bRc
                            icon.source: 'qrc:/file'
                            onClicked: {
                                fileBrowser.nameFilters = ["JSON files (*.json)", "All files (*)"];
                                fileBrowser.target = tfRc;
                                fileBrowser.fileMode = sErc.checked ? Labs.FileDialog.OpenFile : Labs.FileDialog.SaveFile;
                                fileBrowser.open()
                            }
                        }
                    }
                    RowLayout {
                        id: rowCVE
                        Label {
                            id: lCVE
                            Layout.fillWidth: true
                            text: "CVEScanner report"
                            font: fLabel
                            MouseArea {
                                id: mouseCVE
                                anchors.fill: parent
                                hoverEnabled: true
                                onEntered: {
                                    tooltipTimer.map = mapToItem(mainWindow.contentItem, lCVE.x, lCVE.y);
                                    tooltipTimer.text = "CVEScannerV2 report (JSON)";
                                    tooltipTimer.start()
                                }
                                onExited: {
                                    tooltipTimer.stop();
                                    tooltip.hide()
                                }
                            }
                        }
                        TextField {
                            id: tfCVE
                            objectName: 'tfCVE'
                            Layout.preferredWidth: sTextField
                            placeholderText: "Resources script path..."
                            font: fInput
                            selectByMouse: true
                        }
                        ToolButton {
                            id: bCVE
                            icon.source: 'qrc:/file'
                            onClicked: {
                                fileBrowser.nameFilters = ["JSON files (*.json)"];
                                fileBrowser.target = tfCVE;
                                fileBrowser.fileMode = Labs.FileDialog.OpenFile;
                                fileBrowser.open()
                            }
                        }
                    }
                    RowLayout {
                        id: rowErc
                        Label {
                            id: lErc
                            Layout.preferredWidth: lRc.width
                            text: "Edit"
                            font: fSwitch
                            MouseArea {
                                id: mouseErc
                                anchors.fill: parent
                                hoverEnabled: true
                                onEntered: {
                                    tooltipTimer.map = mapToItem(mainWindow.contentItem, lErc.x, lErc.y);
                                    tooltipTimer.text = "Load resources script data to be edited in wizard";
                                    tooltipTimer.start()
                                }
                                onExited: {
                                    tooltipTimer.stop();
                                    tooltip.hide()
                                }
                            }
                        }
                        Item { Layout.fillWidth: true }
                        Switch {
                            id: sErc
                            objectName: 'sErc'
                            checked: true
                        }
                    }
                    Item {
                        id: boxSep45
                        Layout.alignment: Qt.AlignHCenter
                        implicitHeight: sSPad
                        implicitWidth: (parent.width/6) * 5
                        MenuSeparator {
                            width: boxSep45.width
                            anchors.centerIn: parent
                        }
                    }
                    RowLayout {
                        id: rowVcfg
                        Label {
                            id: lVcfg
                            Layout.fillWidth: true
                            text: "Vpn configuration"
                            font: fLabel
                            MouseArea {
                                id: mouseVcfg
                                anchors.fill: parent
                                hoverEnabled: true
                                onEntered: {
                                    tooltipTimer.map = mapToItem(mainWindow.contentItem, lVcfg.x, lVcfg.y);
                                    tooltipTimer.text = "OpenVPN connection file";
                                    tooltipTimer.start()
                                }
                                onExited: {
                                    tooltipTimer.stop();
                                    tooltip.hide()
                                }
                            }
                        }
                        TextField {
                            id: tfVcfg
                            objectName: 'tfVcfg'
                            Layout.preferredWidth: sTextField
                            text: "tools/vulnerable_net/examples/vpn.example.ovpn"
                            placeholderText: "Vpn configuration path..."
                            font: fInput
                            selectByMouse: true
                        }
                        ToolButton {
                            id: bVpn
                            icon.source: 'qrc:/file'
                            onClicked: {
                                fileBrowser.nameFilters = ["OVPN files (*.ovpn)", "All files (*)"];
                                fileBrowser.target = tfVcfg;
                                fileBrowser.fileMode = Labs.FileDialog.SaveFile;
                                fileBrowser.open()
                            }
                        }
                    }
                    RowLayout {
                        id: rowVpn
                        Label {
                            id: lVpn
                            Layout.preferredWidth: lVcfg.width
                            text: "Connect"
                            font: fSwitch
                            MouseArea {
                                id: mouseVpn
                                anchors.fill: parent
                                hoverEnabled: true
                                onEntered: {
                                    tooltipTimer.map = mapToItem(mainWindow.contentItem, lVpn.x, lVpn.y);
                                    tooltipTimer.text = "Establish a vpn using connection file";
                                    tooltipTimer.start()
                                }
                                onExited: {
                                    tooltipTimer.stop();
                                    tooltip.hide()
                                }
                            }
                        }
                        Item { Layout.fillWidth: true }
                        Switch {
                            id: sVpn
                            objectName: 'sVpn'
                        }
                    }
                    Item {
                        id: boxSep67
                        Layout.alignment: Qt.AlignHCenter
                        implicitHeight: sSPad
                        implicitWidth: (parent.width/6) * 5
                        MenuSeparator {
                            width: boxSep67.width
                            anchors.centerIn: parent
                        }
                    }
                    RowLayout {
                        id: rowBcfg
                        Label {
                            id: lBcfg
                            Layout.fillWidth: true
                            text: "Blockchain configuration"
                            font: fLabel
                            MouseArea {
                                id: mouseBcfg
                                anchors.fill: parent
                                hoverEnabled: true
                                onEntered: {
                                    tooltipTimer.map = mapToItem(mainWindow.contentItem, lBcfg.x, lBcfg.y);
                                    tooltipTimer.text = "Blockchain connection file";
                                    tooltipTimer.start()
                                }
                                onExited: {
                                    tooltipTimer.stop();
                                    tooltip.hide()
                                }
                            }
                        }
                        TextField {
                            id: tfBcfg
                            objectName: 'tfBcfg'
                            Layout.preferredWidth: sTextField
                            text: "tools/vulnerable_net/examples/network.example.json"
                            placeholderText: "Blockchain configuration path..."
                            font: fInput
                            selectByMouse: true
                        }
                        ToolButton {
                            id: bBcfg
                            icon.source: 'qrc:/file'
                            onClicked: {
                                fileBrowser.nameFilters = ["JSON files (*.json)", "All files (*)"];
                                fileBrowser.target = tfBcfg;
                                fileBrowser.fileMode = Labs.FileDialog.SaveFile;
                                fileBrowser.open()
                            }
                        }
                    }
                    RowLayout {
                        id: rowBlog
                        Label {
                            id: lBlog
                            Layout.fillWidth: true
                            text: "Blockchain log"
                            font: fLabel
                            MouseArea {
                                id: mouseBlog
                                anchors.fill: parent
                                hoverEnabled: true
                                onEntered: {
                                    tooltipTimer.map = mapToItem(mainWindow.contentItem, lBlog.x, lBlog.y);
                                    tooltipTimer.text = "Blockchain uploaded reports";
                                    tooltipTimer.start()
                                }
                                onExited: {
                                    tooltipTimer.stop();
                                    tooltip.hide()
                                }
                            }
                        }
                        TextField {
                            id: tfBlog
                            objectName: 'tfBlog'
                            Layout.preferredWidth: sTextField
                            text: "output/blockchain.log"
                            placeholderText: "Blockchain log path..."
                            font: fInput
                            selectByMouse: true
                        }
                        ToolButton {
                            id: bBlog
                            icon.source: 'qrc:/file'
                            onClicked: {
                                fileBrowser.nameFilters = ["LOG files (*.log)", "All files (*)"];
                                fileBrowser.target = tfBlog;
                                fileBrowser.fileMode = Labs.FileDialog.SaveFile;
                                fileBrowser.open()
                            }
                        }
                    }
                    RowLayout {
                        id: rowBc
                        Label {
                            id: lBc
                            Layout.preferredWidth: lBcfg.width
                            text: "Store"
                            font: fSwitch
                            MouseArea {
                                id: mouseBc
                                anchors.fill: parent
                                hoverEnabled: true
                                onEntered: {
                                    tooltipTimer.map = mapToItem(mainWindow.contentItem, lBc.x, lBc.y);
                                    tooltipTimer.text = "Upload autoauditor reports to blockchain";
                                    tooltipTimer.start()
                                }
                                onExited: {
                                    tooltipTimer.stop();
                                    tooltip.hide()
                                }
                            }
                        }
                        Item { Layout.fillWidth: true }
                        Switch {
                            id: sBc
                            objectName: 'sBc'
                        }
                    }
                    Item {
                        id: boxSep910
                        Layout.alignment: Qt.AlignHCenter
                        implicitHeight: sSPad
                        implicitWidth: (parent.width/6) * 5
                    }
                    RowLayout {
                        id: rowActions
                        spacing: 60
                        Layout.alignment: Qt.AlignHCenter
                        Item {
                            width: bRun.width
                            height: bRun.height
                            Button {
                                id: bRun
                                text: "Run"
                                icon.source: 'qrc:/run'
                                icon.width: 36
                                icon.height: 36
                                onClicked: {
                                    pbRun.visible = true;
                                    requestRun()
                                }
                                ProgressBar {
                                    id: pbRun
                                    indeterminate: true
                                    width: parent.width
                                    anchors.bottom: parent.bottom
                                    visible: false
                                }
                            }
                        }
                        Button {
                            id: bStore
                            text: "Store"
                            icon.source: 'qrc:/store'
                            icon.width: 36
                            icon.height: 36
                            onClicked: {
                                pbStore.visible = true;
                                requestStore()
                            }
                            ProgressBar {
                                id: pbStore
                                indeterminate: true
                                width: parent.width
                                anchors.bottom: parent.bottom
                                visible: false
                            }
                        }
                        Item {
                            width: bWizard.width
                            height: bWizard.height
                            Button {
                                id: bWizard
                                text: "Wizard"
                                icon.source: 'qrc:/wizard'
                                icon.width: 36
                                icon.height: 36
                                onClicked: {
                                    pbWizard.visible = true;
                                    requestWizard()
                                }
                            }
                            ProgressBar {
                                id: pbWizard
                                indeterminate: true
                                width: parent.width
                                anchors.bottom: parent.bottom
                                visible: false
                            }
                        }
                        Button {
                            id: bStop
                            text: "Stop"
                            icon.source: 'qrc:/stop'
                            icon.width: 36
                            icon.height: 36
                            onClicked: {
                                pbStop.visible = true;
                                requestStop()
                            }
                            ProgressBar {
                                id: pbStop
                                indeterminate: true
                                width: parent.width
                                anchors.bottom: parent.bottom
                                visible: false
                            }
                        }
                    }
                }
                Item { implicitWidth: sMPad }
            }
            Item {
                id: mainBottomPadding
                implicitHeight: sSPad
                implicitWidth: parent.width
                anchors.top: mainLayout.bottom
            }
        }
        Item {
            id: boxAbout
            width: parent.width
            height: parent.height
            Item {
                id: aboutTopPadding
                implicitHeight: sSPad
                implicitWidth: parent.width
            }
            ColumnLayout {
                id: aboutLayout
                width: parent.width
                height: parent.height - aboutTopPadding.height - aboutBottomPadding.height
                anchors.top: aboutTopPadding.bottom
                spacing: 30
                Label {
                    id: lAutoauditor
                    Layout.fillWidth: true
                    text: "autoauditor\nv3.1"
                    font: fLabel
                    horizontalAlignment: Text.AlignHCenter
                    topPadding: sSPad
                }
                Label {
                    id: lAuthor
                    Layout.fillWidth: true
                    text: "Sergio Chica Manjarrez\nPervasive Computing Laboratory\nTelematic Engineering Department\nUniversidad Carlos III de Madrid, Leganés\nMadrid, Spain"
                    font: fInput
                    horizontalAlignment: Text.AlignHCenter
                }
                Label {
                    id: lSupported
                    Layout.fillWidth: true
                    text: "This work has been supported by National R&D Projects TEC2017-84197-C4-1-R, TEC2014-54335-C4-2-R, and by the Comunidad de Madrid project CYNAMON P2018/TCS-4566 and co-financed by European Structural Funds (ESF and FEDER)."
                    font: fInput
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    leftPadding: sLPad
                    rightPadding: sLPad
                }
                Label {
                    id: lYear
                    Layout.fillWidth: true
                    text: new Date().toLocaleDateString(Qt.locale('esES'), 'yyyy')
                    font: fInput
                    horizontalAlignment: Text.AlignHCenter
                    bottomPadding: sSPad
                }
            }
            Item {
                id: aboutBottomPadding
                implicitHeight: sSPad
                implicitWidth: parent.width
                anchors.top: aboutLayout.bottom
            }
        }
        Item {
            id: boxLicense
            width: parent.width
            height: parent.height
            Item {
                id: licenseTopPadding
                implicitHeight: sSPad
                implicitWidth: parent.width
            }
            ColumnLayout {
                id: licenseLayout
                width: parent.width
                height: parent.height - licenseTopPadding.height - licenseBottomPadding.height
                anchors.top: licenseTopPadding.bottom
                spacing: sSPad
                Label {
                    id: lLicense
                    Layout.fillWidth: true
                    text: "autoauditor Copyright (C) 2020-2022 Sergio Chica Manjarrez @ pervasive.it.uc3m.es\nUniversidad Carlos III de Madrid\nThis program comes with ABSOLUTELY NO WARRANTY; for details check below. This is free software, and you are welcome to redistribute it under certain conditions; check below for details."
                    font: fInput
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    topPadding: sSPad
                    leftPadding: sLPad
                    rightPadding: sLPad
                }
                RowLayout {
                    id: boxFullLicense
                    width: parent.width
                    height: parent.height - lLicense.height
                    Item { implicitWidth: sLPad }
                    ScrollView {
                        id: svLicense
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        TextArea {
                            id: taLicense
                            objectName: 'taLicense'
                            font: fTooltip
                            horizontalAlignment: Text.AlignHCenter
                            readOnly: true
                            selectByMouse: true
                            background: Rectangle {
                                color: Material.dialogColor
                            }
                        }
                    }
                    Item { implicitWidth: sLPad }
                }
            }
            Item {
                id: licenseBottomPadding
                implicitHeight: sSPad
                implicitWidth: parent.width
                anchors.top: licenseLayout.bottom
            }
        }
    }
}
