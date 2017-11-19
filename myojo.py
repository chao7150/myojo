import sys
import os
import json
import twitter
import glob
from PIL import Image
import io
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout,
                             QPlainTextEdit, QPushButton, QSizePolicy, QLabel,
                             QMenu)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize

class MyComposer(QPlainTextEdit):
    def __init__(self, attach_callback):
        super().__init__()
        self.callback = attach_callback
        self.attached_images = []

    def dropEvent(self, event):
        event.accept()
        mimeData = event.mimeData()
        print('dropEvent')
        for mimetype in mimeData.formats():
            print('MIMEType:', mimetype)
            print('Data:', mimeData.data(mimetype))
            print()
        print()
        filenames = mimeData.text().replace('\r\n', '').replace('file://', ' ').strip().split()
        print(filenames)
        for filename in filenames:
            if self.callback(filename=filename):
                self.attached_images.append(filename)

    def keyPressEvent(self, e):
        if e.modifiers() == Qt.ControlModifier and (e.key() == Qt.Key_V):
            mimeData = QApplication.clipboard().mimeData()
            if mimeData.hasImage():
                num = str(len(os.listdir('tmp')))
                if ('image/gif' in mimeData.formats()) or ('image/jpeg' in mimeData.formats()) or ('image/png' in mimeData.formats()):
                    if 'image/gif' in mimeData.formats():
                        mimetype = 'image/gif'
                        ext = 'gif'
                    elif 'image/jpeg' in mimeData.formats():
                        mimetype = 'image/jpeg'
                        ext = 'jpeg'
                    elif 'image/png' in mimeData.formats():
                        mimetype = 'image/png'
                        ext = 'png'
                    filename = 'tmp/img' + num + '.' + ext
                    with open(filename, 'wb') as fp:
                        fp.write(mimeData.data(mimetype))
                else:
                    for fmt in mimeData.formats():
                        if fmt[:6] == 'image/':
                            mimetype = fmt
                            break
                    img_pseudofile = io.BytesIO(mimeData.data(mimetype))
                    img_pil = Image.open(img_pseudofile)
                    filename = 'tmp/img' + num + '.png'
                    img_pil.save(filename)
                if self.callback(filename=filename):
                    self.attached_images.append(filename)
            else:
                super().keyPressEvent(e)

        else:
            super().keyPressEvent(e)

class IconLabel(QLabel):
    def __init__(self, parent, filename):
        super().__init__()
        self.parent = parent
        self.filename = filename

    def contextMenuEvent(self, event):
        menu = QMenu()
        delete_action = menu.addAction('delete')
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == delete_action:
            self.parent.compose_textedit.attached_images.remove(self.filename)
            print(self.parent.compose_textedit.attached_images)
            self.parent.lower_hbox.removeWidget(self)
            self.deleteLater()
            self = None
            
class MyWindow(QWidget):
    '''main window'''
    
    def __init__(self):
        super().__init__()
        self.accs = {}
        self.active_accs = []

        self.init_directory()
        self.init_accounts()
        self.init_window()
        self.init_widgets()
        self.show()
        sys.exit(app.exec_())

    def init_directory(self):
        if not os.path.isdir('tmp'):
            os.mkdir('tmp')

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

        self.compose_textedit = MyComposer(self.attach_show)
        middle_hbox.addWidget(self.compose_textedit)
        submit_pushbutton = QPushButton('submit')
        submit_pushbutton.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Ignored)
        submit_pushbutton.clicked.connect(self.submit)
        middle_hbox.addWidget(submit_pushbutton)

        self.lower_hbox.addStretch()

        self.whole_vbox.addLayout(self.upper_hbox)
        self.whole_vbox.addLayout(middle_hbox)
        self.whole_vbox.addLayout(self.lower_hbox)

    def submit(self):
        if not self.active_accs:
            return
        submit_text = self.compose_textedit.toPlainText()
        submit_images = self.compose_textedit.attached_images

        if not submit_images:
            if not submit_text:
                return False
            for key in self.active_accs:
                self.accs[key]['api'].update_status(submit_text)
        else:
            for key in self.active_accs:
                media_ids = [self.accs[key]['api'].media_upload(i).media_id_string for i in submit_images]
                self.accs[key]['api'].update_status(status=submit_text, media_ids=media_ids)

        self.compose_textedit.setPlainText("")
        self.compose_textedit.attached_images = []
        while self.lower_hbox.count() > 1:
            item = self.lower_hbox.takeAt(0)
            if not item:
                continue
            w = item.widget()
            if w:
                w.deleteLater()

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

    def attach_show(self, Qimg=None, filename=None):
        image_cnt = self.lower_hbox.count()
        if image_cnt == 5:
            return False
        attached_label = IconLabel(self, filename)
        if Qimg is not None:
            attached_pixmap = QPixmap.fromImage(Qimg)
        elif filename is not None:
            attached_pixmap = QPixmap(filename)
        attached_pixmap = attached_pixmap.scaled(QSize(60, 60), 1, 1)
        attached_label.setPixmap(attached_pixmap)
        self.lower_hbox.insertWidget(image_cnt - 1, attached_label)
        return True

    def closeEvent(self, event):
        print(os.listdir('tmp'))
        for tmp in os.listdir('tmp'):
            filename = 'tmp/' + tmp
            os.remove(filename)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mywindow = MyWindow()
    
