import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import numpy as np
import pyperclip
from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from tkinter import messagebox

Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
cont = "yes"

while cont == "yes":
    file = askopenfilename(title="Select Roi Data")
    #finds column length of csv
    column_len = list(range(1,len(list(pd.read_csv(file, nrows=1)))))

    #reads csv and transposes it, ignoring the first column on file
    df = pd.read_csv(file, header=None, usecols=column_len)
    inv_df = df.transpose(copy=False)

    #shifts headers down by 1
    list1 = range(0, 20)
    list2 = range(1,21)
    time_frames = {list1[i]: list2[i] for i in range(len(list1))}
    inv_df.rename(columns=time_frames, inplace=True)
    inv_df.columns = range(1, 21)

    #inserts a column with barcode names
    barcode_df = pd.read_csv(askopenfilename(title="Select Barcode Output File"), usecols=["Thresholded"])
    barref_df = pd.read_csv(askopenfilename(title="Select Barcode Reference File"))
    barref_dict = {barref_df["Barcode"].values.tolist()[i]: barref_df["Biosensor"].values.tolist()[i] for i in range(len(barref_df["Barcode"].values.tolist()))}

    #combines columns
    temp_df = barcode_df.replace(barref_dict)
    temp_df.index = column_len
    out_df = pd.concat([temp_df, inv_df], ignore_index=True, axis=1)


    #inserts a column with cell numbers
    out_df.insert(0, "Cell", column_len, True)


    #Output cell numbers with PH-AKT or GCAMP
    SF_Biosensors = ["PH-AKT", "GCaMP6S"]
    SF_df = out_df.loc[out_df[0].isin(SF_Biosensors)]
    SF_list = SF_df["Cell"].tolist()
    SF_list_str = [str(int) for int in SF_list]
    SF_out = " ".join(SF_list_str)
    print(SF_out)
    pyperclip.copy(SF_out)
    messagebox.showinfo(title="Proceed to ImageJ", message="Single Fluorophore Copied to Clipboard. Press OK when Finished with analysis.")

    #read csv and replace values in csv
    for i in range(1, 21):
        for p in SF_list:
            out_df.loc[p, i] = 1
    file2 = askopenfilename(title="Single Fluorophore Output File")
    column_len = list(range(2, len(list(pd.read_csv(file2, nrows=1)))))
    SF_replace = pd.read_csv(file2, header=None, skiprows=1, usecols=column_len)
    SF_replace_inv = SF_replace.transpose(copy=False)
    for num in range(len(SF_list)):
        for i in range(1, 11):
            out_df.loc[SF_list[num], i] = SF_replace_inv.loc[num+2, i-1]
    out_df.to_csv(asksaveasfilename(title="Save Raw Data As")+".csv")


    #get YFP:CFP ration, normalize data frame, and invert PH-AKT, Syk, Src, Lyn-FAK, Prin-CRAF, ERKKTR biosensors
    out_df_copy = out_df.copy(deep=True)
    for row in range(1, out_df_copy.shape[0]+1):
        for col in range(1, 11):
            new_val = out_df_copy.at[row, col]/out_df_copy.at[row, col+10]
            out_df_copy.at[row, col] = new_val
        normalizer = (out_df_copy.loc[row, 1] + out_df_copy.loc[row, 2] + out_df_copy.loc[row, 3])/3
        for col in range(1, 11):
            out_df_copy.at[row, col] = out_df_copy.at[row, col]/normalizer
            if out_df_copy.loc[row, 0] in ["PH-AKT", "Syk", "Src", "Lyn-FAK", "Prin-CRAF"]:
                out_df_copy.at[row, col] = 1/out_df_copy.at[row, col]
    for col in range(11, 21):
        del out_df_copy[col]


    #construct subplots based on biosensors and plot with average and standard deviation
    biosensor_list = barref_df["Biosensor"].values.tolist()[:-1]
    fig, axes = plt.subplots(nrows=1, ncols=len(biosensor_list), figsize=(14,1.5))
    fig.tight_layout()
    x = range(1, 11)
    subplots_avg_ref = {}
    subplots_avg = []
    subplots_std_ref = {}
    subplots_std = []

    for Biosensor in biosensor_list:
        frame = out_df_copy[out_df_copy[0] == Biosensor]
        avg = frame.mean(axis=0)
        subplots_avg.append(avg.tolist()[1:])
        std = frame.std(axis=0)
        subplots_std.append(std.tolist()[1:])

    #Generates plot for each
    for i in range(0, len(biosensor_list)):
        if len(x) == len(subplots_avg[i]) and len(x) == len(subplots_std[i]):
            axes[i].errorbar(x, subplots_avg[i], yerr=subplots_std[i], fmt='', ls='none', color='lightblue', alpha=0.75, elinewidth=1, capsize=2, capthick=1)
            axes[i].plot(x, subplots_avg[i], 'o-', markersize=0.1, color='blue')
        axes[i].set_title(biosensor_list[i])
        plt.sca(axes[i])
        plt.grid(axis='y', color='0.95')
        plt.xticks(np.arange(0, len(x) + 1, 2))
        plt.locator_params(axis="y", nbins=5)
        axes[i].yaxis.set_major_formatter(FormatStrFormatter('%.1f'))

    plt.savefig(asksaveasfilename(title="Save Figure As") + ".png", bbox_inches='tight')
    plt.show()
    messagebox.showinfo(title="Finished", message="Figure Saved")
    cont = messagebox.askquestion("Processing Finished", "Process Another Experiment?", icon='question')