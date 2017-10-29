'''
Berk Norman
Pipeline for reading in dicoms and corresponding inner and outer left ventricle contour data
Also create thresholding classifier for blood pool given the outline of the heart muscle
'''
from __future__ import division
import general_load_functions as dload
import sys
import numpy as np
import scipy.stats as stat
import copy


def normalize01(array):
    '''

    :param array: any type of numpy array
    :return: input array normalized to be between 0-1
    '''
    return (array-np.min(array))/(np.max(array)-np.min(array))

def intensity_extract(dicom_array, joint_mask, normalize=True):
    '''

    :param dicom_array: array from dicom file
    :param joint_mask: joint mask with area between heart muscle and blood pool labelled as 1 and blood pool labelled as
    2
    :param normalize: whether or not to normalize dicom array. Default is set to true
    :return:
    '''
    if normalize:
        dicom_array = normalize01(dicom_array)
    outer_intensities = dicom_array[joint_mask==1]
    inner_intensities = dicom_array[joint_mask==2]
    return outer_intensities, inner_intensities

def threshhold_seg(dicom_array, joint_mask, threshold, normalize=True):
    '''Function that will create predicted left ventricle segmentation masks just based on thresholding and will return
    the dice coefficient between the true left ventricle mask and the predicted one done through thresholding
    
    :param dicom_array: array from dicom file
    :param joint_mask: joint mask with area between heart muscle and blood pool labelled as 1 and blood pool labelled as
    2
    :param threshold: intensity value with which all values great than in the entire heart muscle region will be
    labelled as blood pool
    :param normalize: whether or not to normalize dicom array. Default is set to true
    :return:
    '''
    if normalize:
        dicom_array = normalize01(dicom_array)
    pred_mask = copy.copy(dicom_array)
    true_mask = copy.copy(joint_mask)
    #Remove all itensity surrounding o-contour segmentations
    pred_mask[joint_mask==0] = 0
    #Remove all o-contour below threshold to get predicted i-contour
    pred_mask[pred_mask<threshold]=0
    pred_mask[pred_mask!=0]=1
    true_mask[true_mask==1]=0
    true_mask[true_mask==2]=1
    dice_val = dice_coef(true_mask, pred_mask)
    return true_mask, pred_mask, dice_val

def dice_coef(true_mask, pred_mask):
    '''

    :param true_mask: true contour array mask
    :param pred_mask: predicted contour array mask
    :return: dice coefficient between the true mask and prediction mask, which is essentially just a measure of overlap
    between the two masks
    '''
    truth = np.ndarray.flatten(true_mask)
    pred = np.ndarray.flatten(pred_mask)
    intersection = np.sum(np.multiply(truth, pred))
    pred_card = len(pred[pred!=0])
    truth_card = len(truth[truth!=0])
    return 2*intersection/(pred_card + truth_card)


def main():
    f = open('log.txt', 'w')
    sys.stdout=f
    batch_size = 8
    #Specify data directory locations
    dicom_directory = '/Users/Berk/Downloads/final_data/dicoms/'
    contour_directory = '/Users/Berk/Downloads/final_data/contourfiles/'
    link_coding = '/Users/Berk/Downloads/final_data/link.csv'

    #Create dictionary of dicom files and their corresponding i and o contour files
    dicom_icontour_dict = dload.create_link_dict(dicom_directory, contour_directory, link_coding, 'icontour')
    dicom_ocontour_dict = dload.create_link_dict(dicom_directory, contour_directory, link_coding, 'ocontour')
    #Join dicom keys with both their i contour and o contour files
    joint_contour_dict = [dicom_icontour_dict, dicom_ocontour_dict]
    all_dicom_keys = list(set(dicom_icontour_dict.keys()) & set(dicom_ocontour_dict.keys()))
    all_contour_dict = {}
    for keys in all_dicom_keys:
        all_contour_dict[keys] = list(d[keys] for d in joint_contour_dict)

    #PHASE 1
    #Generate data batches os size batch_size
    dicom_and_contour = dload.batch_generation(batch_size=batch_size)
    # for p in range(int(np.floor(len(all_contour_dict)/batch_size))):
    #     input_batch, output_batch = dicom_and_contour.new_batch(all_contour_dict, image_saving=True)

    #PHASE 2
    all_outer_data=[]
    all_inner_data=[]
    all_dice = []
    for dicom, contour in all_contour_dict.iteritems():
        dicom_array, joint_mask = dicom_and_contour.load_dicom_mask(dicom, contour)
        #extract intensities from o-contours and i-contours
        o_int, i_int = intensity_extract(dicom_array, joint_mask)
        all_outer_data = np.append(all_outer_data, o_int, axis = 0)
        all_inner_data = np.append(all_inner_data, i_int, axis = 0)
        #create predicitons based on threshold intensity
        true_mask, pred_mask, dice_val = threshhold_seg(dicom_array, joint_mask, 0.14)
        all_dice.append(dice_val)
    print('T-test results comparing intensities inside blood pool (inside the i-contour) to those inside the '
          'heart muscles (between i-contour and o-contour)')
    print(stat.ttest_ind(all_outer_data, all_inner_data))

    #Plot overlap of the distributions
    dload.intensity_plot(all_outer_data, all_inner_data)
    #Side by side comparison of a true mask and predicted mask
    dload.side_by_side_mask_overlay(dicom_array, true_mask, pred_mask)
    average_dice_val = np.mean(all_dice)*100
    print('Average dice coefficient using thresholding segmetnations method: %.2f%%' % average_dice_val)
    f.close()
if __name__ == "__main__":
    main()

