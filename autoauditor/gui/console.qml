/* SPDX-License-Identifier: GPL-3.0-or-later */

/* console - Graphical User Interface (Console) QML. */

/* Copyright (C) 2022 Sergio Chica Manjarrez @ pervasive.it.uc3m.es. */
/* Universidad Carlos III de Madrid. */

/* This file is part of autoauditor. */

/* autoauditor is free software: you can redistribute it and/or modify */
/* it under the terms of the GNU General Public License as published by */
/* the Free Software Foundation, either version 3 of the License, or */
/* (at your option) any later version. */

/* autoauditor is distributed in the hope that it will be useful, */
/* but WITHOUT ANY WARRANTY; without even the implied warranty of */
/* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the */
/* GNU General Public License for more details. */

/* You should have received a copy of the GNU General Public License */
/* along with this program.  If not, see <https://www.gnu.org/licenses/>. */

import QtQuick.Controls 6.2
import QtQuick.Layouts 6.2
import QtQuick.Window 6.2
import QtQuick 6.2

ApplicationWindow {
    id: consoleWindow
    title: "console"
    width: mainWindow.minimumWidth
    height: 200
    x: mainWindow.x
    y: mainWindow.y + mainWindow.height + sSPad + sMenuBar
    Material.theme: cTheme.checked ? Material.Light : Material.Dark

    property alias text: taConsole.text
    Item {
        id: consoleTopPadding
        width: parent.width
        height: sSPad
    }
    RowLayout {
        id: boxConsole
        width: parent.width
        height: parent.height - consoleTopPadding.height - consoleBottomPadding.height
        anchors.top: consoleTopPadding.bottom
        Item { implicitWidth: sLPad }
        ScrollView {
            id: svConsole
            Layout.fillWidth: true
            Layout.fillHeight: true
            TextArea {
                id: taConsole
                objectName: 'taConsole'
                font: Qt.font({
                    family: 'Consolas',
                    pixelSize: 15
                })
                wrapMode: Text.WordWrap
                readOnly: true
                selectByMouse: true
                background: Rectangle {
                    color: Material.dialogColor
                }
                Component.onCompleted: rightPadding = sSPad
            }
            onContentHeightChanged: if (contentHeight > consoleWindow.height) {
                Qt.callLater(() => contentItem.contentY = contentHeight - height)
            }
        }
        Item { implicitWidth: sLPad }
    }
    Item {
        id: consoleBottomPadding
        width: parent.width
        height: sSPad
        anchors.top: boxConsole.bottom
    }
}
