# SDTrimSP GUI - a graphical user interface for SDTrimSP to simulate sputtering, ion implantation and the dynamic
# effects of ion irradiation
#
# Copyright(C) 2022, Paul S.Szabo, David Weichselbaum, Herbert Biber, Christian Cupak, Andreas Mutzke,
# Richard A.Wilhelm, Friedrich Aumayr
#
# This program implements libraries of the Qt framework (https://www.qt.io/).
#
# This program is free software: you can redistribute it and / or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not, see
# https://www.gnu.org/licenses/.


from PyQt5.QtCore import pyqtSignal
from TableWidgets.CompTable import CompTable

class TargetCompTable(CompTable):
    syncableValueChanged = pyqtSignal(str, CompTable.SyncedValue, float)

    def __init__(self, parent):
        super().__init__([], parent)

    def addRow(self):
        row = super().addRow()
        row.maxConcentration.valueChanged.connect(lambda value, r=row:\
                        self.emitSyncableValueChange(CompTable.SyncedValue.CONCENTRATION, value, r))
        row.atomicDensity.valueChanged.connect(lambda value, r=row:\
                        self.emitSyncableValueChange(CompTable.SyncedValue.ATOMICDENSITY, value, r))
        row.surfBindEnergy.valueChanged.connect(lambda value, r=row:\
                        self.emitSyncableValueChange(CompTable.SyncedValue.SURFBINDENERGY, value, r))
        row.displEnergy.valueChanged.connect(lambda value, r=row:\
                        self.emitSyncableValueChange(CompTable.SyncedValue.DISPLENERGY, value, r))
        row.inelLossModel.currentIndexChanged.connect(lambda idx, r=row:\
                          self.emitSyncableValueChange(CompTable.SyncedValue.INELMODEL, idx, r))
        return row

    def emitSyncableValueChange(self, valueID, newValue, row):
        if row.element is not None:
            self.syncableValueChanged.emit(row.element.symbol, valueID, newValue)