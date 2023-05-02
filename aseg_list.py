#!/usr/bin/python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name        : aseg_list.py
# Description : Assess a set of segmentations.
#
# Authors     : William A. Romero R.  <romero@creatis.insa-lyon.fr>
#                                     <contact@waromero.com>
#-------------------------------------------------------------------------------
import os
import sys
import argparse

import pandas as pd
from myosaiq import AssessSegmentations


if __name__ == '__main__':
    """
    Example:

    [mainframe@user myosaiq]$ ./aseg_list.py -i ./data/Segmentations.csv -o ./ResultsSegmentations.csv 
    """

    cmdLineParser = argparse.ArgumentParser(description='Calculate evaluation metrics for a set of segmentations.')
    #_________COMMAND-LINE_OPTIONS_________
    cmdLineParser.add_argument("-v", "--version",   action='version', version='%(prog)s 0.1.0 - Assess Segmentations.')
    cmdLineParser.add_argument("-i", "--input",  dest="input_csv_file",  help="Input CSV file with two columns: <REFERENCE FILE>, <TARGET FILE>. Check test data for examples.", required=True)
    cmdLineParser.add_argument("-o", "--output", dest="output_csv_file", help="Output CSV file with results.", required=True)   

    cmdLineArgs = cmdLineParser.parse_args()

    INPUT_CSV_FILE_PATH = cmdLineArgs.input_csv_file
    OUTPUT_CSV_FILE_PATH = cmdLineArgs.output_csv_file

    """
    ----------------------------------------------------------------------------
    1. Create an instance of the AssessSegmentations class
.   ----------------------------------------------------------------------------
    """    
    aSegmentations = AssessSegmentations( INPUT_CSV_FILE_PATH )

    print( aSegmentations )

    
    """
    ----------------------------------------------------------------------------
    2. Calculate metrics and export results.
.   ----------------------------------------------------------------------------
    """  
    
    aSegmentations.Compute()

    evaluationResults = aSegmentations.GetDataFrame()

    # Retrieve specific data: Left-Ventricle volume stats
    statsReference = evaluationResults.loc[evaluationResults['SEGMENTATION ID'].isin(['REFERENCE AVG'])]    
    statsTarget = evaluationResults.loc[evaluationResults['SEGMENTATION ID'].isin(['TARGET AVG'])]

    pd.options.display.float_format = '{:18,.3f}'.format

    print("\n",statsReference,"\n\n",statsTarget )

    aSegmentations.ToCSV( OUTPUT_CSV_FILE_PATH )
