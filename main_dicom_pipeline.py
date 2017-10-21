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
import pylab

def create_link_dict(dicom_directory, contour_directory, link_csv):
    '''
    :param dicom_directory: directory of where dicom folders are stored
    :param contour_directory: directory of where contour folders are stored
    :param link_csv: csv containing the links between dicom folders and contour folders
    :return: dictionary of respective .dcm files and their corresponding contour .txt files
    '''
    directory_link={}
    with open(link_csv, 'rb') as f:
        reader = csv.reader(f)
        #Skip the headers of the .csv file
        reader.next()
        for row in reader:
            #directory_link[os.path.join(dicom_directory+row[0])+'/']=os.path.join(contour_directory+row[1],'i-contours')
            directory_link[os.path.join(dicom_directory + row[0])] = os.path.join(contour_directory + row[1],
                                                                                        'i-contours/')
        dicom_contour_pairs={}
        for key, val in directory_link.items():
            contour_files = [val + t for t in os.listdir(val) if isfile(join(val, t)) and t.endswith('.txt')]
            # Extract the slice the contour file corresponds to by taking the 4 digits before the 'icontour' in the
            # contour path file name
            contour_slices = [int(s[s.find('icontour')-5:s.find('icontour')-1]) for s in contour_files]
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
                        print('%s does not appear to have corresponding contour file' % dicom_file)
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
    def __init__(self, batch_size):
        self.batch_size = batch_size

    def load_dicom_mask(self, dicom_file_dir, contour_file_dir):
        ''' General function to load dicoms and contours into arrays

        :param dicom_file_dir: file path to dicom file
        :param contour_file_dir: file path to contour txt file corresponding to dicome file
        :return: dicom_array is the 256 x256 array representing the MRI slice, contour_mask is a binary mask
                separating "the left ventricular blood pool from the heart muscle"

        '''

        dicom_array = parse.parse_dicom_file(dicom_file_dir)
        dicom_array = dicom_array['pixel_data']
        contour_coords = parse.parse_contour_file(contour_file_dir)
        height = dicom_array.shape[0]
        width = dicom_array.shape[1]
        if height!=256 and width!=256:
            print('%s does not have correct 225 x 225 dimensions. Potentially look into')
        contour_mask = parse.poly_to_mask(contour_coords, height, width)
        contour_mask = np.asarray(contour_mask, dtype=np.int)
        return dicom_array, contour_mask

    # Function that actually generates batch array for input images and output masks, both of size
    # 256 x 256 x batch size
    def new_batch(self, dicom_contour_pairs):
        ''' Function that actually generates batch array for input images and output masks, both of size
        256 x 256 x batch size

        :param dicom_contour_pairs: dictionary of all dicom file paths and their corresponding countoru file paths
        :return: input_batch is an array of batch size # of stacked images and output_batch is the stacked masks
        '''
        n_data = len(dicom_contour_pairs)
        if n_data % self.batch_size !=0:
            sys.exit('Warning: batch size is not divisble by total number of data points')
        batches_to_complete = n_data/self.batch_size
        all_dicoms = list(dicom_contour_pairs.keys())
        #This randomly shuffles the data at the beggining of each new epoch to meet the requirements of Part 2: #3
        if self.new_batches_completed ==0:
            random.shuffle(all_dicoms)
            self.start = 0
        first=True
        for b in range(self.start, self.start + self.batch_size):
            dicom_array, contour_mask = self.load_dicom_mask(all_dicoms[b], dicom_contour_pairs[all_dicoms[b]])
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


def main():
    f = open('log.txt', 'w')
    sys.stdout=f
    batch_size = 8
    dicom_directory = '/Users/Berk/Downloads/final_data/dicoms/'
    contour_directory = '/Users/Berk/Downloads/final_data/contourfiles/'
    link_coding = '/Users/Berk/Downloads/final_data/link.csv'
    dicom_contour_dict = create_link_dict(dicom_directory, contour_directory, link_coding)
    dicom_and_contour = batch_generation(batch_size=batch_size)

    image_count=0
    for p in range(len(dicom_contour_dict)/batch_size):
        input_batch, output_batch = dicom_and_contour.new_batch(dicom_contour_dict)
        for im in range(batch_size):
            mask = output_batch[:,:,im]
            mask = np.ma.masked_where(mask==0, mask)
            plt.imshow(input_batch[:,:,im], cmap=mpl.cm.bone)
            plt.imshow(mask, cmap=mpl.cm.jet_r, interpolation='nearest')
            pylab.savefig(str(image_count) + '.png')
            image_count+=1

    f.close()

if __name__ == "__main__":
    main()

