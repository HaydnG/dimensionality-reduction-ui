import PyQt5
from PyQt5 import QtWidgets, uic


app = QtWidgets.QApplication([])

form = uic.loadUi("menu.ui")

form.show()

def selectFile():
    a = QtWidgets.QFileDialog.getOpenFileName()

    form.filePath.setText(a[0])


form.uploadButton.clicked.connect(selectFile)


app.exec()