# -*- coding: utf-8 -*-
import os
import webbrowser

from qgis.PyQt import uic
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDialog

CHECK_VERSION_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'check_version_base.ui')) # Load the .ui file

class CheckVersionDialog(QDialog, CHECK_VERSION_CLASS):
    def __init__(self, parent=None, version=None):
        QDialog.__init__(self, parent)
        basepath = os.path.dirname(os.path.realpath(__file__))
        icon_path = os.path.join(basepath, 'icon.png')

        self.release = 'https://github.com/ItrendCL/pdd-qgis-plugin/releases/tag/v' + str(version)

        self.setWindowIcon(QIcon(icon_path))
        self.setupUi(self)
        self.setWindowTitle('Notificación de actualización')
        self.buttonBox.accepted.connect(self.accept)
        
    def accept(self):
        webbrowser.open(self.release)
        self.close()
