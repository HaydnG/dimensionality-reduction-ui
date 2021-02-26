import sys

import PyQt5
from PyQt5 import QtWidgets, uic, QtGui, QtCore
import pandas as pd
import numpy as np
import glob

from PyQt5.QtWidgets import QDialog, QApplication

import menu

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import fileObject
import qdarkstyle
import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor
import warnings
warnings.filterwarnings("ignore")



class AppWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
        self.form = menu.Ui_Dialog()
        self.form.setupUi(self)

        self.show()

Qapp = QApplication(sys.argv)
app = AppWindow()
app.show()

DataList = {}

currentFile = None

def selectData(file):
    app.form.placeHolderBar.hide()

    global currentFile


    if file.table.rowCount() < 1:
       file.loadTable()
       file.loadSettings()

    for item in DataList:
        DataList[item].table.hide()
        DataList[item].progressBar.hide()

    app.form.groupBox.setTitle(file.name)

    currentFile = file
    file.updateClassifierStats()
    file.updateDimensionStat()
    file.updateRowStat()

    app.form.tableWidget.hide()
    file.table.show()
    file.progressBar.show()
    app.form.tabWidget_2.setCurrentIndex(file.tabIndex)

def addFile(csv, filename, showError):
    if filename in DataList:
        if showError:

            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle("Filename already exists")
            msg.setText("A file with this name as already been added")
            msg.exec_()
        return

    file = fileObject.FileObject(csv, filename, app.form)

    DataList[filename] = file
    app.form.listWidget.addItem(filename)

    return file

def readCSV(filename):
    try:
        csv = pd.read_csv(filename)
    except Exception as e:
        print(e)
        print("failed to load file")

        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(filename + " - Error loading file")
        msg.setText(filename + " - Pandas Error: " + str(e))
        msg.exec_()
        return None
    return csv

def loadFile():

    a = QtWidgets.QFileDialog.getOpenFileName()

    csv = readCSV(a[0])
    if csv is None:
        return

    names = a[0].split("/")
    filename = names[len(names)-1]

    file = addFile(csv, filename, True)

    if file is None:
        return

    selectData(file)

def loadAllFiles():
    files = glob.glob("data/*.data")

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
    for filename in DataList:
        DataList[filename].clearSettings()

def loadSettings():
    if currentFile is None:
        return
    currentFile.loadSettings()

def executeReduction():
    if currentFile is None:
        return
    currentFile.executeReductionInThread()
    print("hi")

def loadAllSettings():
    for filename in DataList:
        DataList[filename].loadSettings()

def saveAllSettings():
    for filename in DataList:
        DataList[filename].saveSettings()

app.form.loadAllFiles.clicked.connect(loadAllFiles)
app.form.uploadButton.clicked.connect(loadFile)
app.form.enumerateAll.clicked.connect(toggleAllEnumerate)
app.form.saveSettings.clicked.connect(saveSettings)
app.form.loadSettings.clicked.connect(loadSettings)
app.form.saveAllSettings.clicked.connect(saveAllSettings)
app.form.loadAllSettings.clicked.connect(loadAllSettings)
app.form.resetAllSettings.clicked.connect(resetAllSettings)
app.form.resetSettings.clicked.connect(resetSettings)

app.form.executeReduction.clicked.connect(executeReduction)

def setTab():
    currentFile.tabIndex = app.form.tabWidget_2.currentIndex()

app.form.tabWidget_2.currentChanged.connect(setTab)



def deselectList():
    for i in range(app.form.listWidget.count()):
        app.form.listWidget.item(i).setBackground(QBrush(Qt.transparent, Qt.SolidPattern))
        app.form.listWidget.item(i).setForeground(QBrush(Qt.white, Qt.SolidPattern))

def selectionChanged():
    selectData(DataList[app.form.listWidget.selectedItems()[0].text()])
    deselectList()
    selectItem(app.form.listWidget.selectedItems()[0])

def selectItem(item):
    item.setForeground(QBrush(Qt.white, Qt.SolidPattern))
    item.setBackground(QBrush(QColor(20, 100, 160), Qt.SolidPattern))


app.form.listWidget.itemSelectionChanged.connect(selectionChanged)
try:
    os.mkdir("graphs/")
except OSError:
    pass
app.exec()