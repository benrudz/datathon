#Module Configuration Editor Utility

import yaml
import sys
import os
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtPrintSupport import *
from pathlib import *

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "py_lib"))
from amm_module_config import *
from amm_data_dict import *
from fc_tools import *

#Class that handles updates of all GUI lists with Add/Delete Buttons
class ListEditor(QWidget):
    def __init__(self, addButton, delButton, listWidget, getListFcn, addItemFcn,
                 delItemFcn, itemType, fileFilter):
        QWidget.__init__(self)
        addButton.clicked.connect(self.addButtonClicked)
        delButton.clicked.connect(self.delButtonClicked)
        self.getListFcn = getListFcn
        self.listWidget = listWidget
        self.itemType = itemType
        self.addItemFcn = addItemFcn
        self.delItemFcn = delItemFcn
        self.fileFilter = fileFilter

    def updateList(self):
        self.listWidget.clear()
        if len(self.getListFcn()) > 0:
            for item in self.getListFcn():
                self.listWidget.addItem(item)
        return

    def addButtonClicked(self):
        newItem = ""

        if self.itemType == "directory":
            newItem = QFileDialog.getExistingDirectory(self, "Select Data Directory to Open")

        if self.itemType == "file":
            newItem = QFileDialog.getOpenFileName(self, "Select File To Add", ".", self.fileFilter)
            newItem = newItem[0]
        if newItem == "":
            return

        self.addItemFcn(newItem)
        self.updateList()
        return

    def delButtonClicked(self):

        selItem = self.listWidget.currentItem()

        if isinstance(selItem, type(None)):
            return

        self.delItemFcn(selItem.text())
        self.updateList()
        return

#Interface Editor Class
class InterfaceEditor(QWidget):
    def __init__(self, tableWidget, addButton, delButton, config, dd):
        QWidget.__init__(self)
        self.tableWidget = tableWidget
        self.config = config
        self.dd = dd

        addButton.clicked.connect(self.addButtonClicked)
        delButton.clicked.connect(self.delButtonClicked)
        self.tableWidget.cellChanged.connect(self.ioTableCellChanged)

        self.updateIoTable()
        return

    def updateIoTable(self):
        self.tableWidget.clear()
        self.tableWidget.cellChanged.disconnect()
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(['Direction', 'Name', 'Type'])
        self.tableWidget.setColumnWidth(0, 150)
        self.tableWidget.setColumnWidth(1, 200)
        self.tableWidget.setColumnWidth(2, 150)

        msgNames = self.config.getInterfaceList()
        self.tableWidget.setRowCount(len(msgNames))
        self.prevMsgNames = [""] * len(msgNames)

        validMsgs = self.dd.getMessageNames()
        validMsgsModel = QStringListModel()
        validMsgsModel.setStringList(validMsgs)
        validMsgsCompleter = QCompleter()
        validMsgsCompleter.setModel(validMsgsModel)

        pos = 0
        for m in msgNames:
            self.prevMsgNames[pos] = m
            msgDirection = self.config.getInterfaceDirection(m)
            msgIoType = self.config.getInterfaceType(m)

            msgDirCbox = QComboBox()
            msgDirCbox.setProperty("row", pos)
            msgDirCbox.addItems(self.config.getInterfaceDirections())
            self.tableWidget.setCellWidget(pos, 0, msgDirCbox)

            msgDirIdx = msgDirCbox.findText(msgDirection)
            if (msgDirIdx == -1):
                mb = QMessageBox()
                mb.setIcon(QMessageBox.Critical)
                mb.setWindowTitle("Error")
                mb.setWindowTitle("Invalid Message Direction")
                mb.setInformativeText("Invalid Message Direction [" + msgDirection +
                                      "] for message [" + m + "], resetting ...")
                mb.exec()
                msgDirIdx = 0

            msgDirCbox.setCurrentIndex(msgDirIdx)
            msgDirCbox.currentIndexChanged.connect(self.msgTableDirChanged)

            msgNameLineEdit = QLineEdit()
            msgNameLineEdit.setText(m)
            msgNameLineEdit.setProperty("row", pos)
            msgNameLineEdit.setCompleter(validMsgsCompleter)
            msgNameLineEdit.editingFinished.connect(self.msgNameEditFinished)
            self.tableWidget.setCellWidget(pos, 1, msgNameLineEdit)

            ioTypeCbox = QComboBox()
            ioTypeCbox.setProperty("row", pos)
            ioTypeCbox.addItems(self.config.getInterfaceTypes())
            self.tableWidget.setCellWidget(pos, 2, ioTypeCbox)

            ioTypeIdx = ioTypeCbox.findText(msgIoType)
            if (ioTypeIdx == -1):
                mb = QMessageBox()
                mb.setIcon(QMessageBox.Critical)
                mb.setWindowTitle("Error")
                mb.setWindowTitle("Invalid Message Interface Type")
                mb.setInformativeText("Invalid Message Interface Type [" + msgIoType +
                                      "] for message [" + m + "], resetting ...")
                mb.exec()
                ioTypeIdx = 0

            ioTypeCbox.setCurrentIndex(ioTypeIdx)
            ioTypeCbox.currentIndexChanged.connect(self.msgTableIoTypeChanged)

            pos = pos + 1

        self.tableWidget.cellChanged.connect(self.ioTableCellChanged)
        return

    def addButtonClicked(self):
        newInterfaceNum = 0
        newInterfaceName = "new_message_"

        while not self.config.addInterface(newInterfaceName + str(newInterfaceNum)):
            newInterfaceNum = newInterfaceNum + 1

        self.updateIoTable()
        return

    def delButtonClicked(self):
        currentRow = self.tableWidget.currentRow()
        if (currentRow < 0):
            return

        msgName = self.tableWidget.cellWidget(currentRow, 1).text()
        self.config.delInterface(msgName)
        self.updateIoTable()
        return

    def ioTableCellChanged(self, row, col):
        self.updateParameterTable()
        return

    def msgTableDirChanged(self):
        row = self.sender().property("row")
        msgName = self.tableWidget.cellWidget(row, 1).text()
        newDir = self.sender().currentText()
        self.config.setInterfaceDirection(msgName, newDir)
        self.updateIoTable()


        if newDir == 'input' or newDir == 'output':
            validMsgs = self.dd.getMessageNames()
        else:
            validMsgs = self.dd.getServiceNames()

            validMsgsModel = QStringListModel()
            validMsgsModel.setStringList(validMsgs)
            validMsgsCompleter = QCompleter()
            validMsgsCompleter.setModel(validMsgsModel)
            self.tableWidget.cellWidget(row, 1).setCompleter(validMsgsCompleter)
        return

    def msgTableIoTypeChanged(self):
        row = self.sender().property("row")
        msgName = self.tableWidget.cellWidget(row, 1).text()
        newType = self.sender().currentText()
        self.config.setInterfaceType(msgName, newType)
        self.updateIoTable()
        return

    def msgNameEditFinished(self):
        row = self.sender().property("row")
        newName = self.sender().text()
        ioType = self.tableWidget.cellWidget(row, 0).currentText()
        prevName = self.prevMsgNames[row]

        if prevName == newName:
            return

        if ioType == 'input' or ioType == 'output':
            validIo = self.dd.getMessageNames()
        else:
            validIo = self.dd.getServiceNames()

        if newName not in validIo:
            self.sender().setText(prevName)
            return

        self.config.renameInterface(prevName, newName)
        self.updateIoTable()
        return
#FlowChart editor Class
class flowchart(QWidget):
	def __init__(self,QGraphicsView, saveAs, config, dd):
		QWidget.__init__(self)
		self.graphicsView=QGraphicsView
		self.scene= QGraphicsScene()
		self.graphicsView.setScene(self.scene)
		window_width  = self.width()
		window_height = self.height()
		self.config = config
		self.dd = dd
		saveAs.clicked.connect(self.saveAsButtonClicked)
#module box, the main focal points, displaying parameters
	def updateFlowChart(self):
		mod = TextBox("module",QPointF(250,250))
		msgNames = self.config.getInterfaceList()
		pos = 0
		for m in msgNames:
			msgDirection = self.config.getInterfaceDirection(m)
			msgIoType = self.config.getInterfaceType(m)



			if msgDirection == 'input':
				msgBox = TextBox(m,QPointF(50,250))
				arrow = Arrow(msgBox,mod)
			elif msgDirection == 'output':
				msgBox = TextBox(m,QPointF(450,250))
				arrow = Arrow(mod,msgBox)
			else:
				"whoops"
			msgBox.addArrow(arrow)
			mod.addArrow(arrow)
			self.scene.addItem(arrow)
			self.scene.addItem(msgBox)
			self.scene.addItem(mod)
		mod.setZValue(1)

		return
	def saveAsButtonClicked(self):
		fileName="/test.pdf"
		printer = QPrinter(QPrinter.HighResolution)
		printer.setPageSize(QPrinter.A4)
		printer.setOrientation(QPrinter.Portrait)
		printer.setOutputFormat(QPrinter.PdfFormat)
		printer.setOutputFileName(fileName)
		self.scene.render(QPainter(printer))

		return
#Parameter Editor Class
class ParameterEditor(QWidget):
    def __init__(self, tableWidget, addButton, delButton, config):
        QWidget.__init__(self)
        self.tableWidget = tableWidget
        self.config = config

        addButton.clicked.connect(self.addButtonClicked)
        delButton.clicked.connect(self.delButtonClicked)
        self.tableWidget.cellChanged.connect(self.paramTableCellChanged)

        self.updateParameterTable()
        return
    def updateParameterTable(self):
        self.tableWidget.clear()
        self.tableWidget.cellChanged.disconnect()
        self.tableWidget.setColumnCount(6)
        self.tableWidget.setHorizontalHeaderLabels(['Name', 'Description', 'Type', 'Units',
                                                    'Def Val', 'Adjustable'])
        self.tableWidget.setColumnWidth(0, 150)
        self.tableWidget.setColumnWidth(1, 300)
        self.tableWidget.setColumnWidth(2, 100)
        self.tableWidget.setColumnWidth(3, 100)
        self.tableWidget.setColumnWidth(4, 100)
        self.tableWidget.setColumnWidth(5, 100)

        parameterNames = self.config.getParameterList()

        self.tableWidget.setRowCount(len(parameterNames))
        self.prevParameterNames = [""] * len(parameterNames)

        pos = 0
        for p in parameterNames:
            self.prevParameterNames[pos] = p
            parameterDescr = self.config.getParameterDescr(p)
            parameterType = self.config.getParameterType(p)
            parameterUnits = self.config.getParameterUnits(p)
            parameterDefVal = self.config.getParameterDefVal(p)
            parameterAdj = self.config.getParameterAdj(p)

            self.tableWidget.setItem(pos, 0, QTableWidgetItem(p))
            self.tableWidget.setItem(pos, 1, QTableWidgetItem(parameterDescr))

            paramTypeCbox = QComboBox()
            paramTypeCbox.setProperty("row", pos)
            paramTypeCbox.addItems(self.config.getParameterDataTypes())
            self.tableWidget.setCellWidget(pos, 2, paramTypeCbox)

            paramTypeIdx = paramTypeCbox.findText(parameterType)
            if (paramTypeIdx == -1):
                mb = QMessageBox()
                mb.setIcon(QMessageBox.Critical)
                mb.setWindowTitle("Error")
                mb.setWindowTitle("Invalid Paramter Data Type")
                mb.setInformativeText("Invalid Data Type [" + parameterType +
                                      "] for parameter [" + p + "], resetting ...")
                mb.exec()
                paramTypeIdx = 0

            paramTypeCbox.setCurrentIndex(paramTypeIdx)
            paramTypeCbox.currentIndexChanged.connect(self.paramTableTypeChanged)

            self.tableWidget.setItem(pos, 3, QTableWidgetItem(parameterUnits))
            self.tableWidget.setItem(pos, 4, QTableWidgetItem(parameterDefVal))

            cBox = QCheckBox()
            cBox.setProperty("row", pos)
            if parameterAdj == "true":
                cBox.setCheckState(Qt.Checked)
            else:
                cBox.setCheckState(Qt.Unchecked)

            self.tableWidget.setCellWidget(pos, 5, cBox)
            cBox.stateChanged.connect(self.paramTableAdjChanged)

            pos = pos + 1

        self.tableWidget.cellChanged.connect(self.paramTableCellChanged)

        return

    def addButtonClicked(self):
        newParamNum = 0
        newParamName = "new_param_"

        while not self.config.addParameter(newParamName + str(newParamNum)):
            newParamNum = newParamNum + 1

        self.updateParameterTable()
        return

    def delButtonClicked(self):
        currentRow = self.tableWidget.currentRow()
        if (currentRow < 0):
            return

        paramName = self.tableWidget.item(currentRow, 0).text()
        self.config.delParameter(paramName)
        self.updateParameterTable()
        return

    def paramTableCellChanged(self, row, col):
        if col == 0:
            newName = self.tableWidget.item(row, col).text()
            self.config.renameParameter(self.prevParameterNames[row], newName)

        if col == 1:
            paramName = self.tableWidget.item(row, 0).text()
            newDescr = self.tableWidget.item(row, col).text()
            self.config.setParameterDescr(paramName, newDescr)

        if col == 3:
            paramName = self.tableWidget.item(row, 0).text()
            newUnits = self.tableWidget.item(row, col).text()
            self.config.setParameterUnits(paramName, newUnits)

        if col == 4:
            paramName = self.tableWidget.item(row, 0).text()
            newDefVal = self.tableWidget.item(row, col).text()
            self.config.setParameterDefVal(paramName, newDefVal)

        self.updateParameterTable()
        return

    def paramTableTypeChanged(self):
        row = self.sender().property("row")
        paramName = self.tableWidget.item(row, 0).text()
        newType = self.sender().currentText()
        self.config.setParameterType(paramName, newType)
        self.updateParameterTable()
        return

    def paramTableAdjChanged(self):
        row = self.sender().property("row")
        paramName = self.tableWidget.item(row, 0).text()
        newAdj = self.sender().checkState()

        if newAdj == Qt.Checked:
            self.config.setParameterAdj(paramName, "true")
        else:
            self.config.setParameterAdj(paramName, "false")

        self.updateParameterTable()
        return

#MainWindow GUI Class, handles the top level widgets
class MainWindow(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = uic.loadUi(os.path.join(os.path.dirname(__file__), "module_editor.ui"), self)
        self.ui.show()

        self.ui.actionOpen.triggered.connect(self.openMenuSelected)
        self.ui.actionSave.triggered.connect(self.saveMenuSelected)
        self.ui.actionQuit.triggered.connect(self.exitMenuSelected)
        self.ui.dataDictChangeButton.pressed.connect(self.changeDataDictPath)
        self.ui.reloadDict.pressed.connect(self.loadDataDict)
        self.config = AmmModuleConfig()
        self.dataDict = AmmDataDict()
        self.configFile = ""
        self.dataDictPath = ""

        self.ui.descrEdit.textEdited.connect(self.descriptionChanged)

        self.headerPathEditor = ListEditor(self.ui.addHeaderButton,
                                           self.ui.delHeaderButton,
                                           self.ui.headerPathList,
                                           self.config.getHeaderPath,
                                           self.config.addHeaderPath,
                                           self.config.delHeaderPath,
                                           "directory", "All Files (*.*)")

        self.cSourceEditor =    ListEditor(self.ui.addCSrcButton,
                                           self.ui.delCSrcButton,
                                           self.ui.cSrcList,
                                           self.config.getCSources,
                                           self.config.addCSources,
                                           self.config.delCSources,
                                           "file", "C Sources (*.c)")

        self.cxxSourceEditor =  ListEditor(self.ui.addCxxSrcButton,
                                           self.ui.delCxxSrcButton,
                                           self.ui.cxxSrcList,
                                           self.config.getCxxSources,
                                           self.config.addCxxSources,
                                           self.config.delCxxSources,
                                           "file", "CPP Sources (*.cpp)")

        self.libEditor =        ListEditor(self.ui.addLibButton,
                                           self.ui.delLibButton,
                                           self.ui.libList,
                                           self.config.getExtLibs,
                                           self.config.addExtLibs,
                                           self.config.delExtLibs,
                                           "file", "Libraries Sources (*.a, *.so)")

        self.libPathEditor =    ListEditor(self.ui.addLibPathButton,
                                           self.ui.delLibPathButton,
                                           self.ui.libPathList,
                                           self.config.getExtLibPath,
                                           self.config.addExtLibPath,
                                           self.config.delExtLibPath,
                                           "directory", "All Files (*.*)")

        self.parameterEditor =  ParameterEditor(self.ui.paramTable,
                                                self.ui.addParamButton,
                                                self.ui.delParamButton,
                                                self.config)

        self.interfaceEditor =  InterfaceEditor(self.ui.interfaceTable,
                                                self.ui.addInterfaceButton,
                                                self.ui.delInterfaceButton,
                                                self.config,
                                                self.dataDict)

        self.flowchart      =         flowchart(self.ui.graphicsView,
                                                self.ui.saveAs,
                                                self.config,
                                                self.dataDict)
    ############################################################################
    # Signal Handlers
    ############################################################################

    #Catch close event and make sure that we can exit
    def closeEvent(self, event):
        self.exitMenuSelected()
        event.ignore()

    #Signal handler for Quit menu
    def exitMenuSelected(self):
        unsavedChanges = self.config.getConfigChanged()

        if unsavedChanges:
            ans = QMessageBox.question(self, "WARNING", "Unsaved Changes Exist - Confirm Exit",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if ans == QMessageBox.Yes:
                sys.exit()
            return

        sys.exit()

    #Signal handler for Open menu
    def openMenuSelected(self):
        self.configFile = QFileDialog.getOpenFileName(self, "Select Module Confiuration to Open", ".", "yaml(*.yaml)")
        self.configFile = self.configFile[0]

        if self.configFile == "":
            return

        if self.config.load(self.configFile):
            self.ui.statusbar.showMessage("Module Configuration Loaded", 5000)
            self.dataDictPath = os.path.join(Path(self.configFile).parent.parent, "amm_data")
            self.loadDataDict()

            self.headerPathEditor.updateList()
            self.cSourceEditor.updateList()
            self.ui.descrEdit.setText(self.config.getDescription())
            self.parameterEditor.updateParameterTable()
            self.interfaceEditor.updateIoTable()
            self.flowchart.updateFlowChart()
        else:
            self.ui.statusbar.showMessage("Module Configuration Load Failed - " + self.config.getErrorString(), 0)
        return

    #Signal handler for Save menu
    def saveMenuSelected(self):
        try:
            self.config.save(self.configFile)
        except:
            self.ui.statusbar.showMessage("Save Failed !", 0)

        self.ui.statusbar.showMessage("Save Completed", 0)
        return

    #Singnal to handle description changes
    def descriptionChanged(self):
        self.config.setDescription(self.ui.descrEdit.text())
        return

    #Signal to handle button for data dictionary path changes
    def changeDataDictPath(self):
        self.dataDir = QFileDialog.getExistingDirectory(self,
                    "Select Data Directory to Open")

        if self.dataDir == "":
            return

        self.dataDictPath = self.dataDir
        self.loadDataDict()

        return

    #Handle loading of data dictionaries and error reporting
    def loadDataDict(self):
        self.ui.dataDictPathEdit.setText(self.dataDictPath)

        if self.dataDict.load(self.dataDictPath):
            prevMsg = self.ui.statusbar.currentMessage()
            if len(prevMsg) > 0:
                newMsg = prevMsg + " and Data Dictionary Loaded"
            else:
                newMsg = "Data Dictionary Loaded"

            self.ui.statusbar.showMessage(newMsg, 5000)
            self.interfaceEditor.updateIoTable()
        else:
            mb = QMessageBox()
            mb.setIcon(QMessageBox.Critical)
            mb.setWindowTitle("Error")
            mb.setWindowTitle("Unable To Load Data Dictionary")
            mb.setInformativeText("Failed to load data dictionary from [" +
                                  self.dataDictPath + "], this will result in" +
                                  "inability to edit interfaces")
            mb.exec()

        return

############################################################################
# Main Application
############################################################################
app = QApplication(sys.argv)
mw = MainWindow()

app.aboutToQuit.connect(mw.exitMenuSelected)
sys.exit(app.exec())
