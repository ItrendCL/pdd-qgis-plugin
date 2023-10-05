# -*- coding: utf-8 -*-
import os

from qgis.PyQt import uic
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDialog

TABLE_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'table_dialog_base.ui')) # Load the .ui file

class TableDialog(QDialog, TABLE_CLASS):
    def __init__(self, dataset_name, parent=None):
        QDialog.__init__(self, parent)
        basepath = os.path.dirname(os.path.realpath(__file__))
        icon_path = os.path.join(basepath, 'icon.png')
        self.setWindowIcon(QIcon(icon_path))
        self.setupUi(self)
        self.setWindowTitle(dataset_name)
        
        self.changeAllButton.clicked.connect(self.changeAll)
        self.changeSelectionButton.clicked.connect(self.changeSelection)

    def changeAll(self):
        self.tableView.model().changeAll()
    
    def changeSelection(self):
        selectionModel = self.tableView.selectionModel()
        selectedRows = selectionModel.selectedRows()
        if len(selectedRows) > 0:
            self.tableView.model().changeSelection(selectedRows)
