import PyQt5
from PyQt5 import QtWidgets, uic, QtGui, QtCore
import pandas as pd
import numpy as np
from sklearn import preprocessing


app = QtWidgets.QApplication([])

form = uic.loadUi("menu.ui")

form.show()
DataList = {}

def setClassifier(checkbox):
    print("test")

def selectFile():

    a = QtWidgets.QFileDialog.getOpenFileName()
    csv = pd.read_csv(a[0])

    names = a[0].split("/")
    filename = names[len(names)-1]

    DataList[filename] = csv
    form.listWidget.addItem(filename)

    a = 0
    for col in csv.columns:
        form.tableWidget.insertRow(form.tableWidget.rowCount())

        widget = QtWidgets.QWidget()
        checkbox = QtWidgets.QCheckBox()
        checkbox.stateChanged.connect(lambda : setClassifier(checkbox))
        layout = QtWidgets.QHBoxLayout(widget)
        layout.addWidget(checkbox)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)

        form.tableWidget.setItem(a, 0, QtWidgets.QTableWidgetItem(col))
        form.tableWidget.setCellWidget(a, 1, widget)

        a += 1








form.uploadButton.clicked.connect(selectFile)


app.exec()