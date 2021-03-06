'''
Berk Norman
Pipeline for reading in dicoms and corresponding contour data
'''
import dicom_parse_functions as parse
import csv
import os
from os.path import isfile, join
import numpy as np
import random
import sys
import matplotlib.pyplot as plt
import matplotlib as mpl

def create_link_dict(dicom_directory, contour_directory, link_csv, contour_type, warnings=False):
    '''
    :param dicom_directory: directory of where dicom folders are stored
    :param contour_directory: directory of where contour folders are stored
    :param link_csv: csv containing the links between dicom folders and contour folders
    :param contour_type: string specifying much type of contour to generate, must either be 'icontour' or 'ocontour'
    :param warnings: if set to true, dicom directory will be returned if there is no corresponding contour file fore it.
    default value is false
    :return: dictionary of respective .dcm files and their corresponding contour .txt files
    '''
    directory_link={}
    if contour_type == 'icontour':
        contour_sub_dir = 'i-contours/'
    elif contour_type == 'ocontour':
        contour_sub_dir = 'o-contours/'
    else:
        sys.exit('Invalid contour_type. Must either be icontour or ocontour')
    with open(link_csv, 'rb') as f:
        reader = csv.reader(f)
        #Skip the headers of the .csv file
        reader.next()
        for row in reader:
            directory_link[os.path.join(dicom_directory + row[0])] = os.path.join(contour_directory + row[1],
                                                                                        contour_sub_dir)
        dicom_contour_pairs={}
        for key, val in directory_link.items():
            contour_files = [val + t for t in os.listdir(val) if isfile(join(val, t)) and t.endswith('.txt')]
            # Extract the slice the contour file corresponds to by taking the 4 digits before the 'icontour' in the
            # contour path file name
            contour_slices = [int(s[s.find(contour_type)-5:s.find(contour_type)-1]) for s in contour_files]
            for d in os.listdir(key):
                dicom_file = join(key, d)
                if isfile(dicom_file) and dicom_file.endswith('.dcm'):
                    dicom_num = int(d[:-4])
                    #Match dicom file slice with contour slice number, print to log if the dicom slice does not have
                    # corresponding contour file
                    try:
                        contour_ind = contour_slices.index(dicom_num)
                        dicom_contour_pairs[dicom_file]=contour_files[contour_ind]
                    except:
                        if warnings:
                            print('%s does not appear to have corresponding %s file' % (dicom_file, contour_type))
    return dicom_contour_pairs

class batch_generation:
    '''
    Class that allows for batch generation of dicom and corresponding contours.
    Also keeps track of how many epochs have been completed given the number of times the batch generation function
    has been called.
    '''
    epochs_completed = 0
    new_batches_completed = 0
    start = 0
    all_dicoms = []
    image_count = 0
    def __init__(self, batch_size):
        self.batch_size = batch_size

    def load_dicom_mask(self, dicom_file_dir, contour_file_dir, image_saving = False):
        ''' General function to load dicoms and contours into arrays

        :param dicom_file_dir: file path to dicom file
        :param contour_file_dir: file path to contour txt file corresponding to dicome file
        :param image_saving: specify if images of dicoms with contour masks should be saved for examination of validity
        of contour parsing functions
        :return: dicom_array is the 256 x256 array representing the MRI slice, contour_mask is a binary mask
                separating "the left ventricular blood pool from the heart muscle"

        '''
        dicom_array = parse.parse_dicom_file(dicom_file_dir)
        dicom_array = dicom_array['pixel_data']
        height = dicom_array.shape[0]
        width = dicom_array.shape[1]
        if height!=256 and width!=256:
            print('%s does not have correct 225 x 225 dimensions. Potentially look into')
        inner_contour_coords = parse.parse_contour_file(contour_file_dir[0])
        inner_contour_mask = parse.poly_to_mask(inner_contour_coords, height, width)
        inner_contour_mask = np.asarray(inner_contour_mask, dtype=np.int)

        outer_contour_coords = parse.parse_contour_file(contour_file_dir[1])
        outer_contour_mask = parse.poly_to_mask(outer_contour_coords, height, width)
        outer_contour_mask = np.asarray(outer_contour_mask, dtype=np.int)

        joint_mask=outer_contour_mask+inner_contour_mask
        if image_saving:
            current_dir = os.getcwd()
            mask_checking = join(current_dir, 'mask_checking')
            if not os.path.exists(mask_checking):
                os.makedirs(mask_checking)
            contour_mask = np.ma.masked_where(joint_mask == 0, joint_mask)
            plt.imshow(dicom_array, cmap=mpl.cm.bone)
            plt.imshow(contour_mask, cmap=mpl.cm.jet_r, interpolation='nearest')
            plt.axis('off')
            plt.savefig(join(mask_checking, 'joint_' + str(self.image_count) + '.png'))
            plt.close()
            self.image_count += 1
        return dicom_array, joint_mask

    def data_shuffler(self, dicom_contour_pairs):
        '''

        :param dicom_contour_pairs: dictionary of all dicom file paths and their corresponding contour file paths.
        This function is only called on the first iteration of each new epoch. It randomly shuffles all of the data and
        randomly removes the remainder of data set size / batch size
        '''
        n_data = len(dicom_contour_pairs)
        self.all_dicoms = list(dicom_contour_pairs.keys())
        random.shuffle(self.all_dicoms)
        extra_data = n_data % self.batch_size
        if extra_data != 0:
            print(
            'Warning: batch size is not divisble by total number of data points. Randomly deleting remainder %d iterations for this epoch' % extra_data)
            for i in range(extra_data):
                self.all_dicoms.remove(random.choice(self.all_dicoms))

    def new_batch(self, dicom_contour_pairs, image_saving):
        ''' Function that actually generates batch array for input images and output masks, both of size
        256 x 256 x batch size

        :param dicom_contour_pairs: dictionary of all dicom file paths and their corresponding countoru file paths
        :param image_saving: specify if images of dicoms with contour masks should be saved for examination of validity
        of contour parsing functions
        :return: input_batch is an array of batch size # of stacked images and output_batch is the stacked masks
        '''
        n_data = len(dicom_contour_pairs)
        batches_to_complete = n_data/self.batch_size
        #This randomly shuffles the data at the beggining of each new epoch to meet the requirements of Part 2: #3
        if self.new_batches_completed ==0:
            self.data_shuffler(dicom_contour_pairs)
            self.start = 0

        first=True
        for b in range(self.start, self.start + self.batch_size):
            dicom_array, contour_mask = self.load_dicom_mask(self.all_dicoms[b], dicom_contour_pairs[self.all_dicoms[b]], image_saving)
            dicom_array = np.expand_dims(dicom_array, axis=-1)
            contour_mask = np.expand_dims(contour_mask, axis=-1)
            if first:
                input_batch = dicom_array
                output_batch = contour_mask
                first = False
            else:
                input_batch = np.concatenate((input_batch, dicom_array), axis=-1)
                output_batch = np.concatenate((output_batch, contour_mask), axis=-1)
        self.start += self.batch_size
        self.new_batches_completed+=1
        #Restart batch count once epoch is complete
        if self.new_batches_completed==batches_to_complete:
            self.new_batches_completed=0
            self.epochs_completed+=1
            print('%d epoch complete' % self.epochs_completed)
        return input_batch, output_batch


def intensity_plot(all_outer_data, all_inner_data):
    '''

    :param all_outer_data: 1D array of all intensity data from area between heart muscle and the blood pool
    :param all_inner_data: 1D array of all intensity data from blood pool
    :return: saves plot of overlayed histogram of the two intensity distributions
    '''
    bins = np.linspace(0, 1, 100)
    plt.hist(all_outer_data, bins, alpha=0.5, label='Inside Heart Muscle')
    plt.hist(all_inner_data, bins, alpha=0.5, label='Blood Pool')
    plt.xlabel('0-1 normalized dicom intensities')
    plt.legend(loc='upper right')
    plt.savefig('density_comparison.png')
    plt.close()

def side_by_side_mask_overlay(dicom, true_mask, pred_mask):
    '''

    :param dicom: array from dicom file
    :param true_mask: true segmentation mask of blood pool
    :param pred_mask: predicted segmentation mask of blood pool
    :return: side by side image of true segmentation mask overlayed on corresponding dicom
    with predicted contour mask overlayed on corresponding dicom
    '''
    true_mask = np.ma.masked_where(true_mask == 0, true_mask)
    pred_mask = np.ma.masked_where(pred_mask == 0, true_mask)
    f, axarr = plt.subplots(1, 2)
    axarr[0].imshow(dicom,cmap=mpl.cm.bone)
    axarr[0].imshow(true_mask, cmap=mpl.cm.jet_r, interpolation='nearest')
    axarr[0].set_title('True blood pool\n segmentation')
    axarr[0].axis('off')

    axarr[1].imshow(dicom,cmap=mpl.cm.bone)
    axarr[1].imshow(pred_mask, cmap=mpl.cm.jet_r, interpolation='nearest')
    axarr[1].set_title('Threshold predicted blood\n pool segmentation')
    axarr[1].axis('off')
    plt.savefig('true_contour_vs_pred_contour.png')
    plt.close()