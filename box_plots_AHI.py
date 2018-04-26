import sys
import os
import shutil
import datetime

import pandas as pd
#import matplotlib
#matplotlib.use('Agg') # you might not need this
import matplotlib.pyplot as plt
import seaborn as sns
import pdb
pred= pd.read_excel("/mnt/macdata/groups/valcour/vishal/Copy of full_set_FA.xlsx")
#pred=pred[pred.PIDN != 512]
#pred=pred[pred.PIDN != 514]

#ROI = 'Genu_of_corpus_callosum'
ROI = 'Body_of_corpus_callosum'
#ROI = 'Superior_longitudinal_fasciculus_R'
#ROI = 'Splenium_of_corpus_callosum'
#ROI = 'Anterior_corona_radiata_R'
#ROI = 'Anterior_corona_radiata_L'


def box_plots(pred):
    sns.set_style("darkgrid")
    plt.rcParams["font.weight"] = "bold"
    plt.rcParams["axes.labelweight"] = "bold"
    plt.rc('xtick', labelsize=18)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=18)    # fontsize of the tick labels

    #pred = pred.groupby('hivstat').first().reset_index()
    font_size  = 18
    plt.figure(figsize=(12,7))
    #plt.title('(Logistic) CDR vs Regression Score, all time points', fontsize=font_size)
    ROItitle = ROI.replace("_"," ")
    plt.title(ROItitle, fontsize=24, fontweight="bold")
    order      = ["HIV-","cART exposed","no cART"]
    #colors     = {0:'teal',1:'red'}
    #labels     = ['No gene','C9','GRN','MAPT']
    ##box        = sns.boxplot(pred.CDR, pred.PredScore, palette="Set2", order=order)
    swrm       = sns.swarmplot(pred.cART_status, pred[ROI], order=order,size=12, palette="GnBu_d", edgecolor= "black", linewidth=2) # pred[ROI]
    sns.boxplot(pred.cART_status,pred[ROI],order = order, flierprops={'marker': 'o', 'markersize': 0}, boxprops={'facecolor':'None'}, linewidth=2.5)

    #handles, _ = swrm.get_legend_handles_labels()
    #swrm.legend(handles,labels,loc='upper left')
    #plt.axhline(y=0.5, color='steelblue')

    median_width=0.4
    plt.xlabel('Groups', fontsize=font_size)
    for tick, text in zip(swrm.get_xticks(), swrm.get_xticklabels()):
        sample_name = text.get_text()  # "X" or "Y"
        #pdb.set_trace()
        # calculate the median value for all replicates of either X or Y
        #pdb.set_trace()

        median_val = pred.loc[pred.cART_status==sample_name][ROI].mean()
        stdev_above = median_val + 2*(pred.loc[pred.cART_status==sample_name][ROI].std())
        stdev_below = median_val - 2*(pred.loc[pred.cART_status==sample_name][ROI].std())

        #print stdev_above
        #print median_val
        #print stdev_below


        # plot horizontal lines across the column, centered on the tick
        swrm.plot([tick-median_width/2, tick+median_width/2, tick+median_width/2], [median_val, median_val, median_val],
                lw=4, color='gray')
        swrm.plot([tick-median_width/5, tick+median_width/5, tick+median_width/5], [stdev_below, stdev_below, stdev_below],
                lw=4, color='gray')
        swrm.plot([tick-median_width/5, tick+median_width/5, tick+median_width/5], [stdev_above, stdev_above, stdev_above],
                lw=4, color='gray')



    plt.ylabel('Mean FA', fontsize=font_size, fontweight="bold")
    #plt.ylim(-0.3,12)
    plt.savefig(os.path.join('/mnt/macdata/groups/valcour/vishal/', 'HIV_boxplot_r8_baseline.png'), dpi=300)

    plt.show() # comment out if you don't want figure to pop up          

box_plots(pred)                           