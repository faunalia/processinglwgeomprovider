# -*- coding: utf-8 -*-

"""
***************************************************************************
LwgeomAlgorithmProvider.py
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

import os

from processing.core.AlgorithmProvider import AlgorithmProvider
from processinglwgeomprovider.LwgeomAlgorithm import makeValid
from processinglwgeomprovider.LwgeomAlgorithm import buildArea
from processing.core.ProcessingConfig import Setting, ProcessingConfig
from processing.tools.system import isMac, isWindows

class LwgeomAlgorithmProvider(AlgorithmProvider):

    LWGEOM_PATH_SETTING = "LWGEOM_PATH_SETTING"

    def __init__(self):
        AlgorithmProvider.__init__(self)
        self.alglist = [makeValid(), buildArea()]
        for alg in self.alglist:
            alg.provider = self

    def initializeSettings(self):
        '''add settings needed to configure our provider.'''
        # call the parent method which takes care of adding a setting for
        # activating or deactivating the algorithms in the provider
        AlgorithmProvider.initializeSettings(self)

        # add settings
        ProcessingConfig.addSetting(Setting("LWGEOM algorithms", LwgeomAlgorithmProvider.LWGEOM_PATH_SETTING, "Path to liblwgeom", self.lwgeomPath()))
        #To get the parameter of a setting parameter, use ProcessingConfig.getSetting(name_of_parameter)

    def unload(self):
        '''remove settings, so they do not appear anymore when the plugin
        is unloaded'''
        AlgorithmProvider.unload(self)
        ProcessingConfig.removeSetting( LwgeomAlgorithmProvider.LWGEOM_PATH_SETTING )


    def getName(self):
        '''The name that will appear on the toolbox group.'''
        return "LWGEOM algorithms"

    def getDescription(self):
        return "LWGEOM algorithms"

    def getIcon(self):
        '''return the default icon'''
        return AlgorithmProvider.getIcon(self)

    def _loadAlgorithms(self):
        '''list of algorithms in self.algs.'''
        self.algs = self.alglist

    def lwgeomPath(self):
        folder = self.findLwgeomPath()
        if folder is None:
            folder = ProcessingConfig.getSetting(LwgeomAlgorithmProvider.LWGEOM_PATH_SETTING)
        return folder

    def findLwgeomPath(self):
        folder = None

        if isMac():
            pass
        elif isWindows():
            testfolder = os.path.join(os.path.split(os.path.dirname(QgsApplication.prefixPath()))[0], 'bin')
            if os.path.exists(os.path.join(testfolder, 'lwgeom.dll')):
                folder = testfolder
        else:
            testFolders = ["/usr/lib", "/usr/lib64/", "/usr/bin"]
            for f in testFolders:
                if os.path.exists(os.path.join(f, "liblwgeom.so")):
                    return f
        return folder
