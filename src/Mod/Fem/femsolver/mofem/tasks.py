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

import os
from femsolver import task
from os import listdir, mkdir, pread
from os.path import isfile
#from os.path import join
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
from feminout import importVTKResults


"""
Module containing one task class per task required for a solver implementation.
Those tasks divide the process of solving a analysis into the following steps: check, prepare, solve, results
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

    def run(self):  
        FreeCAD.Console.PrintMessage("Preparing files...\n")
        self.read_med = settings.get_binary("read_med")
        w = writer.MedWriterMoFEM(
            self.analysis,
            self.solver,
            membertools.get_mesh_to_solve(self.analysis)[0],
            membertools.AnalysisMember(self.analysis),
            self.directory
        )

        self._create_med(w)
        self._create_cfg(w)
        self._create_h5m(w)

    def _create_med(self, w):
        try:  # Generates MoFEM .med file
            FreeCAD.Console.PrintMessage("Writing .med file\n")
            w.gen_med_file()  #amends the .geo file with mofem bcs and creates med file
        except writer.MedWriterMoFEMError as e:
            self.report.error(str(e))
            self.fail()
        except IOError:
            self.report.error("Can't access working directory.")
            self.fail()

    def _create_cfg(self, w):
        try:  # Generate MoFEM .config file
            FreeCAD.Console.PrintMessage("Writing .config file\n")
            w.gen_cfg_file()
        except writer.MedWriterMoFEMError as e:
            self.report.error(str(e))
            self.fail()
        except IOError:
            self.report.error("Can't access working directory.")
            self.fail()

    def _create_h5m(self, w):
        if self.read_med is not None:
            h5m_log = join(self.directory, 'h5m_log.txt')
            with open(h5m_log, "w") as f:
                try:  # Generate MoFEM-compatible .h5m file
                    FreeCAD.Console.PrintMessage("Generating MoFEM-compatible .h5m file\n")
                    task = [self.read_med, "-med_file",  w.med_path,
                            "-meshsets_config", w.cfg_path,
                            "-output_file", w.work_path]
                    logfile = open(w.include+".log", "w")
                    self._process = subprocess.Popen(  # calls read_med tool
                        task, cwd=self.directory,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
                    out, err = self._process.communicate()
                    if self._process.returncode != 0:
                        for line in err.decode(encoding='utf-8').split('\n'):
                            f.write(line+'\n')
                        self.report.error("read_med tool failed check log file at: "+ h5m_log)
                        self.fail()
                    else:
                        for line in out.decode(encoding='utf-8').split('\n'):
                            f.write(line+'\n')
                        FreeCAD.Console.PrintLog("read_med tool finished, log file located at: "+ h5m_log)
                    
                except IOError:
                    self.report.error("Can't access working directory.")
                    self.fail()
        else:
            self.report.error("read_med executable not found.")
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

        FreeCAD.Console.PrintMessage("Executing solver...\n")
        analysis_type = self.solver.AnalysisType
        binary = settings.get_binary(analysis_type)
        mbconvert_path = settings.get_binary("mbconvert")
        mesh = membertools.get_mesh_to_solve(self.analysis)[0]
        res_dir = join(self.directory, "results_vtk")
        out_dir = join(self.directory, "output_h5m")
        work_file = join(self.directory, mesh.Name+".h5m")
        if mbconvert_path is None:
            self.report.error("mbconvert tool not found.")
            self.fail()
        elif binary is not None:
            solver_log = join(self.directory, 'solver_log.txt')
            with open(solver_log, "w") as f:
                try:
                    if not os.path.isdir(out_dir):
                        os.mkdir(out_dir)
                    task = [binary, "-my_file", work_file]
                    self._process = subprocess.Popen(
                        task, cwd=out_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
                    out, err = self._process.communicate()
                    if self._process.returncode != 0:
                        for line in err.decode(encoding='utf-8').split('\n'):
                            f.write(line+'\n')
                        self.report.error(analysis_type+" failed check log file at: "+ solver_log)
                        self.fail()
                    else:
                        for line in out.decode(encoding='utf-8').split('\n'):
                            f.write(line+'\n')
                        FreeCAD.Console.PrintLog(analysis_type + "finished, log file located at: "+ solver_log)
                except FileNotFoundError:
                    self.report.error(".h5m file is missing from work directory.")
                    self.fail()
                except IOError:
                    self.report.error("Can't access working directory.")
                    self.fail()
            convert_log = join(self.directory, 'convert_log.txt')
            with open(convert_log, "w") as f:
                try:
                    # get all files from directory
                    files_list = [f for f in listdir(out_dir) if isfile(join(out_dir, f))]
                    # check if they are .h5m
                    out_list = [f for f in files_list if f[-3:] == "h5m"]
                    if not out_list:
                        self.report.error("No MoFEM results found. Check "+out_dir+" for .h5m files")
                        self.fail()
                    if not os.path.isdir(res_dir):
                        os.mkdir(res_dir)
                    for out in out_list:
                        res = out.replace('h5m', 'vtk')
                        task = [mbconvert_path, join(out_dir,out), join(res_dir,res)]
                        self._process = subprocess.Popen(
                            task, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
                        out, err = self._process.communicate()
                        if self._process.returncode != 0:
                            for line in err.decode(encoding='utf-8').split('\n'):
                                f.write(line+'\n')
                            self.report.error("mbconvert tool failed check log file at: "+ convert_log)
                            self.fail()
                        else:
                            for line in out.decode(encoding='utf-8').split('\n'):
                                f.write(line+'\n')
                            FreeCAD.Console.PrintLog("mbconvert finished, log file located at: "+ convert_log)
                except IOError:
                    self.report.error("Can't access working directory.")
                    self.fail()
        else:
            self.report.error(analysis_type+" executable not found.")
            self.fail()


class Results(run.Results):

    def run(self):
        FreeCAD.Console.PrintMessage("Loading result vtk files")
        res_dir = join(self.directory, "results_vtk")
        print(res_dir)
        importVTKResults.importVtk(join(res_dir,"out.vtk"),"Result", 0)
        """
        if self.solver.MoFEMResult is None:
            self._createResults()
        postPath = self._getVTK()
        self.solver.MoFEMResult.read(postPath)
        self.solver.MoFEMResult.getLastPostObject().touch()
        self.solver.Document.recompute()
        """

    def _createResults(self):
        self.solver.MoFEMResult = self.analysis.Document.addObject(
            "Fem::FemPostPipeline", self.solver.Name + "Result")
        self.solver.MoFEMResult.Label = self.solver.Label + "Result"
        self.analysis.addObject(self.solver.MoFEMResult)

    def _getVTK(self):
        try:
            pass
        except IOError:
            self.report.error("Can't access working directory.")
            self.fail()
        return join(self.directory, "out.vtk")
# @}
