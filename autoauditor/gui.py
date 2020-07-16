#!/usr/bin/env python3
import PySimpleGUI as sg
import fontawesome as fa

sg.theme('Reddit')	# Add a touch of color
# All the stuff inside your window.
filepng = 'iVBORw0KGgoAAAANSUhEUgAAABgAAAAgCAYAAAAIXrg4AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAACFSURBVEiJ7dC9DkAwGEbhQ8XghlyZwWgzuN4murCUNJTo3+Q7iaGJvE9agBlYgS3wO9LAyEsx4y5wnKcnIGbcB2z2NYoCXiQ3cENKACdSXX4OqXKAp8bSgG4ixwFawDiQtzoBGCzyWsoTfSrlBgIIIIAAAgjwM8AU3F8V0AE9oDKPG2DZAZVbdv9fKQUhAAAAAElFTkSuQmCC'
folderpng = 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAYCAYAAACbU/80AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABtSURBVEiJ7dYxEoAgDETRLwXntgzn4Gww3kILoLESjKZJZrah2Ue3ABFIQAXOh9lRPJko/gQx8/N7RAOwWq6GeAtYSenwuPUHq0vWgMMaQLAsd4ADHOAABzhgAKphfwlANgRkaLNcaDPp90l2AYuzfIE6Q1SuAAAAAElFTkSuQmCC'

lfb = sg.FileBrowse(button_text='', target='inputlog')
lfb.ImageData = filepng
lfb.ImageSize = (32, 32)
lfb.ButtonColor = ('white', 'white')
lfb.BorderWidth = 0

ldb = sg.FolderBrowse(button_text='', target='inputdir')
ldb.ImageData = folderpng
ldb.ButtonColor = ('white', 'white')
ldb.BorderWidth = 0

rcb = sg.FileBrowse(button_text='', target='inputrc')
rcb.ImageData = filepng
rcb.ImageSize = (32, 32)
rcb.ButtonColor = ('white', 'white')
rcb.BorderWidth = 0

vpnit = sg.InputText('client.ovpn', key='inputovpn')
vpnit.Disabled = True

vpnb = sg.FileBrowse(button_text='', target='inputovpn')
vpnb.ImageData = filepng
vpnb.ImageSize = (32, 32)
vpnb.ButtonColor = ('white', 'white')
vpnb.Disabled = True
vpnb.BorderWidth = 0

hfcit = sg.InputText('network.template.json', key='inputhfc')
hfcit.Disabled = True

hfcb = sg.FileBrowse(button_text='', target='inputhfc')
hfcb.ImageData = filepng
hfcb.ImageSize = (32, 32)
hfcb.ButtonColor = ('white', 'white')
hfcb.Disabled = True
hfcb.BorderWidth = 0

hfoit = sg.InputText('output/blockchain.log', key='inputhfo')
hfoit.Disabled = True

hfob = sg.FileBrowse(button_text='', target='inputhfo')
hfob.ImageData = filepng
hfob.ImageSize = (32, 32)
hfob.ButtonColor = ('white', 'white')
hfob.Disabled = True
hfob.BorderWidth = 0

layout = [
    [sg.Text('Log File', size=(30, 1)), sg.InputText('output/msf.log', key='inputlog'), lfb],

    [sg.Text('Log Directory', size=(30, 1)), sg.InputText('output', key='inputdir'), ldb],

    [sg.Text('Resources Script File', size=(30, 1)), sg.InputText('rc5.json', key='inputrc'), rcb],

    [sg.Checkbox('VPN')],
    [sg.Text('OpenVPN Configuration File', size=(30, 1)), vpnit, vpnb],

    [sg.Checkbox('Blockchain')],
    [sg.Text('Blockchain Configuration File', size=(30, 1)), hfcit, hfcb],
    [sg.Text('Blockchain Log File', size=(30, 1)), hfoit, hfob],

    [sg.Checkbox('Stop container(s) after execution.', default=True)],
    [
        sg.Button('Run', button_color=('white', 'green'), key='run'),
        sg.Button('Open Wizard', button_color=('white', 'blue'), key='wizard'),
        sg.Button('Stop Orphan Machines', button_color=('white', 'red'), key='test')
    ]
]



# Create the Window
window = sg.Window('AutoAuditor', layout)
# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'test':	# if user closes window or clicks cancel
        break
    print('You entered ', values[0])

window.close()
