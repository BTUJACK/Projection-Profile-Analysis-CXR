#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import math
import operator, collections
import numpy as np
import scipy.ndimage
import matplotlib.pyplot as plt

from features import extract_features
from save_features import feature_vector, dump, load, label_vec

data_dir = '../data/CXR_png_complete/'

# 0 - black, 255 - white

def profile_one_dim(im):
    im = gray_level(im)
    print(np.shape(im))
    vertical_sum = np.sum(im, axis=0)/np.shape(im)[1]
    fig = plt.figure(0)
    fig.canvas.set_window_title('Projection Profile - ' + filename)
    plt.plot(vertical_sum)
    # plt.show()
    P, X, Y = zone_division(im, vertical_sum)

    density_symmetry, roughness_max, roughness_symmetry = extract_features(im, P, X, Y)
    fv = feature_vector(density_symmetry, roughness_max, roughness_symmetry, filename)
    all_vector.append(fv)
    # print(all_vector)

def gray_level(im):
    num_of_gray_levels = len(np.unique(im))
    image_bit = math.log(num_of_gray_levels, 2)
    '''
    Initialise a gray_level_hist list with all zeros. Indices
    denote the gray level, value at index denote the count.
    '''
    # VERY SLOW
    # gray_level_hist = np.zeros(2**image_bit)
    # for x in im:
    #   for y in x:
    #       gray_level_hist[y]+=1
    # print(gray_level_hist)

    unique, counts = np.unique(im, return_counts=True)
    gray_level_hist_dict = dict(zip(unique, counts))    # keys denote gray_level, values denote gray level count
    '''
    background_value :- is the gray level at which the peak appears
    close to the maximum value in the gray level histogram.
    '''
    background_value = max(gray_level_hist_dict.items(), key=operator.itemgetter(1))[0]
    # print(background_value, gray_level_hist_dict[background_value])
    normalized_im = np.divide(im, background_value)
    return normalized_im

def zone_division(im, vertical_sum):
    low = math.floor(0.25*len(vertical_sum))
    high = math.floor(0.50*len(vertical_sum))
    '''
    mini = min(vertical_sum[low:high])
    ind = list(vertical_sum).index(mini)
    x_right = []
    for x in im:
        # print(x[ind])
        x_right.append(255 - x[ind])
    # print(x_right)
    '''

    '''
    x_right = math.floor(len(vertical_sum)/4)
    print(x_right, 'div')
    vertical_profile_at_xright(im, x_right)
    '''

    # x_right = list(vertical_sum).index(max(vertical_sum[low:high]))
    x_right = np.argmax(vertical_sum[low:high])
    print(x_right, 'x_right')
    vert_prof = vertical_profile_at_xright(im, x_right)

    # For ytop
    def ytop():
        low = math.floor(0.05*len(vert_prof))
        high = math.floor(0.50*len(vert_prof))
        ytopv = min(vert_prof[low:high])
        # ytopv = min(vert_prof[low:high])
        # ytopi = vert_prof.index(ytopv)
        ytopi = np.argmin(np.asarray(vert_prof[low:high])) + low

        print(ytopi, 'y-top index')
        fig = plt.figure(0)
        fig.canvas.set_window_title('Vertical Profile at x_right - ' + filename)
        plt.plot(vert_prof)
        # plt.show()
        return ytopi


    # For ybottom
    def ybottom():
        low = math.floor(0.51*len(vert_prof))
        high = math.floor(0.95*len(vert_prof))
        vert_prof_derivative = np.zeros(len(vert_prof))
        '''Calculate derivative using finite difference
            f'(x) = f(x+h) - f(x)/h'''
        h = 20
        for i in range(0, len(vert_prof)-h):
            vert_prof_derivative[i] = ((vert_prof[i+h] - vert_prof[i])/h)
        ybottomv = min(vert_prof_derivative[low:high])
        # ybottomi = list(vert_prof_derivative[low:high]).index(ybottomv) + low
        ybottomi = np.argmin(np.asarray(vert_prof_derivative[low:high])) + low
        print(ybottomi, 'y-bottom index')

        fig = plt.figure(0)
        fig.canvas.set_window_title('Vertical Profile Derivative at x_right - ' + filename)
        plt.plot(vert_prof_derivative)
        # plt.show()
        return ybottomi

    ytopi = ytop()
    ybottomi = ybottom()

    y1 = ytopi + math.floor(0.25*(ybottomi-ytopi))
    y2 = ytopi + math.floor(0.5*(ybottomi-ytopi))
    y3 = ytopi + math.floor(0.75*(ybottomi-ytopi))
    # Y contains the indices at which the zones are divided.
    Y = [ytopi, y1, y2, y3, ybottomi]
    # print(Y)

    '''Local zone based projection profile'''
    Pz1, Pz2, Pz3, Pz4 = ([] for _ in range(4))
    def chunks(start_row, end_row):
        div_param = end_row - start_row + 1
        return div_param
    
    Pz1 = np.sum(im[ytopi:y1], axis=0)/chunks(ytopi, y1)
    Pz2 = np.sum(im[y1:y2], axis=0)/chunks(y1, y2)
    Pz3 = np.sum(im[y2:y3], axis=0)/chunks(y2, y3)
    Pz4 = np.sum(im[y3:ybottomi], axis=0)/chunks(y3, ybottomi)
    P = [Pz1, Pz2, Pz3, Pz4]
    # print(P)

    fig = plt.figure(0)
    fig.canvas.set_window_title('Zone wise projection profile - ' + filename)
    ax = plt.subplot(111)
    # plt.plot(Pz1, 'r', Pz2, 'g', Pz3, 'b', Pz4, 'r--')
    ax.plot(Pz1, 'r', label = 'Projection Profile for zone 1')
    ax.plot(Pz2, 'g', label = 'Projection Profile for zone 2')
    ax.plot(Pz3, 'b', label = 'Projection Profile for zone 3')
    ax.plot(Pz4, 'r--', label = 'Projection Profile for zone 4')
    ax.legend()
    # plt.show()
    
    X = points_vector(P, vertical_sum)
    # print(X)
    
    return P, X, Y


def points_vector(P, vertical_sum):
    X = np.zeros((4, 5))
    '''
    X(4, 5) - 4 rows, one each for each local zone projection profile
    X = [[xrrib  xrlung  xcenter    xllung  xlrib],
         .
         .
         [xrrib  xrlung  xcenter    xllung  xlrib]]
    '''
    for i in range(0, len(P)):
        # print(len(P[i]))
        # x_center
        low = math.floor(0.25*len(P[i]))
        high = math.floor(0.75*len(P[i]))
        xc = np.argmin(np.asarray(P[i][low:high])) + low
        X[i][2] = xc

        # xrlung
        low = math.floor(0.125*len(P[i]))
        high = xc
        xrlung = np.argmax(np.asarray(P[i][low:high])) + low
        X[i][1] = xrlung

        # xllung
        low = xc + 1
        high = math.floor(0.875*len(P[i]))
        xllung = np.argmax(np.asarray(P[i][low:high])) + low
        X[i][3] = xllung

        # xrrib
        low = 0
        high = xrlung
        xrrib = np.argmin(np.asarray(P[i][low:high]))
        X[i][0] = xrrib

        # xlrib
        low = xllung + 1
        high = len(P[i]) - 1
        xlrib = np.argmin(np.asarray(P[i][low:high])) + low
        X[i][4] = xlrib

    return X.astype(int)


def vertical_profile_at_xright(im, x_right):
    vert_prof = []
    for x in im:
        vert_prof.append(x[x_right])
    return vert_prof


if __name__ == '__main__':
    global filename, all_vector
    all_vector = []
    count = 0
    for image in os.listdir(data_dir):
        filename = str(image)
        print('Processing: {0}'.format(filename))
        im = scipy.ndimage.imread(data_dir + image, flatten=True)
        profile_one_dim(im)
        print('Processed: {0}'.format(filename))
        count += 1
        print('Files processed: {0}'.format(count))
    dump(all_vector, 'features_complete.pkl')
    label_vec(all_vector)