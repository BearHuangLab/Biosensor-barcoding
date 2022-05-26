# main
from barcode_util import *
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import optimizers
from tkinter import *
from tkinter import scrolledtext
from tkinter import filedialog
import time

window = Tk()
window.title("Barcode Prediction")
window.geometry('700x500')

def predict_and_output(barcode_dir, OUTPUT_DIR):
    # generate spectrum data
    spectrum = process_spectrum(txt_spectrum.get())

    # get img path list and generate dataframe
    img_path_list = get_img_path_list(barcode_dir)
    position = [os.path.basename(i).split('_')[-1][:-4] for i in img_path_list]
    cell_barcode = pd.DataFrame({'Index': position, 'Path': img_path_list, 'Spectrum': spectrum})

    # predict BFP channel with model1
    BFP = read_BFP_images(img_path_list)
    cell_barcode['BFP'] = list(np.argmax(model1.predict(BFP), axis=-1))

    # predict RFP channels with model2 or model3 according to BFP and spectrum data
    RFP = read_RFP_images(img_path_list, bin_list=cell_barcode['Spectrum'])
    cell_barcode.loc[cell_barcode['BFP'] == 1, 'RFP'] = list(
        map(int, list(np.argmax(model2.predict(RFP[cell_barcode.BFP == 1]), axis=-1))))
    cell_barcode.loc[cell_barcode['BFP'] == 2, 'RFP'] = list(
        map(int, list(np.argmax(model3.predict(RFP[cell_barcode.BFP == 2]),axis=-1))))
    cell_barcode.loc[cell_barcode['BFP'] == 0, 'RFP'] = 0

    # record the certainty of RFPs
    cell_barcode.loc[cell_barcode['BFP'] == 1, 'RFP_certainty'] = list(
        map(max, list(model2.predict(RFP[cell_barcode.BFP == 1]))))
    cell_barcode.loc[cell_barcode['BFP'] == 2, 'RFP_certainty'] = list(
        map(max, list(model3.predict(RFP[cell_barcode.BFP == 2]))))
    cell_barcode.loc[cell_barcode['BFP'] == 0, 'RFP_certainty'] = 0

    # generate final barcode from the channels
    for index, row in cell_barcode.iterrows():
        bin_no = int(row['Spectrum'])
        barcode_RFP = str(int(row['RFP']))
        barcode_BFP = str(int(row['BFP']))

        if bin_no == 6:
            cell_barcode.loc[index, 'Final'] = 'B' + barcode_RFP + '00' + barcode_BFP
        elif bin_no == 11:
            cell_barcode.loc[index, 'Final'] = 'B0' + barcode_RFP + '0' + barcode_BFP
        elif bin_no == 14:
            cell_barcode.loc[index, 'Final'] = 'B00' + barcode_RFP + barcode_BFP

    # Generate the output if FinalPrediction is in EXP_BARCODE_LIST
    EXP_BARCODE_LIST = barcode_list
    for index, row in cell_barcode.iterrows():
        if row['Final'] in EXP_BARCODE_LIST:
            cell_barcode.loc[index, 'Output'] = row['Final']
        else:
            cell_barcode.loc[index, 'Output'] = '0'
    # generate thresholded output (Threshold = 0.9)
    cell_barcode['Thresholded'] = list(cell_barcode['Output'])
    cell_barcode.loc[(cell_barcode['RFP_certainty'] < threshold_2) & (cell_barcode['BFP'] == 1), 'Thresholded'] = 0
    cell_barcode.loc[(cell_barcode['RFP_certainty'] < threshold_3) & (cell_barcode['BFP'] == 2), 'Thresholded'] = 0
    # output the result
    cell_barcode.to_csv(OUTPUT_DIR)

def process_spectrum(csv_path):
    df = pd.read_csv(csv_path, sep='\t', header = None)
    max_bins = []
    # process the rolling average
    for col in df.columns[1:]:
        df[col] = df[col]/max(df[col])
        df[col] = df.loc[:,col].rolling(window=2).mean()
        max_bins += [np.argmax(df[col])]
    return max_bins

def select_model_1():
    dir = filedialog.askopenfilename(initialdir = "Model 1",title = "Select file",filetypes = (("h5 files","*.h5"),("all files","*.*")))
    output.insert(INSERT, 'Model 1 set: ' + dir + '\n')
    txt_m1.delete(0,END)
    txt_m1.insert(0,dir)
def select_model_2():
    dir = filedialog.askopenfilename(initialdir = "Model 2",title = "Select file",filetypes = (("h5 files","*.h5"),("all files","*.*")))
    output.insert(INSERT, 'Model 2 set: ' + dir + '\n')
    txt_m2.delete(0,END)
    txt_m2.insert(0,dir)
def select_model_3():
    dir = filedialog.askopenfilename(initialdir = "Model 3",title = "Select file",filetypes = (("h5 files","*.h5"),("all files","*.*")))
    output.insert(INSERT, 'Model 3 set: ' + dir + '\n')
    txt_m3.delete(0,END)
    txt_m3.insert(0,dir)
def select_barcode_list():
    dir = filedialog.askopenfilename(initialdir = "Barcode list",title = "Select file",filetypes = (("text","*.txt"),("all files","*.*")))
    output.insert(INSERT, 'Barcode list set: ' + dir + '\n')
    txt_list.delete(0,END)
    txt_list.insert(0,dir)
def select_barcode_dir():
    dir = filedialog.askdirectory()
    output.insert(INSERT, 'Barcode image from: ' + dir + '\n')
    output.insert(INSERT, 'Output directory set: ' + dir + '/modelpred.csv\n')
    txt_folder.delete(0,END)
    txt_folder.insert(0,dir)
    txt_output.delete(0,END)
    txt_output.insert(0,dir+'/modelpred.csv')
def select_output_dir():
    dir = filedialog.askdirectory()
    output.insert(INSERT, 'Output directory set: ' + dir + '/modelpred.csv\n')
    txt_output.delete(0,END)
    txt_output.insert(0,dir+'/modelpred.csv')
def select_spectrum_dir():
    dir = filedialog.askopenfilename(initialdir="Spectrum", title="Select file",
                                     filetypes=(("text", "*.txt"), ("all files", "*.*")))
    output.insert(INSERT, 'spectrum directory set: ' + dir + '\n')
    txt_spectrum.delete(0,END)
    txt_spectrum.insert(0,dir)
#load model
def click_load_models():
    model_1_path = txt_m1.get()
    model_2_path = txt_m2.get()
    model_3_path = txt_m3.get()
    global model1, model2, model3, threshold_2, threshold_3
    threshold_2 = float(txt_threshold2.get())
    threshold_3 = float(txt_threshold3.get())
    # load models
    model1 = load_model(model_1_path)
    model2 = load_model(model_2_path)
    model3 = load_model(model_3_path)
    output.insert(INSERT, f'Models loaded\nThreshold for model 2 = {threshold_2}\nThreshold for model 3 = {threshold_3}\n')

def click_confirm_list():
    barcode_list_path = txt_list.get()
    global barcode_list
    with open(barcode_list_path) as f:
        barcode_list = f.read().strip().split()
    output.insert(INSERT, f'Barcode list used: {barcode_list}\n')
def click_predict_barcodes():
    # variables
    barcode_dir = txt_folder.get()
    OUTPUT_DIR = txt_output.get()
    start_time = time.perf_counter()
    predict_and_output(barcode_dir, OUTPUT_DIR)
    end_time = (time.perf_counter() - start_time)
    output.insert(INSERT, 'Complete prediction...\n--- %0.2f seconds ---\n' % end_time)


lbl_m1 = Label(window, text = 'Model 1')
lbl_m2 = Label(window, text = 'Model 2')
lbl_m3 = Label(window, text = 'Model 3')
lbl_list = Label(window, text = 'Barcode list')
lbl_folder = Label(window, text = 'Barcode image directory')
lbl_output = Label(window, text = 'Output directory')
lbl_spectrum = Label(window, text = 'Spectrum data directory')
lbl_threshold = Label(window, text = 'Set threshold ↓')
lbl_m1.grid(column=0,row=0, padx=5, pady=5)
lbl_m2.grid(column=0,row=1, padx=5, pady=5)
lbl_m3.grid(column=0,row=2, padx=5, pady=5)
lbl_list.grid(column=0,row=3, padx=5, pady=5)
lbl_folder.grid(column=0,row=4, padx=5, pady=5)
lbl_output.grid(column=0,row=5, padx=5, pady=5)
lbl_spectrum.grid(column=0,row=6, padx=5, pady=5)
lbl_threshold.grid(column=3, row=0, padx=5, pady=5)

btn_m1 = Button(window, text = 'Browse',command=select_model_1)
btn_m2 = Button(window, text = 'Browse',command=select_model_2)
btn_m3 = Button(window, text = 'Browse',command=select_model_3)
btn_list = Button(window, text = 'Browse', command=select_barcode_list)
btn_folder = Button(window, text = 'Browse',command=select_barcode_dir)
btn_output = Button(window, text = 'Browse',command=select_output_dir)
btn_spectrum = Button(window, text = 'Browse',command=select_spectrum_dir)
btn_load = Button(window, text = 'Load model',command=click_load_models)
btn_confirm_list = Button(window, text = 'Confirm list',command=click_confirm_list)
btn_run = Button(window, text = 'Predict barcode',command=click_predict_barcodes)
btn_m1.grid(column=1,row=0)
btn_m2.grid(column=1,row=1)
btn_m3.grid(column=1,row=2)
btn_list.grid(column=1,row=3)
btn_folder.grid(column=1,row=4)
btn_output.grid(column=1,row=5)
btn_spectrum.grid(column=1,row=6)
btn_load.grid(column=4,row=0, rowspan=3,sticky=W+E+N+S, padx=5, pady=5)
btn_confirm_list.grid(column=4,row=3, rowspan=1,sticky=W+E+N+S, padx=5, pady=5)
btn_run.grid(column=4,row=4, rowspan=3,sticky=W+E+N+S, padx=5, pady=5)

model_1 = StringVar()
model_2 = StringVar()
model_3 = StringVar()
spectrum_dir = StringVar()
threshold2 = StringVar()
threshold3 = StringVar()
entry_list = StringVar()
model_1.set('Model 1/' + os.listdir('Model 1')[0])
model_2.set('Model 2/' + os.listdir('Model 2')[0])
model_3.set('Model 3/' + os.listdir('Model 3')[0])
spectrum_dir.set('Spectrum/' + os.listdir('Spectrum')[0])
entry_list.set('Barcode list/' + os.listdir('Barcode list')[0])
threshold2.set('0.9')
threshold3.set('0.9')

txt_m1 = Entry(window,width=30, textvariable=model_1)
txt_m2 = Entry(window,width=30, textvariable=model_2)
txt_m3 = Entry(window,width=30, textvariable=model_3)
txt_list = Entry(window,width=30, textvariable=entry_list)
txt_folder = Entry(window,width=30)
txt_output = Entry(window,width=30)
txt_spectrum = Entry(window,width=30, textvariable=spectrum_dir)
txt_threshold2 = Entry(window,width=10, textvariable=threshold2)
txt_threshold3 = Entry(window,width=10, textvariable=threshold3)
txt_m1.grid(column=2,row=0)
txt_m2.grid(column=2,row=1)
txt_m3.grid(column=2,row=2)
txt_list.grid(column=2,row=3)
txt_folder.grid(column=2,row=4)
txt_output.grid(column=2,row=5)
txt_spectrum.grid(column=2,row=6)
txt_threshold2.grid(column=3, row=1)
txt_threshold3.grid(column=3, row=2)

output = scrolledtext.ScrolledText(window)
output.grid(column=0,row=7,columnspan=5)

window.mainloop()
