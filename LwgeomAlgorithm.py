# -*- coding: utf-8 -*-

"""
***************************************************************************
LwgeomAlgorithm.py
---------------------
Date : November 2012
Copyright : (C) 2012 by Giuseppe Sucameli
Email : g.sucameli at gmail.com
***************************************************************************
* *
* This program is free software; you can redistribute it and/or modify *
* it under the terms of the GNU General Public License as published by *
* the Free Software Foundation; either version 2 of the License, or *
* (at your option) any later version. *
* *
***************************************************************************
"""
__author__ = 'Giuseppe Sucameli'
__date__ = 'November 2012'
__copyright__ = '(C) 2012, Giuseppe Sucameli'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.outputs.OutputVector import OutputVector
from processing.parameters.ParameterVector import ParameterVector
from processing.core.Processing import Processing
from processing.core.ProcessingConfig import ProcessingConfig
from processing.core.ProcessingLog import ProcessingLog

import os
from qgis.core import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import ctypes


class GBOX(ctypes.Structure):
    _fields_ = [
        ("flags", ctypes.c_ubyte),
        ("xmin", ctypes.c_double),
        ("xmax", ctypes.c_double),
        ("ymin", ctypes.c_double),
        ("ymax", ctypes.c_double),
        ("zmin", ctypes.c_double),
        ("zmax", ctypes.c_double),
        ("mmin", ctypes.c_double),
        ("mmax", ctypes.c_double)
    ]


class LWGEOM(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ubyte),
        ("flags", ctypes.c_ubyte),
        ("bbox", ctypes.POINTER(GBOX)),
        ("srid", ctypes.c_uint),
        ("data", ctypes.c_void_p),
    ]


class LwgeomAlgorithm(GeoAlgorithm):
    
    OUTPUT_LAYER = "OUTPUT_LAYER"
    INPUT_LAYER = "INPUT_LAYER"

    def checkParameterValuesBeforeExecuting(self):
        if "USE_THREADS" in dir(ProcessingConfig):
            self.useThread = ProcessingConfig.getSetting(ProcessingConfig.USE_THREADS)
            if self.useThread:
                message = "WARNING: Multithread execution has problems. Disable 'Run algorithms in a new thread' feature in Processing General configuration"
                ProcessingLog.addToLog(ProcessingLog.LOG_WARNING, message)
                return message
    
    def getIcon(self):
        filepath = os.path.dirname(__file__) + "/icons/makeValid.png"
        return QIcon(filepath)

    def defineCharacteristics(self):
        raise NotImplemented( "must be implemented in subclasses" )

    def addDefaultParameters(self):
        self.addParameter(ParameterVector(self.INPUT_LAYER, "Input layer", ParameterVector.VECTOR_TYPE_ANY, False))
        self.addOutput(OutputVector(self.OUTPUT_LAYER, "Output layer"))

    def getLwgeomLibrary(self):
        # try to load the LWGEOM library
        libpath = ProcessingConfig.getSetting("LWGEOM_PATH_SETTING")
        lib = ctypes.CDLL(libpath)

        # install a custom error handler to report them to processing log
        def onError(fmt, ap):
            msg = ctypes.c_char_p()
            ret = lib.lw_vasprintf(ctypes.byref(msg), fmt, ap)
            ProcessingLog.addToLog(ProcessingLog.LOG_ERROR, u"FAILURE: liblwgeom error is:\n%s" % msg.value)

        REPORTERFUNC = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_void_p)
        errorreporter = REPORTERFUNC( onError )
        lib.lwgeom_set_handlers(None, None, None, errorreporter, None)

        return lib

    def inputToOutputGeomType(self, inputLayer):
        return inputLayer.wkbType()


    def processAlgorithm(self, progress):
        # get the lib
        liblwgeom = self.getLwgeomLibrary()

        # retrieve the values of the parameters entered by the user
        inputFilename = self.getParameterValue(self.INPUT_LAYER)
        output = self.getOutputValue(self.OUTPUT_LAYER)

        # input layers vales are always a string with its location.
        # That string can be converted into a QGIS object (a QgsVectorLayer in this case))
        # using the Processing.getObject() method
        inputLayer = Processing.getObject(inputFilename)

        # create the output layer
        provider = inputLayer.dataProvider()
        encoding = provider.encoding()
        geomType = self.inputToOutputGeomType(inputLayer)
        writer = QgsVectorFileWriter( output, encoding, provider.fields(), geomType, provider.crs() )

        # Now we take the features and add them to the output layer, 
        # first check for selected features
        selection = inputLayer.selectedFeatures()
        if len(selection) > 0:
            count = len(selection)
            idx = 0

            for feat in selection:
                # run lwgeom algorithm on the feature geometry
                if not self.runLwgeom( feat.geometry(), lib=liblwgeom ):
                    ProcessingLog.addToLog( ProcessingLog.LOG_ERROR, u"FAILURE: previous failure info: layer %s, feature #%s" % (inputLayer.source(), feat.id()) )
                writer.addFeature(feat)

                progress.setPercentage( idx*100/count )
                idx += 1

        else:
            count = inputLayer.featureCount()
            idx = 0

            # no features selected on the layer, process all the features
            features = inputLayer.getFeatures()
            for feat in features:
                # run lwgeom algorithm on the feature geometry
                if not self.runLwgeom( feat.geometry(), lib=liblwgeom ):
                    ProcessingLog.addToLog( ProcessingLog.LOG_ERROR, u"FAILURE: previous failure info: layer %s, feature #%s" % (inputLayer.source(), feat.id()) )
                writer.addFeature(feat)

                progress.setPercentage( idx*100/count )
                idx += 1

        del writer
        progress.setPercentage( 100 )

    def runLwgeom(self, geom, lib, **kwargs):
        # create a LWGEOM geometry parsing the WKB

        # LWGEOM* lwgeom_from_wkb(const uint8_t *wkb,
        #                         const size_t wkb_size,
        #                         const char check)
        lib.lwgeom_from_wkb.argtypes = [ctypes.POINTER(ctypes.c_ubyte),
                                        ctypes.c_size_t,
                                        ctypes.c_char]
        lib.lwgeom_from_wkb.restype = ctypes.POINTER(LWGEOM)

        # uint8_t* lwgeom_to_wkb(const LWGEOM *geom,
        #                        uint8_t variant,
        #                        size_t *size_out)
        lib.lwgeom_to_wkb.argtypes = [ctypes.POINTER(LWGEOM),
                                      ctypes.c_ubyte,
                                      ctypes.POINTER(ctypes.c_size_t)]
        lib.lwgeom_to_wkb.restype = ctypes.POINTER(ctypes.c_ubyte)

        # void lwgeom_free(LWGEOM *lwgeom)
        lib.lwgeom_free.argtypes = [ctypes.POINTER(LWGEOM)]

        wkb_in_buf = ctypes.create_string_buffer(geom.asWkb())
        wkb_in = ctypes.cast(ctypes.addressof(wkb_in_buf), ctypes.POINTER(ctypes.c_ubyte))
        wkb_size_in = ctypes.c_size_t(geom.wkbSize())
        LW_PARSER_CHECK_NONE = ctypes.c_char(chr(0))    #define LW_PARSER_CHECK_NONE   0
        try:
            lwgeom_in = lib.lwgeom_from_wkb( wkb_in, wkb_size_in, LW_PARSER_CHECK_NONE )
        finally:
            del wkb_in

        if not lwgeom_in:
            ProcessingLog.addToLog(ProcessingLog.LOG_ERROR, "FAILURE: liblwgeom wasn't able to parse the WKB!")
            return False

        # execute the liblwgeom function on the LWGEOM geometry
        try:
            lwgeom_out = self.runLwgeomFunc(lwgeom_in, lib=lib, **kwargs)
        finally:
            lib.lwgeom_free( lwgeom_in )
            del lwgeom_in

        if not lwgeom_out:
            return

        # convert the LWGEOM geometry back to WKB
        wkb_size_out = ctypes.c_size_t()
        WKB_ISO = ctypes.c_uint8(1)    #define WKB_ISO   0x01
        try:
            wkb_out = lib.lwgeom_to_wkb( lwgeom_out, WKB_ISO, ctypes.byref(wkb_size_out) )
        finally:
            lib.lwgeom_free( lwgeom_out )
            del lwgeom_out

        if not wkb_out or wkb_size_out <= 0:
            ProcessingLog.addToLog(ProcessingLog.LOG_ERROR, "FAILURE: liblwgeom wasn't able to convert the geometry back to WKB!")
            return False

        # update the QgsGeometry through the WKB
        wkb_geom = ctypes.string_at(wkb_out, wkb_size_out.value)
        lib.lwfree( wkb_out )
        del wkb_out

        geom.fromWkb( wkb_geom )
        return True



class makeValid(LwgeomAlgorithm):

    def defineCharacteristics(self):
        self.name = "Make valid"
        self.group = "[LWGEOM] Miscellaneous"
        LwgeomAlgorithm.addDefaultParameters(self)

    def runLwgeomFunc(self, lwgeom_in, lib, **kwargs):
        # call the liblwgeom make_valid
        # LWGEOM* lwgeom_make_valid(LWGEOM* lwgeom_in)
        lib.lwgeom_make_valid.argtypes = [ctypes.POINTER(LWGEOM)]
        lib.lwgeom_make_valid.restype = ctypes.POINTER(LWGEOM)
        lwgeom_out = lib.lwgeom_make_valid( lwgeom_in )
        if not lwgeom_out:
            ProcessingLog.addToLog(ProcessingLog.LOG_ERROR, "FAILURE: liblwgeom wasn't able to make the geometry valid!")
            return

        return lwgeom_out


class buildArea(LwgeomAlgorithm):

    def defineCharacteristics(self):
        self.name = "Build area"
        self.group = "[LWGEOM] Miscellaneous"
        LwgeomAlgorithm.addDefaultParameters(self)

    #def inputToOutputGeomType(self, inputLayer):
    #    if inputLayer.wkbType() in (QGis.WKBPoint, QGis.WKBLineString25D, QGis.WKBPolygon25D):
    #        return QGis.WKBPolygon25D
    #    if inputLayer.wkbType() in (QGis.WKBMultiPoint, QGis.WKBMultiLineString, QGis.WKBMultiPolygon):
    #        return QGis.WKBMultiPolygon
    #    if inputLayer.wkbType() in (QGis.WKBMultiPoint25D, QGis.WKBMultiLineString25D, QGis.WKBMultiPolygon25D):
    #        return QGis.WKBMultiPolygon25D
    #    return QGis.WKBPolygon

    def runLwgeomFunc(self, lwgeom_in, lib, **kwargs):
        # call the liblwgeom buildarea
        # LWGEOM* lwgeom_buildarea(const LWGEOM *geom)
        lib.lwgeom_buildarea.argtypes = [ctypes.POINTER(LWGEOM)]
        lib.lwgeom_buildarea.restype = ctypes.POINTER(LWGEOM)
        lwgeom_out = lib.lwgeom_buildarea( lwgeom_in )
        if not lwgeom_out:
            ProcessingLog.addToLog(ProcessingLog.LOG_ERROR, "FAILURE: liblwgeom wasn't able to build area!")
            return

        return lwgeom_out

