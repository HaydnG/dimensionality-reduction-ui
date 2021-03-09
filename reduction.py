from sklearn.manifold import LocallyLinearEmbedding, Isomap
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.model_selection import train_test_split
from sklearn import preprocessing
from timeit import default_timer as timer

testDataPercent = 0.33
selectionSeed = 3

def prepareData(x, y):
    return train_test_split(x, y, test_size=testDataPercent,random_state=selectionSeed)  ##random_state=2 data seed

class ReductionMethod:
    def __init__(self, capByClasses, name, method):
        self.name = name
        self.method = method
        self.capByClasses = capByClasses
        self.enabled = True

    def execute(self, dimension, x, y, dataset):
        x = x.values
        y = y.values

        start = timer()
        reducedData = self.method(dimension, x, y)
        end = timer()

        xTrainingData, xTestData, dataset.yTrainingData, dataset.yTestData = prepareData(reducedData, y)

        xTrainingData = preprocessing.scale(xTrainingData)
        xTestData = preprocessing.scale(xTestData)

        return dataset.addReducedData(reducedData, xTrainingData, xTestData, dimension, (end - start) * 1000)




reductionAlgorithms: ReductionMethod = []




reductionAlgorithms.append(ReductionMethod(False, "LLE",
                                           lambda dimensions, x, y:
                                           LocallyLinearEmbedding(n_components=dimensions, eigen_solver='arpack').fit_transform(x)))

reductionAlgorithms.append(ReductionMethod(True, "LDA",
                                           lambda dimensions, x, y:
                                           LDA(n_components=dimensions).fit_transform(x, y)))

reductionAlgorithms.append(ReductionMethod(False, "Isomap",
                                           lambda dimensions, x, y:
                                           Isomap(n_components=dimensions).fit_transform(x)))


