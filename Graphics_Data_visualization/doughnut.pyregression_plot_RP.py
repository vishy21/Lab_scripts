import sys
import os
import shutil
import datetime
from scipy import stats 
import pandas as pd
#import matplotlib
#matplotlib.use('Agg') # you might not need this
import matplotlib.pyplot as plt
import seaborn as sns
import pdb
pred= pd.read_excel("/mnt/macdata/groups/valcour/vishal/RP_NAB_PAOF/Final_metrics/RP_NP_version_box.xlsx")
pred['total_corpus_callosum']= ((pred["Body_of_corpus_callosum"]+pred["Genu_of_corpus_callosum"]+pred["Splenium_of_corpus_callosum"])/3)
pred['Superior_longitudinal_fasciculus'] =((pred["Superior_longitudinal_fasciculus_L"]+pred["Superior_longitudinal_fasciculus_R"])/2)
pred['Uncinate_fasciculus'] =((pred["Uncinate_fasciculus_L"]+pred["Uncinate_fasciculus_R"])/2)


ROI= 'total_corpus_callosum'
#ROI = 'Genu_of_corpus_callosum'
#ROI = 'Body_of_corpus_callosum'
#ROI = 'Splenium_of_corpus_callosum'
#ROI = 'Anterior_corona_radiata_R'
#ROI = 'Anterior_corona_radiata_L'
grouping ='ScanVersion'
NABvar = "Symptom burden"

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
    plt.title(ROItitle, fontsize=font_size, fontweight="bold")
    order      = ["V6_FA","V2_FA","V1_FA"]
    #colors     = {0:'teal',1:'red'}
    #labels     = ['No gene','C9','GRN','MAPT']
    ##box        = sns.boxplot(pred.CDR, pred.PredScore, palette="Set2", order=order)
    swrm       = sns.swarmplot(pred[grouping], pred[ROI], order=order,size=12) # pred[ROI]
    sns.boxplot(pred[grouping],pred[ROI],order = order, flierprops={'marker': 'o', 'markersize': 0}, boxprops={'facecolor':'None'})

    #handles, _ = swrm.get_legend_handles_labels()
    #swrm.legend(handles,labels,loc='upper left')
    #plt.axhline(y=0.5, color='steelblue')




    median_width=0.4
    plt.xlabel('Groups', fontsize=font_size)
    for tick, text in zip(swrm.get_xticks(), swrm.get_xticklabels()):
        sample_name = text.get_text()  # "X" or "Y"
        #pdb.set_trace()
        # calculate the median value for all replicates of either X or Y
#        pdb.set_trace()

        median_val = pred.loc[pred.ScanVersion==sample_name][ROI].mean()

        # plot horizontal lines across the column, centered on the tick
        swrm.plot([tick-median_width/2, tick+median_width/2, tick+median_width/2], [median_val, median_val, median_val],
                lw=4, color='k')




    plt.ylabel('Mean AD', fontsize=font_size, fontweight="bold")
    #plt.ylim(-0.3,12)
    #plt.savefig(os.path.join('/mnt/macdata/groups/valcour/vishal/', 'HIV_boxplot_r7_baseline.png'), dpi=300)

    plt.show() # comment out if you don't want figure to pop up          


#box_plots(pred)                           
def reg_plots(pred, ROI,NABvar):
    plt.rcParams["font.weight"] = "bold"
    plt.rcParams["xtick.labelsize"] = 20
    plt.rcParams["ytick.labelsize"] = 20

    font_size = 14
    sns.set(color_codes=True)
    dti_seq = 'ScanVersion'
    data_input = pred.loc[pred[dti_seq]=="V2_FA"]
    data_input2 = data_input.dropna(axis=0,how='any',subset=[NABvar])
    regression= sns.regplot(data_input2[ROI],data_input2[NABvar], data = data_input2, color= "g", scatter_kws={'s':60})
    slope, intercept, r_value, p_value, std_err = stats.linregress(data_input2[ROI],data_input2[NABvar])
    print ROI, NABvar, "p-value:", p_value
    #print "r-squared", r_value**2
    ks_summ = "p-value = {}\n$r^2$-value = {}".format(round(p_value,3), round(r_value**2,3))

    y_limit= (data_input2[NABvar].max())/1.05
    x_limit= (data_input2[ROI].max())/1.05
    ROItitle = ROI.replace("_"," ")
    plt.title(ROItitle, fontsize=font_size, fontweight="bold")
    plt.annotate(ks_summ, xy=(x_limit ,y_limit), xytext=(x_limit, y_limit))
    plt.xlabel('Mean FA', fontsize=font_size, fontweight="bold")
    plt.ylabel('Symptom burden', fontsize=font_size, fontweight="bold")
    plt.savefig(os.path.join('/mnt/macdata/groups/valcour/vishal/', 'FA_SLF.png'), dpi=300)



    plt.show()

#reg_plots(pred,'Body_of_corpus_callosum','Symptom burden')
#reg_plots(pred,'Genu_of_corpus_callosum','Symptom burden')
#reg_plots(pred,'Splenium_of_corpus_callosum','Symptom burden')
#reg_plots(pred,'total_corpus_callosum','Symptom burden')
#reg_plots(pred,'Superior_longitudinal_fasciculus_R','Symptom burden')
reg_plots(pred,'Superior_longitudinal_fasciculus_L','Symptom burden')
#reg_plots(pred,'Superior_longitudinal_fasciculus','Symptom burden')
#reg_plots(pred,'Uncinate_fasciculus_R','Symptom burden')
#reg_plots(pred,'Uncinate_fasciculus_L','Symptom burden')
#reg_plots(pred,'Uncinate_fasciculus','Symptom burden')


#reg_plots(pred,'Body_of_corpus_callosum','t_score_avg')
#reg_plots(pred,'Genu_of_corpus_callosum','t_score_avg')
#reg_plots(pred,'Splenium_of_corpus_callosum','t_score_avg')
#reg_plots(pred,'total_corpus_callosum','t_score_avg')
#reg_plots(pred,'Superior_longitudinal_fasciculus_R','t_score_avg')
#reg_plots(pred,'Superior_longitudinal_fasciculus_L','t_score_avg')
#reg_plots(pred,'Superior_longitudinal_fasciculus','t_score_avg')
#reg_plots(pred,'Uncinate_fasciculus_R','t_score_avg')
#reg_plots(pred,'Uncinate_fasciculus_L','t_score_avg')
#reg_plots(pred,'Uncinate_fasciculus','t_score_avg')




