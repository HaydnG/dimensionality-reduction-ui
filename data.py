import pandas as pd
import numpy as np
from sklearn import preprocessing
import classification
from matplotlib.lines import Line2D
import xlsxwriter
import os

import matplotlib
matplotlib.use('TkAgg', force=True)

import matplotlib.pylab as plt
from matplotlib.backends.backend_qt5agg import FigureCanvas

workbook = None

def openWorkBook():
    global workbook

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

def scale(csv, label):
    csv = csv.replace('?', np.nan)
    csv = csv.dropna()

    ss = preprocessing.StandardScaler()
    data = np.array(csv[label]).reshape(-1, 1)

    csv[label] = ss.fit_transform(data)

    return csv

# Takes in the data, and a list of labels to apply enumeration
def enumerate_data(csv, labels):
    for l in labels:

        if isinstance(l, int):
            l = csv.columns[l]

        csv = enumerate(csv, l)

    return csv

def scale_data(csv, labels):
    for l in labels:

        if isinstance(l, int):
            l = csv.columns[l]

        csv = scale(csv, l)

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

        if self.maxDimensionalReduction == 1:
            self.maxDimensionalReduction = 2

        self.y = data[data.columns[classifierIndex]]
        self.classes = self.y.nunique()
        self.classList = self.y.unique()
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
        if len(self.name) > 30:
            name = self.name[0:30]
        else:
            name = self.name

        worksheet = workbook.add_worksheet(name)
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
            if not classifier.enabled:
                continue
            worksheet.write(row, col, classifier.name)
            worksheet.write(row, col + 1, self.dimensions)
            worksheet.write(row, col + 2, self.classifierScore[classifier.name])
            worksheet.write(row , col + 3, self.classifierTime[classifier.name])
            row+=1

        worksheet.write(row + 3, col, "Reduction scores")
        row +=4

        for classifier in classification.classificationAlgorithms:
            if not classifier.enabled:
                continue
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
                    worksheet.write(row, col, data.classifierScore[classifier.name])
                    worksheet.write(row, col + 1, data.elapsedTime)
                    col = colOffset
                    row+=1
                colOffset+=2

    def createGraph(self):
        global GraphCount




        widgetList = {}

        for classifier in classification.classificationAlgorithms:
            if not classifier.enabled:
                continue
            plt.figure(GraphCount)
            scoreData = [[0] + [ds.classifierScore[classifier.name] for ds in rds.reducedData] for rds in self.reducedDataSets]
            scoreData.append([self.classifierScore[classifier.name]] + ([0] * (self.dimensions-1)))

            dimensions = [self.dimensions] + [ds.dimension for ds in self.reducedDataSets[0].reducedData]
            if len(scoreData) <= 0:
                continue

            df = pd.DataFrame(np.column_stack(scoreData), index=np.arange(0, self.dimensions, 1).tolist(),
                              columns=[rds.name for rds in self.reducedDataSets] + ["Without Reduction"])

            ax = df.plot.bar(width=0.5)
            lines, labels = ax.get_legend_handles_labels()

            plt.legend(lines, labels, title='Reduction Algorithm',
                       bbox_to_anchor=(-0.3, -0.2, 0.7, 0.1), loc=1,
                       ncol=2, borderaxespad=0.)
            plt.subplots_adjust(wspace=2)
            plt.title(
                self.name,
                loc='right')

            plt.title(classifier.name, loc='left')
            plt.ylabel("Prediction accuracy (bars)")
            plt.xlabel("Number of dimensions")
            plt.margins(y=0)

            plt.xticks(list(range(0, self.dimensions)), dimensions)

            ax2 = ax.twinx()
            for datasets in self.reducedDataSets:
                ax2.plot(list(range(0, self.dimensions)),
                                [None] + [ds.elapsedTime for ds in datasets.reducedData],marker='o',markersize=4, lw=1, markeredgecolor='black')

            ax2.legend(handles=[Line2D([0], [0], marker='o', color='black', label='Reduction Time',
                                      markerfacecolor='red', markersize=10)],
                       bbox_to_anchor=(1, -0.1,0, 0),title='Reduction Time (ms)', loc=1,
                       ncol=1, borderaxespad=0.)

            plt.ylabel("Algorithm execution time (ms) (line)")
            plt.tight_layout()
            ax2.set_ylim(bottom=0)


            plotWidget = FigureCanvas(plt.gcf())

            widgetList[classifier.name] = plotWidget
            GraphCount += 1

        GraphCount += 1

        for rds in self.reducedDataSets:
            if len(rds.reducedData[len(rds.reducedData)-2].xData) <= 0:
                continue

            plt.figure(GraphCount)
            plots = []
            for cl in self.classList:

                x = [rds.reducedData[len(rds.reducedData)-2].xData[index][0] for index in range(len(rds.reducedData[len(rds.reducedData)-2].xData)-1) if self.y.values[index] == cl]
                y = [rds.reducedData[len(rds.reducedData) - 2].xData[index][1] for index in
                 range(len(rds.reducedData[len(rds.reducedData) - 2].xData) - 1) if self.y.values[index] == cl]
                plots.append(plt.scatter(x,y))

            plt.title(rds.name +  " 2nd Dimension Reduction Plotted", loc='center')
            plt.legend(plots, self.classList, title="Class",
                       bbox_to_anchor=(-0.3, -0.2, 0.6, 0.1), loc=1,
                       ncol=2, borderaxespad=0.)
            plt.ylabel("Dimension 1")
            plt.xlabel("Dimension 2")
            plt.tight_layout()

            plotWidget = FigureCanvas(plt.gcf())
            widgetList[rds.name + " - (2) Reduction"] = plotWidget
            GraphCount += 1

        for rds in self.reducedDataSets:
            if len(rds.reducedData[len(rds.reducedData)-3].xData) <= 0:
                continue

            fig = plt.figure(GraphCount)
            ax = fig.add_subplot(projection='3d')
            plots = []
            for cl in self.classList:

                x = [rds.reducedData[len(rds.reducedData)-3].xData[index][0] for index in range(len(rds.reducedData[len(rds.reducedData)-3].xData)-1) if self.y.values[index] == cl]
                y = [rds.reducedData[len(rds.reducedData) - 3].xData[index][1] for index in
                 range(len(rds.reducedData[len(rds.reducedData) - 3].xData) - 1) if self.y.values[index] == cl]
                z = [rds.reducedData[len(rds.reducedData) - 3].xData[index][2] for index in
                     range(len(rds.reducedData[len(rds.reducedData) - 3].xData) - 1) if self.y.values[index] == cl]
                plots.append(ax.scatter(x,y,z))

            plt.title(rds.name +  " 3nd Dimension Reduction Plotted", loc='center')
            plt.legend(plots, self.classList, title="Class",
                       bbox_to_anchor=(-0.3, -0.2, 0.6, 0.1), loc=1,
                       ncol=2, borderaxespad=0.)
            ax.set_ylabel("Dimension 1")
            ax.set_xlabel("Dimension 2")
            ax.set_zlabel("Dimension 3")
            plt.tight_layout()

            plotWidget = FigureCanvas(plt.gcf())
            widgetList[rds.name + " - (3) Reduction"] = plotWidget
            GraphCount += 1


        return widgetList