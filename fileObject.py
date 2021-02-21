from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtCore import Qt
import json
import os

class FileObject:
    def __init__(self, csv, name, form):
        self.name = name
        self.csv = csv
        self.form = form

        self.classifier = None

        self.disabled = []
        self.enumerate = []

        self.classifierBoxes = []
        self.disabledBoxes = []
        self.enumerateBoxes = []

        self.enumAll = False

        self.table = QtWidgets.QTableWidget()

        self.table.setMinimumSize(QtCore.QSize(455, 0))
        self.table.setMaximumSize(QtCore.QSize(455, 16777215))
        self.table.setObjectName("tableWidget")
        self.table.setColumnCount(4)
        self.table.setRowCount(0)
        self.table.setAlternatingRowColors(True)

        self.setupHeader()


        self.form.gridLayout_3.addWidget(self.table, 0, 0, 1, 1)

    def clearSettings(self):
        self.setAllEnumerate(False)
        self.enumAll = False
        for box in self.disabledBoxes:
            box.setChecked(False)
        for box in self.enumerateBoxes:
            box.setChecked(False)
        for box in self.classifierBoxes:
            box.setChecked(False)
        self.classifier = 0

    def updateTableColumns(self):

        for rowIndex in range(0, self.table.rowCount()):
            self.table.setItem(rowIndex, 0, QtWidgets.QTableWidgetItem(self.csv.columns[rowIndex]))


    def setClassifier(self):

        for box in self.classifierBoxes:
            box.setChecked(False)
        self.form.sender().setChecked(True)
        self.classifier = int(self.form.sender().objectName())
        print(self.classifier)

    def setDisabled(self):

        id = int(self.form.sender().objectName())

        if id in self.disabled:
            self.disabled.remove(id)
        else:
            self.disabled.append(id)

        print(self.disabled)

    def setEnumerate(self):
        id = int(self.form.sender().objectName())

        if id in self.enumerate:
            self.enumerate.remove(id)
        else:
            self.enumerate.append(id)

        print(self.enumerate)

    def toggleAllEnumerate(self):
        self.enumAll = not self.enumAll
        self.setAllEnumerate(self.enumAll)

    def setAllEnumerate(self, value):
        for box in self.enumerateBoxes:
            box.setChecked(value)

            id = int(box.objectName())

            if value and id not in self.enumerate:
                self.enumerate.append(id)
            elif not value and id in self.enumerate:
                self.enumerate.remove(id)

        print(self.enumerate)

    def saveSettings(self):

        data = {}
        data['enumerate'] = self.enumerate
        data['disabled'] = self.disabled
        data['classifier'] = self.classifier
        data['enumAll'] = self.enumAll
        data['columnTitles'] = [self.table.item(y, 0).text() for y in range(0, self.table.rowCount())]

        try:
            os.mkdir("data/")
        except OSError:
            pass

        with open("data/" + self.name + '.settings', 'w') as outfile:
            json.dump(data, outfile)

    def loadSettings(self):
        try:
            with open("data/" + self.name + '.settings') as json_file:
                data = json.load(json_file)

                self.enumerate = data['enumerate']
                self.enumAll = data['enumAll']

                if 'columnTitles' in data:
                    self.csv.columns = data['columnTitles']

                self.updateTableColumns()
                if self.enumAll:
                    self.setAllEnumerate(self.enumAll)
                for box in self.enumerateBoxes:
                    id = int(box.objectName())
                    if id in self.enumerate:
                        box.setChecked(True)
                    else:
                        box.setChecked(False)

                self.disabled = data['disabled']
                for box in self.disabledBoxes:
                    id = int(box.objectName())
                    if id in self.disabled:
                        box.setChecked(True)
                    else:
                        box.setChecked(False)

                self.classifier = data['classifier']
                for box in self.classifierBoxes:
                    id = int(box.objectName())
                    if id == self.classifier:
                        box.setChecked(True)
                    else:
                        box.setChecked(False)
        except FileNotFoundError as ex:
            return

    def loadTable(self):
        a = 0
        for col in self.csv.columns:
            self.table.insertRow(self.table.rowCount())

            classifierWidget, checkbox = createCheckbox(str(a), self.setClassifier)
            self.classifierBoxes.append(checkbox)

            disableWidget, checkbox = createCheckbox(str(a), self.setDisabled)
            self.disabledBoxes.append(checkbox)

            enumerateWidget, checkbox = createCheckbox(str(a), self.setEnumerate)
            self.enumerateBoxes.append(checkbox)

            self.table.setItem(a, 0, QtWidgets.QTableWidgetItem(col))
            self.table.setCellWidget(a, 1, classifierWidget)
            self.table.setCellWidget(a, 2, enumerateWidget)
            self.table.setCellWidget(a, 3, disableWidget)
            a += 1



    def setupHeader(self):
        _translate = QtCore.QCoreApplication.translate
        item = QtWidgets.QTableWidgetItem()
        item.setText(_translate("Dialog", "Column Name"))
        self.table.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        item.setText(_translate("Dialog", "Classifier"))
        self.table.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        item.setText(_translate("Dialog", "Enumerate"))
        self.table.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        item.setText(_translate("Dialog", "Disable"))
        self.table.setHorizontalHeaderItem(3, item)
        self.table.verticalHeader().setDefaultSectionSize(8)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)


def createCheckbox(name, clickEvent):
    widget = QtWidgets.QWidget()
    checkbox = QtWidgets.QCheckBox()
    checkbox.setObjectName(str(name))
    checkbox.clicked.connect(clickEvent)

    layout = QtWidgets.QHBoxLayout(widget)
    layout.addWidget(checkbox)
    layout.setAlignment(QtCore.Qt.AlignCenter)
    layout.setContentsMargins(0, 0, 0, 0)
    widget.setLayout(layout)

    return widget, checkbox