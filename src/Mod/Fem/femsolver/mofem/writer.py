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

__title__ = "FreeCAD FEM solver Elmer writer"
__author__ = "Markus Hovorka"
__url__ = "https://www.freecadweb.org"

# \addtogroup FEM
#  @{

import os
import os.path
import subprocess
import tempfile

from FreeCAD import Console
from FreeCAD import Units
from FreeCAD import ParamGet

import Fem
import FreeCAD
from os.path import join

from .. import writerbase
from femtools import geomtools

from .. import settings
from femmesh import gmshtools
from femmesh import meshtools
from femtools import constants
from femtools import femutils
from femtools import membertools


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
        self.med_path = join(self.include, "_med.med")
        self.cfg_path = join(self.include, "_med.config")
        writerbase.FemInputWriter.__init__(
            self,
            analysis_obj,
            solver_obj,
            mesh_obj,
            member,
            dir_name
        )

    def add_mofem_bcs(self):
        print("Fixed obj", self.member.cons_fixed)
        print("Fixed Disp", self.member.cons_displacement)
        unvGmshFd, unvGmshPath = tempfile.mkstemp(suffix=".unv")
        brepFd, brepPath = tempfile.mkstemp(suffix=".brep")
        geoFd, geoPath = tempfile.mkstemp(suffix=".geo")
        os.close(brepFd)
        os.close(geoFd)
        os.close(unvGmshFd)

        tools = gmshtools.GmshTools(self.mesh_obj, analysis=self.analysis)

        tools.get_group_data()  # Try to get group data

        # print(tools.group_elements) # print to see if we have it
        tools.group_elements['FIX_ALL'] = tools.group_elements.pop(
            'ConstraintFixed')
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
