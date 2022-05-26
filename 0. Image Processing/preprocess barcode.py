import tifffile
import cv2
import os
import numpy as np

barcode_dir = '/raw_images/cytosol/' # directory to the barcode images
save_dir = '/processed_images' # directory to save the processed images

img_path_list = [os.path.join(barcode_dir, i) for i in os.listdir(barcode_dir) if i.endswith('.tif')]

# resize the images to 150x150
nrows = 150
ncols = 150

def crop_1x2(img):
    #crop images
    y, x = img.shape
    A = img[0:, 0:int(x/2)]
    B = img[0:, int(x/2):int(x)]
    return A, B

# normalize to [0, 255], set limit for outlier (default 99%)
def normalize_saturate_outlier(image, percentile=99):
    upperlimit = np.percentile(image, percentile)
    lowerlimit = np.percentile(image, 100 - percentile)
    image = np.minimum(upperlimit, image)
    image = np.maximum(lowerlimit, image)
    image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    return image

# save the preprocessed barcodes 
for img_path in img_path_list:

    # read grayscale image
    img = cv2.imread(img_path, cv2.IMREAD_ANYDEPTH) 

    # crop images according to barcode ABCD
    A, B = crop_1x2(img)
    
    # rescale and clip the extreme (1%) signals
    A = normalize_saturate_outlier(A, percentile=99)
    B = normalize_saturate_outlier(B, percentile=99)

    # resize the images
    A = cv2.resize(A, (nrows, ncols), interpolation=cv2.INTER_CUBIC)
    B = cv2.resize(B, (nrows, ncols), interpolation=cv2.INTER_CUBIC)

    # save image
    tifffile.imsave(f'{save_dir}/{os.path.basename(img_path)}', np.concatenate(([A], [B])))
