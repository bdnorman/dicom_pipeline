# dicom_pipeline
This is a pipeline for loading in dicom and contour files. The pipeline also has the functionality of generating batches of the dicom/contour data as arrays of `height x width x batch size`, while also keeping track of the number of epochs used.
Use of this function is simply  
`$ python main_dicom_pipeline.py`  
This will return a log of the output in the *log.txt* file which will indicate: 
 * which dicom files did not have a corresponding contour files
 * message if a loaded dicom file is not of shape 256x256. 
 * if data list needs to have random remainder removed if total dataset size is not evenly divisible by batch size
 * how many epochs have been completed
 
 Finally, this script, as is, will also generate images of all dicoms with their contours overlayed onto them as .pngs if `image_saving=True` in the `new_batch` function.
 
It should be noted that dicoms that did not have corresponding contour files were not used as it seems contours were made on every 10th slice or so of the entire MRI volume. As such, saving the dicoms that did not have contours with blank masks is not appropriate. This is further discussed at the end when adressing enhancmenets to the pipeline.

## Part 1: Parse the DICOM images and Contour Files
In order to ensure that the parsing contours were done correctly, all 96 of the dicom images with their corresponding overlays were examined. An example of this image can be viewed below.
Example image:
![](https://github.com/bdnorman/dicom_pipeline/blob/master/90.png)
Examination of these images was to ensure that the contours were in fact highlighting the separation of the left ventricular blood pool from the heart muscle. Examining every single image is not a scalable approach with a larger dataset, however randomly sampling a small number of these types of images from the larger dataset is still a valid way to ensure that the contour masks are making sense.
It should also be noted that no adjustments were made to the suplied code from `dicom_parse_function.py`

## Part 2: Model training pipeline
A change I made from Part 1 to Part 2 in my code is actually using the batch generation to generate the overlay images over 1 epoch. This also allowed for the testing of the `new_batch` function to ensure the epochs were being calculated correctly. This was confirmed since "1 epoch complete" was printed after I ran the new_batch function 12 times (`dataset size / batch size = 8`). Additionally, all the outputted images from the batch data were different, meaning the code was correctly going through all the randomly shuffled dicom/contour dictionary in 1 epoch.

One of the defficiencies in the code is that all dicom files without corresponding contour files were not used. This is already a fairly small dataset size so doing some type of interpolation between slices given the contours could help increase the datasize by generating more target masks. Other enhancements to the pipeline could include a built-in division of training, validation, and testing data. Given more info about the 2D convolution model, it would also be helpful to have a class for image augmentation or patch-based division.
