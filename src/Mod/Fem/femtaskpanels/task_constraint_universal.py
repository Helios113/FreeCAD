# ***********************************************************************************
# *   Copyright (c) 2017 Markus Hovorka <m.hovorka@live.de>                         *
# *   Copyright (c) 2020 Bernd Hahnebach <bernd@bimstatik.org>                      *
# *   Copyright (c) 2021 Preslav Aleksandrov <preslav.aleksandrov@protonmail.com>   *
# *                                                                                 *
# *   This file is part of the FreeCAD CAx development system.                      *
# *                                                                                 *
# *   This program is free software; you can redistribute it and/or modify          *
# *   it under the terms of the GNU Lesser General Public License (LGPL)            *
# *   as published by the Free Software Foundation; either version 2 of             *
# *   the License, or (at your option) any later version.                           *
# *   for detail see the LICENCE text file.                                         *
# *                                                                                 *
# *   This program is distributed in the hope that it will be useful,               *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of                *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                 *
# *   GNU Library General Public License for more details.                          *
# *                                                                                 *
# *   You should have received a copy of the GNU Library General Public             *
# *   License along with this program; if not, write to the Free Software           *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307          *
# *   USA                                                                           *
# *                                                                                 *
# ***********************************************************************************

__title__ = "FreeCAD FEM constraint universal task panel for the document object"
__author__ = "Prelsav Aleksandrov"
__url__ = "https://www.freecadweb.org"

# @package task_constraint_universal
#  \ingroup FEM
#  \brief task panel for constraint universal object

import posix
from subprocess import check_output

import FreeCAD
import FreeCADGui
from FreeCAD import Units
from femtools.femutils import is_of_type
from femguiutils import selection_widgets
from femtools import femutils
from femtools import membertools
import re
import json
import os
from PySide import QtCore, QtGui
import FemGui


class _TaskPanel(object):

    def __init__(self, obj):
        self._obj = obj
        self._refWidget = selection_widgets.GeometryElementsSelection(
            obj.References,
            ["Solid", "Face"],
            True,
            False
        )
        self._paramWidget = FreeCADGui.PySideUic.loadUi(
            FreeCAD.getHomePath() + "Mod/Fem/Resources/ui/ConstraintUniversal.ui")
        
        self.form = [self._refWidget, self._paramWidget]
        self._analysis = obj.getParentGroup()
        self._solver = None
        self._json_path = None
        self._mesh = None
        if self._analysis is None:
            print(
                "An analysis is needed to use the automatic boundary detection.")
            # check if MoFEM is in analysis
        else:
            self._mesh = membertools.get_single_member(
                self._analysis, "Fem::FemMeshObject")
            for i in self._analysis.Group:
                if is_of_type(i, "FEM::SolverMoFEM"):
                    if i.Module is not None:
                        mod_number = re.search(r'\d+', i.Module).group(0)
                        arguments = [i.Path, '-module', mod_number, '-bc']
                        self._json_path = check_output(arguments).decode("utf-8").splitlines()[0]
                        self._solver = i
                        print(self._json_path)
            if self._solver is None:
                print(
                "A mofem solver is needed to use the automatic boundary detection.")
        self._initParamWidget()
        self._part = None            
        if self._mesh is not None:
            self._part = femutils.get_part_to_mesh(self._mesh)
        self._partVisible = None
        self._meshVisible = None
        self._isPosix = (os.name == "posix")

    def open(self):
        if self._mesh is not None and self._part is not None:
            self._meshVisible = self._mesh.ViewObject.isVisible()
            self._partVisible = self._part.ViewObject.isVisible()
            self._mesh.ViewObject.hide()
            self._part.ViewObject.show()

    def reject(self):
        self._restoreVisibility()
        FreeCADGui.ActiveDocument.resetEdit()
        return True

    def accept(self):
        if self._obj.References != self._refWidget.references:
            self._obj.References = self._refWidget.references
        self._applyWidgetChanges()
        self._obj.Document.recompute()
        FreeCADGui.ActiveDocument.resetEdit()
        self._restoreVisibility()
        return True

    def _restoreVisibility(self):
        if self._mesh is not None and self._part is not None:
            if self._meshVisible:
                self._mesh.ViewObject.show()
            else:
                self._mesh.ViewObject.hide()
            if self._partVisible:
                self._part.ViewObject.show()
            else:
                self._part.ViewObject.hide()

    def _initParamWidget(self):
        self._paramWidget.tabWidget.setTabEnabled(2, False)
        if self._json_path is not None:
            self._paramWidget.tabWidget.setTabEnabled(2, True)
            self._loadAutoFile()

        self._paramWidget.fc_file.setFilter("*.json")
        self._clearWindow()
        self._paramWidget.fc_file.fileNameChanged.connect(self._fileSelect)
        self._paramWidget.btn_file.clicked.connect(self._addFileBC)

        self._paramWidget.btn_manual.clicked.connect(self._addManualBC)
        self._paramWidget.sb_manual.valueChanged.connect(self._updateMTable)

        self._paramWidget.btn_automatic.clicked.connect(self._addManualBC)

    def _applyWidgetChanges(self):
        return
        """
        unit = "V"
        self._obj.PotentialEnabled = \
            not self._paramWidget.potentialBox.isChecked()
        if self._obj.PotentialEnabled:
            # if the input widget shows not a green hook, but the user presses ok
            # we could run into a syntax error on getting the quantity, try mV
            quantity = None
            try:
                quantity = Units.Quantity(self._paramWidget.potentialTxt.text())
            except ValueError:
                FreeCAD.Console.PrintMessage(
                    "Wrong input. OK has been triggered without a green hook "
                    "in the input field. Not recognised input: '{}' "
                    "Potential has not been set.\n"
                    .format(self._paramWidget.potentialTxt.text())
                )
            if quantity is not None:
                self._obj.Potential = float(quantity.getValueAs(unit))
        self._obj.PotentialConstant = self._paramWidget.potentialConstantBox.isChecked()

        self._obj.ElectricInfinity = self._paramWidget.electricInfinityBox.isChecked()

        calc_is_checked = self._paramWidget.electricForcecalculationBox.isChecked()
        self._obj.ElectricForcecalculation = calc_is_checked  # two lines because max line length

        self._obj.CapacitanceBodyEnabled = \
            not self._paramWidget.capacitanceBodyBox.isChecked()
        if self._obj.CapacitanceBodyEnabled:
            self._paramWidget.capacitanceBody_spinBox.setEnabled(True)
            self._obj.CapacitanceBody = self._paramWidget.capacitanceBody_spinBox.value()

            """

    # Manual Tab settings
    def _updateMTable(self):
        n = self._paramWidget.sb_manual.value()
        self._paramWidget.tw_manual.setRowCount(n)

    def _addManualBC(self):
        # TODO check if name is empty
        self._obj.Blockset = self._paramWidget.in_manual.text()
        for i in range(self._paramWidget.tw_manual.rowCount()):
            name = self._paramWidget.tw_manual.item(i, 0)
            val = self._paramWidget.tw_manual.item(i, 1)
            if name is None:
                continue
            name = name.text()
            print(name, val)
            if not hasattr(self._obj, name):
                self._obj.addProperty(
                    "App::PropertyString",
                    name,
                    "Parameter",
                    name
                )
                if val is None:
                    continue
                setattr(self._obj, name, val.text())
        self.accept()

    # File Tab settings
    def _clearWindow(self):
        self._paramWidget.tw_file.clear()
        empt = QtGui.QWidget()
        self._paramWidget.tw_file.addTab(empt, "Empty")

    def _fileSelect(self, a):
        self._paramWidget.tw_file.clear()
        f = open(a,)
        data = json.load(f)
        for key, value in data.items():
            # TODO get info from json file
            n = len(value)
            table = QtGui.QTableWidget(n, 2, None)
            table.setObjectName("ab_"+key)
            table.setHorizontalHeaderLabels(["Name", "Values"])
            table.horizontalHeader().setStretchLastSection(True)
            rows = 0
            for i, j in value.items():
                newItem = QtGui.QTableWidgetItem(i)
                table.setItem(rows, 0, newItem)
                newItem = QtGui.QTableWidgetItem(j)
                table.setItem(rows, 1, newItem)
                rows += 1
            self._paramWidget.tw_file.addTab(table, key)
        # TODO add widget to list of widgets
        f.close()
        # self._paramWidget.tw_file

    def _addFileBC(self):

        i = self._paramWidget.tw_file.currentIndex()

        self._obj.Blockset = self._paramWidget.tw_file.tabText(i)
        table = self._paramWidget.tw_file.currentWidget()

        for i in range(table.rowCount()):
            name = table.item(i, 0)
            val = table.item(i, 1)
            if name is None:
                continue
            name = name.text()
            print(name, val)
            if not hasattr(self._obj, name):
                self._obj.addProperty(
                    "App::PropertyString",
                    name,
                    "Parameter",
                    name
                )
                if val is None:
                    continue
                setattr(self._obj, name, val.text())
        self.accept()
        return
    # Auto tab settings
    def _loadAutoFile(self):
        table = self._paramWidget.tw_automatic
        table.clear()
        table.setHorizontalHeaderLabels(["Name", "Values"])
        f = open(self._json_path)
        data = json.load(f)
        self._paramWidget.tw_automatic.setRowCount(len(data)-1)
        
        rows = 0
        for key, value in list(data.items())[1:]:
            newItem = QtGui.QTableWidgetItem(key)
            table.setItem(rows, 0, newItem)
            newItem = QtGui.QTableWidgetItem(value)
            table.setItem(rows, 1, newItem)
            rows += 1
        # TODO add widget to list of widgets
        f.close()
        # self._paramWidget.tw_file
    def _addAutoBC(self):
        print("Apply auto")