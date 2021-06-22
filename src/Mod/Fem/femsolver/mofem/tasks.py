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

__title__ = "FreeCAD FEM MoFEM tasks"
__author__ = "Preslav Aleksandrov"
__url__ = "https://www.freecadweb.org"

# \addtogroup FEM
#  @{

from femsolver import task
import os
import os.path
from posixpath import join
import subprocess
import sys
from platform import system
from tempfile import SpooledTemporaryFile

import FreeCAD

from . import writer
from .. import run
from .. import settings
from femtools import femutils
from femtools import membertools


"""
Module containing one task class per task required for a solver implementation.
Those tasks divide the process of solving a analysis into the following steps: check, prepare, solve, results
"""
"""

class Check(run.Check):

    def run(self):
        self.pushStatus("Checking analysis...\n")
        if (self.checkMesh()):
            self.checkMeshType()
        self.checkMaterial()
        self.checkEquations()

    def checkMeshType(self):
        mesh = membertools.get_single_member(
            self.analysis, "Fem::FemMeshObject")
        if not femutils.is_of_type(mesh, "Fem::FemMeshGmsh"):
            self.report.error(
                "Unsupported type of mesh. "
                "Mesh must be created with gmsh.")
            self.fail()
            return False
        return True

    def checkEquations(self):
        equations = self.solver.Group
        if not equations:
            self.report.error(
                "Solver has no equations. "
                "Add at least one equation.")
            self.fail()

"""


# Implementation of the Check class
# This class checks to see if:
# 1. there is only one fem mesh
# 2. the mesh is created with gmsh
# 3. a material has been assigned
class Check(run.Check):

    def run(self):
        self.pushStatus("Checking analysis...\n")
        if self.checkMesh():  # works for only one mesh if more meshes are needed this check needs to be amended
            self.pushStatus("Mesh OK\n")
            if self.checkMeshType():
                self.pushStatus("Mesh created with gmsh\n")
        self.checkMaterial()
        # self.checkEquations() implements equations - not used for now

    def checkMeshType(self):
        mesh = membertools.get_mesh_to_solve(self.analysis)[0]
        if not femutils.is_of_type(mesh, "Fem::FemMeshGmsh"):
            self.report.error(
                "Unsupported type of mesh. "
                "Mesh must be created with gmsh.")
            self.fail()
            return False
        return True

    def checkEquations(self):
        equations = self.solver.Group
        if not equations:
            self.report.error(
                "Solver has no equations. "
                "Add at least one equation.")
            self.fail()


# Implementation of the Prepare class
# This class takes a gmsh file, converts it to a med file
# with MoFEM boundary conditions
# through the use of a .geo file,
# then calls read_med to create a .config file,
# then calls read_med to create a .h5m file
# which can be used by mofem for analysis
class Prepare(run.Prepare):

    def run(self):  # called by GUI

        FreeCAD.Console.PrintMessage("Preparing files...\n")
        # Gets the read med binary
        self.read_med = FreeCAD.ParamGet(
            "User parameter:BaseApp/Preferences/Mod/Fem/MoFEM").GetString("MoFEMMedPath")
        w = writer.MedWriterMoFEM(
            self.analysis,
            self.solver,
            # This is the mesh to solve, pre check has been done already
            membertools.get_mesh_to_solve(self.analysis)[0],
            membertools.AnalysisMember(self.analysis),
            self.directory
        )

        self._create_med(w)
        self._create_cfg(w)
        self._create_h5m(w)

    def _create_med(self, w):
        try:  # Generate MoFEM .config file
            FreeCAD.Console.PrintMessage("Initializing writer\n")
            w.gen_med_file()  # amends the .geo file with mofem bcs and creates med file
        except writer.MedWriterMoFEMError as e:
            self.report.error(str(e))
            self.fail()
        except IOError:
            self.report.error("Can't access working directory.")
            self.fail()

    def _create_cfg(self, w):
        try:  # Generate MoFEM .config file
            FreeCAD.Console.PrintMessage("Writing config file\n")
            w.gen_cfg_file()  # amends the .geo file with mofem bcs and creates med file
        except writer.MedWriterMoFEMError as e:
            self.report.error(str(e))
            self.fail()
        except IOError:
            self.report.error("Can't access working directory.")
            self.fail()
    """
            task = [read_med, "-med_file",  w.med_path]
            self._process = subprocess.Popen(
                task, cwd=self.directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        """

    def _create_h5m(self, w):
        try:  # Generate MoFEM-compatible mesh
            FreeCAD.Console.PrintMessage("Generating MoFEM-compatible mesh\n")
            task = [self.read_med, "-med_file",  w.med_path,
                    "-meshsets_config", w.cfg_path,
                    "-output_file", w.work_path]
            logfile = open(w.include+".log", "w")
            self._process = subprocess.Popen(  # creates the mofem readable mesh
                task, cwd=self.directory,
                stdout=logfile,
                stderr=subprocess.PIPE)
            self._process.wait()
            logfile.close()
        except IOError:
            self.report.error("Can't access working directory.")
            self.fail()

    def checkHandled(self, w):
        handled = w.getHandledConstraints()
        allConstraints = membertools.get_member(
            self.analysis, "Fem::Constraint")
        for obj in set(allConstraints) - handled:
            self.report.warning("Ignored constraint %s." % obj.Label)


# Implementation of the Solve class
# This class gets the mofem binary
# and runs the analysis
class Solve(run.Solve):

    def run(self):
        # on rerun the result file will not deleted before starting the solver
        # if the solver fails, the existing result from a former run file will be loaded
        # TODO: delete result file (may be delete all files which will be recreated)
        print("Executing solver...\n")
        analysis_type = self.solver.AnalysisType
        print("Type", analysis_type)
        binary = settings.get_binary(analysis_type)
        print(analysis_type, binary)
        mesh = membertools.get_mesh_to_solve(self.analysis)[0]
        work_dir = join(self.directory, mesh.Name+".h5m")

        if binary is not None:
            try:
                task = [binary, "-my_file", work_dir]
                self._process = subprocess.Popen(
                    task, cwd=self.directory,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
            except IOError:
                self.report.error("Can't access working directory.")
                self.fail()
            try:
                task = [mbconver_path, join(
                    self.directory, "out.h5m"), join(
                    self.directory, "out.vtk")]
                self._process = subprocess.Popen(
                    task, cwd=self.directory,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
            except IOError:
                self.report.error("Can't access working directory.")
                self.fail()

            self._updateOutput()
        else:
            self.report.error(analysis_type+" executable not found.")
            self.fail()


class Results(run.Results):

    def run(self):
        if self.solver.MoFEMResult is None:
            self._createResults()
        postPath = self._getVTK()
        self.solver.MoFEMResult.read(postPath)
        self.solver.MoFEMResult.getLastPostObject().touch()
        self.solver.Document.recompute()

    def _createResults(self):
        self.solver.MoFEMResult = self.analysis.Document.addObject(
            "Fem::FemPostPipeline", self.solver.Name + "Result")
        self.solver.ElmerResult.Label = self.solver.Label + "Result"
        self.analysis.addObject(self.solver.MoFEMResult)

    def _getVTK(self):
        try:
            pass
        except IOError:
            self.report.error("Can't access working directory.")
            self.fail()
        return join(self.directory, "out.vtk")
# @}
