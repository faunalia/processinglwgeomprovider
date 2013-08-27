# -*- coding: utf-8 -*-

"""
***************************************************************************
__init__.py
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

def name():
    return "Processing LWGEOM provider"

def description():
    return "Expose liblwgeom functions to Processing."

def author():
    return "Giuseppe Sucameli (Faunalia)"

def authorName():  # for compatibility only
    return author()

def email():
    return "sucameli@faunalia.it"

def version():
    return "0.3"

def icon():
    return "icon.png"

def qgisMinimumVersion():
    return "2.0"

def classFactory(iface):
    from processinglwgeomprovider.ProcessingLwgeomProviderPlugin import ProcessingLwgeomProviderPlugin
    return ProcessingLwgeomProviderPlugin()
