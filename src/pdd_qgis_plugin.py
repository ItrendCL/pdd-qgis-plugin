# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PDDQgisPlugin
                                 A QGIS plugin
 Descarga de datos
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2022-11-10
        git sha              : $Format:%H$
        copyright            : (C) 2022 by Sebastián Castro
        email                : sebastian.castro@itrend.cl
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QTreeWidgetItem, QTreeWidgetItemIterator, \
                                QHeaderView, QFileDialog, QMessageBox

# Initialize Qt resources from file resources.py
# from .resources import *
# Import the code for the dialog
from .pdd_qgis_plugin_dialog import PDDQgisPluginDialog
from .table_dialog import TableDialog
from .QCustom import QCustomTableModel
from .credentials_dialog import CredentialsDialog

import os
import json
import urllib
import zipfile
import requests
import pandas as pd
from .pddUtils import normalizeString
from qgis.core import QgsMessageLog, QgsVectorLayer, QgsRasterLayer, QgsProject

class PDDQgisPlugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'PDDQgisPlugin_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Instituto para la Resiliencia ante Desastres')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None
        
        self.table = None
        self.categories = None
        self.mapping = {}
        self.selectedDatasets = []
        self.itrendApi = 'https://6olpgdxhp8.execute-api.us-east-1.amazonaws.com/prod/itrend-developer-tools'
        self.headers = {
            'access_key_id': QSettings().value('pdd-qgis-plugin/access_key_id'),
            'secret_access_key': QSettings().value('pdd-qgis-plugin/secret_access_key')
        }
        self.baseFolder = QSettings().value('pdd-qgis-plugin/baseFolder')
        self.params = None
        self.forceDownload = False

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('PDDQgisPlugin', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        basepath = os.path.dirname(os.path.realpath(__file__))
        icon_path = os.path.join(basepath, 'icon.png')
        self.add_action(
            icon_path,
            text=self.tr(u'Plataforma de Datos de Itrend'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Plataforma de Datos de Itrend'),
                action)
            self.iface.removeToolBarIcon(action)
            
    def areCredentialsValid(self):
        access_key_id = self.headers.get('access_key_id')
        secret_access_key = self.headers.get('secret_access_key')
        
        if access_key_id is None or secret_access_key is None:
            return False
        else:
            response = requests.post(self.itrendApi, json={'headers': self.headers})
            response = json.loads(response.text)
            if response.get('errorMessage') is None:
                return True
            else:
                return False
    
    def isBaseFolderValid(self):
        if self.baseFolder is None:
            return False
        else:
            return os.path.exists(self.baseFolder)
        
    def setBaseFolder(self):
        if self.isBaseFolderValid():
            folder = QFileDialog.getExistingDirectory(None, 'Seleccione una carpeta', self.baseFolder)
        else:
            folder = QFileDialog.getExistingDirectory(None, 'Seleccione una carpeta')
        
        if folder != '':
            self.baseFolder = folder
            s = QSettings()
            s.setValue('pdd-qgis-plugin/baseFolder', self.baseFolder)
            return True
        else:
            return False
        
    def setCredentials(self):
        credentialsDialog = CredentialsDialog()
        credentialsDialog.exec_()
        self.headers = {
            'access_key_id': QSettings().value('pdd-qgis-plugin/access_key_id'),
            'secret_access_key': QSettings().value('pdd-qgis-plugin/secret_access_key')
        }
        return self.areCredentialsValid()

    def getCategories(self):
        response = requests.get('https://6olpgdxhp8.execute-api.us-east-1.amazonaws.com/prod/categories?withDatasets=true')
        categories = json.loads(response.text)

        for category in categories:
            category['num_datasets'] = 0
            for subcategory in category.get('tree'):
                subcategory['num_datasets'] = 0
                for listname in subcategory.get('subtree'):
                    n = int(listname['num_datasets'])
                    if n > 0:
                        to_drop = []
                        for i, dataset in enumerate(listname.get('datasets')):
                            if not (dataset.get('active') and (dataset.get('isGeoreferential') or dataset.get('isMapCollection'))):
                                to_drop.append(i)
                            else:
                                
                                isCollection = bool(dataset.get('isMapCollection'))
                                collectionId = dataset.get('collectionID')
                                delimiter = dataset.get('delimiter')
                                if delimiter == 'pipe':
                                    delimiter = '|'
                                    
                                if isCollection:
                                    mapType = dataset.get('collectionMapType')
                                else:
                                    mapType = dataset.get('mapType')
                                
                                if mapType == 'raster':
                                    fmt = 'tif'
                                else:
                                    fmt = 'shp'
                                    
                                self.mapping[dataset['name']] = {
                                    'dataset_id': dataset.get('key'),
                                    'fmt': fmt,
                                    'isMapCollection': isCollection,
                                    'collectionId': collectionId,
                                    'delimiter': delimiter
                                }
                        
                        for i in reversed(to_drop):
                            listname['datasets'].pop(i)
                        
                        listname['num_datasets'] = len(listname['datasets'])
                    else:
                        listname['num_datasets'] = 0
                        listname['datasets'] = []
                    subcategory['num_datasets'] += listname['num_datasets']
                category['num_datasets'] += subcategory['num_datasets']
        return categories
    
    def download(self, params):
        dataset_id = params.get('dataset_id')
        fmt = params.get('fmt')
        element_id = params.get('element_id')
        
        response = requests.get(self.itrendApi, params=params, headers=self.headers)
        body = response.json()
        if response.status_code == 200:
            url = body.get('url')
            folder = os.path.join(self.baseFolder, dataset_id)
            
            if not os.path.exists(folder):
                os.mkdir(folder)

            if element_id is not None:
                folder = os.path.join(folder, element_id)
                if not os.path.exists(folder):
                    os.mkdir(folder)
            
            if element_id is None:
                filename = os.path.join(folder, dataset_id + '.' + fmt)
                zipname = os.path.join(folder, dataset_id + '.zip')
            else:
                filename = os.path.join(folder, element_id + '.' + fmt)
                zipname = os.path.join(folder, element_id + '.zip')
            
            if fmt == 'shp':
                _ = urllib.request.urlretrieve(url, zipname)
                
                zf = zipfile.ZipFile(zipname)
                filenames = zf.namelist()
                zf.extractall(folder)
                zf.close()
                os.remove(zipname)
                
                for filename in filenames:
                    if filename.endswith('.shp'):
                        break
                filename = os.path.join(folder, filename)
            else:
                _ = urllib.request.urlretrieve(url, filename)
            
            return filename
    
    def downloadCollectionTable(self, dataset_id, dataset_name):
        params = {
            'dataset_id': dataset_id,
            'fmt': 'csv'
        }
        
        filename = os.path.join(self.baseFolder, dataset_id, dataset_id + '.csv')
        if os.path.exists(filename) and not self.forceDownload:
            return filename
        
        return self.download(params)
    
    def downloadDataset(self, dataset_id, dataset_name, fmt, element_id = None):
        params = {
            'dataset_id': dataset_id,
            'fmt': fmt,
            'element_id': element_id
        }
        
        if element_id is None:
            filename = os.path.join(self.baseFolder, dataset_id, dataset_id + '.' + fmt)
        else:
            filename = os.path.join(self.baseFolder, dataset_id, element_id, element_id + '.' + fmt)

        if os.path.exists(filename) and not self.forceDownload:
            return filename
        
        return self.download(params)
            
    def loadDataset(self, filename, layer_name, fmt, group_name = None):
        root = QgsProject.instance().layerTreeRoot()
        if group_name is not None:
            group = root.findGroup(group_name)
            if group is None:
                group = root.insertGroup(0, group_name)
        
        if fmt == 'shp':
            layer = QgsVectorLayer(filename, layer_name, 'ogr')
        else:
            layer = QgsRasterLayer(filename, layer_name)
            
        if not layer.isValid():
            QgsMessageLog.logMessage('Layer failed to load!', 'Mensajes')
        else:
            QgsProject.instance().addMapLayer(layer, False)
            if group_name is None:
                root.insertLayer(0, layer)
            else:
                group.insertLayer(0, layer)
        
    def updateSelectedDatasets(self):
        self.selectedDatasets = []
        it = QTreeWidgetItemIterator(self.dlg.treeWidget, QTreeWidgetItemIterator.NoChildren)
        while it.value():
            treeWidgetItem = it.value()
            checkState = treeWidgetItem.checkState(0)
            if checkState == Qt.Checked:
                datasetName = treeWidgetItem.text(0)
                if datasetName not in self.selectedDatasets:
                    self.selectedDatasets.append(datasetName)
            it += 1
    
    def accept(self):
        
        if not self.areCredentialsValid():
            valid = self.setCredentials()
            if not valid:
                msg = QMessageBox()
                msg.setWindowTitle('Error')
                msg.setText('Debe ingresar credenciales válidas')
                msg.setIcon(QMessageBox.Critical)
                result = msg.exec_()
                return None
        
        if not self.isBaseFolderValid():
            valid = self.setBaseFolder()
            if not valid:
                msg = QMessageBox()
                msg.setWindowTitle('Error')
                msg.setText('Debe configurar una carpeta para descargar los archivos')
                msg.setIcon(QMessageBox.Critical)
                result = msg.exec_()
                return None
        
        # Update selected datasets
        self.updateSelectedDatasets()
        if self.dlg.checkBox.checkState() == Qt.Checked:
            self.forceDownload = True
        
        # Iterate through datasets
        for dataset_name in reversed(self.selectedDatasets):
            dataset_id = self.mapping[dataset_name].get('dataset_id')
            fmt = self.mapping[dataset_name].get('fmt')
            isCollection = self.mapping[dataset_name].get('isMapCollection')
            
            if isCollection:
                # Download table
                filename = self.downloadCollectionTable(dataset_id, dataset_name)
                delimiter = self.mapping[dataset_name]['delimiter']
                collectionId = self.mapping[dataset_name]['collectionId']
                df = pd.read_csv(filename, delimiter=delimiter, dtype={collectionId: str})
                
                m = len(df)
                checked = [False for _ in range(m)]
                df.insert(0, '', checked)
                
                tableDialog = TableDialog(dataset_name)
                header = tableDialog.tableView.horizontalHeader()
                model = QCustomTableModel(df)
                tableDialog.tableView.setModel(model)
                tableDialog.tableView.setSortingEnabled(True)
                header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
                tableDialog.show()
                
                result = tableDialog.exec_()
                if result:
                    selectedElements = tableDialog.tableView.model()._data[tableDialog.tableView.model()._data.iloc[:,0] == True][collectionId].tolist()
                    for element_id in reversed(selectedElements):
                        filename = self.downloadDataset(dataset_id, dataset_name, fmt, normalizeString(element_id))
                        self.loadDataset(filename, element_id, fmt, dataset_name)
            else:
                # Download selected dataset and get location
                filename = self.downloadDataset(dataset_id, dataset_name, fmt)
                self.loadDataset(filename, dataset_name, fmt)
    
    def cancel(self):
        return None
    
    def selectAll(self):
        it = QTreeWidgetItemIterator(self.dlg.treeWidget, QTreeWidgetItemIterator.NoChildren)
        while it.value():
            treeWidgetItem = it.value()
            treeWidgetItem.setCheckState(0, Qt.Checked)
            it += 1
            
    def unselectAll(self):
        it = QTreeWidgetItemIterator(self.dlg.treeWidget, QTreeWidgetItemIterator.NoChildren)
        while it.value():
            treeWidgetItem = it.value()
            treeWidgetItem.setCheckState(0, Qt.Unchecked)
            it += 1
    
    def anyWordInSentence(self, listOfWords, sentence):
        for word in listOfWords:
            if word in sentence:
                return True
        
        return False
        
    
    def searchContent(self):
        self.dlg.treeWidget.collapseAll()
        text = self.dlg.lineEdit.text().strip()
        words = []
        
        for word in text.split():
            normalizedWord = word.strip().lower()
            if len(normalizedWord) > 0:
                words.append(normalizedWord)
        
        nCategories = len(self.categories)
        for i in range(nCategories):
            category = self.dlg.treeWidget.topLevelItem(i)
            normalizedCategoryName = category.text(0).strip().lower()
            if self.anyWordInSentence(words, normalizedCategoryName):
                category.setExpanded(True)
                continue
            
            nSubCategories = category.childCount()
            for j in range(nSubCategories):
                subcategory = category.child(j)
                normalizedSubCategoryName = subcategory.text(0).strip().lower()
                if self.anyWordInSentence(words, normalizedSubCategoryName):
                    category.setExpanded(True)
                    subcategory.setExpanded(True)
                    continue
                
                nLists = subcategory.childCount()
                for k in range(nLists):
                    listname = subcategory.child(k)
                    normalizedListName = listname.text(0).strip().lower()
                    if self.anyWordInSentence(words, normalizedListName):
                        category.setExpanded(True)
                        subcategory.setExpanded(True)
                        listname.setExpanded(True)
                        continue
                    
                    nDatasets = listname.childCount()
                    for l in range(nDatasets):
                        dataset = listname.child(l)
                        normalizedDatasetName = dataset.text(0).strip().lower()
                        if self.anyWordInSentence(words, normalizedDatasetName):
                            category.setExpanded(True)
                            subcategory.setExpanded(True)
                            listname.setExpanded(True)
                            break

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = PDDQgisPluginDialog()
            if self.categories is None:
                self.categories = self.getCategories()
            
                self.dlg.treeWidget.setColumnCount(1)
                self.dlg.treeWidget.setHeaderLabel('Categorías')
                for category in self.categories:
                    if category['num_datasets'] == 0:
                        continue
                    l1 = QTreeWidgetItem(self.dlg.treeWidget)
                    l1.setText(0, category['name'])
                    l1.setFlags(l1.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
                    for subcategory in category['tree']:
                        if subcategory['num_datasets'] == 0:
                            continue
                        l2 = QTreeWidgetItem()
                        l2.setFlags(l1.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
                        l2.setText(0, subcategory['name'])
                        l2.setCheckState(0, Qt.Unchecked)
                        l1.addChild(l2)
                        for listname in subcategory['subtree']:
                            if listname['num_datasets'] == 0:
                                continue
                            l3 = QTreeWidgetItem()
                            l3.setFlags(l2.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
                            l3.setText(0, listname['name'])
                            l3.setCheckState(0, Qt.Unchecked)
                            l2.addChild(l3)
                            for dataset in listname['datasets']:
                                l4 = QTreeWidgetItem()
                                l4.setFlags(l3.flags() | Qt.ItemIsUserCheckable)
                                l4.setText(0, dataset['name'])
                                l4.setCheckState(0, Qt.Unchecked)
                                l3.addChild(l4)
            
            self.dlg.treeWidget.sortItems(0, Qt.AscendingOrder)
            
            # Connect to function
            self.dlg.button_box.accepted.connect(self.accept)
            self.dlg.button_box.rejected.connect(self.cancel)
            self.dlg.selectAllButton.clicked.connect(self.selectAll)
            self.dlg.unselectAllButton.clicked.connect(self.unselectAll)
            self.dlg.folderButton.clicked.connect(self.setBaseFolder)
            self.dlg.credentialsButton.clicked.connect(self.setCredentials)
            self.dlg.searchButton.clicked.connect(self.searchContent)
        else:
            self.unselectAll()
            self.dlg.treeWidget.collapseAll()
            self.dlg.checkBox.setCheckState(Qt.Unchecked)
            self.dlg.lineEdit.clear()
        
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass