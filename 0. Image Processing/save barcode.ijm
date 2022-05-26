//Example of an imageJ macro that concatenates and saves barcode images.

directory = "./raw_images/cytosol/" // change this to your directory
file_name = "20220101_cytosol_B4001" // change this to your experiment ID
roi_no = roiManager("count")

//Rename roi
for (i = 0; i < roiManager("count"); i++) {
	roiManager("Select", i)
	roiManager("rename", i+1)
}

//enables background calculation, 20x faster
setBatchMode("hide")

for (i = 0; i < roi_no; i++) {
	//select windows, duplicate each roi
	selectWindow("633Ex");roiManager("Select", i);
	roi_name = Roi.getName;
	run("Duplicate...", "title=A");
	selectWindow("405Ex");roiManager("Select", i);
	run("Duplicate...", "title=B");
	//combine
	run("Combine...", "stack1=A stack2=B");
	//save & close
	saveAs("Tiff", directory + file_name +"_"+ roi_name +".tif");
	close();
}
//disables background calculation
setBatchMode("show")

//close all windows
close("633Ex")
close("405Ex")
