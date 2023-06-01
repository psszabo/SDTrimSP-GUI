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


from PyQt5.QtWidgets import QDoubleSpinBox
from TableWidgets.CompTable import CompTable, CompRow, CompEntry
import Utility

class BeamCompEntry(CompEntry):
    def __init__(self, element, abundance, kinEnergy, angle, maxConcentration, atomicDensity, surfBindEnergy, displEnergy, inelLossModel):
        super().__init__(element, maxConcentration, atomicDensity, surfBindEnergy, displEnergy, inelLossModel)
        self.abundance = abundance
        self.kinEnergy = kinEnergy
        self.angle = angle

class BeamCompRow(CompRow):
    def createWidgets(self):
        super().createWidgets()
        self.abundance = QDoubleSpinBox()
        self.kinEnergy = QDoubleSpinBox()
        self.angle = QDoubleSpinBox()
        self.rowWidgets[self.insertIdx:self.insertIdx] = [self.abundance, self.kinEnergy, self.angle]

    def initWidgets(self):
        super().initWidgets()
        self.abundance.setRange(0, 1)
        self.abundance.setSingleStep(0.01)
        self.abundance.valueChanged.connect(lambda: self.updateAbundanceHighlight())
        self.abundance.valueChanged.connect(self.contentChanged.emit)
        self.kinEnergy.setRange(0, 1e8)
        self.kinEnergy.setValue(500)
        self.kinEnergy.setMaximumWidth(75)
        self.kinEnergy.valueChanged.connect(self.contentChanged.emit)
        self.angle.setRange(-90, 90)
        self.angle.setSingleStep(0.01)
        self.angle.valueChanged.connect(self.contentChanged.emit)
        self.updateAbundanceHighlight()

    def setRowData(self, element, abundance, kinEnergy, angle, maxConcentration, atomicDensity, surfBindEnergy, displEnergy, inelLossModel):
        super().setRowData(element, maxConcentration, atomicDensity, surfBindEnergy, displEnergy, inelLossModel)
        self.abundance.setValue(abundance)
        self.kinEnergy.setValue(kinEnergy)
        self.angle.setValue(angle)

    def getRowData(self):
        return BeamCompEntry(self.element, self.abundance.value(), self.kinEnergy.value(),
                             self.angle.value(), self.maxConcentration.value(), self.atomicDensity.value(),
                             self.surfBindEnergy.value(), self.displEnergy.value(), self.inelLossModel.currentIndex())

    def updateAbundanceHighlight(self):
        Utility.setWidgetHighlight(self.abundance, self.abundance.value()==0)

class BeamCompTable(CompTable):

    def __init__(self, parent):
        self.kinEnergyEditable = True
        self.angleEditable = True
        labels = ['Abundance', 'Energy [eV]', 'Angle [°]']
        super().__init__(labels, parent)
        self.horizontalHeaderItem(3).setToolTip('<i>qubeam</i><br>How much each element contributes to the beam composition.'+\
                                                '\nThe abundances of all elements sum up to 1')
        self.horizontalHeaderItem(4).setToolTip('<i>e0</i><br>The kinetic energy (in eV) of the incoming ions')
        self.horizontalHeaderItem(5).setToolTip('<i>alpha</i><br>The angle of incidence (α) of the incoming ions, measured in degrees from the surface normal')

    def createRow(self):
        return BeamCompRow()

    def addRow(self):
        row = super().addRow()
        row.kinEnergy.setEnabled(self.kinEnergyEditable)
        row.angle.setEnabled(self.angleEditable)
        row.abundance.editingFinished.connect(self.updateAbundances)
        self.updateAbundances()
        return row

    def addRows(self, beamCompEntries):
        for e in beamCompEntries:
            row = self.addRow()
            row.setRowData(e.element, e.abundance, e.kinEnergy, e.angle, e.maxConcentration,\
                           #e.atomicDensity, e.surfBindEnergy, e.displEnergy, e.inelLossModel)
                           e.atomicDensity, e.surfBindEnergy, e.displEnergy, int(e.inelLossModel))

    def removeCustomRow(self, rowIdx):
        super().removeCustomRow(rowIdx)
        self.updateAbundances()

    def updateAbundances(self):
        Utility.limitSum(self.rows, 1.0, Utility.FieldType.ABUNDANCE)

    def setKinEnergyEditable(self, editable):
        self.kinEnergyEditable = editable
        for r in self.rows:
            r.kinEnergy.setEnabled(editable)

    def setAngleEditable(self, editable):
        self.angleEditable = editable
        for r in self.rows:
            r.angle.setEnabled(editable)

    """"Dis-/Enables the certain input fields of each element in this table depending on whether the
    same element is also present in the target ('targetElements'). Also syncs values of the fields"""
    def updateSyncedFields(self, targetElements):
        symbols = [entry.element.symbol for entry in targetElements if entry.element is not None]
        for r in self.rows:
            if r.element is None:
                continue
            enabled = r.element.symbol not in symbols

            # Skip entries which won't change their enabled state
            if r.inelLossModel.isEnabled() == enabled:
                continue

            r.maxConcentration.setEnabled(enabled)
            r.atomicDensity.setEnabled(enabled)
            r.surfBindEnergy.setEnabled(enabled)
            r.displEnergy.setEnabled(enabled)
            r.inelLossModel.setEnabled(enabled)

            elementIndex = 0  # zero-indices will be corrected when all indices are updated
            modelIdx, maxConcentration = 2, 1.0
            atomicDensity = r.element.atomic_density
            surfBindEnergy = r.element.surface_binding_energy
            displEnergy = r.element.displacement_energy
            if not enabled:
                targetEntry = targetElements[symbols.index(r.element.symbol)]

                # For both entries, set the element index to the lower one of the two
                newElIdx = min(targetEntry.elementIndex.value(), r.elementIndex.value())
                elementIndex = newElIdx
                targetEntry.elementIndex.setValue(newElIdx)

                modelIdx = targetEntry.inelLossModel.currentIndex()
                maxConcentration = targetEntry.maxConcentration.value()
                surfBindEnergy = targetEntry.surfBindEnergy.value()
                displEnergy = targetEntry.displEnergy.value()
                atomicDensity = targetEntry.atomicDensity.value()
            r.elementIndex.setValue(elementIndex)
            r.inelLossModel.setCurrentIndex(modelIdx)
            r.maxConcentration.setValue(maxConcentration)
            r.surfBindEnergy.setValue(surfBindEnergy)
            r.displEnergy.setValue(displEnergy)
            r.atomicDensity.setValue(atomicDensity)

    """Sets a value given by the 'valueID' of the element with name 'name' to the given 'newValue'"""
    def updateSyncedValue(self, elementSymbol, valueID, newValue):
        assert isinstance(valueID, CompTable.SyncedValue)
        for r in self.rows:
            if r.element is None or r.element.symbol != elementSymbol:
                continue
            if valueID == CompTable.SyncedValue.INELMODEL:
                r.inelLossModel.setCurrentIndex(int(newValue))
            if valueID == CompTable.SyncedValue.CONCENTRATION:
                r.maxConcentration.setValue(newValue)
            if valueID == CompTable.SyncedValue.SURFBINDENERGY:
                r.surfBindEnergy.setValue(newValue)
            if valueID == CompTable.SyncedValue.DISPLENERGY:
                r.displEnergy.setValue(newValue)
            if valueID == CompTable.SyncedValue.ATOMICDENSITY:
                r.atomicDensity.setValue(newValue)
            return