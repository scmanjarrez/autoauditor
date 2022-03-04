import QtQuick.Controls 6.2
import QtQuick.Layouts 6.2
import QtQuick.Window 6.2
import OptionsModel
import QtQuick 6.2

ApplicationWindow {
    id: moduleWindow
    minimumWidth: mainWindow.minimumWidth
    minimumHeight: mainWindow.minimumHeight
    Material.theme: cTheme.checked ? Material.Light : Material.Dark
    visible: true
    onClosing: {
        if (!isPayload) {
            tmpRemoveModule(wid);
            delete openedModules[wid]
        } else {
            parentWindow.openedPayload = false
        }
    }

    property font fComboBox: Qt.font({
        family: roboto.name,
        weight: Font.Light,
        pixelSize: 15
    })
    property font fModule: Qt.font({
        family: roboto.name,
        weight: Font.Medium,
        pixelSize: 13
    })
    property int sLLPad: sLPad + 1
    property int sMMPad: sLPad - 16
    property int sKey: 150
    property int sKKey: 120
    property int sReq: 80
    property int sTextField: 300
    property QtObject module
    property bool newModule
    property var parentWindow
    property var idMap: ({
        'cbPayload': cbPayload,
        'bPayAdd': bPayAdd,
        'bPayEdit': bPayEdit,
        'bPayRemove': bPayRemove,
        'bPayload': bPayInfo,
        'mOpts': moduleModel,
        'mPayload': boxPayload,
        'mPayloads': cbPayload
    })
    property int wid
    property bool isPayload: false
    property bool openedPayload: false
    signal optionInfo(opt: string, pay: bool)
    onOptionInfo: (opt, pay) => {
        var info
        if (pay) {
            info = module.payload.opt_info(opt);
        } else {
            info = module.opt_info(opt);
        }
        infoModel.clear();
        for (var k in info) {
            infoModel.append(
                {key: k[0].toUpperCase() + k.substring(1),
                 value: info[k]})
        }
        infoDialog.width = 485;
        infoDialog.height = 285;
        infoDialog.open()
    }
    signal payloadInfo()
    onPayloadInfo: {
        infoModel.clear();
        var pinfo = module.payload_info();
        for (var k in pinfo) {
            infoModel.append(
                {'key': k[0].toUpperCase() + k.substring(1),
                 'value': pinfo[k]})
        }
        infoDialog.width = 600;
        infoDialog.height = 400;
        infoDialog.open()
    }
    signal openPayloadOptions()
    onOpenPayloadOptions: {
        if (!openedPayload) {
            var window = Qt.createComponent('module.qml').createObject(moduleWindow);
            openedPayload = true;
            var pay = module.payload
            window.title = "payload/" + pay.mname;
            window.module = module;
            window.parentWindow = moduleWindow;
            window.wid = pay.wid;
            window.isPayload = true;
            fillModuleOptions(window.idMap['mOpts'], pay);
            window.idMap['mPayload'].visible = false
        }
    }
    signal showError(error: string)
    onShowError: error => {
        optionErrorDialogText.text = error;
        optionErrorDialog.open()
    }
    Dialog {
        id: optionErrorDialog
        anchors.centerIn: parent
        ColumnLayout {
            Label {
                id: optionErrorDialogText
                font: fInput
            }
            DialogButtonBox {
                standardButtons: DialogButtonBox.Ok
                onAccepted: optionErrorDialog.close()
            }
        }
    }
    Dialog {
        id: infoDialog
        anchors.centerIn: parent
        onClosed: infoView.positionViewAtBeginning()
        ColumnLayout {
            id: boxInfoDialog
            width: parent.width
            height: parent.height
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                color: Material.dialogColor
                ListModel {
                    id: infoModel
                }
                Component {
                    id: infoDelegate
                    RowLayout {
                        spacing: sLPad
                        width: boxInfoDialog.width
                        Label {
                            text: key
                            font: fSwitch
                            Layout.preferredWidth: sKKey
                            Layout.alignment: Qt.AlignTop
                        }
                        TextArea {
                            text: value
                            font: fComboBox
                            Layout.preferredWidth: boxInfoDialog.width - sKKey - sLPad * 2
                            wrapMode: Text.WordWrap
                            topPadding: 0
                            bottomPadding: 0
                            readOnly: true
                            selectByMouse: true
                            background: Rectangle {
                                color: Material.dialogColor
                            }
                        }
                    }
                }
                ListView {
                    id: infoView
                    anchors.fill: parent
                    model: infoModel
                    delegate: infoDelegate
                    spacing: 10
                    ScrollBar.vertical: ScrollBar {}
                    boundsBehavior: Flickable.StopAtBounds
                }
            }
            DialogButtonBox {
                standardButtons: DialogButtonBox.Ok
                onAccepted: infoDialog.close()
            }
        }
    }
    Item {
        id: boxModule
        width: moduleWindow.width
        height: moduleWindow.height
        Item {
            id: moduleTopPadding
            implicitHeight: sSPad
            implicitWidth: parent.width
        }
        RowLayout {
            id: moduleLayout
            width: moduleWindow.width
            height: moduleWindow.height - moduleTopPadding.height - moduleBottomPadding.height
            anchors.top: moduleTopPadding.bottom
            Item { implicitWidth: sLPad }
            ColumnLayout {
                spacing: sSPad
                RowLayout {
                    Layout.preferredHeight: 20
                    Label {
                        text: "Option"
                        font: fLabel
                        Layout.fillWidth: true
                    }
                    Rectangle {
                        Layout.preferredWidth: 36
                    }
                    Label {
                        text: "Value"
                        font: fLabel
                        Layout.preferredWidth: sTextField
                    }
                    Label {
                        text: "Required"
                        font: fLabel
                        Layout.preferredWidth: sReq
                    }
                }
                Rectangle {
                    id: boxOptions
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    color: Material.backgroundColor
                    OptionsModel {
                        id: moduleModel
                    }
                    Component {
                        id: moduleDelegate
                        RowLayout {
                            width: boxOptions.width
                            TextField {
                                id: tfKey
                                text: key
                                font: fSwitch
                                Layout.fillWidth: true
                                readOnly: true
                                selectByMouse: true
                                background: Rectangle {
                                    color: Material.backgroundColor
                                }
                                Component.onCompleted: ensureVisible(0)
                            }
                            ToolButton {
                                icon.source: 'qrc:/info'
                                onClicked: optionInfo(tfKey.text, isPayload)
                            }
                            TextField {
                                id: tfValue
                                text: value
                                font: fComboBox
                                Layout.preferredWidth: sTextField
                                wrapMode: Text.WordWrap
                                topPadding: 0
                                bottomPadding: 0
                                selectByMouse: true
                                visible: !isCombo
                                onEditingFinished: module.set_mopt(moduleWindow,
                                                                   tfKey.text,
                                                                   tfValue.text,
                                                                   isPayload)
                            }
                            ComboBox {
                                id: cbValue
                                font: fComboBox
                                model: ListModel {
                                    Component.onCompleted: {
                                        if (isCombo) {
                                            for (var vl in valueList){
                                                if (vl != 0) {
                                                    append({text: valueList[vl]})
                                                }
                                            }
                                        }
                                    }
                                }
                                Layout.preferredWidth: sTextField
                                visible: isCombo
                                Component.onCompleted: {
                                    if (isCombo) {
                                        currentIndex = parseInt(valueList[0])
                                    }
                                }
                                onActivated: {
                                    module.set_mopt(moduleWindow,
                                                    tfKey.text,
                                                    currentText,
                                                    isPayload)
                                }
                            }
                            Label {
                                text: req
                                font: fSwitch
                                Layout.preferredWidth: sReq
                                Layout.alignment: Qt.AlignVCenter
                            }
                        }
                    }
                    ListView {
                        anchors.fill: parent
                        model: moduleModel
                        delegate: moduleDelegate
                        spacing: sSPad
                        ScrollBar.vertical: ScrollBar {}
                        boundsBehavior: Flickable.StopAtBounds
                    }
                }
                RowLayout {
                    id: boxPayload
                    Layout.preferredHeight: 15
                    Label {
                        text: "Add payload..."
                        Layout.fillWidth: true
                        font: fSwitch
                    }
                    ToolButton {
                        id: bPayInfo
                        icon.source: 'qrc:/info'
                        enabled: false
                        onClicked: payloadInfo()
                    }
                    ComboBox {
                        id: cbPayload
                        Layout.preferredWidth: sTextField
                        font: fComboBox
                        onActivated: {
                            module.payload_load(currentText);
                            bPayInfo.enabled = true;
                            bPayAdd.enabled = true;
                        }
                    }
                    RowLayout {
                        spacing: -8
                        ToolButton {
                            id: bPayAdd
                            Layout.preferredHeight: 32
                            Layout.preferredWidth: 32
                            icon.source: 'qrc:/add'
                            enabled: false
                            onClicked: openPayloadOptions()
                        }
                        ToolButton {
                            id: bPayEdit
                            Layout.preferredHeight: 32
                            Layout.preferredWidth: 32
                            icon.source: 'qrc:/edit'
                            enabled: false
                            onClicked: openPayloadOptions()
                        }
                        ToolButton {
                            id: bPayRemove
                            Layout.preferredHeight: 32
                            Layout.preferredWidth: 32
                            icon.source: 'qrc:/remove'
                            enabled: false
                            onClicked: {
                                module.payload_unset();
                                cbPayload.enabled = true;
                                bPayAdd.enabled = true;
                                bPayEdit.enabled = false;
                                bPayRemove.enabled = false
                            }
                        }
                    }
                }
                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 30
                    Button {
                        id: bAccept
                        text: "Accept"
                        onClicked: {
                            var correct = false
                            if (!isPayload) {
                                if (!module.missing_required(moduleWindow)
                                    && newModule) {
                                    correct = true
                                    addModule(module)
                                }
                            } else {
                                if (!module.payload.missing_required(moduleWindow)) {
                                    correct = true
                                    parentWindow.idMap['cbPayload'].enabled = false;
                                    parentWindow.idMap['bPayAdd'].enabled = false;
                                    parentWindow.idMap['bPayEdit'].enabled = true;
                                    parentWindow.idMap['bPayRemove'].enabled = true;
                                    module.payload_set()
                                }
                            }
                            if (correct)
                                moduleWindow.close()
                        }
                    }
                    Button {
                        id: bCancel
                        text: "Cancel"
                        onClicked: moduleWindow.close()
                    }
                }
            }
            Item { implicitWidth: sLPad }
        }
        Item {
            id: moduleBottomPadding
            implicitHeight: sSPad
            implicitWidth: parent.width
            anchors.top: moduleLayout.bottom
        }
    }
}
