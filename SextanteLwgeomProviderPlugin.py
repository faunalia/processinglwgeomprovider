# -*- coding: utf-8 -*-

"""
***************************************************************************
SextanteLwgeomProviderPlugin.py
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

from qgis.core import *
import os, sys
import inspect
from sextante.core.Sextante import Sextante
from sextantelwgeomprovider.LwgeomAlgorithmProvider import LwgeomAlgorithmProvider

cmd_folder = os.path.split(inspect.getfile( inspect.currentframe() ))[0]
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

class SextanteLwgeomProviderPlugin:

    def __init__(self):
        self.provider = LwgeomAlgorithmProvider()

    def initGui(self):
        Sextante.addProvider(self.provider)

    def unload(self):
        Sextante.removeProvider(self.provider)

