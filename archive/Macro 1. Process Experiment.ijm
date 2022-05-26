/* ImageJ Workflow Macro for Dr. Huang's Lab
 * 
 * Used to analyze biosensors using double fluorophore barcoding system
 * 
 */




/* Functions
 *  
 *  Name							Use
 *  Openfile(ending)				Searches for and opens a file in the directory based "ending" (ex. ".tif")		
 *  CreateFolder(name)				Creates folder with "name" in the directory
 *  Spilce(pos, channel)			Splits opened hyperstack by channel and stitches positions together (must open and rename hyperstack to Z first)
 *  Segmentate()					Autosegmentates ROIs or opens pre-defined ROIs
 *  SaveROIData()					Saves ROI data for CFP and YFP channels into a .csv file
 *  GenerateBarcodes(file_name,n)	Creates Barcode Strips for the model to use
 * 	getSpectralData()				Generates Spectrum txt data for model to use
 * 
 */

///////////////////////////////////////////Opens a File Based on the ending of the file | Global Variables: Dir///////////////////////////////////////////////////////

function OpenFile(ending) {
	filelist = getFileList(Dir);
setBatchMode(true);
for (i = 0; i < lengthOf(filelist); i++) {
    if (endsWith(filelist[i], ending)) { 
        open(Dir + File.separator + filelist[i]);
    } 
}
setBatchMode("exit and display");
	
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////Creates a new folder with a name | Global Variables: Dir///////////////////////////////////////////////

function CreateFolder(name) {
	newDir = Dir + name + "\\";
	File.makeDirectory(newDir);
	}
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

/////////Splits Hyperstack into 1 Channel + Stiches Different Microscope Positions Together | Global Variables Used: Dir, position | Needs function CreateFolder //////////////////////////////////////////////////

function Splice(pos, channel) {		//Make sure to rename opened file to Z before running
	setBatchMode(true);
	selectWindow("Z");
	if (channel == "C") {			//Choose processed channel by setting channel parameter to C (for CFP) or Y (for YFP)
		channel_no = 1;
		fin_name = "combined-CFP";
	}
	if (channel == "Y") {
		channel_no = 2;
		fin_name = "combined-YFP";
	}
	run("Duplicate...", "duplicate channels=" + channel_no);		//Isolate channel, Splits stack into substacks based on positions, saves each stack as .tif in CutImages folder
	run("Stack Splitter", "number=" + pos);
	CreateFolder("CutImages");
	for (i=1; i<=pos;i++){
		ext = "000";
		if (i >= 10 && i <100){
			ext = "00";
			}
		if (i >= 100 && i <1000) {
			ext = "0";
			}
		if (i >=1000) {
			ext = "";
			}
		selectWindow("stk_" + ext + i + "_Z-1");
		saveAs("tiff", Dir + "CutImages\\" + channel + i + ".tif");
		close();
	}
	close();
	setBatchMode("exit and display");
	run("Grid/Collection stitching", "type=[Grid: row-by-row] order=[Right & Down                ] grid_size_x=" + pos +" grid_size_y=1 tile_overlap=0 first_file_index_i=1 directory=[" + Dir + "CutImages\\] file_names=" + channel + "{i}.tif output_textfile_name=TileConfiguration.txt fusion_method=Average regression_threshold=0.30 max/avg_displacement_threshold=2.50 absolute_displacement_threshold=3.50 ignore_z_stage computation_parameters=[Save computation time (but use more RAM)] image_output=[Fuse and display] use");
	run("Grays");
	saveAs("tiff", Dir + "CutImages\\" + fin_name + ".tif");
}		//runs Grid/Collection stitching to combine substacks into full image

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

/////////////////////////////////////////////////////AutoSegmentates Cells and Saves ROIs | Global Variables: Dir, file_name/////////////////////////////////////////

function Segmentate(own, auto) {
	s = 1; //how smooth the mask will be + fine the filtering of smaller particles is (larger value = slower, but less artifacts)
	mx = 40000; //max size of cell
	mn = 5000; //min size of cell
	tar = 0; //1 or 0 (0 = draw circle around cell or 1 = overlapping area of cell)

	if (own == false && auto == true) {
		setBatchMode(true);
		selectWindow("combined-YFP");			//Processes YFP for autosegmentation algorithm by enhancing contracts/reducing noise
		run("Duplicate...", "duplicate");
		run("Enhance Contrast...", "saturated=10 normalize process_all");
		run("Despeckle", "stack");
		run("Remove Outliers...", "radius=s threshold=50 which=Bright stack");
		run("Gaussian Blur...", "sigma=5 stack");
		run("Smooth", "stack");
		run("Enhance Contrast", "saturated=0.35");
		run("Enhance Contrast", "saturated=0.35");
		run("Enhance Contrast...", "saturated=10 normalize process_all");
		run("Enhance Contrast...", "saturated=10 normalize process_all");
		setAutoThreshold("Default dark");
		setOption("BlackBackground", false);
		run("Convert to Mask", "method=Default background=Dark calculate black");
		run("Z Project...", "projection=[Sum Slices]");			//Combines frames into a Z stack to account for cell movement
		setAutoThreshold("Default dark");

		if (tar == 0) {				//Sets threshold to select for inner part of cell (darker part of Z stack) or outer (all of Z stack)
			setThreshold(80.0000, 1000000000000000000000000000000.0000);
			setThreshold(80.0000, 1000000000000000000000000000000.0000);
			}
		if (tar == 1) {
			setThreshold(2300, 1000000000000000000000000000000.0000);
			setThreshold(2300, 1000000000000000000000000000000.0000);
			}
		run("Convert to Mask");
		selectWindow("combined-YFP-1");
		close();
		setBatchMode("exit and display");
	
		run("Analyze Particles...", "size=mn-mx show=Outlines overlay add");	//autosegmentates Z stack to make ROIs, displays ROIs
		selectWindow("Drawing of SUM_combined-YFP-1");
		roiManager("Show All without labels");
		roiManager("Show All with labels");
		selectWindow("SUM_combined-YFP-1");
		close();
		selectWindow("combined-YFP");
		selectWindow("combined-CFP");
		roiManager("Show None");
		roiManager("Show All");
		selectWindow("Drawing of SUM_combined-YFP-1");
		close();
		selectWindow("combined-YFP");
		roiManager("Show None");
		roiManager("Show All");

		for (i = 0; i < roiManager("count"); i++) {			//renames and saves ROIs
			roiManager("Select", i)
			roiManager("rename", i+1)
			}
	
		roiManager("Save", Dir + file_name + "_FRET_RoiSet.zip");
			}
			
	if (own == false && auto == true) {
		waitForUser("Select ROI's");
		}
	
	if (own == true) {
		roiManager("Open", Dir + file_name + "_FRET_RoiSet.zip");
		}
}

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////Saves ROI data into a .csv file | Global variables: Dir, file_name///////////////////////////////////////////

function SaveROIData() {
	setBatchMode(true);
	roiManager("Deselect");		//renames and saves ROIs
	run("Select All");
	run("Set Measurements...", "mean display redirect=None decimal=3");
	selectWindow("combined-YFP");
	roiManager("Multi Measure");
	selectWindow("combined-CFP");
	roiManager("multi-measure measure_all one append");
	setBatchMode("exit and display");

	//copy results
	String.copyResults();
	saveAs("Results", Dir + file_name + "ROIData.csv");
}

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


///////////////////////////////Opens 405 and 633 Wavelengths and creats barcode strips | Global Variables: Dir, file_name///////////////////////////////////////////

function GenerateBarcodes(file_name,n){ //n is positions
	setBatchMode(true);
	regex_4 = ".*405Ex.*"; //the image with 405Ex (channel D)
	regex_5 = ".*633Ex.*"; //the image with 633Ex (channel B/C)

	roi_no = roiManager("count");
	CreateFolder("Barcodes");
	directory = Dir;

//catch titles that match the patterns 
	list = getList("image.titles");
  if (list.length==0)
     print("No image windows are open");
  else {
     for (i=0; i<list.length; i++) {
        //catch first window
        if (list[i].matches(regex_4))
        	title_4 = list[i];
        //catch second window
        if (list[i].matches(regex_5)) 
        	title_5 = list[i];
        }
  }

	//Make barcode strip
	selectWindow(title_4); 
	run("Make Montage...", "columns=n rows=1 scale=1");
	close(title_4);
	selectWindow("Montage"); rename("4");

	selectWindow(title_5); 
	run("Make Montage...", "columns=n rows=1 scale=1");
	close(title_5);

	selectWindow("Montage"); run("Duplicate...", "title=5-1 duplicate channels=1");run("Grays");
	selectWindow("Montage"); run("Duplicate...", "title=5-2 duplicate channels=2");run("Grays");
	selectWindow("Montage"); run("Duplicate...", "title=5-3 duplicate channels=3");run("Grays");
	close("Montage");

	//subtract background
	selectWindow("4");
	run("Subtract Background...", "rolling=5 sliding");
	selectWindow("5-1");
	run("Subtract Background...", "rolling=5 sliding");
	selectWindow("5-2");
	run("Subtract Background...", "rolling=5 sliding");
	selectWindow("5-3");
	run("Subtract Background...", "rolling=5 sliding");


	//enables background calculation, 20x faster
	setBatchMode("hide");

for (i = 0; i < roi_no; i++) {
	//selection windows, duplicate each roi
	selectWindow("5-1");roiManager("Select", i);
	roi_name = Roi.getName;
	run("Duplicate...", "title=A1");
	selectWindow("5-2");roiManager("Select", i);
	run("Duplicate...", "title=B1");
	selectWindow("5-3");roiManager("Select", i);
	run("Duplicate...", "title=C2");
	selectWindow("4");roiManager("Select", i);
	run("Duplicate...", "title=D3");
	//combine
	run("Combine...", "stack1=A1 stack2=B1");
	run("Combine...", "stack1=[Combined Stacks] stack2=C2");
	run("Combine...", "stack1=[Combined Stacks] stack2=D3");
	
	//save & close
	saveAs("Tiff", directory + "Barcodes\\" + roi_name +".tif");
	close();
}
	//disables background calculation
	setBatchMode("show");

	//close all windows
while (nImages>0) { 
  selectImage(nImages); 
  close(); 
} 

setBatchMode(false);

}

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////Saves Spectral Data to txt file////////////////////////////////////////////////////////////
function getSpectralData() {
	ModelDir = Dir;
	run("Make Montage...", "columns=30 rows=1 scale=1");
	selectWindow("Montage");
	run("Set Measurements...", "mean display redirect=None decimal=3");
	roiManager("Multi Measure");
	run("Set Measurements...", "mean display redirect=None decimal=3");
	roiManager("Multi Measure");

	//copy results
	String.copyResults();
	Table.showRowNumbers(true);
	run("Input/Output...", "jpeg=85 gif=-1 file=.txt use_file");
	saveAs("Results", ModelDir + "TS" + trials - (trials* 2 - (i + 1)) + "spectrum data.txt");
}

///////////////////////////////////////////////////////////////////////////Processes Image Set with Above Functions//////////////////////////////////////////////////////////////////////////////////


function ProcessImageSet(floc, pos, fname, own, auto) {
	Dir = floc;
	positions = pos;
	file_name = fname;
	ownROI = own;

	OpenFile("FRET.lsm");			//Opens the FRET file as "Z", splices channels and positions, renames windows for further use down the line
	rename("Z");
	Splice(positions, "C");
	Splice(positions, "Y");
	selectWindow("Z");
	close();
	selectWindow("combined-CFP.tif");
	rename("combined-CFP");
	selectWindow("combined-YFP.tif");
	rename("combined-YFP");			//Returns only combined-YFP and combined-CFP windows


	Segmentate(ownROI, auto);			//Autosegmentates or uses predefined ROI's. Saves data and closes all windows afterwards
	SaveROIData();
	close();
	close();

	roiManager("Deselect");			//Cleans up open windows
	roiManager("Delete");			
	selectWindow("Results"); 
	run("Close");
	selectWindow("Log");
	run("Close");
	close("*");

	OpenFile("405Ex.lsm");			//Opens files & ROIs and gets barcode strips
	OpenFile("633Ex_Linear unmixing.lsm");
	roiManager("Open", Dir + file_name + "_FRET_RoiSet.zip");
	GenerateBarcodes(file_name, positions);


	roiManager("Deselect");			//Cleans up open windows
	roiManager("Delete");			
	close("*");

	
	OpenFile("633Ex.lsm");			//Opens files & ROIs and gets spectral data
	roiManager("Open", Dir + file_name + "_FRET_RoiSet.zip");
	getSpectralData();
	
	roiManager("Deselect");			//Cleans up open windows
	roiManager("Delete");			
	selectWindow("Results"); 
	run("Close");
	close("*");
	}


/////////////////////////////////////////////////////////Script: Allows User to run analysis on multiple image sets///////////////////////////////////////////////////////////////////////////////////////

Dialog.create("Inputs");			//Creates Dialogue Box to determine # of trials, and if user wants to use own ROI
Dialog.addMessage("Parameters for Multiprocessing");
Dialog.addNumber("Trials", 4);
Dialog.addCheckbox("Use Premade ROIs", false);
Dialog.addCheckbox("Automatic Segmentation?", false);

Dialog.show();



//Stores parameters in variables
trials = Dialog.getNumber();
ownROI = Dialog.getCheckbox();
autoSeg = Dialog.getCheckbox();

dir_array = newArray(trials);
fname_array = newArray(trials);
pos_array = newArray(trials);

for (i = 1; i <= trials; i++) {				//Creates dialogue sequence to determine where image files are and number of positions
	Dialog.create("T" + i);
	Dialog.addMessage("Name of Trial");
	Dialog.addString("File name", "[Name of Experiment]");
	Dialog.addNumber("Positions", 30);
	Dialog.show();

	tar_file = Dialog.getString();
	tar_pos = Dialog.getNumber();
	tar_dir = getDir("Directory of Trial");	//Asks user to specify directory where things are stored

	
	a = Array.concat(fname_array,tar_file);		//creates 3 arrays with (1) file names, (2) number of positions, (3) directory of files
	b = Array.concat(pos_array,tar_pos);
	c = Array.concat(dir_array,tar_dir);

	fname_array = a;
	pos_array = b;
	dir_array = c;
	}


for (i = trials*2-1; i >= trials;i--) {			//Due to array manipulation with FIJI, arrays add extra zeroes in front, equal to the number of trials (ex. recording 2 positions, a and b, will output array [0,0,a,b] instead of [a,b]. Solve this by just counting backwards instead
	ProcessImageSet(dir_array[i], pos_array[i], fname_array[i], ownROI, autoSeg);		//Process image with parameters
	}