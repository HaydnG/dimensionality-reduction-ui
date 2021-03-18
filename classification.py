from sklearn import neighbors, ensemble, pipeline, preprocessing, svm, linear_model, naive_bayes
from sklearn import metrics
from timeit import default_timer as timer


class ClassificationMethod:
    def __init__(self, name, method):
        self.name = name
        self.method = method
        self.enabled = True

    def execute(self, xTrainingData, xTestData, yTrainingData, yTestData):
        start = timer()
        yTestPredictedData = self.method(xTrainingData, xTestData, yTrainingData, yTestData)
        end = timer()



        return metrics.accuracy_score(yTestData, yTestPredictedData), (end - start) * 1000


classificationAlgorithms: ClassificationMethod = []


classificationAlgorithms.append(ClassificationMethod("KNeighbors",
                                           lambda xTrainingData, xTestData, yTrainingData, yTestData:
                                           neighbors.KNeighborsClassifier().fit(xTrainingData, yTrainingData).predict(xTestData)))

classificationAlgorithms.append(ClassificationMethod("RandomForests",
                                           lambda xTrainingData, xTestData, yTrainingData, yTestData:
                                           ensemble.RandomForestClassifier(max_depth=2, random_state=0).fit(xTrainingData, yTrainingData).predict(xTestData)))

classificationAlgorithms.append(ClassificationMethod("SVM",
                                           lambda xTrainingData, xTestData, yTrainingData, yTestData:
                                           pipeline.make_pipeline(preprocessing.StandardScaler(), svm.SVC(gamma='auto')).fit(xTrainingData, yTrainingData).predict(xTestData)))

classificationAlgorithms.append(ClassificationMethod("LogisticRegression",
                                           lambda xTrainingData, xTestData, yTrainingData, yTestData:
                                           linear_model.LogisticRegression(random_state=0).fit(xTrainingData, yTrainingData).predict(xTestData)))

classificationAlgorithms.append(ClassificationMethod("NaiveBayes",
                                           lambda xTrainingData, xTestData, yTrainingData, yTestData:
                                           naive_bayes.GaussianNB().fit(xTrainingData, yTrainingData).predict(xTestData)))

