# -*- coding: utf-8 -*-
"""
Created on Fri Nov  2 15:27:10 2018

@author: Yasmin Kamel
"""
import sys
import os
import cv2
import numpy as np
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtGui
import pandas as pd
import math

class RecordVideo(QtCore.QObject):
    image_data = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, mainWidget, parent=None):
        super().__init__(parent)
        
        self.mainWidget = mainWidget
        self.timer = QtCore.QBasicTimer()

    def start_recording(self):
        self.timer.start(0, self)
        self.camera = cv2.VideoCapture(0)
        self.mainWidget.openCameraBtn.setVisible(False)
        self.mainWidget.captureBtn.setVisible(True)
        self.mainWidget.photoCountText.setVisible(True)
        self.mainWidget.captureBtn.setEnabled(True)
        self.mainWidget.face_detection_widget.setVisible(True)
        self.mainWidget.mainWindow.setFixedSize(QtCore.QSize(830, 600))

    def timerEvent(self, event):
        if (event.timerId() != self.timer.timerId()):
            return

        read, data = self.camera.read()
        if read:
            self.image_data.emit(data)


class FaceDetectionWidget(QtWidgets.QWidget):
    def __init__(self, haar_cascade_filepath, main_widget, parent=None):
        super().__init__(parent)
        self.main_widget = main_widget
        self.classifier = cv2.CascadeClassifier(haar_cascade_filepath)
        self.image = QtGui.QImage()
        self._green = (0, 255,0)
        self._width = 2
        self._min_size = (30, 30)

    def detect_faces(self, image: np.ndarray):
        # haarclassifiers work better in black and white
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray_image = cv2.equalizeHist(gray_image)

        faces = self.classifier.detectMultiScale(gray_image,
                                                 scaleFactor=1.3,
                                                 minNeighbors=4,
                                                 flags=cv2.CASCADE_SCALE_IMAGE,
                                                 minSize=self._min_size)

        return faces

    def image_data_slot(self, image_data):
        faces = self.detect_faces(image_data)
        
        for (x, y, w, h) in faces:
            cv2.rectangle(image_data,
                          (x, y),
                          (x+w, y+h),
                          self._green,
                          self._width)

        self.image = self.get_qimage(image_data)
        if self.image.size() != self.size():
            self.setFixedSize(self.image.size())

        self.update()

    def get_qimage(self, image: np.ndarray):
        height, width, colors = image.shape
        bytesPerLine = 3 * width
        QImage = QtGui.QImage

        image = QImage(image.data,
                       width,
                       height,
                       bytesPerLine,
                       QImage.Format_RGB888)

        image = image.rgbSwapped()
        return image

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawImage(0, 0, self.image)
        self.image = QtGui.QImage()


class MainWidget(QtWidgets.QWidget):
    def __init__(self, haarcascade_filepath, mainWindow, parent=None):
        super().__init__(parent)
        self.mainWindow = mainWindow
        self.dataFileName = 'employees.csv'
        
        fp = haarcascade_filepath
        self.face_detection_widget = FaceDetectionWidget(fp, self)
        
        self.record_video = RecordVideo(self)

        image_data_slot = self.face_detection_widget.image_data_slot
        self.record_video.image_data.connect(image_data_slot)

        layout = QtWidgets.QGridLayout(self)    

        self.title = QtWidgets.QLabel("Enter the name", self) 
        self.title.setAlignment(QtCore.Qt.AlignLeft)
        layout.addWidget(self.title,0,0)
        
        self.nameText = QtWidgets.QLineEdit(self)
        self.nameText.textChanged.connect(self.disableButton)
        layout.addWidget(self.nameText,0,1)
        
        self.photoTitle = QtWidgets.QLabel("Take 10 photos", self) 
        self.photoTitle.setAlignment(QtCore.Qt.AlignLeft)
        self.photoTitle.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.photoTitle,1,0)

        layout.addWidget(self.face_detection_widget)
        self.openCameraBtn = QtWidgets.QPushButton('Open Camera')
        layout.addWidget(self.openCameraBtn,1,2)

        self.openCameraBtn.clicked.connect(self.record_video.start_recording)
        
        self.captureBtn = QtWidgets.QPushButton("Capture")
        self.captureBtn.setVisible(False)
        self.captureBtn.clicked.connect(self.photoCapture)
        self.photoCount = 0
        self.employeeId = read_last_id(self.dataFileName) + 1
        layout.addWidget(self.captureBtn, 1, 2)
        
        self.photoCountText = QtWidgets.QLabel(np.str(self.photoCount), self)
        self.photoCountText.setVisible(False)
        layout.addWidget(self.photoCountText, 1, 3)
        
        self.saveBtn = QtWidgets.QPushButton("Save")
        self.saveBtn.setEnabled(False)
        self.saveBtn.clicked.connect(self.save)
        layout.addWidget(self.saveBtn, 2, 1)
        
        self.setLayout(layout)
    
    def photoCapture(self):
        self.photoCount += 1;
        self.photoCountText.setText(np.str(self.photoCount))
        return_value, image = self.record_video.camera.read()
        directory = os.path.abspath(os.path.join(os.path.curdir))
        self.directoryFolder = directory +"/images/"+np.str(self.employeeId)
        if not os.path.exists(self.directoryFolder):
            os.makedirs(self.directoryFolder)
        path_image = self.directoryFolder+'/'+np.str(self.photoCount)+'_'+np.str(self.employeeId)+".png" 
        cv2.imwrite(path_image, image)
        
        if self.photoCount == 10:
            self.captureBtn.setEnabled(False)
        self.disableButton()
    
    def disableButton(self):
        if len(self.nameText.text()) > 0 and self.photoCount == 10:
            self.saveBtn.setEnabled(True)
        else:
            self.saveBtn.setEnabled(False)
    
    def save(self):
        ds = pd.read_csv(self.dataFileName)
        length = len(ds)
        ds.loc[length] =[self.nameText.text(),self.employeeId,self.directoryFolder]
        ds.to_csv(self.dataFileName,index=False)
        self.newRegister()
        
    def newRegister(self):
        self.nameText.setText('')
        self.photoCount = 0
        self.openCameraBtn.setVisible(True)
        self.captureBtn.setVisible(False)
        self.face_detection_widget.setVisible(False)
        self.record_video.camera.release()
        self.photoCountText.setVisible(False)
        self.captureBtn.setEnabled(True)
        self.mainWindow.setFixedSize(QtCore.QSize(500, 150))
        self.photoCountText.setText(np.str(self.photoCount))
        self.employeeId = read_last_id(self.dataFileName) + 1

def read_last_id(file_name):
    df = pd.read_csv(file_name)
    last_index = df.Id
    count=last_index.max()
    if not math.isnan(count): 
        return count
    else:
        count = 0
        return count

def check_dir(file_name):
    exist= os.path.isfile(file_name)
    if not exist:
        df = pd.DataFrame()
        init_data = {'Name':[], 'Id':[], 'Path':[]}
        df = pd.DataFrame(init_data, columns = ['Name', 'Id', 'Path'])
        df.to_csv(file_name,index=False)
        df
 
def main(haar_cascade_filepath):
    app = QtWidgets.QApplication(sys.argv)

    check_dir('employees.csv')
    
    main_window = QtWidgets.QMainWindow()
   
    main_window.setFixedSize(QtCore.QSize(500, 150))
    main_widget = MainWidget(haar_cascade_filepath, main_window)
    
    menu1 = main_window.menuBar().addMenu('New')
    action1 = menu1.addAction('New Employee')
    action1.triggered.connect(main_widget.newRegister)
        
    menu2 = main_window.menuBar().addMenu('Quit')
    action2 = menu2.addAction('Quit')
    action2.triggered.connect(QtWidgets.QApplication.quit)
    
    main_window.setWindowTitle("Face Base Attendance System") 
    
    main_window.setCentralWidget(main_widget)
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.realpath(__file__))
    cascade_filepath = os.path.join(script_dir,
                                 'haarcascade_frontalface_default.xml')

    cascade_filepath = os.path.abspath(cascade_filepath)
    main(cascade_filepath)