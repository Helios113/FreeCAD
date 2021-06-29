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

from pprint import pp
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


# Generate .geo file
# Change the physical group names
# Generate .med
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

        order_index = 0
        if self.material_objects:
            self._bc_parse(self.material_objects, new_group_data,
                           str(order_index) + "mat", )
            order_index += 1

        #if self.material_nonlinear_objects

        if self.fixed_objects:
            self._bc_parse(self.fixed_objects, new_group_data,
                           str(order_index) + "fix_all")
            order_index += 1

        if self.displacement_objects:
            self._bc_parse(self.displacement_objects, new_group_data,
                           str(order_index) + "disp")
            order_index += 1

        if self.pressure_objects:
            self._bc_parse(self.pressure_objects, new_group_data,
                           str(order_index) + "pressure")
            order_index += 1
        
        if self.selfweight_objects:
            for i, ele in enumerate(self.selfweight_objects):
                print("___________")
                work_obj = ele['Object']
                print(work_obj)
                print(work_obj.Gravity_x)
                print(work_obj.Gravity_y)
                print(work_obj.Gravity_z)
            #self._bc_parse(self.selfweight_objects, new_group_data,
            #               str(order_index) + "sw")
            #order_index += 1
        
        if self.force_objects:
            for i, ele in enumerate(self.force_objects):
                print("___________")
                work_obj = ele['Object']
                print(work_obj)
                print(work_obj.Force) # magnitude
                print(work_obj.DirectionVector)# the one we need normalised
                print(work_obj.References) 
            self._bc_parse(self.force_objects, new_group_data,
                           str(order_index) + "force")
            order_index += 1
        print(new_group_data)
        return new_group_data

    def _bc_parse(self, obj, new_group_data, name):
        for i, ele in enumerate(obj):
            work_obj = ele['Object']
            new_group_data[name + str(i)] = [work_obj.References[0][1][0]]

    def gen_med_file(self):
        brepFd, brepPath = tempfile.mkstemp(dir=self.dir_name, suffix=".brep")
        geoFd, geoPath = tempfile.mkstemp(dir=self.dir_name, suffix=".geo")
        unvGmshFd, unvGmshPath = tempfile.mkstemp(suffix=".unv")
        os.close(brepFd)
        os.close(geoFd)
        os.close(unvGmshFd)

        if self.mesh_obj.ElementOrder == '2nd':
            Console.PrintError("Only element order one supported by MoFem")
            Console.PrintError("Changing order")
            self.mesh_obj.ElementOrder = '1st'

        tools = gmshtools.GmshTools(self.mesh_obj, analysis=self.analysis)
        tools.get_group_data()

        tools.group_elements = self.get_mofem_bcs()
        tools.group_nodes_export = True
        tools.ele_length_map = {}
        tools.temp_file_geometry = brepPath
        tools.temp_file_geo = geoPath
        tools.temp_file_mesh = unvGmshPath
        tools.get_dimension()
        tools.get_region_data()
        tools.get_boundary_layer_data()
        tools.write_part_file()
        tools.write_geo()
        tools.get_gmsh_command()
        tools.run_gmsh_with_geo()
        tools.read_and_set_new_mesh()
        tools.temp_file_mesh = self.med_path
        tools.write_geo(33)
        tools.run_gmsh_with_geo()
        
        os.remove(brepPath)
        os.remove(geoPath)
        os.remove(unvGmshPath)

    """def _change_MeshFormat(self, geoPath):
        file = fileinput.input(geoPath, inplace=True, backup='.bak')
        for line in file:
            if line == 'Mesh.Format = 2;\n':
                print('Mesh.Format = 10;', end='\n')
            else:
                print(line, end='')
        file.close()
        """

    def gen_cfg_file(self):
        cfg = open(self.cfg_path, "w")
        
        block_number = 2

        if self.material_objects:
            for mat in self.material_objects:
                work_obj = mat['Object']
                youngs_modulus = work_obj.Material['YoungsModulus']
                youngs_modulus = [float(s) for s in youngs_modulus.split() if s.isnumeric()][0]
                poissons = work_obj.Material['PoissonRatio']
                cfg.write(("[block_{block_id}]\nid={id}\nadd=BLOCKSET\n"
                           "name={name}\nyoung={E}\npoisson={lam}\n\n").format(
                        block_id=block_number, id=100+block_number,
                        name="MAT_ELASTIC", E=youngs_modulus, lam=poissons))
                # print("Our obj")
                # print(work_obj.Material)
                block_number += 1

        if self.fixed_objects:
            for fix in self.fixed_objects:
                cfg.write(("[block_{block_id}]\nid={id}\nadd=NODESET\n"
                          "disp_flag1=1\ndisp_ux=0.0\ndisp_flag2=1\n"
                          "disp_uy=0.0\ndisp_flag3=1\ndisp_uz=0.0\n\n").format(
                        block_id=block_number, id=100+block_number))
                block_number += 1
        if self.displacement_objects:
            for disp in self.displacement_objects:
                # implement proper displacements
                work_obj = disp['Object']
                cfg.write("[block_{block_id}]\nid={id}\nadd=BLOCKSET\n".format(
                    block_id=block_number, id=100+block_number))
                cfg.write(("disp_flag1={x}\ndisp_ux={ux}\n"
                           "disp_flag2={y}\ndisp_uy={uy}\n"
                           "disp_flag3={z}\ndisp_uz={uz}\n\n")).format(
                            x=int(work_obj.xFix == 'true'),
                            ux=work_obj.xDisplacement,
                            y=int(work_obj.yFix == 'true'),
                            uy=work_obj.yDisplacement,
                            z=int(work_obj.zFix == 'true'),
                            uz=work_obj.zDisplacement)
                block_number += 1

        if self.pressure_objects:
            for press in self.pressure_objects:
                work_obj = press['Object']
                name = "PRESSURE"
                cfg.write("[block_{block_id}]\nid={id}\nadd=SIDESET\nname={name}\n".format(
                    block_id=block_number, id=100+block_number, name=name))
                cfg.write("pressure_flag2=0\npressure_magnitude={dirmag}\n\n".format(
                    dirmag=-work_obj.Pressure if work_obj.Reversed else work_obj.Pressure))
                block_number += 1
            


class MedWriterMoFEMError(Exception):
    pass

# @}
