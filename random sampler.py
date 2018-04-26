

##############################

import numpy as np 
import os 
import pandas as pd
import pdb

pd.set_option('display.max_rows',1000)

Controlmen_ = pd.read_excel("/mnt/macdata/groups/valcour/vishal/resampling_forNP.xlsx")
Controlmen = Controlmen_.loc[Controlmen_['AgeAtDC'] <75]
Controlmen2 = Controlmen.loc[Controlmen['AgeAtDC']>54]
#Controlmen = Controlmen_.loc[Controlmen_['AgeAtDC'] >60]
PIDN = Controlmen['PIDN']
Age = Controlmen['AgeAtDC']
Education = Controlmen['Educ']

i = 0
test = []
Age = []
meanage = []
updatedmean = [100]
groupmean = 62
updatededuc = [20]
groupeduc = 16.5

while updatedmean >= groupmean:# or updatededuc >= groupeduc:
	i += 1

	test = Controlmen2.sample(12)

	updatedmean = test['AgeAtDC'].mean()
        updatededuc = test['Educ'].mean()
	#pdb.set_trace()
	meanage.append( updatedmean)
        
	
	#standarddev = test['AgeAtDC'].std()
#print meanage
	print i, updatedmean, updatededuc

print test

#test.to_csv('/mnt/mac/Research/HIV Protocols/02 Papers/UCSF Longitudinal patterns in HAND and AD - VISHAL-BENEDETTA/Matching_groups/MCI_57_controls.csv')

#return test, meanage

#find min(meanage)
#	return test[xxx]
#	print test['PIDN']


