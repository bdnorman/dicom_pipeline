# dicom_pipeline
This is a pipeline for loading in dicom and contour files. The pipeline also has the functionality of generating batches of the dicom/contour data as arrays of size height x width x batch size, while also keeping track of the number of epochs used.
Use of this function is simply  
`$ python main_dicom_pipeline`  
This will return a log of the output in the log.txt file which will indicate which dicom files did not have a corresponding contour files. It will also throw a message if a loaded dicom file is not of shape 256x256. Finally, this script as is will also generate images of all dicoms with their contours overlayed onto them as .pngs.

## Part 1: Parse the DICOM images and Contour Files
In order to ensure that the parsing contours were done correctly, all 96 of the dicom images with their corresponding overlays were examined. An example of this image can be viewed below.
Example image:
![](https://github.com/bdnorman/dicom_pipeline/blob/master/90.png)
Examination of these images was to ensure that the contours were in fact highlighting the separation of the left ventricular blood pool from the heart muscle. Examining every single image is not a scalable approach, however randomly sampling a small number of these types of images when using a much larger dataset is still a valid way to ensure that the contour masks are making sense.
It should also be noted that no adjustments were made to the suplied code from `dicom_parse_function.py`

## Part 2: Model training pipeline
A change I made from Part 1 to Part 2 in my code is actually using the batch generation to generate the overlay images over all the images instead of looping through the entire dictionary from Part 1 and feading that into another load_dicom_mask function. This allowed for the testing of the new_batch function to ensure the epochs were being calculated correctly. This was confirmed since "1 epoch complete" was printed after ran the new_batch function 12 times (data size/ batch size = 8). Additionally, all the outputted images from the batch data were different, meaning the code was correctly selecting through the randomly shuffled dictionary.
