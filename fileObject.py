import sys
import traceback

from PyQt5.QtCore import Qt, QThreadPool, QRunnable, pyqtSlot, QObject, pyqtSignal
import json
import os
import classification
import reduction
import data

from PyQt5 import QtCore, QtWidgets, uic
import matplotlib
matplotlib.use('QT5Agg')

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

DataList = {}
currentFile = None

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
    def __init__(self, csv, name, app):
        self.name = name
        self.csv = csv
        self.app = app
        self.threadpool = QThreadPool()
        self.classifier = None
        self.disabled = []
        self.enumerate = []
        self.scale = []
        self.graphWidgets = {}
        self.graphToolBars = {}
        self.tabIndex = 0

        self.classifierBoxes = []
        self.disabledBoxes = []
        self.enumerateBoxes = []
        self.scaleBoxes = []

        self.enumAll = False

        self.table = QtWidgets.QTableWidget()

        self.table.setMinimumSize(QtCore.QSize(540, 0))
        self.table.setMaximumSize(QtCore.QSize(540, 16777215))
        self.table.setObjectName("tableWidget")
        self.table.setColumnCount(5)
        self.table.setRowCount(0)
        self.table.setAlternatingRowColors(True)

        self.Exception = None
        self.setupHeader()

        self.graphList = QtWidgets.QListWidget(self.app.form.tab_4)
        self.graphList.setMaximumSize(QtCore.QSize(150, 16777215))
        self.graphList.setObjectName("graphList")
        self.app.form.gridLayout_8.addWidget(self.graphList, 0, 0, 1, 1)
        self.graphList.itemSelectionChanged.connect(self.selectionChanged)

        self.progressBar = QtWidgets.QProgressBar(self.app.form.groupBox)
        self.progressBar.setMaximumSize(QtCore.QSize(16777215, 10))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setInvertedAppearance(False)
        self.progressBar.setObjectName("progressBar")
        self.progressBar.hide()

        self.allProgress = None
        self.app.form.gridLayout_5.addWidget(self.progressBar, 9, 0, 1, 1)
        self.do = None

        self.totalIterations = 0
        self.iterationCount = 0
        self.app.form.gridLayout_3.addWidget(self.table, 0, 0, 1, 1)

    def selectionChanged(self):
        self.hideGraphs()
        self.setGraphSelection()

    def hideGraphs(self):
        for graph in self.graphWidgets:
            self.graphWidgets[graph].hide()
            self.graphToolBars[graph].hide()

    def setGraphSelection(self):
        if len(self.graphList) <= 0:
            return

        selected = self.graphList.selectedItems()
        if len(selected) <= 0:
            return

        self.graphWidgets[self.graphList.selectedItems()[0].text()].show()
        self.graphToolBars[self.graphList.selectedItems()[0].text()].show()

    def executeReductionInModal(self, layout, next):

        groupBox = QtWidgets.QVBoxLayout()


        self.allProgress = QtWidgets.QProgressBar()
        self.allProgress.setMaximumSize(QtCore.QSize(16777215, 10))
        self.allProgress.setProperty("value", 0)
        self.allProgress.setTextVisible(False)
        self.allProgress.setInvertedAppearance(False)
        self.allProgress.setObjectName("allProgress")
        self.allProgress.show()

        label = QtWidgets.QLabel(self.name)
        label.setMinimumSize(100, 20)
        label.setMaximumSize(100, 40)
        groupBox.addWidget(label)
        groupBox.addWidget(self.allProgress)
        layout.addLayout(groupBox)


        worker = Worker(self.executeReduction)

        self.threadpool.start(worker)
        worker.signals.finished.connect(next)


    def executeReductionInThread(self):
         worker = Worker(self.executeReduction)

         worker.signals.finished.connect(self.loadGraphs)

         self.threadpool.start(worker)

        #self.executeReduction()

    def loadGraphs(self):

        if self.do is None:
            if self.Exception is not None:
                msg = QtWidgets.QMessageBox()
                msg.setWindowTitle("Reduction/Classification Error")
                msg.setText("Reduction/Classification Error: " + self.Exception)
                msg.exec_()

            return

        if len(self.do.reducedDataSets) <= 0:
            return

        if len(self.graphWidgets) > 0:
            for wid in self.graphWidgets:
                self.graphWidgets[wid].hide()
                self.graphWidgets[wid].deleteLater()

        self.graphWidgets = self.do.createGraph()
        self.graphList.clear()
        self.graphList.addItems([a for a in self.graphWidgets])



        last = None
        for graph in self.graphWidgets:
            self.graphWidgets[graph].hide()

            self.app.form.graphLayout.addWidget(self.graphWidgets[graph])
            toolbar = NavigationToolbar(self.graphWidgets[graph], None)
            toolbar.hide()
            self.graphToolBars[graph] = toolbar
            self.app.form.graphLayout.addWidget(toolbar)
            self.iterationCount += 1
            if self.allProgress is not None:
                self.allProgress.setValue((self.iterationCount / self.totalIterations) * 100)
            self.progressBar.setValue((self.iterationCount / self.totalIterations) * 100)
            last = graph

        if last is None:
            return

        if currentFile == self:
            self.graphWidgets[last].show()
            self.graphToolBars[last].show()


    def executeReduction(self):

        try:
            if self.classifier is None:
                self.Exception = "No classifier has been set"
                return

            canRun = False
            for method in reduction.reductionAlgorithms:
                if method.enabled:
                    canRun = True
                    break

            csv = self.csv.copy(deep=True)

            if self.enumAll:
                csv = data.enumerate_all(csv)
            elif len(self.enumerate) > 0:
                csv = data.enumerate_data(csv, self.enumerate)

            if len(self.scale) > 0:
                csv = data.scale_data(csv, self.scale)

            self.disabled.sort(reverse=True)

            for columnIndex in self.disabled:
                del csv[csv.columns[columnIndex]]
                if columnIndex < self.classifier:
                    self.classifier = self.classifier -1

            self.do = data.DataObject(self.name, csv, self.classifier)




            self.do.xTrainingData,  self.do.xTestData,  self.do.yTrainingData,  self.do.yTestData = reduction.prepareData( self.do.x,  self.do.y)
            for classifier in classification.classificationAlgorithms:
                temp_score, elapsedTime = classifier.execute( self.do.xTrainingData,  self.do.xTestData,
                                                              self.do.yTrainingData,
                                                              self.do.yTestData)
                self.do.addClassifierScore(classifier.name, temp_score, elapsedTime)


            self.totalIterations =  (self.do.maxDimensionalReduction * len([ra for ra in reduction.reductionAlgorithms if ra.enabled]) * len([cla for cla in classification.classificationAlgorithms if cla.enabled])) + len([cla for cla in classification.classificationAlgorithms if cla.enabled])
            self.iterationCount = 0
            self.progressBar.setValue(0)
            if self.allProgress is not None:
                self.allProgress.setValue(0)

            for method in reduction.reductionAlgorithms:
                if not method.enabled:
                    continue

                dataset = self.do.newReducedDataSet(method.name)
                for dimension in range( self.do.maxDimensionalReduction, 0, -1):


                    if method.capByClasses and dimension > self.do.classes - 1:
                        reducedData = dataset.addReducedData([], [], [], dimension, 0)
                        for classifier in classification.classificationAlgorithms:
                            if not classifier.enabled:
                                continue
                            reducedData.addClassifierScore(classifier.name, 0, 0)
                            self.iterationCount+=1
                            if self.allProgress is not None:
                                self.allProgress.setValue((self.iterationCount / self.totalIterations) * 100)
                            self.progressBar.setValue((self.iterationCount / self.totalIterations) * 100)

                        continue

                    reducedData = method.execute(dimension,  self.do.x,  self.do.y, dataset)

                    for classifier in classification.classificationAlgorithms:
                        if not classifier.enabled:
                            continue
                        temp_score, elapsedTime = classifier.execute(reducedData.xTrainingData, reducedData.xTestData,
                                                                     dataset.yTrainingData,
                                                                     dataset.yTestData)
                        reducedData.addClassifierScore(classifier.name, temp_score, elapsedTime)
                        self.iterationCount += 1

                        if self.allProgress is not None:
                            self.allProgress.setValue((self.iterationCount / self.totalIterations) * 100)

                        self.progressBar.setValue((self.iterationCount / self.totalIterations) * 100)
        except Exception as e:
            print(e)
            self.Exception = str(e)
            self.do = None
            return None


    def clearSettings(self):
        self.setAllEnumerate(False)
        self.enumAll = False
        for box in self.disabledBoxes:
            box.setChecked(False)
        for box in self.enumerateBoxes:
            box.setChecked(False)
        for box in self.scaleBoxes:
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
        self.app.sender().setChecked(True)
        self.classifier = int(self.app.sender().objectName())
        self.updateClassifierStats()
        print(self.classifier)

    def updateClassifierStats(self):
        if self.classifier is None:
            return

        self.classes = self.csv[self.csv.columns[self.classifier]].nunique()
        self.app.form.classificationValue.setText(str(self.classes))

    def updateDimensionStat(self):
        self.dimensions = len(self.csv.columns) - (len(self.disabled))
        self.app.form.dimensionValue.setText(str(self.dimensions))

    def updateRowStat(self):
        self.rows = len(self.csv.index)
        self.app.form.rowValue.setText(str(self.rows))


    def setDisabled(self):

        id = int(self.app.sender().objectName())

        if id in self.disabled:
            self.disabled.remove(id)
        else:
            self.disabled.append(id)

        print(self.disabled)
        self.updateDimensionStat()

    def setEnumerate(self):
        id = int(self.app.sender().objectName())

        if id in self.enumerate:
            self.enumerate.remove(id)
        else:
            self.enumerate.append(id)

        print(self.enumerate)

    def setScale(self):
        id = int(self.app.sender().objectName())

        if id in self.scale:
            self.scale.remove(id)
        else:
            self.scale.append(id)

        print(self.scale)

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
        data['scale'] = self.scale
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

                if 'scale' in data:
                    self.scale = data['scale']
                    for box in self.scaleBoxes:
                        id = int(box.objectName())
                        if id in data['scale']:
                            box.setChecked(True)
                        else:
                            box.setChecked(False)

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

            scaleWidget, checkbox = createCheckbox(str(a), self.setScale)
            self.scaleBoxes.append(checkbox)

            self.table.setItem(a, 0, QtWidgets.QTableWidgetItem(col))
            self.table.setCellWidget(a, 1, classifierWidget)
            self.table.setCellWidget(a, 2, enumerateWidget)
            self.table.setCellWidget(a, 3, scaleWidget)
            self.table.setCellWidget(a, 4, disableWidget)
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
        item.setText(_translate("Dialog", "Scale"))
        self.table.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        item.setText(_translate("Dialog", "Disable"))
        self.table.setHorizontalHeaderItem(4, item)
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