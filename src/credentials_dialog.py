# -*- coding: utf-8 -*-
import os

from qgis.PyQt import uic
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QDialog

CREDENTIALS_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'credentials_dialog_base.ui')) # Load the .ui file

class CredentialsDialog(QDialog, CREDENTIALS_CLASS):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        basepath = os.path.dirname(os.path.realpath(__file__))
        icon_path = os.path.join(basepath, 'icon.png')
        self.setWindowIcon(QIcon(icon_path))
        self.setupUi(self)
        self.setWindowTitle('Configurar credenciales')
        self.buttonBox.accepted.connect(self.accept)
        
    def accept(self):
        s = QSettings()
        s.setValue('pdd-qgis-plugin/access_key_id', self.accessKeyId.text())
        s.setValue('pdd-qgis-plugin/secret_access_key', self.secretAccessKey.text())
        self.close()
