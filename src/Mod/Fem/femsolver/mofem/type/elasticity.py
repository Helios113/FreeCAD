# ***************************************************************************
# *   Copyright (c) 2017 Markus Hovorka <m.hovorka@live.de>                 *
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

__title__ = "FreeCAD FEM solver MoFEM analysis type object Elasticity"
__author__ = "Preslav Aleksandrov"
__url__ = "https://www.freecadweb.org"

# \addtogroup FEM
#  @{

from femtools import femutils
from ... import equationbase
from . import linear


def create(doc, name="Linear Elasticity"):
    return femutils.createObject(
        doc, name, Proxy, ViewProxy)


class Proxy(equationbase.TypeElasticityProxy):  # add linear proxy later

    Type = "Fem::TypeMoFEMLinerElasticity"

    def __init__(self, obj):
        super(Proxy, self).__init__(obj)
        obj.addProperty(
            "App::PropertyBool",
            "DoFrequencyAnalysis",
            "Elasticity",
            ""
        )
        obj.addProperty(
            "App::PropertyInteger",
            "EigenmodesCount",
            "Elasticity",
            ""
        )
        obj.addProperty(
            "App::PropertyBool",
            "CalculateStrains",
            "Elasticity",
            ""
        )
        obj.addProperty(
            "App::PropertyBool",
            "CalculateStresses",
            "Elasticity",
            ""
        )
        obj.addProperty(
            "App::PropertyBool",
            "CalculatePrincipal",
            "Elasticity",
            ""
        )
        obj.addProperty(
            "App::PropertyBool",
            "CalculatePangle",
            "Elasticity",
            ""
        )


class ViewProxy(equationbase.TypeElasticityViewProxy):
    pass

# @}
