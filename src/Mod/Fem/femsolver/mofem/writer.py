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
import fileinput
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
        self.mesh_name = self.mesh_obj.Name
        self.dir_name = dir_name
        self.include = join(self.dir_name, self.mesh_name)
        self.med_path = self.include+".med"
        self.cfg_path = self.include+".config"
        self.work_path = self.include+".h5m"
        writerbase.FemInputWriter.__init__(
            self,
            analysis_obj,
            solver_obj,
            mesh_obj,
            member,
            dir_name
        )

    def get_mofem_bcs(self):
        # This here is done for concistency
        # The order of the different conditions matters
        # We change them here so we can use the same order later
        # When creating the block sets for the FEM solver
        new_group_data = {}

        if self.fixed_objects:
            for i, fix in enumerate(self.fixed_objects):
                work_obj = fix['Object']
                print("Object refrence", work_obj.References)
                new_group_data['FIX_ALL_' +
                               str(i)] = [work_obj.References[0][1][0]]

        if self.displacement_objects:
            for i, disp in enumerate(self.displacement_objects):
                work_obj = disp['Object']
                new_group_data['FIX_DISP_' +
                               str(i)] = [work_obj.References[0][1][0]]

        if self.pressure_objects:
            for i, press in enumerate(self.pressure_objects):
                work_obj = press['Object']
                new_group_data['PRESSURE_' +
                               str(i)] = [work_obj.References[0][1][0]]

        print("New group data", new_group_data)
        return new_group_data

    def gen_med_file(self):
        brepFd, brepPath = tempfile.mkstemp(suffix=".brep")
        geoFd, geoPath = tempfile.mkstemp(suffix=".geo")
        os.close(brepFd)
        os.close(geoFd)

        if self.mesh_obj.ElementOrder == '2nd':
            Console.PrintError("Only element order one supported by MoFem")
            Console.PrintError("Changing order")
            self.mesh_obj.ElementOrder = '1st'

        tools = gmshtools.GmshTools(self.mesh_obj, analysis=self.analysis)
        tools.get_group_data()  # Try to get group data
        print("Old group data", tools.group_elements)
        tools.group_elements = self.get_mofem_bcs()

        tools.group_nodes_export = True
        tools.ele_length_map = {}
        tools.temp_file_geometry = brepPath
        tools.temp_file_geo = geoPath
        tools.temp_file_mesh = self.med_path

        tools.get_dimension()
        tools.get_region_data()
        tools.get_boundary_layer_data()
        tools.write_part_file()
        tools.write_geo()
        tools.get_gmsh_command()
        self._change_MeshFormat(geoPath)
        print("GeoPath", geoPath)
        print("Med path", self.med_path)
        print("CFG path", self.cfg_path)
        tools.run_gmsh_with_geo()

        os.remove(brepPath)
        os.remove(geoPath)

    def _change_MeshFormat(self, geoPath):
        with fileinput.FileInput(geoPath,
                                 inplace=True, backup='.bak') as f:
            for line in f:
                if line == 'Mesh.Format = 2;\n':
                    print('Mesh.Format = 10;', end='\n')
                else:
                    print(line, end='')

    def gen_cfg_file(self):
        cfg = open(self.cfg_path, "w")
        cfg.write(
            "[block_1]\nid=101\nadd=BLOCKSET\nname=MAT_ELASTIC\nyoung=1\npoisson=0.1\n\n")
        block_number = 2
        if self.fixed_objects:
            for fix in self.fixed_objects:
                cfg.write("[block_{block_id}]\nid={id}\nadd=BLOCKSET\nname={name}\n\n".format(
                    block_id=block_number, id=100+block_number, name="FIX_ALL"))
                block_number += 1
        if self.displacement_objects:
            for disp in self.displacement_objects:
                work_obj = disp['Object']
                name = "FIX_"
                if work_obj.xFix:
                    name += "X"
                if work_obj.yFix:
                    name += "Y"
                if work_obj.zFix:
                    name += "Z"
                cfg.write("[block_{block_id}]\nid={id}\nadd=BLOCKSET\nname={name}\n\n".format(
                    block_id=block_number, id=100+block_number, name=name))
                block_number += 1

        if self.pressure_objects:
            for press in self.pressure_objects:
                work_obj = press['Object']
                cfg.write("[block_{block_id}]\nid={id}\nadd=SIDESET\nname={name}\n".format(
                    block_id=block_number, id=100+block_number, name=name))
                cfg.write("pressure_flag2=0\npressure_magnitude={dirmag}".format(
                    dirmag=-work_obj.Pressure if work_obj.Reversed else work_obj.Pressure))
                block_number += 1

        cfg.close()


class MedWriterMoFEMError(Exception):
    pass

# @}
