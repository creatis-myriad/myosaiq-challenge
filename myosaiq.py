#!/usr/bin/python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name        : myosaiq.py
# Description : Default parameters, baseline classes and functions.
#
# Authors     : William A. Romero R.  <romero@creatis.insa-lyon.fr>
#                                     <contact@waromero.com>
#-------------------------------------------------------------------------------
import os
import traceback

from pathlib import Path

import numpy as np
import pandas as pd
import SimpleITK as sitk


#-------------------------------------------------------------------------------
# DEFS
#-------------------------------------------------------------------------------
LEFT_VENTRICULAR_CAVITY = 1
MYOCARDIUM = 2
MYOCARDIAL_INFARCTION = 3
MVO = 4

LABEL = { LEFT_VENTRICULAR_CAVITY:"LV",
          MYOCARDIUM:"MYO",
          MYOCARDIAL_INFARCTION:"MI",
          MVO:"MVO" }

METRIC = [ "VOLUME",
           "VOLUME MAE",
           "VOLUME CC",
           "VOLUME LOA"
           "DICE",
           "HD",
           "ASSD" ]

ROUND_DECIMALS = 4
ROUND_DECIMALS_ASSD_HD = 3  # Default 3
ROUND_DECIMALS_DICE = 3     # Default 3
ROUND_DECIMALS_VOLUME = 1   # Default 1

MAX_VOLUME = 600            # in mL

MM_TO_ML_FACTOR = 0.001

#-------------------------------------------------------------------------------
# Core classes and functions.
#-------------------------------------------------------------------------------
class AssessSegmentations( object ):
    """
    Input file list manager class.
    """
    def __init__( self, inputFilePath ):
        """
        Default constructor.
        """
        self.FILE_PATH = None
        self.NUM_SEGMENTATIONS = 0

        self.segmentationsData = None
        self.referenceList = None
        self.targetList = None

        self.assessments = []

        self.overallReferenceMetrics = MyosaiqMetrics("REFERENCE AVG")
        self.overallTargetMetrics = MyosaiqMetrics("TARGET AVG")

        if verifyFile( inputFilePath ):
            self.FILE_PATH = inputFilePath
            self.__Load()
        else:
            print("[AssessSegmentations] File does not exist!")


    def __str__( self ):
        """
        Default String obj.
        """
        assessSegmentationsStr = "\n[AssessSegmentations]\n\n"
        assessSegmentationsStr += "Input file: \n\t%s\n\n" % self.FILE_PATH

        if self.referenceList is not None:
            assessSegmentationsStr += "Contents (File paths REFERENCE <- TARGET) : \n"
            for index, row in self.referenceList.iterrows():
                assessSegmentationsStr += "\t" + row[0]
                assessSegmentationsStr += "  <-  " + self.targetList.iloc[index]["TARGET"]
                assessSegmentationsStr += "\n" 
            assessSegmentationsStr += "\nTotal: %d segmentations.\n\n" % self.NUM_SEGMENTATIONS

        return assessSegmentationsStr


    def __Load( self ):
        """
        Load segmentation file list from csv file.
        """
        try:
            self.segmentationsData = pd.read_csv( self.FILE_PATH, sep="," )
            self.referenceList = self.segmentationsData[ ["REFERENCE"] ]
            self.targetList = self.segmentationsData[ ["TARGET"] ]
            self.NUM_SEGMENTATIONS = int( self.referenceList.count() )

        except Exception as exception:
            print("[AssessSegmentations::Load Exception] %s" % str(exception))
            print("[AssessSegmentations::Load Exception] %s" % str(traceback.format_exc()))


    def Compute( self ):
        """
        Calculate metrics
        """
        if self.FILE_PATH is None:
            print("[AssessSegmentations::Compute] Finished!")
            return

        print("[AssessSegmentations::Compute] Executing ...")
                  
        assessmentPlan = self.__VerifyFilePaths()

        for segmentation in assessmentPlan:
            aseg = AssessSegmentation( segmentation[0],  # Reference 
                                       segmentation[1] ) # Target
            aseg.Compute()
            
            self.assessments.append( aseg )

        for key in LABEL:

            refVolume = []
            refVolumeAD = []
            refDICE = []
            refHD = []
            refASSD = []

            tarVolume = []
            tarVolumeAD = []
            tarDICE = []
            tarHD = []
            tarASSD = []            

            for seg in self.assessments:
                refVolume.append(  seg.referenceMetrics.VOLUME[key].value )
                refVolumeAD.append(seg.referenceMetrics.VOLUME_MAE[key].value)
                refDICE.append(    seg.referenceMetrics.DICE[key].value)
                refHD.append(      seg.referenceMetrics.HD[key].value)
                refASSD.append(    seg.referenceMetrics.ASSD[key].value)

                tarVolume.append(  seg.targetMetrics.VOLUME[key].value )
                tarVolumeAD.append(seg.targetMetrics.VOLUME_MAE[key].value)
                tarDICE.append(    seg.targetMetrics.DICE[key].value)
                tarHD.append(      seg.targetMetrics.HD[key].value)
                tarASSD.append(    seg.targetMetrics.ASSD[key].value)

            self.overallReferenceMetrics.VOLUME[key].value = np.mean(refVolume)
            self.overallReferenceMetrics.VOLUME[key].std = np.std(refVolume)

            actual, predicted = np.array(refVolume), np.array(tarVolume)
            mae = float( np.mean( np.abs(actual - predicted) ) )

            # print( np.corrcoef(actual, predicted) )
            
            coco = np.corrcoef(actual, predicted)[0,1].tolist()

            self.overallReferenceMetrics.VOLUME_MAE[key].value = mae
            self.overallReferenceMetrics.VOLUME_CC[key].value = coco

            self.overallReferenceMetrics.VOLUME_LOA[key].value = 1.96 * self.overallReferenceMetrics.VOLUME[key].std
            
            self.overallReferenceMetrics.DICE[key].value = np.mean(refDICE)
            self.overallReferenceMetrics.DICE[key].std = np.std(refDICE,0)

            self.overallReferenceMetrics.HD[key].value = np.mean(refHD)
            self.overallReferenceMetrics.HD[key].std = np.std(refHD)

            self.overallReferenceMetrics.ASSD[key].value = np.mean(refASSD)
            self.overallReferenceMetrics.ASSD[key].std = np.std(refASSD) 

            self.overallTargetMetrics.VOLUME[key].value = np.mean(tarVolume)
            self.overallTargetMetrics.VOLUME[key].std = np.std(tarVolume,0)

            self.overallTargetMetrics.VOLUME_MAE[key].value = mae
            self.overallTargetMetrics.VOLUME_CC[key].value = coco

            self.overallTargetMetrics.VOLUME_LOA[key].value = 1.96 * self.overallTargetMetrics.VOLUME[key].std
            
            self.overallTargetMetrics.DICE[key].value = np.mean(tarDICE)
            self.overallTargetMetrics.DICE[key].std = np.std(tarDICE,0)

            self.overallTargetMetrics.HD[key].value = np.mean(tarHD)
            self.overallTargetMetrics.HD[key].std = np.std(tarHD)

            self.overallTargetMetrics.ASSD[key].value = np.mean(tarASSD)
            self.overallTargetMetrics.ASSD[key].std = np.std(tarASSD)

        print("[AssessSegmentations::Compute] Finished!")



    def __VerifyFilePaths( self ):
        """
        Verify files.
        """
        verifiedList = []

        for index, row in self.referenceList.iterrows():
            referenceSegmentation = row[0]
            targetSegmentation = self.targetList.iloc[index]["TARGET"]
            
            if verifyFile(referenceSegmentation) and \
               verifyFile(targetSegmentation):
                verifiedList.append( (referenceSegmentation, targetSegmentation) )
            else:
                print("[AssessSegmentations::VerifyFilePaths Warning] %s  <- %s  File does not exist!" % (referenceSegmentation, targetSegmentation) )

        return verifiedList
    

    def GetDataFrame( self ):
        """
        Return DataFrame
        """
        dataFrame = self.overallReferenceMetrics.GetDataFrame()
        dataFrame = pd.concat([dataFrame, self.overallTargetMetrics.GetDataFrame()])
                
        for aseg in self.assessments:            
            dataFrame = pd.concat( [dataFrame, aseg.referenceMetrics.GetDataFrame()] )
            dataFrame = pd.concat( [dataFrame, aseg.targetMetrics.GetDataFrame()] )


        return dataFrame

    
    def ToCSV( self, filePath ):
        """
        Export results to CSV file.
        """
        try:
            dataFrame = self.GetDataFrame()
            dataFrame.to_csv (filePath, index = None, header=True, sep=",")
            print("[AssessSegmentations::ToCSV] Results to CSV file done!")

        except Exception as exception:
            print("[AssessSegmentations::ToCSV Exception] %s" % str(exception))
            print("[AssessSegmentations::ToCSV Exception] %s" % str(traceback.format_exc()))


class AssessSegmentation( object ):
    """
    Input file list manager class.
    """
    def __init__( self, refSegFilePath, tarSegFilePath ):
        """
        Default constructor.
        """
        self.REFERENCE_SEGMENTATION_FILE_PATH = None
        self.TARGET_SEGMENTATION_FILE_PATH = None
        
        self.referenceImageSegmentation = None
        self.targetImageSegmentation = None

        self.REFERENCE_SEGMENTATION_FILE_NAME = None
        self.TARGET_SEGMENTATION_FILE_NAME = None

        self.referenceMetrics = None
        self.targetMetrics = None


        self.referenceLabels = None

        self.pixelVolume = 0

        if ( verifyFile(refSegFilePath) ):

            if ( verifyFile(tarSegFilePath) ):
                self.REFERENCE_SEGMENTATION_FILE_PATH = refSegFilePath
                self.TARGET_SEGMENTATION_FILE_PATH = tarSegFilePath

                self.REFERENCE_SEGMENTATION_FILE_NAME = "r_" + str(Path(self.REFERENCE_SEGMENTATION_FILE_PATH).with_suffix('').stem)
                self.TARGET_SEGMENTATION_FILE_NAME = "t_" + str(Path(self.TARGET_SEGMENTATION_FILE_PATH).with_suffix('').stem)

                self.referenceMetrics = MyosaiqMetrics( self.REFERENCE_SEGMENTATION_FILE_NAME )
                self.targetMetrics = MyosaiqMetrics( self.TARGET_SEGMENTATION_FILE_NAME )

                self.__Load()

            else:
                print("[AssessSegmentation] Missing target segmentation file!")

        else:
            print("[AssessSegmentation] Missing reference segmentation file!")


    def __str__( self ):
        """
        Default String obj.
        """
        assessSegmentationStr = "\n[AssessSegmentation]\n\n"
        assessSegmentationStr += "Reference segmentation (file path) : \n\t%s\n\n" % self.REFERENCE_SEGMENTATION_FILE_PATH
        assessSegmentationStr += "Target segmentation (file path) : \n\t%s\n\n" % self.TARGET_SEGMENTATION_FILE_PATH

        return assessSegmentationStr


    def __Load( self ):
        """
        Load images.
        """
        try:            
            self.referenceImageSegmentation = sitk.Cast(sitk.ReadImage( self.REFERENCE_SEGMENTATION_FILE_PATH ), sitk.sitkUInt16 ) 
            self.targetImageSegmentation = sitk.Cast(   sitk.ReadImage( self.TARGET_SEGMENTATION_FILE_PATH ),    sitk.sitkUInt16 )

            referenceLabelShapeStats = sitk.LabelShapeStatisticsImageFilter()
            referenceLabelShapeStats.Execute(self.referenceImageSegmentation)

            self.referenceLabels = referenceLabelShapeStats.GetLabels()

        except Exception as exception:
            print("[AssessSegmentation::Load Exception] %s" % str(exception))
            print("[AssessSegmentation::Load Exception] %s" % str(traceback.format_exc()))


    def Compute( self ):
        """
        Calculate metrics
        """
        if (self.REFERENCE_SEGMENTATION_FILE_PATH is None) or (self.TARGET_SEGMENTATION_FILE_PATH is None):
            return 
        
        self.__VerifySpacingOrigin()

        self.__CalcVolume()
        self.__CalcDICE()
        self.__CalcHD()
        self.__CalcASSD()


    def __VerifySpacingOrigin( self ):
        """
        Verify pixel spacing and origin.
        """
        referenceXSize, referenceYSize, referenceZSize = self.referenceImageSegmentation.GetSpacing()
        targetXSize, targetYSize, targetZSize = self.targetImageSegmentation.GetSpacing()        

        if (referenceXSize != targetXSize) or \
           (referenceYSize != targetYSize) or \
           (referenceZSize != targetZSize):
           print("[AssessSegmentation::VerifySegmentations Warning] Pixel spacing does not match!")

        self.pixelVolume = referenceXSize * referenceYSize * referenceZSize


    def __CalcVolume( self ):
        """
        Calculate volume
        """
        refLabelShapeStats = sitk.LabelShapeStatisticsImageFilter()
        tarLabelShapeStats = sitk.LabelShapeStatisticsImageFilter()

        refLabelShapeStats.Execute(self.referenceImageSegmentation)
        tarLabelShapeStats.Execute(self.targetImageSegmentation)

        # xSize, ySize, zSize = self.referenceImageSegmentation.GetSpacing()
        # pixelVolume = xSize*ySize*zSize

        for label in self.referenceLabels:
            try:
                referencePixels = refLabelShapeStats.GetNumberOfPixels( label )
                targetPixels = tarLabelShapeStats.GetNumberOfPixels( label ) 

                referenceVolume = referencePixels * self.pixelVolume * MM_TO_ML_FACTOR
                targetVolume    = targetPixels * self.pixelVolume * MM_TO_ML_FACTOR

                absDifference = np.abs(referenceVolume - targetVolume)

                self.referenceMetrics.VOLUME[label].value = referenceVolume
                self.referenceMetrics.VOLUME_MAE[label].value = absDifference

                self.targetMetrics.VOLUME[label].value = targetVolume
                self.targetMetrics.VOLUME_MAE[label].value = absDifference
        
            except Exception as exception:
                print("[AssessSegmentation::CalcVolume Exception] %s" % str(exception))
                print("[AssessSegmentation::CalcVolume Exception] %s" % str(traceback.format_exc()))                


    def __CalcDICE( self ):
        """
        Calculate DICE
        """
        overlapMeasures = sitk.LabelOverlapMeasuresImageFilter()
        overlapMeasures.Execute(self.referenceImageSegmentation, self.targetImageSegmentation)

        for label in self.referenceLabels:
            try:
                self.referenceMetrics.DICE[label].value = overlapMeasures.GetDiceCoefficient( label )
                self.targetMetrics.DICE[label].value = overlapMeasures.GetDiceCoefficient( label )

            except Exception as exception:
                print("[AssessSegmentation::CalcVolume Exception] %s" % str(exception))
                print("[AssessSegmentation::CalcVolume Exception] %s" % str(traceback.format_exc()))   


    def __CalcHD( self ):
        """
        Calculate Hausdorff distance
        """

        hausdorffDistanceImage = sitk.HausdorffDistanceImageFilter()

        for label in self.referenceLabels:
            try:
                hausdorffDistanceImage.Execute( self.referenceImageSegmentation == label, 
                                                self.targetImageSegmentation == label )
                
                self.referenceMetrics.HD[label].value = hausdorffDistanceImage.GetHausdorffDistance()
                self.targetMetrics.HD[label].value = hausdorffDistanceImage.GetHausdorffDistance()

            except Exception as exception:
                print("[AssessSegmentation::CalcVolume Exception] %s" % str(exception))
                print("[AssessSegmentation::CalcVolume Exception] %s" % str(traceback.format_exc()))   


    def __CalcASSD( self ):
        """
        Calculate Average Symmetric Surface distance
        """
        for label in self.referenceLabels:
            try:
                # Symmetric surface distance measures
                referenceDistanceMap = sitk.Abs( sitk.SignedMaurerDistanceMap(self.referenceImageSegmentation == label, squaredDistance=False) )
                referenceSurface = sitk.LabelContour(self.referenceImageSegmentation == label)

                statisticsImageFilter = sitk.StatisticsImageFilter()
                # Get the number of pixels in the reference surface by counting all pixels that are 1.
                statisticsImageFilter.Execute(referenceSurface)
                numReferenceSurfacePixels = int(statisticsImageFilter.GetSum()) 


                targetDistanceMap = sitk.Abs( sitk.SignedMaurerDistanceMap(self.targetImageSegmentation == label, squaredDistance=False) )
                targetSurface = sitk.LabelContour(self.targetImageSegmentation == label)
                
                # Multiply the binary surface segmentations with the distance maps. The resulting distance
                # maps contain non-zero values only on the surface (they can also contain zero on the surface)
                tar2refDistanceMap = referenceDistanceMap*sitk.Cast(targetSurface, sitk.sitkFloat32)
                ref2tarDistanceMap = targetDistanceMap*sitk.Cast(referenceSurface, sitk.sitkFloat32)

                # Get the number of pixels in the segmented surface by counting all pixels that are 1.
                statisticsImageFilter.Execute(targetSurface)
                numTargetSurfacePixels = int(statisticsImageFilter.GetSum())
            
                # Get all non-zero distances and then add zero distances if required.
                tar2refDistanceMapArray = sitk.GetArrayViewFromImage(tar2refDistanceMap)
                tar2refDistances = list(tar2refDistanceMapArray[tar2refDistanceMapArray!=0]) 

                tar2refDistances = tar2refDistances + \
                                   list( np.zeros(numTargetSurfacePixels - len(tar2refDistances)) )
                
                ref2tarDistanceMapArray = sitk.GetArrayViewFromImage(ref2tarDistanceMap)
                ref2tarDistances = list(ref2tarDistanceMapArray[ref2tarDistanceMapArray!=0]) 

                ref2tarDistances = ref2tarDistances + \
                                   list( np.zeros(numReferenceSurfacePixels - len(ref2tarDistances)) )
                
                surfaceDistances = tar2refDistances + ref2tarDistances

                self.referenceMetrics.ASSD[label].value = np.mean( surfaceDistances )
                self.targetMetrics.ASSD[label].value = np.mean( surfaceDistances )                

            except Exception as exception:
                print("[AssessSegmentation::CalcVolume Exception] %s" % str(exception))
                print("[AssessSegmentation::CalcVolume Exception] %s" % str(traceback.format_exc()))   


    def PrintSingleMetrics( self ):
        """
        Print metrics.
        """
        self.referenceMetrics.PrintSingleMetrics()
        self.targetMetrics.PrintSingleMetrics()


class MyosaiqMetrics( object ):
    """
    Measurement class.
    """
    def __init__( self, segmentationName=None ):

        if segmentationName is None:
            self.segmentationName = "UNKNOWN"

        else:
            self.segmentationName = segmentationName

        self.VOLUME = { LEFT_VENTRICULAR_CAVITY:Measurement(0, 0),
                        MYOCARDIUM:Measurement(0, 0),
                        MYOCARDIAL_INFARCTION:Measurement(0, 0),
                        MVO:Measurement(0, 0) }
        
        self.VOLUME_MAE = { LEFT_VENTRICULAR_CAVITY:Measurement(0, 0),
                            MYOCARDIUM:Measurement(0, 0),
                            MYOCARDIAL_INFARCTION:Measurement(0, 0),
                            MVO:Measurement(0, 0) }

        self.VOLUME_CC = { LEFT_VENTRICULAR_CAVITY:Measurement(0, 0),
                           MYOCARDIUM:Measurement(0, 0),
                           MYOCARDIAL_INFARCTION:Measurement(0, 0),
                           MVO:Measurement(0, 0) }   
        
        self.VOLUME_LOA = { LEFT_VENTRICULAR_CAVITY:Measurement(0, 0),
                            MYOCARDIUM:Measurement(0, 0),
                            MYOCARDIAL_INFARCTION:Measurement(0, 0),
                            MVO:Measurement(0, 0) }                   

        self.DICE = { LEFT_VENTRICULAR_CAVITY:Measurement(0, 0),
                      MYOCARDIUM:Measurement(0, 0),
                      MYOCARDIAL_INFARCTION:Measurement(0, 0),
                      MVO:Measurement(0, 0) }

        self.HD = { LEFT_VENTRICULAR_CAVITY:Measurement(0, 0),
                    MYOCARDIUM:Measurement(0, 0),
                    MYOCARDIAL_INFARCTION:Measurement(0, 0),
                    MVO:Measurement(0, 0) }     

        self.ASSD = { LEFT_VENTRICULAR_CAVITY:Measurement(0, 0),
                      MYOCARDIUM:Measurement(0, 0),
                      MYOCARDIAL_INFARCTION:Measurement(0, 0),
                      MVO:Measurement(0, 0) }


    def PrintSingleMetrics( self ):
        """
        Print metrics.
        """

        print("\n{:<18} {:^5} {:^18} {:<11} {:<11}\n".format( "SEGMENTATION ID", "LABEL", "METRIC", "VALUE", "STD") )

        for key in LABEL:
            print("{:<18} {:^5} {:^18} {:<11} {:<11}".format( self.segmentationName,
                                                              LABEL[key],
                                                              "VOLUME",
                                                              np.round(self.VOLUME[key].value, ROUND_DECIMALS_VOLUME),
                                                              np.round(self.VOLUME[key].std,   ROUND_DECIMALS_VOLUME) ) )        
        print()    
        for key in LABEL:
            print( "{:<18} {:^5} {:^18} {:<11} {:<11}".format( self.segmentationName,
                                                               LABEL[key],
                                                               "VOLUME AD",
                                                               np.round(self.VOLUME_MAE[key].value, ROUND_DECIMALS_VOLUME),
                                                               np.round(self.VOLUME_MAE[key].std,   ROUND_DECIMALS_VOLUME) ) ) 

        print()
        for key in LABEL:
            print( "{:<18} {:^5} {:^18} {:<11} {:<11}".format( self.segmentationName,
                                                               LABEL[key],
                                                               "DICE",
                                                               np.round(self.DICE[key].value, ROUND_DECIMALS_DICE),
                                                               np.round(self.DICE[key].std,   ROUND_DECIMALS_DICE) ) )
        print()
        for key in LABEL:
            print( "{:<18} {:^5} {:^18} {:<11} {:<11}".format( self.segmentationName,
                                                               LABEL[key],
                                                               "HD",
                                                               np.round(self.HD[key].value, ROUND_DECIMALS_ASSD_HD),
                                                               np.round(self.HD[key].std,   ROUND_DECIMALS_ASSD_HD) ) )   
        print()
        for key in LABEL:
            print( "{:<18} {:^5} {:^18} {:<11} {:<11}".format( self.segmentationName,
                                                               LABEL[key],
                                                               "ASSD",
                                                               np.round(self.ASSD[key].value, ROUND_DECIMALS_ASSD_HD),
                                                               np.round(self.ASSD[key].std,   ROUND_DECIMALS_ASSD_HD) ) )


    def GetDataFrame( self ):
        """
        Return a Pandas data frame.
        """
        metricsData = self.GetTable()
        dataFrame = pd.DataFrame( data=metricsData,
                                  columns=["SEGMENTATION ID", "LABEL", "METRIC", "VALUE", "STD"] )
        
        return dataFrame


    def PrintMetrics( self ):
        """
        Print ALL metrics.
        """

        table = self.GetTable()

        print("\n{:<18} {:^5} {:^18} {:<11} {:<11}\n".format( "SEGMENTATION ID", "LABEL", "METRIC", "VALUE", "STD") )

        doIhaveToInstertA = Counter( 6 )

        for row in table:
            print( "{:<18} {:^5} {:^18} {:<11} {:<11}".format(row[0], row[1], row[2], row[3], row[4]) )
            if doIhaveToInstertA.Break(): print()


    def GetTable( self ):
        """
        Return a table with all metrics.
        """

        table = []

        for key in LABEL:

            volume = []
            volume.append( self.segmentationName )
            volume.append( LABEL[key] )
            volume.append( "VOLUME" )
            volume.append( np.round(self.VOLUME[key].value, ROUND_DECIMALS_VOLUME) )
            volume.append( np.round(self.VOLUME[key].std, ROUND_DECIMALS_VOLUME) )
            table.append( volume )

            volumeMAE = []
            volumeMAE.append( self.segmentationName )
            volumeMAE.append( LABEL[key] )
            volumeMAE.append( "VOLUME MAE" )
            volumeMAE.append( np.round(self.VOLUME_MAE[key].value, ROUND_DECIMALS_VOLUME) )
            volumeMAE.append( np.round(self.VOLUME_MAE[key].std, ROUND_DECIMALS_VOLUME) )
            table.append( volumeMAE )

            volumeCC = []
            volumeCC.append( self.segmentationName )
            volumeCC.append( LABEL[key] )
            volumeCC.append( "VOLUME CC" )
            volumeCC.append( np.round(self.VOLUME_CC[key].value, ROUND_DECIMALS_VOLUME) )
            volumeCC.append( np.round(self.VOLUME_CC[key].std, ROUND_DECIMALS_VOLUME) )
            table.append( volumeCC )

            dice = []
            dice.append( self.segmentationName )
            dice.append( LABEL[key] )
            dice.append( "DICE" )
            dice.append( np.round(self.DICE[key].value, ROUND_DECIMALS_DICE) )
            dice.append( np.round(self.DICE[key].std, ROUND_DECIMALS_DICE) )
            table.append( dice )

            hd = []
            hd.append( self.segmentationName )
            hd.append( LABEL[key] )
            hd.append( "HD" )
            hd.append( np.round(self.HD[key].value, ROUND_DECIMALS_ASSD_HD) )
            hd.append( np.round(self.HD[key].std, ROUND_DECIMALS_ASSD_HD) )
            table.append( hd )

            assd = []
            assd.append( self.segmentationName )
            assd.append( LABEL[key] )
            assd.append( "ASSD" )
            assd.append( np.round(self.ASSD[key].value, ROUND_DECIMALS_ASSD_HD) )
            assd.append( np.round(self.ASSD[key].std, ROUND_DECIMALS_ASSD_HD) )
            table.append( assd )

        return table         

       
class Measurement( object ):
    """
    Measurement class.
    """
    def __init__(self, value, std):
        self.value = value
        self.std = std


class Counter( object ):
    def __init__(self, limit):
        self.limit = limit
        self.count = 0

    def Break(self):
        self.count += 1
        if self.count == self.limit:
            self.count = 0
            return True
        else:
            return False


class VolumesCDFException(Exception):
    """
    Default manager exception class.
    """


class VolumesCDF(object):
    """
    Class for the management of cumulative probability distribution's file.
    """
    def __init__( self, inputFilePath ):
        """
        Default constructor.
        """
        self.FILE_PATH = None
        self.NUM_VOLUMES = 0

        self.volumeList = None
        self.volumesData = None

        if verifyFile( inputFilePath ):
            self.FILE_PATH = inputFilePath
            self.__Load()
        else:
            print("[VolumesCDF] File does not exist!")


    def __str__( self ):
        """
        Default String obj.
        """
        volumesCDFStr = "\n[VolumesCDF]\n\n"
        volumesCDFStr += "Input file: \n\t%s\n\n" % self.FILE_PATH

        if self.volumeList is not None:
            volumesCDFStr += "Contents (Volume ID) : \n"
            for index, row in self.volumeList.iterrows():
                volumesCDFStr += "\t" + row["ID"]
                volumesCDFStr += "\n" 
            volumesCDFStr += "\nTotal: %d volumes.\n\n" % self.NUM_VOLUMES

        return volumesCDFStr


    def __Load( self ):
        """
        Load volumes CDF data from csv file.
        """
        try:
            self.volumesData = pd.read_csv( self.FILE_PATH, sep="," )
            self.volumeList = self.volumesData[ ["ID"] ]
            self.NUM_VOLUMES = int( self.volumeList.count() )

        except Exception as exception:
            print("[VolumesCDF::Load Exception] %s" % str(exception))
            print("[VolumesCDF::Load Exception] %s" % str(traceback.format_exc()))


    def H(self, x):
        """
        Heaviside step function:
            1 if x is positive or zero, 0 otherwise

        H(x) = \left\{ \begin{array}{cl}
                        1 & : \ x \ge 0 \\
                        0 & : \text{Otherwise}
               \end{array} \right.

        """
        if x < 0.0:
            return 0 
        return 1


    def CalcCRPS( self ):
        """
        Calculate Continuous Ranked Probability Score (CRPS).
        """

        crps = 0

        if self.volumesData is None:
            return crps

        try:
            # N is the number of rows in the test set (equal to twice the number of cases)
            N = self.NUM_VOLUMES
            print("[VolumesCDF] Number of volumes: %d" % N)
            print("[VolumesCDF] Calculating CRPS ...\n")

            mSum = 0

            #-----------------------------------------------------------------------
            # volumeData  data of the m-th volume
            #     m       index across volumes (cases)
            #     n       index across the cdf
            #-----------------------------------------------------------------------        
            for index, volumeData in self.volumesData.iterrows():
                print("\tReading data from %s (%.4f mL) ..." % (volumeData[0], volumeData[1]))

                elementsInARow = int ( volumeData.shape[0] ) 

                if (elementsInARow < MAX_VOLUME+2):
                    print("\tThe row %d does not have the number of elemens required (ID, VOL, P0, P1, P2,... P599) ...\n" % index)
                    return crps

                # n:[0,599]
                n = 0

                # V is the actual volume (in mL) 
                Vm = volumeData[1]

                nSum = 0

                for j in range(2, MAX_VOLUME+2):
                    # $P(y \le n)$
                    Pn = volumeData[j]

                    if not isinstance(Pn, float):
                        print("\tThe row %d has a corrupted element!\n" % index)
                        return crps                   

                    if np.isnan(Pn):
                        print("\tThe row %d has a corrupted element!\n" % index)
                        return crps

                    # \sum_{n=0}^{599} \left( P(y \le n) - H(n-V_{m}) \right)^2
                    nSum += np.power(  Pn - self.H(n-Vm), 2 )
                    n += 1

                mSum += nSum

            crps = 1/(MAX_VOLUME*N) * mSum

            return np.round(crps, ROUND_DECIMALS)

        except Exception as exception:
            print("[VolumesCDF::Load Exception] %s" % str(exception))
            print("[VolumesCDF::Load Exception] %s" % str(traceback.format_exc()))

            return 0


    @staticmethod
    def GetDummyCDF( volume ):
        """
        Returns cumulative probability distribution.
        """
        cdf = np.zeros( MAX_VOLUME )

        if (volume > 0) and (volume < MAX_VOLUME):
            volumeIndex = int( np.fix( volume ) )
            cdf[volumeIndex:] = 1

        return cdf


def verifyFile( filePath ):
    """
    Verify file path.
    """
    if os.path.isfile( filePath ):
        return True
    
    else:
        return False 
