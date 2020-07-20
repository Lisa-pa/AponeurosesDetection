"""Main module."""

"*****************************************************************************"
"**********************************PACKAGES***********************************"
"*****************************************************************************"

import math as m
import cv2
import numpy as np
from skimage.transform import radon, iradon
import tkinter as tk
from tkinter.filedialog import askopenfilename

"*****************************************************************************"
"*********************************FUNCTIONS***********************************"
"*****************************************************************************"

def d2_gaussianMasks(s):
    """Implements Gaussian's second derivatives masks for a given standard
    deviation s.
    The masks' size is set as 6*s rounded to the superior integer (+1 if even).

    Args:
        s (double) : standard deviation

    Returns:
        mask_xx, mask_xy, mask_yy (array_like): masks obtained from derivation of a gaussian,
        according to x and x, to x and y, to y and y respectively.

    """
    
    'Calculation of the size of the masks'
    size = m.ceil(s*6)
    if size%2==0: #if size if even, make it odd
        size+=1
        
    half =  m.floor(size/2)
    mask_xx = np.zeros((size,size))
    mask_xy = np.zeros((size,size))
    mask_yy = np.zeros((size,size))

    'Second derivatives expressions'
    for x in range (-half, half +1):
        for y in range (-half, half +1):

            mask_xx[x + half][y + half] = (x**2/s**2-1.)/(2.*m.pi*s**4)\
                                                *m.exp(-(x**2+y**2)/(2.*s**2))
                                                
            mask_xy[x + half][y + half] = x*y/(2.*m.pi*s**6)\
                                                *m.exp(-(x**2+y**2)/(2.*s**2))
                                                
            mask_yy[x + half][y + half] = (y**2/s**2-1.)/(2.*m.pi*s**4)\
                                                *m.exp(-(x**2+y**2)/(2.*s**2))
    return mask_xx, mask_xy, mask_yy

'-----------------------------------------------------------------------------'

def MVEF_2D(I, scales, thresholds):
    """Multiscale Vessel Enhancement Method for 2D images - based on Frangi's,
    Rana's, and Jalborg's works.
    I is a grayscale image. thresholds is a list of two thresholds that 
    control the sensitivity of the line filter to the measures Fr and R.  
    scales is a list of lengths that correspond to the diameter of the 
    tube-like structure the operator wants to find"""
    
    vesselness = np.zeros((I.shape[0], I.shape[1], len(scales)))
    I2 = np.zeros((I.shape[0], I.shape[1]))
    
    for sc in range(len(scales)):    

        'Calculation of the Hessian matrix coefficients'
        mask_xx = cv2.flip(d2_gaussianMasks(scales[sc])[0],flipCode = -1)
        mask_xy = cv2.flip(d2_gaussianMasks(scales[sc])[1],flipCode = -1)
        mask_yy = cv2.flip(d2_gaussianMasks(scales[sc])[2],flipCode = -1)
        
        hessian_xx = cv2.filter2D(I, -1, mask_xx, anchor = (-1,-1))  
        hessian_xy = cv2.filter2D(I, -1, mask_xy, anchor = (-1,-1))
        hessian_yy = cv2.filter2D(I, -1, mask_yy, anchor = (-1,-1))
        
#        cv2.imshow('maskx',hessian_xx);
#        cv2.imshow('maskxy',hessian_xy);
#        cv2.imshow('masky',hessian_yy);
#        cv2.waitKey(0) & 0xFF;
#        cv2.destroyAllWindows();
        
        for i in range(I.shape[0]):
            for j in range(I.shape[1]):
           
                'For each pixel, find and order the eigenvalues of the '
                'Hessian matrix'
                H = np.array([[hessian_xx[i,j], hessian_xy[i,j]],\
                              [hessian_xy[i,j], hessian_yy[i,j]]])
                eigvals, eigvects = np.linalg.eig(H)
                #reordering eigenvalues in increasing order if needed:
                if abs(eigvals[0])>abs(eigvals[1]):
                    eigvals[0], eigvals[1] = eigvals[1], eigvals[0]
                    eigvects[:,0],eigvects[:,1] = eigvects[:,1], eigvects[:,0]
                
                'Calculation of vesselness: looking for a POSITIVE highest'
                'eigenvalue <=> looking for dark tube-like structures; looking'
                'for a NEGATIVE highest eigen value <=> looking for bright'
                'tube-like structures'
                #bright tube-like structures search did not work so the 
                #temporary solution is to inverse the ultrasound image 
                #and search for dark tube-like structures
                if eigvals[1]<=0:
                    vesselness[i,j,sc] = 0

                if eigvals[1]>0:
                    
                    'ratio - for second order ellipsoid'
                    R = eigvals[0]/eigvals[1]

                    'Frobenius norm - for second order structureness'
                    Fr = m.sqrt(eigvals[0]*eigvals[0] + eigvals[1]*eigvals[1])

                    b = thresholds[0]
                    c = thresholds[1]
                    vesselness[i,j,sc]=scales[sc]*m.exp(-R*R/(2.*b*b))*(1.-m.exp(-Fr*Fr/(2*c*c)))

    'Keep the highest value of vesselness across all scales'
    for ind1 in range(I2.shape[0]):
        for ind2 in range(I2.shape[1]):
            I2[ind1,ind2] = np.max(vesselness[ind1,ind2,:])

    return I2, vesselness, hessian_xy, hessian_xx, hessian_yy
'-----------------------------------------------------------------------------'
def apoLocation(I, thresh):
    """Function that does segmentation on radon transform of image I
    to detect the two aponeuroses as the two largest white lines.
    It returns the inverse transform of the segmented radon transform as
    well as location of two horizontal bands containing aponeuroses
    
    Args:
        I (array): one canal image
        thresh: threshold used for segmentation. In the radon transform, all
        pixels where value > thresh are kept, so that to keep only whiter areas
        and remove gray areas.
    
    Returns:
        I_reconstructed (array): array of same size than I, where the lines detected
        equal 1, otherwise pixels equal 0.
        loc1 (tuple): indicates two lines (distant of 50 pixels) of I between 
        which the upper aponeurosis is.
        loc2 (tuple): indicates two lines (distant of 50 pixels) of I between 
        which the lower aponeurosis is.
    """

    if len(I.shape) > 2:
        I = cv2.cvtColor(I, cv2.COLOR_RGB2GRAY)
        

    #working with a square because radon function working on a circle only
    if I.shape[0] != I.shape[1]:
        mini = np.min(I.shape)
        I = I[0:mini,0:mini]
        
    I_radon = radon(I, circle = True)
    I_radon2 = I_radon/np.max(I_radon)*255 #spreading values between 0 and 255 to enhance white points
    I_radon3 = cv2.threshold(I_radon2, thresh, 255, cv2.THRESH_BINARY)[1].astype(np.uint8) #keeping whitest regions

    contours = cv2.findContours(I_radon3,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)[0] #find white regions
    contours_tuples = [(i, contours[i][:,0,:], contours[i].size) for i in range(len(contours))]

    if len(contours_tuples)<2:
        raise TypeError('Less than two aponeuroses have been located. Try a lower threshold for binarization.')
    elif len(contours_tuples)>2: #remove smaller white points, that do not correspond to aponeuroses
        contours_tuples.sort(key=lambda contours: contours[2])
        for x in range(len(contours_tuples)-2):
            #change smaller white points into black points
            center, radius = cv2.minEnclosingCircle(contours_tuples[x][1])
            cv2.circle(I_radon3, (int(center[0]), int(center[1])), int(np.ceil(radius)+1), 0, thickness=cv2.FILLED, lineType=8, shift=0)
    
    I_reconstructed = (iradon(I_radon3)>0)*255.   
    
    #find locations of aponeuroses
    j=0
    while I_reconstructed[j,int(I_reconstructed.shape[1]/2)]==0:
        j = j+1
    upLine1 = max(0, j-20)
    
    j=0
    while I_reconstructed[I_reconstructed.shape[0]-1-j,int(I_reconstructed.shape[1]/2)]==0:
        j=j+1
    downLine2 = min(I_reconstructed.shape[0]-1-j + 20, I_reconstructed.shape[0])
    
    loc1 = (upLine1,upLine1+50)
    loc2 = (downLine2-50,downLine2)  
  
    return I_reconstructed, loc1, loc2

"*****************************************************************************"
"*********************************TEST****************************************"
"*****************************************************************************"
image = cv2.imread('skmuscle.jpg', -1)
imageG = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)  

aponeuroses_Linear, apon1, apon2 = apoLocation(image, 220.)

#color in green to see what has been spotted
for x in range(aponeuroses_Linear.shape[0]):
    for y in range(aponeuroses_Linear.shape[1]):
        if aponeuroses_Linear[x,y] >0:
            image[x,y,:] = [0,255,0]

#cv2.imwrite('Radon_cropped_Kevin_jamon_20181002_153734_image.jpg', image);
cv2.imshow('image ini',image)
cv2.imshow('Trasnformed I',aponeuroses_Linear)
cv2.imshow('apo1', image[apon1[0]:apon1[1],:])
cv2.imshow('apo2', image[apon2[0]:apon2[1],:])
cv2.waitKey(0) & 0xFF
cv2.destroyAllWindows()


"*****************************************************************************"
"*****************************************************************************"
"*****************************************************************************"