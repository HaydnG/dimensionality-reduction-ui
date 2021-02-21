import PyQt5
from PyQt5 import QtWidgets, uic, QtGui, QtCore
import pandas as pd
import numpy as np
import glob
import fileObject
import qdarkstyle
import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor

app = QtWidgets.QApplication([])

app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))

form = uic.loadUi("menu.ui")

form.show()
DataList = {}

currentFile = None

def selectData(file):
    global currentFile


    if file.table.rowCount() < 1:
       file.loadTable()
       file.loadSettings()

    for item in DataList:
        DataList[item].table.hide()

    form.groupBox.setTitle(file.name)

    currentFile = file

    form.tableWidget.hide()
    file.table.show()

def addFile(csv, filename, showError):
    if filename in DataList:
        if showError:

            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle("Filename already exists")
            msg.setText("A file with this name as already been added")
            msg.exec_()
        return

    file = fileObject.FileObject(csv, filename, form)

    DataList[filename] = file
    form.listWidget.addItem(filename)

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
    selectItem(form.listWidget.item(form.listWidget.count() - 1))
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

def loadAllSettings():
    for filename in DataList:
        DataList[filename].loadSettings()

def saveAllSettings():
    for filename in DataList:
        DataList[filename].saveSettings()

form.loadAllFiles.clicked.connect(loadAllFiles)
form.uploadButton.clicked.connect(loadFile)
form.enumerateAll.clicked.connect(toggleAllEnumerate)
form.saveSettings.clicked.connect(saveSettings)
form.loadSettings.clicked.connect(loadSettings)
form.saveAllSettings.clicked.connect(saveAllSettings)
form.loadAllSettings.clicked.connect(loadAllSettings)
form.resetAllSettings.clicked.connect(resetAllSettings)
form.resetSettings.clicked.connect(resetSettings)



def deselectList():
    for i in range(form.listWidget.count()):
        form.listWidget.item(i).setBackground(QBrush(Qt.transparent, Qt.SolidPattern))
        form.listWidget.item(i).setForeground(QBrush(Qt.white, Qt.SolidPattern))

def selectionChanged():
    selectData(DataList[form.listWidget.selectedItems()[0].text()])
    deselectList()
    selectItem(form.listWidget.selectedItems()[0])

def selectItem(item):
    item.setForeground(QBrush(Qt.white, Qt.SolidPattern))
    item.setBackground(QBrush(QColor(20, 100, 160), Qt.SolidPattern))


form.listWidget.itemSelectionChanged.connect(selectionChanged)

app.exec()