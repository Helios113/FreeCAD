# ***************************************************************************
# *   Copyright (c) 2017 Markus Hovorka <m.hovorka@live.de>                 *
# *   Copyright (c) 2020 Bernd Hahnebach <bernd@bimstatik.org>              *
# *                                                                         *
# *   This file is part of the FreeCAD CAx development system.              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

__title__ = "FreeCAD FEM MoFEM solver"
__author__ = "Preslav Aleksandrov"
__url__ = "https://www.freecadweb.org"

# \addtogroup FEM
#  @{
from . import tasks
from .type import elasticity
from .type import bone
from .. import run
import re
import os
from subprocess import check_output
from .. import solverbase

from .. import settings
from femtools import femutils
import FreeCAD


"""
Document object visible in the tree-view.
Implemented in python via a document proxy and view proxy.
"""


def create(doc, name="MoFEMSolver"):
    return femutils.createObject(
        doc, name, Proxy, ViewProxy)


# Implementation of the Proxy class
# This class is called from the GUI
# to create a solver object
# It defines all parameters that the user
# can amend through addAttribute


class Proxy(solverbase.Proxy):
    """Proxy for FemSolverMoFEM """

    Type = "FEM::SolverMoFEM"
    # Name of command which is called
    # Has to be the same as in GUI/workbench.cpp

    # Ad the properties needed to solve the mesh

    _EQUATIONS = {
        "Linear Elasticity": elasticity,
        "Bone Remodeling": bone
    }

    def __init__(self, obj):
        super(Proxy, self).__init__(obj)
        add_attributes(self, obj)

    def createMachine(self, obj, directory, testmode=False):
        return run.Machine(
            solver=obj, directory=directory,
            check=tasks.Check(),
            prepare=tasks.Prepare(),
            solve=tasks.Solve(),
            results=tasks.Results(),
            testmode=testmode)

    def createEquation(self, doc, eqId):
        return self._EQUATIONS[eqId].create(doc)

    def isSupported(self, eqId):
        return eqId in self._EQUATIONS


def add_attributes(self, obj):


    # get analysis types from executable
    
    # Assume for now we have the binary
    
    self.mofem = settings.get_binary("read_med")

    self._isPosix = (os.name == "posix")
    if self._isPosix:
        arguments = [self.mofem, '-get_modules']
        ANALYSIS_TYPES = check_output(arguments).decode("utf-8").splitlines()
        print(ANALYSIS_TYPES)
    obj.addProperty(
            "App::PropertyString",
            "Path",
            "Base",
            "",
            4 | 8
        )
    obj.Path = self.mofem
    obj.addProperty(
        "App::PropertyEnumeration",
        "Module",
        "Fem",
        "Type of the analysis"
    )
    obj.Module = ANALYSIS_TYPES
    obj.addProperty(
            "App::PropertyLink",
            "GmshMesh",
            "Base",
            "",
            4 | 8
        )
    obj.addProperty(
            "App::PropertyLink",
            "MoFEMResult",
            "Base",
            "",
            4 | 8
        )

# Implementation of the ViewProxy class
# This class is called from the GUI
# to create a solver object
# It gives the solver icon
class ViewProxy(solverbase.ViewProxy):
    """Proxy for FemSolverMoFEMs View Provider."""

    def getIcon(self):
        return ":/icons/FEM_SolverMoFEM.svg"

# @}
