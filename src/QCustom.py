# -*- coding: utf-8 -*-
"""
Created on Tue Nov 15 09:59:35 2022

@author: sebacastroh
"""
from qgis.PyQt.QtCore import Qt, QAbstractTableModel

class QCustomTableModel(QAbstractTableModel):
    def __init__(self, df, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._data = df

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._data.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            if index.column() == 0:
                return ''
            else:
                return str(self._data.iat[index.row(), index.column()])
            
        if role == Qt.CheckStateRole and index.column() == 0:
            checked = self._data.iat[index.row(), 0]
            return Qt.Checked if checked else Qt.Unchecked
        
        if role == Qt.TextAlignmentRole:
            if index.column() == 0:
                return Qt.AlignHCenter
            else:
                if self._data.dtypes[index.column()].name in ['float64', 'int64']:
                    return Qt.AlignRight
                else:
                    return Qt.AlignLeft
        
    def setData(self, index, value, role):
        if role == Qt.CheckStateRole:
            checked = value == Qt.Checked
            self._data.iat[index.row(), 0] = checked
            return True
    
    def headerData(self, section, orientation, role):
        """Override method from QAbstractTableModel
        Return dataframe index as vertical header data and columns as horizontal header data.
        """
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])
            
            if orientation == Qt.Vertical:
                return str(self._data.index[section])
            
        return None
    
    def sort(self, column, order):
        ascending = order == Qt.AscendingOrder
        
        if column == 0:
            pass
        else:
            by = self._data.columns[column]
            self.layoutAboutToBeChanged.emit()
            self._data.sort_values(by, ascending=ascending, inplace=True)
            self.layoutChanged.emit()
    
    def flags(self, index):
        if index.column() == 0:
            return Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
        else:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def changeAll(self):
        self.layoutAboutToBeChanged.emit()
        self._data.iloc[:,0] = not self._data.iloc[:,0].all()
        self.layoutChanged.emit()

    def changeSelection(self, indexList):
        firstIndex = indexList[0]
        checked = self._data.iat[firstIndex.row(), 0]
        indices = [index.row() for index in indexList]
        self.layoutAboutToBeChanged.emit()
        self._data.iloc[indices,0] = not checked
        self.layoutChanged.emit()
