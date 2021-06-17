/***************************************************************************
 *   Copyright (c) 2015 FreeCAD Developers                                 *
 *   Author: Bernd Hahnebach <bernd@bimstatik.ch>                          *
 *   Based on src/Mod/Fem/Gui/DlgSettingsFemCcxImp.cpp                     *
 *                                                                         *
 *   This file is part of the FreeCAD CAx development system.              *
 *                                                                         *
 *   This library is free software; you can redistribute it and/or         *
 *   modify it under the terms of the GNU Library General Public           *
 *   License as published by the Free Software Foundation; either          *
 *   version 2 of the License, or (at your option) any later version.      *
 *                                                                         *
 *   This library  is distributed in the hope that it will be useful,      *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU Library General Public License for more details.                  *
 *                                                                         *
 *   You should have received a copy of the GNU Library General Public     *
 *   License along with this library; see the file COPYING.LIB. If not,    *
 *   write to the Free Software Foundation, Inc., 59 Temple Place,         *
 *   Suite 330, Boston, MA  02111-1307, USA                                *
 *                                                                         *
 ***************************************************************************/


#include "PreCompiled.h"

#include "DlgSettingsFemMoFEMImp.h"
#include "ui_DlgSettingsFemMoFEM.h"

#include <Gui/Application.h>
#include <Gui/PrefWidgets.h>

using namespace FemGui;

DlgSettingsFemMoFEMImp::DlgSettingsFemMoFEMImp( QWidget* parent )
  : PreferencePage( parent )
  , ui(new Ui_DlgSettingsFemMoFEMImp)
{
    ui->setupUi(this);
}

DlgSettingsFemMoFEMImp::~DlgSettingsFemMoFEMImp()
{
    // no need to delete child widgets, Qt does it all for us
}

void DlgSettingsFemMoFEMImp::saveSettings()
{
    ui->cb_mofem_binary_std->onSave();
    ui->cb_bone_std->onSave();
    ui->cb_elasticity_std->onSave();


    ui->fc_mofem_binary_path->onSave();
    ui->fc_mofem_readmed_path->onSave();
    ui->fc_bone_path->onSave();
    ui->fc_elasticity_path->onSave();
}

void DlgSettingsFemMoFEMImp::loadSettings()
{
    ui->cb_mofem_binary_std->onRestore();
    ui->cb_bone_std->onRestore();
    ui->cb_elasticity_std->onRestore();


    ui->fc_mofem_binary_path->onRestore();
    ui->fc_mofem_readmed_path->onRestore();
    ui->fc_bone_path->onRestore();
    ui->fc_elasticity_path->onRestore();
}

/**
 * Sets the strings of the subwidgets using the current language.
 */
void DlgSettingsFemMoFEMImp::changeEvent(QEvent *e)
{
    if (e->type() == QEvent::LanguageChange) {
        ui->retranslateUi(this);
    }
    else {
        QWidget::changeEvent(e);
    }
}

#include "moc_DlgSettingsFemMoFEMImp.cpp"
