# dicom_pipeline Phase 2
*Note: original README from Phase 1 is now save as README_phase1.md*

This is a pipeline for loading in dicome and corresponding contour files for the left ventricle heart muscle outline and left ventricular blood pool. The pipeline also has the functionality of generating batches of the dicom/contour data as arrays of `height x width x batch size`, while also keeping track of the number of epochs used. Finally, it also uses a heuristic thresholding approach to predict the left ventricular blood pool segmentation given the left ventricle heart muscle outline.
Use of this function is simply  
`$ python main_dicom_pipeline.py`  

This will return a log of the output in the *log.txt* file which will indicate:
* The t-test results between the intensities of the area between the left ventricular heart muscle and blood pool (which from now on will be reffered to as the between muscle area) and the blood pool itself
* The average Dice coefficient between the true blood pool segmentations and the predicted blood pool segmentation created using thresholding (where Dice's coefficient is just $2*\frac{T\bigcap P}{|T| + |P|}$ for true segmentation mask T and predicted segmentation mask P)

The script will also create a folder in the cloned directory called `mask_checking` that saves 1 epoch of pngs of the dicoms and the i-contour and o-contour segmentations overlayed on them. Depending on the `batch_size` defined in the main function, this will not save every single dicome file that had o- and i-contours. The script will also save images of the overlayed intensity distributions of the intensities of the area between the between msucle area and the blood pool itself(*density_comparison.png*) and a side by side comparison of the blood pool true segmentation and thresholding generated segmentation(*true_contour_vs_pred_contour.png*)


## Part 1: Parse the o-contours
In order to add the o-contours to their corresponding dicoms and i-contours, my original `create_link_dict` function (now in the `general_load_functions.py` script) also takes in the "contour_type" which can be specified to "icontour" or "ocontour" this will specify if a dictionary mapping dicoms to o-contours should be created or a dictionary mapping dicoms to i-contours. Another change to this function from Phase 1 is that an additional argument called "warnings" was added. It is defaulted to false, but if set to true it will list which dicoms do not have a corresponding icontour or ocontour file. This was set to false (unlike its setup in Phase 1) to allow for a clearn log file.

The `create_link_dict` function was called twice for both contour types and then the two dictionaries were merged so each dicom mapped to a list of its corresponding o-contour and i-contour file. This also meant I had to change the `load_dicom_mask` function so that it now reads in two contour files and then stacks them so the final mask has value 1 for area between the heart muscle and blood pool and the plood pool has value 2.

As in Phase 1, these new segmnetaion masks were save (this time in a new folder that gets created) to ensure that they were being done correctly. An example image of one of these 3-class masks can be viewed below: 
![](https://github.com/bdnorman/dicom_pipeline/blob/master/90.png)


## Part 2: Heuristic LV Segmentation approaches
In order to assess how well a thresholding segmentation would work for the blood pool assuming we are given the outline border of the heart muscle, a general idea of the intensity differences between the between muscle area and blood pool was examined through a two-sample t-test and an overlayed histogram of the intesnities of the two areas.

The t-test revlead an extremely large t-statistic resulting in a p-value of esentially 0, indicating the intensity means of the two intensity distributions are different. This is promising for a thresholding segmetnation problem, however when looking at the overlayed histograms, there does still seem to be a good bit of intensity overlap between the two areas
