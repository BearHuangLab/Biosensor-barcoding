
//Create Dialog to obtain parameters
Dialog.create("New Image- Make Sure Image has been imported");
Dialog.addMessage("For Microscope LSM Image");
Dialog.addNumber("Positions", 30);
Dialog.addNumber("Time Points", 10);

Dialog.show();

//Store Parameters in Variables
n=Dialog.getNumber();
m=Dialog.getNumber(); //n=time points; m=positions

setBatchMode(true);
//CFP
rename("Z");
selectWindow("Z");
run("Set Scale...", "distance=0 known=0 pixel=1 unit=pixel");
run("Duplicate...", "duplicate channels=1");
//run("Smooth", "stack");run("Smooth", "stack");run("Smooth", "stack");
rename("1");

//M1
run("Duplicate...", "duplicate range=1-n");rename("combined-CFP");
selectWindow("1");
for (i=0; i<n;i++){
	run("Delete Slice");
}
//M2-Mm
for (j=2;j<m;j++){
selectWindow("1");
run("Duplicate...", "duplicate range=1-n");rename("a");
run("Combine...", "stack1=combined-CFP stack2=a");rename("combined-CFP");
selectWindow("1");
for (i=0;i<n;i++){
	run("Delete Slice");
}
}
selectWindow("1");rename("a");
run("Combine...", "stack1=combined-CFP stack2=a");rename("combined-CFP");
//run("Smooth", "stack");run("Smooth", "stack");
setBatchMode("exit and display");


setBatchMode(true);
//YFP
selectWindow("Z");
run("Set Scale...", "distance=0 known=0 pixel=1 unit=pixel");
run("Duplicate...", "duplicate channels=2");
//run("Smooth", "stack");run("Smooth", "stack");run("Smooth", "stack");
rename("1");
run("Duplicate...", "duplicate range=1-n");rename("combined-YFP");
selectWindow("1");
for (i=0; i<n;i++){
	run("Delete Slice");
}

for (j=2;j<m;j++){
selectWindow("1");
run("Duplicate...", "duplicate range=1-n");rename("a");
run("Combine...", "stack1=combined-YFP stack2=a");rename("combined-YFP");
selectWindow("1");
for (i=0;i<n;i++){
	run("Delete Slice");
}
}
selectWindow("1");rename("a");
run("Combine...", "stack1=combined-YFP stack2=a");rename("combined-YFP");
//run("Smooth", "stack");run("Smooth", "stack");
close("Z")
setBatchMode(false);

//Save files
dir=File.directory;
selectWindow("combined-CFP");
save(dir + "combined-CFP.tif");
selectWindow("combined-YFP");
save(dir + "combined-YFP.tif");

//Asks User to Select ROIs
waitForUser("Select ROIs by using \nthe selection tools \non the ImageJ toolbar. \nSave ROIs by pressing T.\nPress OK when finished.");
for (i = 0; i < roiManager("count"); i++) {
	roiManager("Select", i)
	roiManager("rename", i+1)
}
roiManager("save", dir + "FRET_RoiSet.zip");

//Ask for experiment ID
Dialog.create("Experiment ID");
Dialog.addString("Enter ID", "Experiment ID");
Dialog.show();
expID = Dialog.getString();

//Save ROI intensity data into csv file
setBatchMode(true);
roiManager("Deselect");		//renames and saves ROIs
run("Select All");
run("Set Measurements...", "mean display redirect=None decimal=3");
selectWindow("combined-YFP");
roiManager("Multi Measure");
selectWindow("combined-CFP");
roiManager("multi-measure measure_all one append");
setBatchMode("exit and display");
String.copyResults();		//copy results
saveAs("Results", File.directory + expID + "ROIData.csv");
selectWindow("Results"); 
run("Close");
close("*");

//Function to open files, used in getting Image Barcodes and generating Spectral Data
function OpenFile(ending) {
	filelist = getFileList(File.directory);
setBatchMode(true);
for (i = 0; i < lengthOf(filelist); i++) {
    if (endsWith(filelist[i], ending)) { 
        open(File.directory + File.separator + filelist[i]);
    } 
}
setBatchMode("exit and display");
}

//Gets Image Barcodes
	OpenFile("405Ex.lsm");			//Opens files & ROIs and gets barcode strips
	OpenFile("633Ex_Linear unmixing.lsm");
	setBatchMode(true);
	regex_4 = ".*405Ex.*"; //the image with 405Ex (channel D)
	regex_5 = ".*633Ex.*"; //the image with 633Ex (channel B/C)

	roi_no = roiManager("count");
	File.makeDirectory(File.directory + "Barcodes\\");
	directory = File.directory;

	list = getList("image.titles");		//catch titles that match the patterns 
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
	selectWindow(title_4); 			//Make barcode strip
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

	selectWindow("4");				//subtract background
	run("Subtract Background...", "rolling=5 sliding");
	selectWindow("5-1");
	run("Subtract Background...", "rolling=5 sliding");
	selectWindow("5-2");
	run("Subtract Background...", "rolling=5 sliding");
	selectWindow("5-3");
	run("Subtract Background...", "rolling=5 sliding");

	setBatchMode("hide");			//enables background calculation, 20x faster

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
	saveAs("Tiff", File.directory + "Barcodes\\" + roi_name +".tif");
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


//Get Spectral Data
OpenFile("633Ex.lsm");			//Opens files & ROIs and gets spectral data
run("Make Montage...", "columns=30 rows=1 scale=1");
selectWindow("Montage");
run("Set Measurements...", "mean display redirect=None decimal=3");
roiManager("Multi Measure");
run("Set Measurements...", "mean display redirect=None decimal=3");
roiManager("Multi Measure");

String.copyResults();			//copy results
Table.showRowNumbers(true);
run("Input/Output...", "jpeg=85 gif=-1 file=.txt use_file");
saveAs("Results", File.directory + expID + "_spectrum data.txt");

roiManager("Deselect");			//Cleans up open windows
roiManager("Delete");	
selectWindow("Results"); 
run("Close");
close("*");

//Finished Dialog Box
Dialog.create("Congrats!");
Dialog.addMessage("Processing Complete!");
Dialog.show();
