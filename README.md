# dicom_pipeline Phase 2
*Note: original README from Phase 1 is now saved as README_phase1.md*

This is a pipeline for loading in dicom and corresponding contour files for the left ventricle heart muscle outline and left ventricular blood pool. The pipeline also has the functionality of generating batches of the dicom/contour data as arrays of `height x width x batch size`, while also keeping track of the number of epochs used. Finally, it also uses a heuristic thresholding approach to predict the left ventricular blood pool segmentation given the left ventricle heart muscle outline.
Use of this function is simply  
`$ python main_dicom_pipeline.py`  

This will return a log of the output in the *log.txt* file which will indicate:
* The t-test results between the intensities of the area between the left ventricular heart muscle and blood pool (which from now on will be reffered to as the between muscle area) and the blood pool itself
* The average Dice coefficient between the true blood pool segmentations and the predicted blood pool segmentation created using thresholding (where Dice's coefficient is just <a href="https://www.codecogs.com/eqnedit.php?latex=2*\frac{T\bigcap&space;P}{|T|&space;&plus;&space;|P|}" target="_blank"><img src="https://latex.codecogs.com/gif.latex?2*\frac{T\bigcap&space;P}{|T|&space;&plus;&space;|P|}" title="2*\frac{T\bigcap P}{|T| + |P|}" /></a> for true segmentation mask T and predicted segmentation mask P)

The script will also create a folder in the cloned directory called `mask_checking` that saves 1 epoch of pngs of the dicoms and their respective i-contour and o-contour segmentations overlayed on them. Depending on the `batch_size` defined in the main function, this will not save every single dicom file with had o- and i-contours. The script will also save images of the overlayed intensity distributions of the intensities of the between the between msucle area and the blood pool itself(*density_comparison.png*) and a side by side comparison of the blood pool true segmentation and thresholding generated segmentation(*true_contour_vs_pred_contour.png*)


## Part 1: Parse the o-contours
In order to add the o-contours to their corresponding dicoms and i-contours, my original `create_link_dict` function (now in the `general_load_functions.py` script) also takes in the "contour_type" which can be specified to "icontour" or "ocontour", which will specify if a dictionary mapping dicoms to o-contours should be created or a dictionary mapping dicoms to i-contours. Another change to this function from Phase 1 is that an additional argument called "warnings" was added. It is defaulted to false, but if set to true it will list which dicoms do not have a corresponding i-contour or o-contour file. This was set to false (unlike its setup in Phase 1) to allow for a cleaner log file.

The `create_link_dict` function was called twice for both contour types and then the two dictionaries were merged so each dicom mapped to a list of its corresponding o-contour and i-contour files. This also meant I had to change the `load_dicom_mask` function so that it now reads in two contour files and then adds them so the final mask has value 1 for area between the heart muscle and blood pool and the plood pool has value 2.

As in Phase 1, these new segmnetaion masks were saved (this time in a new folder that gets created) to ensure that they were being done correctly. An example image of one of these 3-class masks can be viewed below: 
![](https://github.com/bdnorman/dicom_pipeline/blob/master/image_folder/joint_30.png)


## Part 2: Heuristic LV Segmentation approaches
In order to assess how well a thresholding segmentation would work for the blood pool assuming we are given the outline border of the heart muscle, a general idea of the intensity differences between the between muscle area and blood pool was examined through a two-sample t-test and an overlayed histogram of the normalized intesnities of the two areas. Before extracting the itensities of these two areas, each individual dicom was normalized to be between 0 and 1. This was done since the subjects could have been taken with different scan parameters and in order to undertsand the intensity differences better it is best to have pixels in the same anatomatical regions across dicoms to have similar values.

The t-test revlead an extremely large t-statistic resulting in a p-value of esentially 0, indicating the intensity means of the two intensity distributions are not equal. This is promising for a thresholding segmetnation problem, but when looking at the overlayed histograms, there does still seem to be a decent amount of intensity overlap between the two areas. However, this intensity distribution graphic can be used to create a general threshold cutoff between the two distributions without running anything too mathematically rigorous to find out where they intersect. See figure below:
![](https://github.com/bdnorman/dicom_pipeline/blob/master/image_folder/density_comparison.png)

Through visual examination fo the above figure, it was decided that a normalized dicom intensity value of 0.14 would be best to try and differentiate the blood pool from the heart muscle.

Using the manually picked threshold cutoff, all thresholded blood pool masks were generated in the `threshold_seg` function and compared to the true blood pool masks using Dice's coefficient to examine overlap. The average Dice coefficient across the 46 samples was 82.02%. I am unsure of how this compares to the literature of this problem, but for such a simple approach this seems to be a reasonable result. An example of the true blood segmentation mask vs. the threshold predicted one can be viewed below:
![](https://github.com/bdnorman/dicom_pipeline/blob/master/image_folder/true_contour_vs_pred_contour.png)

Given blood pools are relatively consistent in their circular shape and size with regards to the heart muscle outline there are a few other heuristic approaches that could be used for this segmentation problem: 

* One simple approach is to calculate the average ratio of the area that the blood pool takes up with respect to the area of the entire heart muscle. Then, given a new heart muscle segmentation, take its center and construct a circle with a radius that makes it such that the area of that circle with respect to the whole heart muscle volume is the average ratio of blood pool to heart muscle area calculated before.
* In a similar vein as the problem proposed above, create the same circle using the same method but then use a circular Hough tranform for and unknown radius in the range of the radius calculated based on the blood pool heart muscle area ratio plus and minus a few pixels.
* This approach slightly ventures away from heuristics, but given that all blood pools appear to at least have some part in the center of heart muscle, start in the center of heart muscle segmentation and use a region growing method to construct the blood pool.
