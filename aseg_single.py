#!/usr/bin/python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name        : aseg_single.py
# Description : Assess a single segmentation.
#
# Authors     : William A. Romero R.  <romero@creatis.insa-lyon.fr>
#                                     <contact@waromero.com>
#-------------------------------------------------------------------------------
import argparse

from myosaiq import AssessSegmentation


if __name__ == '__main__':
    """
    Example:

    [mainframe@user myosaiq]$ ./aseg_single.py -r ./references/RefSegmentation_01.nii.gz -t ./TarSegmentation.nii.gz
    """

    cmdLineParser = argparse.ArgumentParser(description='Calculate evaluation metrics.')
    #_______COMMAND-LINE OPTIONS_____
    cmdLineParser.add_argument("-v", "--version",  action='version', version='%(prog)s 0.1.0 - Assess Segmentation.')
    cmdLineParser.add_argument("-r", "--reference", dest="reference_file",  help="Reference segmentation (File path ./<PATH>/RefSegmentation.nii).", required=True)
    cmdLineParser.add_argument("-t", "--target",    dest="target_file",     help="Target segmentation (File path ./<PATH>/TarSegmentation.nii).", required=True)

    cmdLineArgs = cmdLineParser.parse_args()

    REFERENCE_SEGMENTATION_FILE_PATH = cmdLineArgs.reference_file
    TARGET_SEGMENTATION_FILE_PATH = cmdLineArgs.target_file

    """
    ----------------------------------------------------------------------------
    1. Create an instance of the AssessSegmentation class
.   ----------------------------------------------------------------------------
    """
    aSegmentation = AssessSegmentation( REFERENCE_SEGMENTATION_FILE_PATH, 
                                        TARGET_SEGMENTATION_FILE_PATH )

    print( aSegmentation )
    
    """
    ----------------------------------------------------------------------------
    2. Calculate metrics and print results.
.   ----------------------------------------------------------------------------
    """    
    aSegmentation.Compute()
    aSegmentation.PrintSingleMetrics()
