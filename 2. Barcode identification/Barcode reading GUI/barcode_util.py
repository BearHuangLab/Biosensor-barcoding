import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import tifffile
import cv2


# For the given path, get the List of all files in the directory tree
def getListOfFiles(dirName):
    # create a list of file and sub directories
    # names in the given directory
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory
        if os.path.isdir(fullPath):
            allFiles = allFiles + getListOfFiles(fullPath)
        else:
            allFiles.append(fullPath)
    return allFiles

# return all paths for all tif files in the barcode folder
def getImgPaths(barcode_dir):
    img_path_list = [i for i in getListOfFiles(barcode_dir) if i.endswith('.tif')]
    img_path_list.sort(key=lambda x: os.path.getmtime(x)) # arrange them by date
    return img_path_list

def get_img_path_list(barcode_dir):
    img_path_list = [i for i in getListOfFiles(barcode_dir) if i.endswith('.tif')]
    img_path_list.sort(key=lambda x: os.path.getmtime(x)) # arrange them by date
    return img_path_list

# read excel and return numpy array with Cell and Position
def read_excel_barcode(file_path):
    df = pd.read_excel(file_path, sheet_name='Position',
                       usecols=['Position', 'Cell'])  # read excel //change sheet and cols if needed!!!!!!!
    df = df[df['Cell'].str.startswith('B')]  # drop cell images without barcode
    df.reset_index(drop=True, inplace=True)  # reset index
    return df


# input barcode (eg B1002), return a list of location
def readbarcode(b):
    barcode = {'0': 'none',
               '1': 'nucleus',
               '2': 'membrane',
               '3': 'nuc_mem',
               '4': 'cytosol'}
    ans = []
    for i in list(b[1:]):
        ans.append(barcode[i])
    return ans


# input barcode plasmid (eg A2B3), return a list of location
def readbarcodeplasmid(A2B3):
    barcode = {'1': 'nucleus',
               '2': 'membrane',
               '3': 'nuc_mem',
               '4': 'cytosol'}
    channel = {'A': 0, 'B': 1, 'C': 2, 'D': 3}

    ans = ['none', 'none', 'none', 'none']
    ans[channel[A2B3[0]]] = barcode[A2B3[1]]
    ans[channel[A2B3[2]]] = barcode[A2B3[3]]
    return ans


# input barcode plasmid (eg A2B3), return its barcode (eg B2300)
def readbarcodeplasmid2(A2B3):
    barcode = {'1': 'nucleus',
               '2': 'membrane',
               '3': 'nuc_mem',
               '4': 'cytosol'}
    channel = {'A': 0, 'B': 1, 'C': 2, 'D': 3}

    ans = list('0000')
    ans[channel[A2B3[0]]] = A2B3[1]
    ans[channel[A2B3[2]]] = A2B3[3]
    return 'B' + ''.join(ans)

# normalize image to [0, 255]
def normalize(image):
    image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    return image


# normalize to [0, 255], set limit for outlier (default 99.9%)
def normalize_saturate_outlier(image, percentile=99.9):
    upperlimit = np.percentile(image, percentile)
    lowerlimit = np.percentile(image, 100 - percentile)
    image = np.minimum(upperlimit, image)
    image = np.maximum(lowerlimit, image)
    return normalize(image)


# mutual exclusion for two images
def mutual_exclusive(img1, img2):
    rows, cols = img1.shape
    for row in range(rows):
        for col in range(cols):
            if img1[row][col] > img2[row][col]:
                img2[row][col] = 0
            else:
                img1[row][col] = 0
    return img1, img2


def mutual_exclusive_for_3(img1, img2, img3):
    rows, cols = img1.shape
    for row in range(rows):
        for col in range(cols):
            px1 = img1[row][col]
            px2 = img2[row][col]
            px3 = img3[row][col]
            if px1 > px2 and px1 > px3:
                img2[row][col] = 0
                img3[row][col] = 0
            elif px2 > px1 and px2 > px3:
                img1[row][col] = 0
                img3[row][col] = 0
            elif px3 > px2 and px3 > px1:
                img2[row][col] = 0
                img1[row][col] = 0
    return img1, img2, img3


def mutual_exclusive_for_3_new(img1, img2, img3):
    # new comparison, run mutual_exclusive(min(img2, img3), img1) -> then mutual_exclusive(img2, img3)
    rows, cols = img1.shape
    for row in range(rows):
        for col in range(cols):
            px1 = img1[row][col]
            px2 = img2[row][col]
            px3 = img3[row][col]
            if px1 > px2 and px1 > px3:
                img2[row][col] = 0
                img3[row][col] = 0
            elif px2 > px3:
                if px1 > px3:
                    img3[row][col] = 0
                else:
                    img1[row][col] = 0
                    img3[row][col] = 0
            else:
                if px1 > px2:
                    img2[row][col] = 0
                else:
                    img1[row][col] = 0
                    img2[row][col] = 0

    return img1, img2, img3

def crop_1x4(img):
    #crop images according to barcode ABCD
    y, x = img.shape
    A = img[0:, 0:int(x/4)]
    B = img[0:, int(x/4):int(x/2)]
    C = img[0:, int(x/2): int(3*x/4)]
    D = img[0:, int(3*x/4): x]
    return A, B, C, D


# crop an input barcode image path and return a list of four images (A=BFP, B=TagRFP, C=mCardinal, D=iRFP)
def crop_barcode_image(img_path, blur = False, me3 = True, channel = 'single', nrows = 150, ncols = 150):

    # read 16 bit grayscale image
    img = cv2.imread(img_path, cv2.IMREAD_ANYDEPTH)

    #crop img
    A, B, C, D = crop_1x4(img)

    # blur or not
    if blur == True:
        A = cv2.blur(A, (3,3))
        B = cv2.blur(B, (3,3))
        C = cv2.blur(C, (3,3))
        D = cv2.blur(D, (3,3))

    # mutual exclusive (bleedthrough control)
    if me3 is True:
        A, B, C = mutual_exclusive_for_3(A,B,C)
    else: 
        A, B, C = mutual_exclusive_for_3_new(A,B,C)

    # normalize the histogram
    A = normalize_saturate_outlier(A)
    B = normalize_saturate_outlier(B)
    C = normalize_saturate_outlier(C)
    D = normalize_saturate_outlier(D)

    # resize to 150x150 pixel
    A = cv2.resize(A, (nrows, ncols), interpolation=cv2.INTER_CUBIC)
    B = cv2.resize(B, (nrows, ncols), interpolation=cv2.INTER_CUBIC)
    C = cv2.resize(C, (nrows, ncols), interpolation=cv2.INTER_CUBIC)
    D = cv2.resize(D, (nrows, ncols), interpolation=cv2.INTER_CUBIC)
    
    if channel == 'single':
        X = np.array([A, B, C, D]) # shape = (4,150,150)
        X = X.reshape(X.shape[0],X.shape[1],X.shape[2],1)/255. # divide by 255
        # shape = (4, 150, 150, 1)
    elif channel == 'single+composite':
        All = normalize(0.25*A + 0.25*B + 0.25*C + 0.25*D)
        All = cv2.resize(All, (nrows, ncols), interpolation=cv2.INTER_CUBIC)
        X = np.asarray((np.dstack((A,All)), np.dstack((B,All)), np.dstack((C,All)), np.dstack((D,All))))/255. 
        # shape = (4,150,150,2)
    elif channel == 'single+nucBFP':
        X = np.asarray((np.dstack((A,D)), np.dstack((B,D)), np.dstack((C,D)), np.dstack((np.zeros((nrows, ncols)),D))))/255.
        # shape = (4,150,150,1)
    elif channel == 'single+nucBFP_drop4':
        X = np.array([A, B, C, np.zeros((nrows,ncols))]) # shape = (4,150,150)
        X = X.reshape(X.shape[0],X.shape[1],X.shape[2],1)/255. # divide by 255        
    else:
        raise ValueError('please specify channel: single, single+composite, single+nucBFP')
    return X


def read_BFP_images(img_path_list, nrows=150, ncols=150):
    # return (n,150,150,1) only one channel
    X = []
    for img_path in img_path_list:
        img = cv2.imread(img_path, cv2.IMREAD_ANYDEPTH)
        A, B, C, D = crop_1x4(img)  # crop img
        D = normalize_saturate_outlier(D)  # normalize
        D = cv2.resize(D, (nrows, ncols), interpolation=cv2.INTER_CUBIC)  # resize to 150x150
        X += [D]
    X = np.array(X)
    X = X.reshape(X.shape[0], X.shape[1], X.shape[2], 1) / 255.  # divide by 255

    return X


def read_RFP_images(img_path_list, bin_list, nrows=150, ncols=150):
    # return (n,150,150,2), select only the correct channel in (A,B,C)
    # bin = 6 -> mCherry -> channel A
    # bin = 11 -> mCardinal -> channel B
    # bin = 14 -> iRFP -> channel C
    X = []
    for img_path, bin_no in zip(img_path_list, bin_list):
        img = cv2.imread(img_path, cv2.IMREAD_ANYDEPTH)
        A, B, C, D = crop_1x4(img)  # crop img
        D = normalize_saturate_outlier(D)  # normalize
        D = cv2.resize(D, (nrows, ncols), interpolation=cv2.INTER_CUBIC)  # resize to 150x150

        bin_no = int(bin_no)
        if bin_no == 6:
            RFP = normalize_saturate_outlier(A)
            RFP = cv2.resize(RFP, (nrows, ncols), interpolation=cv2.INTER_CUBIC)
        elif bin_no == 11:
            RFP = normalize_saturate_outlier(B)
            RFP = cv2.resize(RFP, (nrows, ncols), interpolation=cv2.INTER_CUBIC)
        elif bin_no == 14:
            RFP = normalize_saturate_outlier(C)
            RFP = cv2.resize(RFP, (nrows, ncols), interpolation=cv2.INTER_CUBIC)
        else:
            RFP = np.zeros((nrows, ncols))
        X += [np.dstack((RFP, D))]
    X = np.array(X) / 255.  # divide by 255

    return X


# input array eg (4, 150, 150, 1) -> predict an array of classes eg [1,0,4,0] -> returns barcode B1040
def predict_barcode_with_model(X,model):
    pred = model.predict_classes(X)
    return "B"+"".join(map(str,pred.flatten().tolist()))

# input 2 barcode predictions, ouput the combined barcode
def combine_outputs(barcode1, barcode2):
    barcode = ["B"]
    for i in range(1,5):
        if barcode1[i] == '0':
            barcode.append(barcode1[i])
        else:
            barcode.append(barcode2[i])
    return "".join(barcode)


def load_model_3(MODEL_PATH='C:/Users/wchi6/Google Drive/Colab Notebooks/0317_test_2ch/0317-5class-39-0.96.h5'):
    model3 = load_model(MODEL_PATH,compile=False)
    model3.compile(loss='sparse_categorical_crossentropy', optimizer=optimizers.Adam(lr=1e-4, decay=1e-6), metrics=['acc'])
    return model3