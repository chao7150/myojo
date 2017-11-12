import sys
import os
import json
import twitter
import glob
import tweepy
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout,
                             QPlainTextEdit, QPushButton, QSizePolicy, QLabel)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize

class MyComposer(QPlainTextEdit):
    def __init__(self, attach_callback):
        super().__init__()
        self.callback = attach_callback

    def dropEvent(self, event):
        event.accept()
        mimeData = event.mimeData()
        print('dropEvent')
        for mimetype in mimeData.formats():
            print('MIMEType:', mimetype)
            print('Data:', mimeData.data(mimetype))
            print()
        print()

    def keyPressEvent(self, e):
        if e.modifiers() == Qt.ControlModifier and (e.key() == Qt.Key_V):
            image = QApplication.clipboard().image()
            self.callback(image)
        else:
            super().keyPressEvent(e)

class MyWindow(QWidget):
    '''main window'''
    
    def __init__(self):
        super().__init__()
        self.accs = {}
        self.active_accs = []

        self.init_accounts()
        self.init_window()
        self.init_widgets()
        self.show()
        sys.exit(app.exec_())

    def init_accounts(self):
        '''load account AT and AS from local and create api object and stream'''
        if not os.path.exists("images"):
            os.mkdir("images")
        if os.path.isfile("auth.json"):
            with open('auth.json', 'r') as f:
                authdic = json.load(f)
            for name, keys in authdic["Twitter"].items():
                api = twitter.connect(keys["ACCESS_TOKEN"], keys["ACCESS_SECRET"])
                self.accs[name] = {'api' : api}
                if not glob.glob("images/" + name + ".*"):
                    self.accs[name]['icon_path'] = twitter.getmyicon(api, name)
                else:
                    self.accs[name]['icon_path'] = glob.glob("images/" + name + ".*")[0]
        else:
            default = {
                "Twitter"  : {},
                "Mastodon" : {}
            }
            with open('auth.json', 'w') as f:
                json.dump(default, f, indent=2)
            self.authdic = {}


    def init_window(self):
        #self.setGeometry(300, 100, 200, 125)
        self.setWindowTitle("myojo")

    def init_widgets(self):
        self.whole_vbox = QVBoxLayout(self)
        self.upper_hbox = QHBoxLayout()
        middle_hbox = QHBoxLayout()
        self.lower_hbox = QHBoxLayout()

        add_account_pushbutton = QPushButton('+')
        add_account_pushbutton.clicked.connect(self.add_acc)
        self.upper_hbox.addWidget(add_account_pushbutton)
        for key, value in self.accs.items():
            acc_pushbutton = QPushButton(QIcon(value['icon_path']), None, None)
            acc_pushbutton.setWhatsThis(key)
            acc_pushbutton.setCheckable(True)
            acc_pushbutton.toggled.connect(self.choose_acc)
            self.upper_hbox.addWidget(acc_pushbutton)

        self.compose_textedit = MyComposer(self.attach)
        middle_hbox.addWidget(self.compose_textedit)
        submit_pushbutton = QPushButton('submit')
        submit_pushbutton.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Ignored)
        submit_pushbutton.clicked.connect(self.submit)
        middle_hbox.addWidget(submit_pushbutton)

        self.whole_vbox.addLayout(self.upper_hbox)
        self.whole_vbox.addLayout(middle_hbox)
        self.whole_vbox.addLayout(self.lower_hbox)

    def submit(self):
        if not self.active_accs:
            return
        submittext = self.compose_textedit.toPlainText()
        if not submittext:
            return
        for key in self.active_accs:
            self.accs[key]['api'].update_status(submittext)
        self.compose_textedit.setPlainText("")

    def add_acc(self):
        api, name = twitter.authentication()
        self.accs[name] = {'api' : api}
        if not glob.glob("images/" + name + ".*"):
            self.accs[name]['icon_path'] = twitter.getmyicon(api, name)
        else:
            self.accs[name]['icon_path'] = glob.glob("images/" + name + ".*")[0]
        acc_pushbutton = QPushButton(QIcon(self.accs[name]['icon_path']), None, None)
        acc_pushbutton.setWhatsThis(name)
        acc_pushbutton.setCheckable(True)
        acc_pushbutton.toggled.connect(self.choose_acc)
        self.upper_hbox.addWidget(acc_pushbutton)

    def choose_acc(self):
        acc = self.sender()
        if acc.isChecked():
            self.active_accs.append(acc.whatsThis())
        else:
            self.active_accs.remove(acc.whatsThis())

    def attach(self, image):
        attached_label = QLabel()
        attached_pixmap = QPixmap.fromImage(image)
        attached_pixmap = attached_pixmap.scaled(QSize(60, 60), 1, 1)
        attached_label.setPixmap(attached_pixmap)
        self.lower_hbox.addWidget(attached_label)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mywindow = MyWindow()
    
