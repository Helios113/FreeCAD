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

from femtools import membertools
from femtools import femutils
from femtools import constants
from femmesh import meshtools
from femmesh import gmshtools
from .. import settings
from femtools import geomtools
from .. import writerbase
from os.path import join
import FreeCAD
import Fem
from FreeCAD import ParamGet
from FreeCAD import Units
from FreeCAD import Console
__title__ = "FreeCAD FEM MoFEM writer"
__author__ = "Preslav Aleksandrov"
__url__ = "https://www.freecadweb.org"

# \addtogroup FEM
#  @{

import os
import os.path
import subprocess
import tempfile
from collections import defaultdict


# Generate .geo file
# Change the physical group names
# Generate .unv and write as .med
# Write the .med file to a usable directory
class MedWriterMoFEM(writerbase.FemInputWriter):
    def __init__(
        self,
        analysis_obj,
        solver_obj,
        mesh_obj,
        member,
        dir_name=None
    ):
        self.mesh_obj = mesh_obj
        self.member = member
        print("Mesh object", self.mesh_obj)
        self.mesh_name = self.mesh_obj.Name
        self.dir_name = dir_name
        self.include = join(self.dir_name, self.mesh_name)
        self.med_path = self.include+"_med.med"
        self.cfg_path = self.include+"_med.config"
        writerbase.FemInputWriter.__init__(
            self,
            analysis_obj,
            solver_obj,
            mesh_obj,
            member,
            dir_name
        )

    def get_mofem_bcs(self, tools):
        new_group_data = {}

        if self.fixed_objects:
            new_group_data['FIX_ALL'] = []
            for fix in self.fixed_objects:
                work_obj = fix['Object']
                print("Object refrence", type(work_obj.References[0][1][0]))
                new_group_data['FIX_ALL'].append(work_obj.References[0][1][0])
        if self.displacement_objects:
            new_group_data['FIX_X'] = []
            new_group_data['FIX_Y'] = []
            new_group_data['FIX_Z'] = []
            for disp in self.displacement_objects:
                work_obj = disp['Object']
                if work_obj.xFix:
                    print("Object refrence", type(
                        work_obj.References[0][1][0]))
                    new_group_data['FIX_X'].append(
                        work_obj.References[0][1][0])
                elif work_obj.yFix:
                    print("Object refrence", type(
                        work_obj.References[0][1][0]))
                    new_group_data['FIX_Y'].append(
                        work_obj.References[0][1][0])
                elif work_obj.zFix:
                    print("Object refrence", type(
                        work_obj.References[0][1][0]))
                    new_group_data['FIX_Z'].append(
                        work_obj.References[0][1][0])
            new_group_data = {k: v for k,
                              v in new_group_data.items() if v != []}
        """
        print("disp group", tools.group_elements['ConstraintDisplacement'])
        print(self.displacement_objects)
        for disp in self.displacement_objects:
            print("Disp object is")
            print(disp)
            print(disp['Object'])
            print(disp['Object'].xFix)
            print(disp['Object'].Name)
            print(disp['Object'].References)
        """
        return new_group_data

    def add_mofem_bcs(self):
        # print("Fixed obj", self.member.cons_fixed)
        # print("Fixed Disp", self.member.cons_displacement)
        unvGmshFd, unvGmshPath = tempfile.mkstemp(suffix=".unv")
        brepFd, brepPath = tempfile.mkstemp(suffix=".brep")
        geoFd, geoPath = tempfile.mkstemp(suffix=".geo")
        os.close(brepFd)
        os.close(geoFd)
        os.close(unvGmshFd)

        tools = gmshtools.GmshTools(self.mesh_obj, analysis=self.analysis)

        tools.get_group_data()  # Try to get group data
        print("At line 117")
        tools.group_elements = self.get_mofem_bcs(tools)
        print(tools.group_elements)  # print to see if we have it

        tools.group_nodes_export = False
        tools.ele_length_map = {}
        tools.temp_file_geometry = brepPath
        tools.temp_file_geo = geoPath
        tools.temp_file_mesh = unvGmshPath

        tools.get_dimension()
        tools.get_region_data()
        tools.get_boundary_layer_data()
        tools.write_part_file()
        tools.write_geo()
        if False:
            Console.PrintMessage(
                "Solver Elmer testmode, Gmsh will not be used. "
                "It might not be installed.\n"
            )
            import shutil
            shutil.copyfile(geoPath, os.path.join(
                self.directory, "group_mesh.geo"))
        else:
            tools.get_gmsh_command()
            tools.run_gmsh_with_geo()

            ioMesh = Fem.FemMesh()
            ioMesh.read(unvGmshPath)

            print("MED file path", self.med_path)

            ioMesh.write(self.med_path)

        os.remove(brepPath)
        os.remove(geoPath)
        os.remove(unvGmshPath)


class MedWriterMoFEMError(Exception):
    pass

# @}
