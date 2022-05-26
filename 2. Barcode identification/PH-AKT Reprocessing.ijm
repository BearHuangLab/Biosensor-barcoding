/* ImageJ Workflow Macro for Dr. Huang's Lab
 * 
 * Used to reprocess single fluorophore biosensors
 * 
 */

/* Functions
 *  
 *  Name							Use
 *  Openfile(ending)				Searches for and opens a file in the directory based "ending" (ex. ".tif")		
 *  SaveROIData()					Saves ROI data for CFP and YFP channels into a .csv file
 * 
 */

///////////////////////////////////////////Opens a File Based on the ending of the file | Global Variables: Dir///////////////////////////////////////////////////////

function OpenFile(ending) {
	filelist = getFileList(Dir+"/CutImages/");
setBatchMode(true);
for (i = 0; i < lengthOf(filelist); i++) {
    if (endsWith(filelist[i], ending)) { 
        open(Dir + File.separator + filelist[i]);
    } 
}
setBatchMode("exit and display");
	
}
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////Saves ROI data into a .csv file | Global variables: Dir, file_name///////////////////////////////////////////

function SaveROIData(Dir, file_name) {
	setBatchMode(true);
	run("Set Measurements...", "mean display redirect=None decimal=3");
	selectWindow("combined-YFP.tif");
	roiManager("Multi Measure");
	setBatchMode("exit and display");

	//copy results
	String.copyResults();
	saveAs("Results", Dir + file_name + "SFROIData" + trials - (trials* 2 - (i + 1)) + ".csv");
}

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

function ProcessImageSet(floc, pos, fname, own) {
	Dir = floc;
	file_name = fname;
	rois = split(pos);
	ori_roi_len = roiManager("count");


	OpenFile("combined-YFP.tif");
	print("opened YFP");
	roiManager("Open", Dir + file_name + "_FRET_RoiSet.zip");
	print("opened ROIs");
	
		for (elem = 0; elem < rois.length; elem++) {
		roiManager("Select", parseInt(rois[elem])-1);
		wait(100);
		run("To Selection");
		waitForUser("Edit and press t to save");
		roiManager("add");
		}

	}


/////////////////////////////////////////////////////////Script: Allows User to run analysis on multiple image sets///////////////////////////////////////////////////////////////////////////////////////

Dialog.create("Inputs");			//Creates Dialogue Box to determine # of trials, and if user wants to use own ROI
Dialog.addMessage("Parameters for Multiprocessing");
Dialog.addNumber("Trials", 4);

Dialog.show();



//Stores parameters in variables
trials = Dialog.getNumber();
ownROI = false;

dir_array = newArray(trials);
fname_array = newArray(trials);
pos_array = newArray(trials);

for (i = 1; i <= trials; i++) {				//Creates dialogue sequence to determine where image files are and number of positions
	Dialog.create("T" + i);
	Dialog.addMessage("Name of Trial");
	Dialog.addString("File name", "[NAME]_FRET_RoiSet");
	Dialog.addString("Positions to Investigate", "Separate with spaces");
	Dialog.show();

	tar_file = Dialog.getString();
	tar_pos = Dialog.getString();
	tar_dir = getDir("Directory of Trial");	//Asks user to specify directory where things are stored

	
	a = Array.concat(fname_array,tar_file);		//creates 3 arrays with (1) file names, (2) number of positions, (3) directory of files
	b = Array.concat(pos_array,tar_pos);
	c = Array.concat(dir_array,tar_dir);

	fname_array = a;
	pos_array = b;
	dir_array = c;
	}


for (i = trials*2-1; i >= trials;i--) {			//Due to array manipulation with FIJI, arrays add extra zeroes in front, equal to the number of trials (ex. recording 2 positions, a and b, will output array [0,0,a,b] instead of [a,b]. Solve this by just counting backwards instead
	ProcessImageSet(dir_array[i], pos_array[i], fname_array[i], ownROI);		//Process image with parameters
	waitForUser("Please Select ROIs");
	//roiManager("Save", Dir + file_name + "SFRoiSet.zip");
	SaveROIData(dir_array[i], fname_array[i]);
	print("Results Saved");
	while (nImages>0) { 
          selectImage(nImages); 
          close(); 
		}
	}
