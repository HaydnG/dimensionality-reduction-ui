import sys
import traceback

from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtCore import Qt, QThreadPool, QRunnable, pyqtSlot, QObject, pyqtSignal
import json
import os
import classification
import reduction
import data

from PyQt5 import QtCore, QtWidgets, uic
import matplotlib
matplotlib.use('QT5Agg')

import matplotlib.pylab as plt
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)

class Worker(QRunnable):

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(
                *self.args, **self.kwargs
            )
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done

class FileObject:
    def __init__(self, csv, name, form):
        self.name = name
        self.csv = csv
        self.form = form
        self.threadpool = QThreadPool()
        self.classifier = None
        self.disabled = []
        self.enumerate = []
        self.tabIndex = 0

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

        self.progressBar = QtWidgets.QProgressBar(self.form.groupBox)
        self.progressBar.setMaximumSize(QtCore.QSize(16777215, 10))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setInvertedAppearance(False)
        self.progressBar.setObjectName("progressBar")
        self.progressBar.hide()
        self.form.gridLayout_5.addWidget(self.progressBar, 8, 0, 1, 1)


        self.form.gridLayout_3.addWidget(self.table, 0, 0, 1, 1)

    def executeReductionInThread(self):
         worker = Worker(self.executeReduction)

         worker.signals.finished.connect(self.loadGraphs)

         self.threadpool.start(worker)

        #self.executeReduction()

    def loadGraphs(self):

        widgets = self.do.createGraph()

        plotWidget = widgets[0]

        lay = QtWidgets.QVBoxLayout(self.form.content_plot)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(plotWidget)
        lay.addWidget(NavigationToolbar(plotWidget, None))
        plotWidget.show()

    def executeReduction(self):

        csv = self.csv.copy(deep=True)

        if self.enumAll:
            csv = data.enumerate_all(csv)
        elif len(self.enumerate) > 0:
            csv = data.enumerate_data(csv, self.enumerate)

        for columnIndex in self.disabled:
            del csv[csv.columns[columnIndex]]


        self.do = data.DataObject(self.name, csv, self.classifier)

        self.do.xTrainingData,  self.do.xTestData,  self.do.yTrainingData,  self.do.yTestData = reduction.prepareData( self.do.x,  self.do.y)
        for classifier in classification.classificationAlgorithms:
            temp_score, elapsedTime = classifier.execute( self.do.xTrainingData,  self.do.xTestData,
                                                          self.do.yTrainingData,
                                                          self.do.yTestData)
            self.do.addClassifierScore(classifier.name, temp_score, elapsedTime)

        totalIterations =  self.do.maxDimensionalReduction * len(reduction.reductionAlgorithms) * len(classification.classificationAlgorithms)
        iterationCount = 0
        self.progressBar.setValue(0)

        for method in reduction.reductionAlgorithms:

            dataset =  self.do.newReducedDataSet(method.name)
            for dimension in range( self.do.maxDimensionalReduction, 0, -1):

                if method.capByClasses and dimension >  self.do.classes - 1:
                    reducedData = dataset.addReducedData([], [], [], dimension, 0)
                    for classifier in classification.classificationAlgorithms:
                        reducedData.addClassifierScore(classifier.name, 0, 0)
                        iterationCount+=1
                        self.progressBar.setValue((iterationCount / totalIterations) * 100)

                    continue

                reducedData = method.execute(dimension,  self.do.x,  self.do.y, dataset)

                for classifier in classification.classificationAlgorithms:
                    temp_score, elapsedTime = classifier.execute(reducedData.xTrainingData, reducedData.xTestData,
                                                                 dataset.yTrainingData,
                                                                 dataset.yTestData)
                    reducedData.addClassifierScore(classifier.name, temp_score, elapsedTime)
                    iterationCount += 1
                    self.progressBar.setValue((iterationCount / totalIterations) * 100)

                print('.', end='')
            print("")
        print(iterationCount, totalIterations)


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
        self.updateClassifierStats()
        print(self.classifier)

    def updateClassifierStats(self):
        if self.classifier is None:
            return

        self.classes = self.csv[self.csv.columns[self.classifier]].nunique()
        self.form.classificationValue.setText(str(self.classes))

    def updateDimensionStat(self):
        self.dimensions = len(self.csv.columns) - (len(self.disabled))
        self.form.dimensionValue.setText(str(self.dimensions))

    def updateRowStat(self):
        self.rows = len(self.csv.index)
        self.form.rowValue.setText(str(self.rows))


    def setDisabled(self):

        id = int(self.form.sender().objectName())

        if id in self.disabled:
            self.disabled.remove(id)
        else:
            self.disabled.append(id)

        print(self.disabled)
        self.updateDimensionStat()

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