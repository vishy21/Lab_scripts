#!python

import pandas as pd
import numpy as np
import os
import xlsxwriter
import sys



#
# Syntax: python generate_GLM_files.py <design type>
# 	design type options:
#		1: 2-sample t-test (UNIMPLEMENTED)
#		2: multivariable regression
#
#
#
#
#
#
#
#
#
#
#
#
####################################################################
####################################################################

input_file = os.path.join("R:",os.sep,"groups","valcour","kevin","02_Local","sCD163_and_neop","analysis","diffusion","TBSS","Trio")


independent_var = "CD163_pg_ml"
covariates_names = ["Scanner","Diag","Age_screen","Sex","Race_white","Educ_yrs"]
num_ppts = 24



def do_multivariable_regression():
	