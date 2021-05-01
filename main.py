import sys


from PyQt5 import QtWidgets, uic, QtGui, QtCore
import pandas as pd
import glob
import reduction, data, classification
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog
import menu
import fileObject
import qdarkstyle
import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor
import warnings
import re

warnings.filterwarnings("ignore")

currentTab = 0
currentFile = None






def ExportData():

    data.openWorkBook()

    if not os.path.exists("graphs/"):
        os.mkdir("graphs/")

    for dl in fileObject.DataList:
        for index in range(len(fileObject.DataList[dl].graphWidgets)):
            fileObject.DataList[dl].graphWidgets[list(fileObject.DataList[dl].graphWidgets)[index]].figure.savefig('graphs/' + fileObject.DataList[dl].name + "_" + list(fileObject.DataList[dl].graphWidgets)[index] + '.png', bbox_inches='tight')
        if fileObject.DataList[dl].do is not None:
            fileObject.DataList[dl].do.createSpreadSheet()

    data.workbook.close()
    msg = QtWidgets.QMessageBox()
    msg.setWindowTitle("Export Complete")
    msg.setText("Graphs have been exported to the graphs folder.\n\n"
                "ReductionData.xlsx exported to application path")
    msg.exec_()


class AppWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
        self.form = menu.Ui_Dialog()
        self.form.setupUi(self)
        button = QtWidgets.QToolButton()
        button.setStyleSheet("QToolButton::hover"
                             "{"
                             "background-color : #3c596990;"
                             "}"
                             "QToolButton"
                             "{"
                             "border :1.5px solid ;"
                             "border-color: #3c5969;"
                             "}")
        button.setText("Export Graphs and Data")
        button.clicked.connect(ExportData)
        self.form.tabWidget_2.setCornerWidget(button)

        self.show()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            processFile(f)

Qapp = QApplication(sys.argv)
app = AppWindow()
app.show()


def selectData(file):
    app.form.placeHolderBar.hide()

    global currentFile

    for item in fileObject.DataList:
        fileObject.DataList[item].table.hide()
        fileObject.DataList[item].progressBar.hide()
        fileObject.DataList[item].graphList.hide()
        fileObject.DataList[item].hideGraphs()

    app.form.groupBox.setTitle(file.name)

    currentFile = file
    file.updateClassifierStats()
    file.updateDimensionStat()
    file.updateRowStat()

    app.form.tableWidget.hide()
    file.setGraphSelection()
    file.table.show()
    file.progressBar.show()
    file.graphList.show()

    # if len(file.graphWidgets) <= 0:
    #     if currentTab =
    #     app.form.tabWidget_2.setCurrentIndex(0)
    # else:
    #     app.form.tabWidget_2.setCurrentIndex(currentTab)

def addFile(csv, filename, showError):
    if filename in fileObject.DataList:
        if showError:

            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle("Filename already exists")
            msg.setText("A file with this name as already been added")
            msg.exec_()
        return

    file = fileObject.FileObject(csv, filename, app)

    file.loadTable()
    file.loadSettings()

    fileObject.DataList[filename] = file
    app.form.listWidget.addItem(filename)

    return file

def readCSV(filename):
    if os.path.isfile(filename) is False:
        return

    try:
        csv = pd.read_csv(filename)
    except Exception as e:
        if e == FileNotFoundError:
            return

        print(e)
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(filename + " - Error loading file")
        msg.setText(filename + " - Pandas Error: " + str(e))
        msg.exec_()
        return None
    return csv

def loadFile():
    dlg = QFileDialog()
    dlg.setFileMode(QFileDialog.AnyFile)
    dlg.exec_()

    a = dlg.selectedFiles()
    if len(a) <= 0:
        return

    processFile(a[0])


def processFile(url):
    csv = readCSV(url)
    if csv is None:
        return

    names = url.split("/")
    filename = names[len(names) - 1]

    file = addFile(csv, filename, True)

    if file is None:
        return

    selectData(file)

def loadAllFiles():
    files = glob.glob("data/*.data")

    files = files + (glob.glob("data/*.csv"))

    last = None
    for file in files:
        csv = readCSV(file)
        if csv is None:
            continue
        names = file.split("\\")
        filename = names[len(names) - 1]
        newFile = addFile(csv, filename, False)
        last = newFile

    if last is None:
        return

    deselectList()
    selectItem(app.form.listWidget.item(app.form.listWidget.count() - 1))
    selectData(last)


def toggleAllEnumerate():
    if currentFile is None:
        return
    currentFile.toggleAllEnumerate()

def saveSettings():
    if currentFile is None:
        return
    currentFile.saveSettings()

def resetSettings():
    if currentFile is None:
        return
    currentFile.clearSettings()

def resetAllSettings():
    for filename in fileObject.DataList:
        fileObject.DataList[filename].clearSettings()

def loadSettings():
    if currentFile is None:
        return
    currentFile.loadSettings()

counter = 0
msg = None
scroll = None
layout = None
running = False

def executeAllReduction():
    global counter,  msg, scroll, layout,running

    if running:
        return


    if len(fileObject.DataList) <= 0:
        return

    msg = QtWidgets.QDialog()
    msg.setWindowModality(QtCore.Qt.ApplicationModal)


    counter = 0
    msg.setWindowTitle("Reduction")
    #msg.setWindowFlags(
    #QtCore.Qt.Window |
    #QtCore.Qt.CustomizeWindowHint |
    #QtCore.Qt.WindowTitleHint |
    #QtCore.Qt.WindowMinimizeButtonHint
    #)
    msg.setMaximumSize(400, 9999)
    msg.setMinimumSize(400, 100)
    scroll = QtWidgets.QScrollArea()
    layout = QtWidgets.QVBoxLayout(scroll)
    scroll.setLayout(layout)

    msg.setLayout(layout)
    msg.setFixedSize(app.layout().sizeHint())

    msg.show()
    running = True
    startExecution()

def startExecution():
    global counter, running
    if counter != 0:
        fileObject.DataList[list(fileObject.DataList)[counter-1]].loadGraphs()

    if counter >= len(fileObject.DataList):
        counter = 0
        msg.hide()
        running = False
        return

    fileObject.DataList[list(fileObject.DataList)[counter]].executeReductionInModal(layout, startExecution)
    counter = counter + 1




def executeReduction():
    if currentFile is None:
        return
    currentFile.executeReductionInThread()
def loadAllSettings():
    for filename in fileObject.DataList:
        fileObject.DataList[filename].loadSettings()

def saveAllSettings():
    for filename in fileObject.DataList:
        fileObject.DataList[filename].saveSettings()

app.form.loadAllFiles.clicked.connect(loadAllFiles)
app.form.uploadButton.clicked.connect(loadFile)
app.form.enumerateAll.clicked.connect(toggleAllEnumerate)
app.form.saveSettings.clicked.connect(saveSettings)
app.form.loadSettings.clicked.connect(loadSettings)
app.form.saveAllSettings.clicked.connect(saveAllSettings)
app.form.loadAllSettings.clicked.connect(loadAllSettings)
app.form.resetAllSettings.clicked.connect(resetAllSettings)
app.form.resetSettings.clicked.connect(resetSettings)
app.form.executeAllButton.clicked.connect(executeAllReduction)

app.form.executeReduction.clicked.connect(executeReduction)

def setTab():
    global currentTab
    if currentFile is None:
        return

    currentFile.tabIndex = app.form.tabWidget_2.currentIndex()

    currentTab = currentFile.tabIndex

app.form.tabWidget_2.currentChanged.connect(setTab)
_translate = QtCore.QCoreApplication.translate


def deselectList():
    for i in range(app.form.listWidget.count()):
        app.form.listWidget.item(i).setBackground(QBrush(Qt.transparent, Qt.SolidPattern))
        app.form.listWidget.item(i).setForeground(QBrush(Qt.white, Qt.SolidPattern))

def selectionChanged():
    selectData(fileObject.DataList[app.form.listWidget.selectedItems()[0].text()])
    deselectList()
    selectItem(app.form.listWidget.selectedItems()[0])

def selectItem(item):
    item.setForeground(QBrush(Qt.white, Qt.SolidPattern))
    item.setBackground(QBrush(QColor(20, 100, 160), Qt.SolidPattern))


app.form.listWidget.itemSelectionChanged.connect(selectionChanged)
app.setAcceptDrops(True)

app.form.graphLayout = QtWidgets.QVBoxLayout(app.form.content_plot)
app.form.graphLayout.setContentsMargins(0, 0, 0, 0)


checkboxes2 = {}
checkboxes1 = {}

def selectReduction(value):
    checkbox = app.sender()

    reduction.reductionAlgorithms[int(checkbox.objectName())].enabled = value

    checkboxes2[reduction.reductionAlgorithms[int(checkbox.objectName())].name].setChecked(value)
    checkboxes1[reduction.reductionAlgorithms[int(checkbox.objectName())].name].setChecked(value)

text = QtWidgets.QLabel("Reduction")
app.form.verticalLayout_6.addWidget(text)
for i in range(len(reduction.reductionAlgorithms)):
    reductionBox = QtWidgets.QCheckBox(app.form.scrollAreaWidgetContents)
    reductionBox.setObjectName(str(i))
    reductionBox.setText(_translate("Dialog", reduction.reductionAlgorithms[i].name))
    reductionBox.setChecked(reduction.reductionAlgorithms[i].enabled)
    reductionBox.clicked.connect(selectReduction)
    app.form.verticalLayout_5.addWidget(reductionBox)
    checkboxes1[reduction.reductionAlgorithms[i].name] = reductionBox

    reductionBox = QtWidgets.QCheckBox(app.form.scrollAreaWidgetContents)
    reductionBox.setObjectName(str(i))
    reductionBox.setText(_translate("Dialog", reduction.reductionAlgorithms[i].name))
    reductionBox.setChecked(reduction.reductionAlgorithms[i].enabled)
    reductionBox.clicked.connect(selectReduction)
    reductionBox.setMaximumSize(100, 30)
    checkboxes2[reduction.reductionAlgorithms[i].name] = reductionBox
    app.form.verticalLayout_6.addWidget(reductionBox)
    app.form.verticalLayout_6.setSpacing(1)
    app.form.verticalLayout_6.setAlignment(QtCore.Qt.AlignTop)

def selectClassification(value):
    checkbox = app.sender()

    classification.classificationAlgorithms[int(checkbox.objectName())].enabled = value

text = QtWidgets.QLabel("Classifiers")
app.form.verticalLayout_7.addWidget(text)
for i in range(len(classification.classificationAlgorithms)):
    classifierBox = QtWidgets.QCheckBox(app.form.scrollAreaWidgetContents)
    classifierBox.setObjectName(str(i))
    classifierBox.setText(_translate("Dialog", classification.classificationAlgorithms[i].name))
    classifierBox.setChecked(classification.classificationAlgorithms[i].enabled)
    classifierBox.clicked.connect(selectClassification)
    classifierBox.setMaximumSize(100, 30)
    app.form.verticalLayout_7.addWidget(classifierBox)
    app.form.verticalLayout_7.setSpacing(1)
    app.form.verticalLayout_7.setAlignment(QtCore.Qt.AlignTop)


def updateSeed():
    input = re.sub('\D', '', app.form.selectionSeed.text())
    if len(input) <= 0:
        app.form.selectionSeed.setText("")
        return

    value = int(input)
    reduction.selectionSeed = value
    app.form.selectionSeed.setText(input)

def updatePercent():
    input = re.sub('[^0-9.]', '', app.form.testData.text())
    if input == "0.":
        reduction.testDataPercent = 0.
        app.form.testData.setText("0.")
        return
    if len(input) <= 0:
        app.form.testData.setText("")
        return

    try:
        value = float(input)
    except Exception:
        reduction.testDataPercent = 0.33
        app.form.testData.setText(str(0.33))
        return

    if value > 1:
        newstr = input.split(".")[0]
        div = float("1"+"".zfill(len(newstr)))
        value = value / div
        reduction.testDataPercent = value
        app.form.testData.setText(str(value))
        return

    reduction.testDataPercent = value
    app.form.testData.setText(input)

app.form.selectionSeed.setText(str(reduction.selectionSeed))
app.form.selectionSeed.textEdited.connect(updateSeed)
app.form.testData.setText(str(reduction.testDataPercent))
app.form.testData.textEdited.connect(updatePercent)
try:
    os.mkdir("graphs/")
except OSError:
    pass
app.exec()