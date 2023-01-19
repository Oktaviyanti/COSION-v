from django.conf import settings

import cv2
import inspect
import math
import matplotlib
matplotlib.use('TkAgg')
import numpy as np
import os

from matplotlib import pyplot as plt
from scipy import ndimage, signal
from skimage import (
    img_as_float,
    img_as_ubyte,
    io,
    measure,
    morphology,
    segmentation,
)
from time import process_time

def visual_callback_2d(background, fig=None):
    """
    Returns a callback than can be passed as the argument `iter_callback`
    of `morphological_geodesic_active_contour` and
    `morphological_chan_vese` for visualizing the evolution
    of the levelsets. Only works for 2D images.

    Parameters
    ----------
    background : (M, N) array
        Image to be plotted as the background of the visual evolution.
    fig : matplotlib.figure.Figure
        Figure where results will be drawn. If not given, a new figure
        will be created.

    Returns
    -------
    callback : Python function
        A function that receives a levelset and updates the current plot
        accordingly. This can be passed as the `iter_callback` argument of
        `morphological_geodesic_active_contour` and
        `morphological_chan_vese`.

    """

    # Prepare the visual environment.
    if fig is None:
        visual_callback_2d.fig = plt.figure()
    visual_callback_2d.fig.clf()
    visual_callback_2d.ax1 = visual_callback_2d.fig.add_subplot(1, 2, 1)
    visual_callback_2d.ax1.imshow(background, cmap=plt.cm.gray)

    ax2 = visual_callback_2d.fig.add_subplot(1, 2, 2)
    ax_u = ax2.imshow(np.zeros_like(background), vmin=0, vmax=1, cmap=plt.cm.gray)
    plt.pause(0.1)

    def callback(levelset):

        if visual_callback_2d.ax1.collections:
            del visual_callback_2d.ax1.collections[0]
        visual_callback_2d.ax1.contour(levelset, [0.5], colors='r')
        ax_u.set_data(levelset)
        visual_callback_2d.fig.canvas.draw()
        plt.pause(0.1)

    return callback

# Function
def img2graydouble(image):
    _,_,c = image.shape
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # image.astype(float)
    return image

def estructurant(radius):
    kernel = np.zeros((2*radius+1, 2*radius+1) ,np.uint8)
    y,x = np.ogrid[-radius:radius+1, -radius:radius+1]
    mask = x**2 + y**2 <= radius**2
    kernel[mask] = 1
    kernel[0,radius-1:kernel.shape[1]-radius+1] = 1
    kernel[kernel.shape[0]-1,radius-1:kernel.shape[1]-radius+1]= 1
    kernel[radius-1:kernel.shape[0]-radius+1,0] = 1
    kernel[radius-1:kernel.shape[0]-radius+1,kernel.shape[1]-1] = 1
    return kernel

def matlab_style_gauss2D(shape=(3,3),sigma=0.5):
    """
    2D gaussian mask - should give the same result as MATLAB's
    fspecial('gaussian',[shape],[sigma])
    """
    m,n = [(ss-1.)/2. for ss in shape]
    y,x = np.ogrid[-m:m+1,-n:n+1]
    h = np.exp( -(x*x + y*y) / (2.*sigma*sigma) )
    h[ h < np.finfo(h.dtype).eps*h.max() ] = 0
    sumh = h.sum()
    if sumh != 0:
        h /= sumh
    return h

def initLS(image):
    height,width = image.shape
    height = float(height)
    width = float(width)
    yy , xx = np.mgrid[0:height,0:width]
    x = float(math.floor(width/2))
    y = float(math.floor(height/2))
    r = float(math.floor(min(.2*width, .2*height)))
    phi0 = (np.sqrt(((xx - x)**2 + (yy - y)**2 ))-r)
    phi0 = np.sign(phi0)*2
    return phi0

def Neumann(phi):
    nrow , ncol = phi.shape
    nrow -=1
    ncol -=1
    g = phi
    (g[0,0],g[0,ncol],g[nrow,0],g[nrow,ncol]) = (g[2,2],g[2,ncol-3],g[nrow-3,2],g[nrow-3,ncol-3])
    (g[0,1:-1],g[nrow,1:-1]) = (g[2,1:-1],g[nrow-3,1:-1])
    (g[1:-1,1],g[1:-1,ncol]) = (g[1:-1,2],g[1:-1,ncol-3])
    return g

def Curvature(phi):
    ny , nx = np.gradient(phi)
    absR = np.sqrt((nx**2)+(ny**2))
    absR = absR + (absR==0)*np.finfo(float).eps
    _,nxx1 = np.gradient(nx/absR)
    nyy1,_ = np.gradient(ny/absR)
    Kappa = nxx1 + nyy1
    return (Kappa , absR)

def Heaviside(phi):
    H = (1/np.pi)*np.arctan(phi)+0.5
    return H

def Dirac(phi):
    a = 1 + phi**2
    D = (1/np.pi)
    Dir = D/a
    return Dir

def FittingAverage(img, phi):
    Hphi = Heaviside(phi)
    cHphi = 1-Hphi
    ca = np.sum(np.multiply(img,Hphi))
    cb = np.sum(np.multiply(img,cHphi))
    c1 = ca/(np.sum(Hphi))
    c2 = cb/(np.sum(cHphi))
    
    global local_vars
    local_vars = inspect.currentframe().f_locals
    return (c1,c2)

def Convergence(phi,iteration=0,absR=0,teta=0.1,maxs=50, preArea= 0, preLength = 0):
    phip = np.where(phi<0, 1, 0)
    Area = np.sum(phip)
    ErrorArea = abs(Area-preArea)
    dPhi = Dirac(phi)
    Length = np.sum(absR*dPhi)
    ErrorLength = abs(Length-preLength)
    if (ErrorArea <= teta) and (ErrorLength <= teta) or (iteration==maxs):
        Converge = True
    else:
        Converge = False
    return (Converge,Area,Length,ErrorArea,ErrorLength)

# Global Parameter
local_vars = {}
maxs = 150
dt = 5
teta = 1
seMorf = morphology.disk(1)
kernel = matlab_style_gauss2D((3,3),1)

class Segmentation:
    config = None
    filename = None

    def __init__(self, base, name):
        if not self.config:
            self.config = settings.MEDIA_ROOT
        
        if not self.filename:
            self.filename = name
        
        self.base = base
        self.name = name
        self.information = []
    
    def __ObDetection(self, img, phi):
        g = np.where(phi <= 0, 1, 0)
        se = estructurant(2)
        g1 = img_as_ubyte(g)
        opening = cv2.morphologyEx(g1, cv2.MORPH_OPEN, se)
        clearObj = segmentation.clear_border(opening)
        fillObj = ndimage.binary_fill_holes(clearObj)
        labelObj = measure.label(fillObj)
        propObj = measure.regionprops(labelObj)

        BW = propObj
        maskBW = np.zeros(self.image.shape, dtype=np.uint8)
        area = []

        for region in (propObj):
            area.append(region.minor_axis_length)

        for region in (propObj):
            if(region.minor_axis_length/max(area)) >= 0.7:
                print(region.minor_axis_length)
                minr, minc, maxr, maxc = region.bbox
                cv2.rectangle(maskBW, (minc, minr), (maxc, maxr), (255, 255, 255, -1))
                cv2.rectangle(self.imgResult, (minc-20, minr-20), (maxc+20, maxr+20), (0, 255, 0), 2)
                cv2.putText(self.imgResult, "Area : " + str(int(region.area)), (minc, minr-30), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 255, 0), 1)

                self.information.append({
                    "name": self.filename,
                    "area": region.area,
                    "bbox_area": region.bbox_area,
                    "convex_area": region.convex_area,
                    "primeter": round(region.perimeter, 2),
                    "orientation": round(region.orientation, 2),
                    "major_axis_length": round(region.major_axis_length, 2),
                    "minor_axis_length": round(region.minor_axis_length, 2),
                    "eccentricity": round(region.eccentricity, 2),
                    "equivalent_diameter": round(region.equivalent_diameter, 2),
                    "bbox": region.bbox,
                    "centroid": region.centroid,
                    "coords": region.coords
                })
        g = fillObj
        phi = -2*maskBW+1
        init = 0
        return (phi, g, init)
    
    def __segmentation(self):
        print("LOKASI ", self.lokasi, "IMAGE ", self.image, "RESULT ", self.imgResult)

        # RGB2GRAY
        # image = self.image

        # # Init LS
        # phi = self.phi

        # Initial Allpcation
        height, width = self.image.shape
        g = np.zeros((height,width))
        error = np.zeros((2,1))
        Beta = np.zeros((1,1))
        preLength = 0
        preArea = 0
        beta = 0
        i = 1
        callback = visual_callback_2d(self.image)

        waktu = []

        time = process_time()
        while i >= 0:
            # Beta[i-1] = beta
            phi = Neumann(self.phi)

            div, absR = Curvature(phi)
            c1, c2 = FittingAverage(self.image, phi)
            
            # AACMR
            AACMR = div*absR + (1-abs(beta)) * (self.image - (c1+c2)/2) + beta*g*absR
            phi = phi + dt * AACMR

            # Binary Gaussian
            phi = np.sign(phi)
            phi = signal.convolve2d(phi, kernel, mode='same')

            # Morph Regularization
            phi = np.where(phi > 0, 1, 0)
            phi2 = img_as_ubyte(phi)

            phi = morphology.dilation((morphology.erosion(phi,seMorf)), seMorf)
            phi2 = cv2.dilate((cv2.erode(phi2,seMorf)), seMorf)
            phi = morphology.erosion((morphology.dilation(phi,seMorf)),seMorf)
            phi2 = cv2.erode(cv2.dilate(phi2,seMorf),seMorf)
            phi = (np.where(phi > 0, 1, -1)).astype(float)

            if beta == 0:
                Converge, preArea, preLength, ErrorArea, ErrorLength = Convergence(phi, iteration=i, absR=absR, teta=teta, preArea=preArea, preLength=preLength)
                if Converge:
                    phiShrink, gShrink, initialShrink = self.__ObDetection(self.image,phi)
                    g = 1-gShrink
                    phi = phiShrink
                    beta = 1
            else:
                callback(phi)
                phiShrink = phi
                Converge, preArea, preLength, ErrorArea, ErrorLength = Convergence(phi, iteration=1, absR=absR, teta=teta, preArea=preArea, preLength=preLength)
                if Converge:
                    break
                g = 1-gShrink
                phi = phiShrink
        extent = visual_callback_2d.ax1.get_window_extent().transformed(visual_callback_2d.fig.dpi_scale_trans.inverted())
        plt.savefig(os.path.join(self.config, "output_" + self.filename), bbox_inches=extent, dpi=300, quality=95)
        time = process_time() - time
        self.information.append({
            "reslt": '/media/output_' + self.filename
        })
        return self.information
    
    @property
    def lokasi(self):
        return os.path.join(self.base, self.name)
    
    @property
    def image(self):
        image = cv2.imread(self.lokasi)
        # RGB2GRAY
        image = img2graydouble(image)
        cv2.imshow("Image", image)
        # GT_image = io.imread((self.lokasi), as_gray=True)
        image = img_as_float(image)
        image *= 255
        return image
    
    @property
    def phi(self):
        # Init LS
        phi = initLS(self.image)
        return phi
    
    @property
    def imgResult(self):
        return self.image.copy()

        # image = img2graydouble(image)
    
    def result(self):
        return self.__segmentation()