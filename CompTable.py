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


from enum import Enum
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QComboBox, QPushButton, QDoubleSpinBox, QSpinBox
from TableWidgets.CustomTable import CustomTable, CustomRow
from ElementData import Element
from Utility import setWidgetHighlight

class CompEntry():
    def __init__(self, element, maxConcentration, atomicDensity, surfBindEnergy, displEnergy, inelLossModel):
        self.element = element
        self.maxConcentration = maxConcentration
        self.atomicDensity = atomicDensity
        self.surfBindEnergy = surfBindEnergy
        self.displEnergy = displEnergy
        self.inelLossModel = inelLossModel

class CompRow(CustomRow):
    elementChanged = pyqtSignal(Element)
    selectElementText = '...'
    inelLossModelLabels = ['1: Lindhard-Scharff', '2: Oen-Robinson', '3: average of (1) and (2) (default)',
                        '4: H,D,T (>25 keV)', '5: He3,He4 (>100 keV)', '6: Ziegler']
    inelLossModelTooltips = ['Necessary condition: E < 25 · Z^(4/3) · M (in keV) where E, Z, M are the energy, the atomic number and the atomic mass of the moving particle',
                             'Necessary condition:E < 25 · Z^(4/3) · M (in keV)',
                             'Equipartition of Lindhard-Scharff and Oen-Robinson',
                             'High energy hydrogen (H,D,T) (energy > 25 keV), values taken from "table3"',
                             'High energy helium (He3,He) (energy > 100 keV), values taken from "table4"',
                             'Values are calculated for each element based on values taken from "table6a" and "table6b"']

    def __init__(self):
        super().__init__()
        self.element = None

    def createWidgets(self):
        super().createWidgets()
        self.elementIndex = QSpinBox()
        self.selectElement = QPushButton(f'{CompRow.selectElementText}')
        self.maxConcentration = QDoubleSpinBox()
        self.atomicDensity = QDoubleSpinBox()
        self.surfBindEnergy = QDoubleSpinBox()
        self.displEnergy = QDoubleSpinBox()
        self.inelLossModel = QComboBox()
        self.rowWidgets.extend([self.elementIndex, self.selectElement, self.maxConcentration, self.atomicDensity,\
                                self.surfBindEnergy, self.displEnergy, self.inelLossModel])

        # The index where (i.e., before which) additional widgets of inheriting rows will be placed so that the shared properties are always last
        self.insertIdx = self.rowWidgets.index(self.maxConcentration)

    def initWidgets(self):
        super().initWidgets()
        self.remove.setToolTip('Remove this element from the composition')
        self.elementIndex.setEnabled(False)

        self.maxConcentration.setRange(0, 1)
        self.maxConcentration.setDecimals(4)
        self.maxConcentration.setValue(1)
        self.maxConcentration.valueChanged.connect(self.contentChanged.emit)

        self.atomicDensity.setRange(-1e3, 1e3)
        self.atomicDensity.setDecimals(5)
        self.atomicDensity.setMaximumWidth(100)
        self.atomicDensity.valueChanged.connect(lambda _: self.updateHighlight(CompTable.SyncedValue.ATOMICDENSITY))
        self.atomicDensity.valueChanged.connect(self.contentChanged.emit)

        self.surfBindEnergy.setRange(-1e3, 1e3)
        self.surfBindEnergy.setDecimals(5)
        self.surfBindEnergy.valueChanged.connect(lambda _: self.updateHighlight(CompTable.SyncedValue.SURFBINDENERGY))
        self.surfBindEnergy.valueChanged.connect(self.contentChanged.emit)

        self.displEnergy.setRange(-1e3, 1e3)
        self.displEnergy.setDecimals(5)
        self.displEnergy.valueChanged.connect(lambda _: self.updateHighlight(CompTable.SyncedValue.DISPLENERGY))
        self.displEnergy.valueChanged.connect(self.contentChanged.emit)

        self.inelLossModel.addItems(CompRow.inelLossModelLabels)
        self.inelLossModel.currentIndexChanged.connect(self.contentChanged.emit)
        for i in range(self.inelLossModel.count()):
            self.inelLossModel.setItemData(i, CompRow.inelLossModelTooltips[i], Qt.ToolTipRole)
        self.inelLossModel.setCurrentIndex(2)

    def selectRowInput(self):
        self.selectElement.setFocus()

    def setElement(self, element):
        self.element = element
        self.selectElement.setText(element.symbol)
        # Only set the element's density if it's not defined by the global density
        if self.atomicDensity.isEnabled():
            self.atomicDensity.setValue(self.element.atomic_density)
        self.surfBindEnergy.setValue(element.surface_binding_energy)
        self.displEnergy.setValue(element.displacement_energy)

        self.elementChanged.emit(element)
        self.contentChanged.emit()

    def containsData(self):
        return self.element is not None

    def getRowData(self):
        return CompEntry(self.element, self.maxConcentration.value(), self.atomicDensity.value(),
                           self.surfBindEnergy.value(), self.displEnergy.value(), self.inelLossModel.currentIndex())

    def setRowData(self, element, maxConcentration, atomicDensity, surfBindEnergy, displEnergy, inelLossModel):
        self.setElement(element)
        self.maxConcentration.setValue(maxConcentration)
        self.atomicDensity.setValue(atomicDensity)
        self.surfBindEnergy.setValue(surfBindEnergy)
        self.displEnergy.setValue(displEnergy)
        self.inelLossModel.setCurrentIndex(inelLossModel)

    def updateHighlight(self, syncedValue):
        if self.element is None:
            return
        if syncedValue == CompTable.SyncedValue.ATOMICDENSITY:
            defaultValue = self.element.atomic_density
            spinBox = self.atomicDensity
        elif syncedValue == CompTable.SyncedValue.SURFBINDENERGY:
            defaultValue = self.element.surface_binding_energy
            spinBox = self.surfBindEnergy
        elif syncedValue == CompTable.SyncedValue.DISPLENERGY:
            defaultValue = self.element.displacement_energy
            spinBox = self.displEnergy

        if spinBox.value() < 0:
            spinBox.setValue(defaultValue)
        isHighlit = False
        # Highlight if it's enabled and it differs from the default value
        if spinBox.isEnabled():
            isHighlit = spinBox.value() != defaultValue
        setWidgetHighlight(spinBox, isHighlit)

class CompTable(CustomTable):
    rowRemoved = pyqtSignal(int)
    rowAdded = pyqtSignal(CustomRow)
    elementChanged = pyqtSignal(CompRow, Element)
    elementClicked = pyqtSignal(CompRow)

    class SyncedValue(Enum):
        INELMODEL = 1
        CONCENTRATION = 2
        SURFBINDENERGY = 3
        ATOMICDENSITY = 4
        DISPLENERGY = 5

    def __init__(self, otherLabels, parent):
        self.concentrationEditable = False
        syncHint = '\nIf the element occurs in both the beam and the target, the value is defined in the target table.'
        modifyHint = '\nA red highlight indicates a modified value. A negative number resets it back to the default one.'
        labels = ['#', 'Element', 'Max conc.', 'Dens. [1/Å^3]', 'Surf. bind. energy [eV]', 'Displ. energy [eV]', 'Inelastic loss model']
        insertIdx = labels.index('Max conc.') # Before which column the subclasses' columns will be inserted
        labels[insertIdx:insertIdx] = otherLabels
        super().__init__(0, labels, parent)
        self.addButton.setToolTip('Add a new element to the composition')
        self.horizontalHeaderItem(labels.index('#')+1).setToolTip('The index of the element as it occurs in the input file')

        self.horizontalHeaderItem(len(self.headerLabels)-5).setToolTip('<i>qumax</i><br>The maximum allowed concentration of each element in the target'+\
                                                                        ' (only dynamic calculations).'+syncHint)
        self.horizontalHeaderItem(len(self.headerLabels)-4).setToolTip('<i>dns0</i><br>The atomic density (in [1/Å³]) of the element, fetched from table1.'+\
                                                        modifyHint+'\nModifying is disabled if a global density is defined.'+syncHint)
        self.horizontalHeaderItem(len(self.headerLabels)-3).setToolTip('<i>e_surfb</i><br>The surface binding energy (in eV) of this element, fetched from table1'+\
                                                                       modifyHint+syncHint)
        self.horizontalHeaderItem(len(self.headerLabels)-2).setToolTip('<i>e_displ</i><br>The displacement energy (in eV) of this element, fetched from table1' + \
                                                                            modifyHint + syncHint)
        self.horizontalHeaderItem(len(self.headerLabels)-1).setToolTip('<i>inel0</i><br>The inelastic loss model used for calculations'+syncHint)

    def createRow(self):
        return CompRow()

    def addRow(self):
        row = super().addRow()
        row.selectElement.clicked.connect(lambda checked: self.elementClicked.emit(row))
        row.elementChanged.connect(lambda el: self.elementChanged.emit(row, el))
        row.maxConcentration.setEnabled(self.concentrationEditable)
        self.rowAdded.emit(row)
        return row

    def addRows(self, compEntries):
        for e in compEntries:
            row = self.addRow()
            row.setRowData(e.element, e.maxConcentration, e.atomicDensity, e.surfBindEnergy, e.displEnergy, e.inelLossModel)

    def removeCustomRow(self, rowIdx):
        super().removeCustomRow(rowIdx)
        self.rowRemoved.emit(rowIdx)

    def setConcentrationEditable(self, editable):
        self.concentrationEditable = editable
        for r in self.rows:
            if r.inelLossModel.isEnabled(): # Only if the row is not synced
                r.maxConcentration.setEnabled(editable)