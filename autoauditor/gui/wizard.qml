import QtQuick.Controls 6.2
import QtQuick.Layouts 6.2
import QtQuick.Window 6.2
import QtQuick 6.2

ApplicationWindow {
    id: wizardWindow
    title: "wizard"
    minimumWidth: mainWindow.minimumWidth
    minimumHeight: mainWindow.minimumHeight
    Material.theme: cTheme.checked ? Material.Light : Material.Dark

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
    property int sKey: 120
    property var idMap: ({
        'mName': cbMname,
        'mInfo': infoModel,
        'mInfoDialog': infoDialog,
        'mList': modulesModel,
        'bSave': bSave,
        'warnDialog': warnDialog
    })
    onClosing: cWizard.checked = false
    Dialog {
        id: warnDialog
        anchors.centerIn: parent
        ColumnLayout {
            Label {
                id: warnDialogText
                text: "File " + tfRc.text + " exists.\nOverwrite?"
                font: fInput
            }
            DialogButtonBox {
                standardButtons: DialogButtonBox.Save | DialogButtonBox.Cancel
                onAccepted: {
                    generateRc();
                    warnDialog.close()
                }
                onRejected: warnDialog.close()
            }
        }
    }
    Dialog {
        id: infoDialog
        width: 600
        height: 400
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
                            Layout.preferredWidth: sKey
                            Layout.alignment: Qt.AlignTop
                        }
                        TextArea {
                            text: value
                            font: fComboBox
                            Layout.preferredWidth: boxInfoDialog.width - sKey - sLPad * 2
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
        id: boxWizard
        width: parent.width
        height: parent.height
        Item {
            id: wizardTopPadding
            implicitHeight: sSPad
            implicitWidth: parent.width
        }
        RowLayout {
            id: wizardLayout
            width: parent.width
            height: parent.height - wizardTopPadding.height - wizardBottomPadding.height
            anchors.top: wizardTopPadding.bottom
            Item { implicitWidth: sLPad }
            ColumnLayout {
                spacing: sSPad
                RowLayout {
                    id: rowMtype
                    Label {
                        id: lMtype
                        Layout.fillWidth: true
                        text: 'Module type'
                        font: fLabel
                    }
                    Item { Layout.preferredWidth: bMname.width }
                    ComboBox {
                        id: cbMtype
                        Layout.preferredWidth: sTextField
                        model: ['auxiliary', 'encoder', 'exploit', 'nop', 'payload', 'post']
                        font: fComboBox
                        currentIndex: -1
                        onActivated: {
                            moduleTypeSelected(currentText);
                            cbMname.enabled = true;
                            bAdd.enabled = true
                        }
                    }
                }
                RowLayout {
                    id: rowMname
                    Label {
                        id: lMname
                        Layout.fillWidth: true
                        text: 'Module name'
                        font: fLabel
                    }
                    ToolButton {
                        id: bMname
                        icon.source: 'qrc:/info'
                        onClicked: moduleInfo(-1)
                        Component.onCompleted: enabled = false
                    }
                    ComboBox {
                        id: cbMname
                        Layout.preferredWidth: sTextField
                        font: fComboBox
                        onCurrentTextChanged: {
                            bMname.enabled = true;
                            moduleNameSelected(cbMtype.currentText, cbMname.currentText)
                        }
                        Component.onCompleted: enabled = false
                    }
                }
                RowLayout {
                    id: rowAdd
                    Button {
                        id: bAdd
                        text: "Add"
                        icon.source: 'qrc:/add'
                        Component.onCompleted: enabled = false
                        onClicked: requestModule(-1)
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        id: bSave
                        text: "Save"
                        icon.source: 'qrc:/save'
                        onClicked: checkSave()
                        Component.onCompleted: enabled = false
                    }
                }
                Rectangle {
                    id: boxModules
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    color: Material.dialogColor
                    ListModel {
                        id: modulesModel
                    }
                    Component {
                        id: modulesDelegate
                        RowLayout {
                            width: boxModules.width
                            Label {
                                id: lHidden
                                text: hidden
                                visible: false
                            }
                            ToolButton {
                                icon.source: 'qrc:/edit'
                                onClicked: requestModule(lHidden.text)
                            }
                            ToolButton {
                                icon.source: 'qrc:/remove'
                                onClicked: deleteModule(lHidden.text)
                            }
                            Item {
                                Layout.fillWidth: true
                            }
                            ToolButton {
                                icon.source: 'qrc:/info'
                                onClicked: moduleInfo(lHidden.text)
                            }
                            TextField {
                                text: name
                                font: fSwitch
                                Layout.preferredWidth: sTextField - sMenuBar
                                leftPadding: 12
                                topPadding: 0
                                bottomPadding: 0
                                readOnly: true
                                selectByMouse: true
                                background: Rectangle {
                                    color: Material.dialogColor
                                }
                                Component.onCompleted: ensureVisible(0)
                            }
                            Item { implicitWidth: sSPad }
                        }
                    }
                    ListView {
                        anchors.fill: parent
                        model: modulesModel
                        delegate: modulesDelegate
                        spacing: sSPad
                        ScrollBar.vertical: ScrollBar {}
                        boundsBehavior: Flickable.StopAtBounds
                    }
                }
            }
            Item { implicitWidth: sLLPad }
        }
        Item {
            id: wizardBottomPadding
            implicitHeight: sSPad
            implicitWidth: parent.width
            anchors.top: wizardLayout.bottom
        }
    }
}
