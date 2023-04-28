#!/usr/bin/python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name        : calc_crps.py
# Description : Calculate CRPS from .csv file.
#
# Authors     : William A. Romero R.  <romero@creatis.insa-lyon.fr>
#                                     <contact@waromero.com>
#-------------------------------------------------------------------------------
import os
import sys
import argparse

from myosaiq import VolumesCDF


if __name__ == '__main__':
    """
    Example:

    [mainframe@user myosaiq]$ ./calc_crps.py -f ./data/MYO_volumes.csv
    """

    cmdLineParser = argparse.ArgumentParser(description='Calculate CRPS from a .csv file.')
    #_________COMMAND-LINE_OPTIONS_________
    cmdLineParser.add_argument("-v", "--version",   action='version', version='%(prog)s 0.1.0 - Calculate CRPS.')
    cmdLineParser.add_argument("-f", "--file", dest="cdf_file",  help="CSV file with cumulative distributions. Check test data for examples.", required=True)
   
    cmdLineArgs = cmdLineParser.parse_args()

    CDF_FILE_PATH = cmdLineArgs.cdf_file

    volumes = VolumesCDF( CDF_FILE_PATH )

    crps = volumes.CalcCRPS()

    print("\nCRPS = %.4f\n" %  crps)

