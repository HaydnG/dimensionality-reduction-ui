import inline as inline
import pandas as pd
import numpy as np
from sklearn import preprocessing
import classification
import matplotlib.patheffects as pe
from matplotlib.legend_handler import HandlerLine2D, HandlerTuple
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import xlsxwriter
import os

from PyQt5 import QtCore, QtWidgets, uic
import matplotlib
matplotlib.use('QT5Agg')

import matplotlib.pylab as plt
from matplotlib.backends.backend_qt5agg import FigureCanvas


if os.path.exists("ReductionData.xlsx"):
  os.remove("ReductionData.xlsx")

workbook = xlsxwriter.Workbook('ReductionData.xlsx')

np.set_printoptions(precision=4, suppress=True)
plt.style.use('seaborn-whitegrid')

pd.set_option("display.max.columns", None)
from sklearn import metrics
GraphCount = 0

# Converts string data to engtumerated data
def enumerate(csv, label):
    csv = csv.replace('?', np.nan)
    csv = csv.dropna()

    le = preprocessing.LabelEncoder()
    le.fit(csv[label])
    csv[label] = le.transform(csv[label])

    return csv

# Takes in the data, and a list of labels to apply enumeration
def enumerate_data(csv, labels):
    for l in labels:

        if isinstance(l, int):
            l = csv.columns[l]

        csv = enumerate(csv, l)

    return csv

# Enumerates all columns in dataset
def enumerate_all(csv):
    for l in csv.columns:
        csv = enumerate(csv, l)
    return csv

class ReducedData:
    def __init__(self, xData, xTrainingData , xTestData, dimension, elapsedTime):
        self.xData = xData
        self.xTrainingData = xTrainingData
        self.xTestData = xTestData
        self.dimension = dimension
        self.classifierScore = {}
        self.classifierTime = {}
        self.elapsedTime = elapsedTime

    def addClassifierScore(self, name, score, elapsedTime):
        self.classifierScore[name] = score
        self.classifierTime[name] = elapsedTime


class ReducedDataSet:
    def __init__(self, name):
        self.name = name
        self.reducedData: ReducedData = []
        self.yTrainingData = None
        self.yTestData = None

    def addReducedData(self, xData, xTrainingData , xTestData, Dimension, elapsedTime):
        self.reducedData.append(ReducedData(xData, xTrainingData , xTestData, Dimension, elapsedTime))
        return self.reducedData[-1]


class DataObject:

    def __init__(self, name, data, classifierIndex):
        self.name = name


        data = data.replace('?', np.nan)
        data = data.dropna()
        datacopy = data.copy(deep=True)

        self.x = datacopy.drop([data.columns[classifierIndex]],  axis=1)
        self.dimensions = len(data.columns) - 1

        self.maxDimensionalReduction = self.dimensions - 1
        if self.maxDimensionalReduction > 26:
            self.maxDimensionalReduction = 26

        self.y = data[data.columns[classifierIndex]]
        self.classes = self.y.nunique()
        self.yTrainingData = None
        self.yTestData = None
        self.xTrainingData = None
        self.xTestData = None
        self.reducedDataSets: ReducedDataSet = []
        self.classifierScore = {}
        self.classifierTime = {}

    def addClassifierScore(self, name, score, elapsedTime):
        self.classifierScore[name] = score
        self.classifierTime[name] = elapsedTime

    def newReducedDataSet(self, name):
        self.reducedDataSets.append(ReducedDataSet(name))
        return self.reducedDataSets[-1]

    def createSpreadSheet(self):
        worksheet = workbook.add_worksheet(self.name)
        worksheet.set_column(0, (len(self.reducedDataSets) * 2) + 1, 20)

        row = 0
        col = 0

        worksheet.write(row, col, "Result without reduction")
        row=1
        worksheet.write(row, col, "Classification Algorithm")
        worksheet.write(row, col + 1, "Dimensions")
        worksheet.write(row, col + 2, "Score")
        worksheet.write(row, col + 3, "Classification Time")
        row += 1
        for classifier in classification.classificationAlgorithms:
            worksheet.write(row, col, classifier.name)
            worksheet.write(row, col + 1, self.dimensions)
            worksheet.write(row, col + 2, self.classifierScore[classifier.name])
            worksheet.write(row , col + 3, self.classifierTime[classifier.name])
            row+=1

        worksheet.write(row + 3, col, "Reduction scores")
        row +=4

        for classifier in classification.classificationAlgorithms:
            col = 0
            worksheet.write(row, col, classifier.name + " Classifier")
            row += 1
            rowOffset = row
            row+=1

            for dimension in [ds.dimension for ds in self.reducedDataSets[0].reducedData]:
                worksheet.write(row, col, dimension)
                row+=1
            row = rowOffset

            colOffset = 1

            for datasets in self.reducedDataSets:
                col = colOffset
                row=rowOffset
                worksheet.write(row, col, datasets.name + " Score")
                worksheet.write(row, col + 1, datasets.name + " Time")
                row+=1
                for data in datasets.reducedData:
                    col = colOffset
                    worksheet.write(row, col, data.classifierScore["KNeighbors"])
                    worksheet.write(row, col + 1, data.elapsedTime)
                    col = colOffset
                    row+=1
                colOffset+=2

    def createGraph(self):
        global GraphCount


        plt.figure(GraphCount)

        widgetList = {}

        for classifier in classification.classificationAlgorithms:

            scoreData = []
            for datasets in self.reducedDataSets:
                scores = [ds.classifierScore[classifier.name] for ds in datasets.reducedData]
                scoreData.append(scores)


            dimensions = [ds.dimension for ds in self.reducedDataSets[0].reducedData]
            if len(scoreData) <= 0:
                continue

            df = pd.DataFrame(np.column_stack(scoreData), index=np.arange(0, self.maxDimensionalReduction, 1).tolist(),
                              columns=[rds.name for rds in self.reducedDataSets])

            ax = df.plot.bar()

            lines, labels = ax.get_legend_handles_labels()

            plt.legend(lines, labels, title='Reduction Algorithm',
                       bbox_to_anchor=(-0.3, -0.2, 0.6, 0.1), loc=1,
                       ncol=2, borderaxespad=0.)
            plt.subplots_adjust(wspace=2)
            plt.title(
                self.name,
                loc='right')

            plt.title(classifier.name, loc='left')
            plt.ylabel("Prediction accuracy (bars)")
            plt.xlabel("Number of dimensions")
            plt.margins(y=0)

            plt.xticks(list(range(0, self.maxDimensionalReduction)), dimensions)

            ax2 = ax.twinx()
            for datasets in self.reducedDataSets:
                ax2.plot(list(range(0, self.maxDimensionalReduction)),
                                [ds.elapsedTime for ds in datasets.reducedData],marker='o',markersize=4, lw=1, markeredgecolor='black')

            # ax2.plot(list(range(0, self.maxDimensionalReduction)),
            #          [ds.classifierTime[classifier.name] for ds in datasets.reducedData], marker='*', markersize=5, lw=1,
            #          markeredgecolor='red')

            ax2.legend(handles=[Line2D([0], [0], marker='o', color='black', label='Reduction Time',
                                      markerfacecolor='red', markersize=10)],
                       bbox_to_anchor=(1, -0.1,0, 0),title='Execution Time (ms)', loc=1,
                       ncol=1, borderaxespad=0.)


            plt.ylabel("Algorithm execution time (ms) (line)")
            plt.tight_layout()
            ax2.set_ylim(bottom=0)


            #plt.show()
            GraphCount += 1

            plotWidget = FigureCanvas(plt.gcf())

            widgetList[classifier.name] = plotWidget

            #plt.savefig('graphs/' + self.name + "_" + classifier.name + '.png', bbox_inches='tight')
        return widgetList