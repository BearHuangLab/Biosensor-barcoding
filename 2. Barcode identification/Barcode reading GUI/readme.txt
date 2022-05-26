This python script is dependent on numpy, pandas, tkinter, tensorflow, and cv2. Most of them are in the anaconda distribution, but tensorflow and cv2 may have to be installed manually. 

In the command line, type the following to install cv2 and tensorflow

''''''''''''''''''''''''''''' 
' pip install opencv-python '
' conda install tensorflow '
'''''''''''''''''''''''''''''

or 

'''''''''''''''''''''''''''''
'  '
'''''''''''''''''''''''''''''

The structure of the directory looks like this:

Folder--Barcode.py
      |-Model 1 --model1.h5
      |-Model 2 --model2.h5
      |-Model 3 --model3.h5
to use this script, open command line in windows, and cd to the folder containing this script
type this to open the GUI:

''''''''''''''''''''''''''
' python Barcode.py      '
''''''''''''''''''''''''''


1. The models are preselected according to the first file in the Model folders. Click browse to change the models.
2. Click [Load model] to load the models.
3. Select the folder containing barcode images. The output folder is automatically set to the same folder.
4. Change the output folder and name if you want 
5. Click [Predict barcode] to run. It usually takes less than 1 min for an experiment. Close the application if it crushes. 
