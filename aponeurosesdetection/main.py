from calibration.calib import autoCalibration
from preprocessing.cropping import autocropping
from preprocessing.preprocessing import preprocessingApo
import aponeurosesdetection as apoD
import aponeuroses_contours as apoC

import cv2
import numpy as np
import tkinter.messagebox as tkbox
import tkinter as tk
from PIL import ImageTk, Image
###################################FOR SIMPLE US IMAGES###################################


#Opening the image
RGBimage = cv2.imread('C:/Users/Lisa Paillard/Desktop/AponeurosesDetection/aponeurosesdetection/data/simple_echo.jpg', -1)

#################################################

#Calibrate the image
calibX, calibY = autoCalibration(RGBimage)

#################################################

#Crop the image to keep essential US data
USimage = autocropping(RGBimage, 10., 15., 12., 25., calibY)

#--------ask for validation; if cropping does not suit the user, ask the user for thresholds
ok = False
while ok == False:
    cv2.imshow('Cropped US image', USimage)
    ok = tkbox.askyesno('Need user validation', 'Do you validate the cropping ? If no, we will ask you new thresholds in the command prompt. After clicking yes or no, please close the image window to continue.', default = 'yes', icon='question')
    cv2.waitKey(0) & 0xFF
    cv2.destroyAllWindows()

    if ok == False:
        entry1 = input("Please enter an integer between 0 and 255 for minimum threshold to test for columns' mean. Recommended value is 10: ")
        entry2 = input("Please enter an integer between 0 and 255 for maximum threshold to test for columns' mean. Recommended value is 15: ")
        entry3 = input("Please enter an integer between 0 and 255 for minimum threshold to test for raws' mean. Recommended value is 12.: ")
        entry4 = input("Please enter an integer between 0 and 255 for maximum threshold to test for raws' mean. Recommended value is 25.: ")

        thresh1 = int(entry1)
        thresh2 = int(entry2)
        thresh3 = int(entry3)
        thresh4 = int(entry4)
        print(f'You entered the following thresholds: {thresh1, thresh2, thresh3, thresh4}')
        if thresh1>255 or thresh1<0 or thresh2>255 or thresh2<0 or thresh3>255 or thresh3<0 or\
            thresh4>255 or thresh4<0:
            raise ValueError('All thresholds must be integers between 0 and 255')
        USimage = autocropping(RGBimage, thresh1, thresh2, thresh3, thresh4, calibY)

#################################################

#Locate aponeuroses and find linear approximation of aponeuroses
aponeuroses_Linear, apon1, apon2 = apoD.apoLocation(USimage, 220.)
upperApo = USimage[apon1[0]:apon1[1],:]
lowerApo = USimage[apon2[0]:apon2[1],:]

#################################################

#Pre-process the sub-images of upper and lower aponeuroses
upperApo_pp = preprocessingApo(upperApo, 'localmean', 0, 41)
lowerApo_pp = preprocessingApo(lowerApo, 'localmean', 0, 41)

#################################################

# Get exact contour of each aponeurosis
# First - we ask the user to click on points to get an initial contour
#close to the real boundary of each aponeurosis (faster convergence)
points = []
def _pickCoordinates(event):
    xe = event.x
    ye = event.y
    points.append((ye,xe))
window = tk.Tk()
canvas = tk.Canvas(window, width = upperApo_pp.shape[1], height = upperApo_pp.shape[0])      
canvas.pack()      
displayI = ImageTk.PhotoImage(image = Image.fromarray(upperApo_pp), master = window)     
canvas.create_image(0,0, anchor='nw', image=displayI) 
window.bind('<Button-1>',_pickCoordinates) 
window.mainloop()
points = np.array(points)
print(points)
ini_upApo = apoC.initiateContour(upperApo_pp, typeC = 'set_of_points', setPoints = points)
contourUp,nUp=apoC.activeContour(upperApo_pp,ini_upApo,0.3,0.01,0.02,3.0, 1.0, 1.0, 65.025, 0.10)
contourUpimage, contourPointsUp = apoC.extractContour(contourUp, upperApo)
print('Upper aponeurosis contour found in ', nUp, ' steps')

points = []
window = tk.Tk()
canvas = tk.Canvas(window, width = lowerApo_pp.shape[1], height = lowerApo_pp.shape[0])      
canvas.pack()      
displayI = ImageTk.PhotoImage(image = Image.fromarray(lowerApo_pp), master = window)     
canvas.create_image(0,0, anchor='nw', image=displayI) 
window.bind('<Button-1>',_pickCoordinates) 
window.mainloop()
points = np.array(points)
ini_lowApo = apoC.initiateContour(lowerApo_pp, typeC = 'set_of_points', setPoints = points)
contourLow, nLow = \
    apoC.activeContour(lowerApo_pp, ini_lowApo, 0.5, 0.01, 0.02, 3.0, 1.0, 1.0, 65.025, 0.10)
contourLowimage, contourPointsLow = apoC.extractContour(contourLow, lowerApo)
print('Lower aponeurosis contour found in ', nLow, ' steps')

#################################################

#validation of the contours
#if not validated, linear approximation is used
cv2.imshow('Upper aponeurosis contour', contourUpimage)
cv2.imshow('Lower aponeurosis contour', contourLowimage)
valid = tkbox.askyesno('Need user validation', 'Do you validate the contours ? If no, linear approximation will be used in the rest of the process. After clicking yes or no, please close the image windows to continue.', default = 'yes', icon='question')
cv2.waitKey(0) & 0xFF
cv2.destroyAllWindows()

#################################################
#B-spline to approximate each aponeurosis if contours suited
# '''still in development'''
# imgdenoised= preprocessingapo(image, 'localmean', 0, 51)

###################################FOR PANORAMIC US IMAGES###################################