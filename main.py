# -*- coding: utf-8 -*-
"""
Created on Fri Nov  2 15:27:10 2018

@author: Yasmin Kamel
"""

import sys
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QMainWindow, QLabel, QGridLayout, QWidget
from PyQt5.QtCore import QSize    
import os
import pandas as pd
import cv2
import math
import numpy as np 

class Registration(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
   
        self.dataFileName = 'employees.csv'
    
        self.setFixedSize(QSize(500, 150))
        self.setWindowTitle("Attendance System") 
        
        centralWidget = QWidget(self)          
        self.setCentralWidget(centralWidget)   
 
        gridLayout = QGridLayout(self)     
        centralWidget.setLayout(gridLayout)  
        
        title = QLabel("Enter the name", self) 
        title.setAlignment(QtCore.Qt.AlignLeft)
        gridLayout.addWidget(title, 0, 0)
        
        self.nameText = QtWidgets.QLineEdit(self)
        self.nameText.textChanged.connect(self.disableButton)
        gridLayout.addWidget(self.nameText, 0, 1)
        
        menu1 = self.menuBar().addMenu('New')
        action1 = menu1.addAction('New Employee')
        action1.triggered.connect(self.newRegister)
        
        menu2 = self.menuBar().addMenu('Quit')
        action2 = menu2.addAction('Quit')
        action2.triggered.connect(QtWidgets.QApplication.quit)
        
        self.photoTitle = QLabel("Take 10 photos", self) 
        self.photoTitle.setAlignment(QtCore.Qt.AlignLeft)
        self.photoTitle.setAlignment(QtCore.Qt.AlignCenter)
        gridLayout.addWidget(self.photoTitle, 1, 0)
        
        self.photoLabel = QtWidgets.QLabel(self)
        self.photoLabel.setVisible(False)
        gridLayout.addWidget(self.photoLabel, 1, 1)
        
        self.openCameraBtn = QtWidgets.QPushButton("Open Camera")
        self.openCameraBtn.clicked.connect(self.openCamera)
        gridLayout.addWidget(self.openCameraBtn, 1, 1)
        
        self.captureBtn = QtWidgets.QPushButton("Capture")
        self.captureBtn.setVisible(False)
        self.captureBtn.clicked.connect(self.photoCapture)
        self.photoCount = 0
        self.employeeId = read_last_id(self.dataFileName) + 1
        gridLayout.addWidget(self.captureBtn, 1, 2)
        
        self.photoCountText = QLabel(np.str(self.photoCount), self)
        self.photoCountText.setVisible(False)
        gridLayout.addWidget(self.photoCountText, 1, 3)
        
        self.saveBtn = QtWidgets.QPushButton("Save")
        self.saveBtn.setEnabled(False)
        self.saveBtn.clicked.connect(self.save)
        gridLayout.addWidget(self.saveBtn, 2, 1)
    
    def openCamera(self):
        self.openCameraBtn.setVisible(False)
        self.captureBtn.setVisible(True)
        self.photoLabel.setVisible(True)
        self.photoCountText.setVisible(True)
        self.captureBtn.setEnabled(True)
        self.setFixedSize(QSize(500, 400))
        camera_port = 0
        self.camera = cv2.VideoCapture(camera_port)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(5)
    
    def update_frame(self):
        ret,self.image=self.camera.read()
        self.displayImage(self.image,1)
    
    def displayImage(self,img,window=1):
        qformat=QtGui.QImage.Format_Indexed8
        if len(img.shape)==3:
            if img.shape[2]==4:
                qformat=QtGui.QImage.Format_RGB8888
            else:
                qformat=QtGui.QImage.Format_RGB888
        outImage=QtGui.QImage(img,img.shape[1],img.shape[0],img.strides[0],qformat)

        outImage=outImage.rgbSwapped()
        if window==1:
            self.photoLabel.setPixmap(QtGui.QPixmap.fromImage(outImage))
            self.photoLabel.setScaledContents(True)
    
    def photoCapture(self):
        self.photoCount += 1;
        self.photoCountText.setText(np.str(self.photoCount))
        return_value, image = self.camera.read()
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
        self.photoLabel.setVisible(False)
        self.photoCountText.setVisible(False)
        self.captureBtn.setEnabled(True)
        self.setFixedSize(QSize(500, 150))
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
 
if __name__ == "__main__":
    def run_app():
        check_dir('employees.csv')
        app = QtWidgets.QApplication(sys.argv)
        mainWin = Registration()
        mainWin.show()
        app.exec_()
    run_app()