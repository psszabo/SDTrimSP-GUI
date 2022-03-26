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


from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import pyqtSignal, QRegExp
from PyQt5.QtWidgets import QLineEdit, QSpinBox, QDoubleSpinBox
from TableWidgets.CustomTable import CustomTable, CustomRow
import Utility

class TargetLayerEntry():
    # Stores the information to be written to the layers.inp file.
    # Thus, only the segment thickness is needed
    def __init__(self, segmentCount, segmentThickness, abundances, layerName):
        self.segmentCount = segmentCount
        self.segmentThickness = segmentThickness
        self.abundances = abundances
        self.layerName = layerName

class TargetLayersRow(CustomRow):
    def __init__(self, elements):
        self.nameValidator = QRegExpValidator(QRegExp('[a-zA-Z1-9]+'))
        self.elementCells = []
        self.segmentThickness = 0
        super().__init__()

        # Add a cell for each element already added previously
        for e in elements:
            self.addElementCell()

    def createWidgets(self):
        super().createWidgets()
        self.segmentCount = QSpinBox()
        self.layerThickness = QDoubleSpinBox()
        self.layerName = QLineEdit()
        self.rowWidgets.extend([self.segmentCount, self.layerThickness, self.layerName])

    def initWidgets(self):
        super().initWidgets()
        self.remove.setToolTip('Remove this layer from the target')
        self.segmentCount.setRange(0, int(1e8))
        self.layerThickness.setEnabled(False)
        self.layerThickness.setRange(0, 1e8)
        self.layerThickness.setDecimals(2)
        self.layerName.setMaximumWidth(100)
        self.layerName.setValidator(self.nameValidator)
        self.segmentCount.valueChanged.connect(self.contentChanged.emit)
        self.layerName.textChanged.connect(self.contentChanged.emit)

    def selectRowInput(self):
        self.layerName.setFocus()

    def addElementCell(self):
        cell = QDoubleSpinBox()
        cell.setButtonSymbols(QSpinBox.NoButtons)
        cell.setRange(0, 1)
        cell.setDecimals(5)
        cell.setSingleStep(1e-5)
        self.rowWidgets.insert(-1, cell)
        self.elementCells.append(cell)
        cell.valueChanged.connect(self.contentChanged.emit)
        return cell

    def removeElementCell(self, cellIdx):
        del(self.rowWidgets[cellIdx+3])
        del(self.elementCells[cellIdx])

    def setRowData(self, segments, segmentThickness, abundances, layerName):
        self.segmentCount.setValue(segments)
        self.segmentThickness = segmentThickness
        self.layerThickness.setValue(segments*segmentThickness)
        for i in range(len(abundances)):
            ec = self.elementCells[i]
            ec.setValue(abundances[i])
        self.layerName.setText(layerName)

    def getRowData(self):
        return TargetLayerEntry(self.segmentCount.value(), self.segmentThickness,
                                [ec.value() for ec in self.elementCells], self.layerName.text())

class TargetLayersTable(CustomTable):
    layersChanged = pyqtSignal(list, list)
    def __init__(self, parent, targetThickness, targetSegmentsCount):
        self.elements = []
        self.segmentThickness = targetThickness/targetSegmentsCount
        self.targetSegmentsCount = targetSegmentsCount
        labels = ['Segments', 'Layer thickness [Å]', 'Name']
        super().__init__(0, labels, parent)
        self.addButton.setToolTip('Add a new layer to the target')
        self.horizontalHeaderItem(1).setToolTip('The amount of discrete segments a layer is made of.'+\
                                                '\nThe segments of all layer sum up to the maximum amount')
        self.horizontalHeaderItem(2).setToolTip('The thickness of this layer, calculated from the total target thickness and the respective layer segment count')
        self.horizontalHeaderItem(3).setToolTip('The name of the layer which is used in <i>layer.inp</i> '+\
                                                'if multiple layers are defined')

    def createRow(self):
        row = TargetLayersRow(self.elements)
        row.segmentThickness = self.segmentThickness
        row.segmentCount.setMaximum(self.targetSegmentsCount)
        return row

    def addRow(self):
        row = super().addRow()
        row.layerName.setText(f'Layer{len(self.rows)}')
        row.contentChanged.connect(self.updateLayers)
        self.updateLayers(row)
        return row

    def addRows(self, targetLayerEntries):
        # Add the blank rows first and then fill in their data to fill up everything correctly
        for e in targetLayerEntries:
            self.addRow()
        for i,e in enumerate(targetLayerEntries):
            self.rows[i].setRowData(e.segmentCount, e.segmentThickness, e.abundances, e.layerName)
        self.updateLayers()

    def removeCustomRow(self, rowIdx):
        super().removeCustomRow(rowIdx)
        self.updateLayers()

    def addElementColumn(self):
        self.insertColumn(len(self.headerLabels)-1)
        for i, row in enumerate(self.rows):
            row.addElementCell()
            self.updateCellWidgets(i)
        self.elements.append('??')

        self.headerLabels.insert(-1, '?? abundance')
        self.setHorizontalHeaderLabels(self.headerLabels)
        self.horizontalHeaderItem(len(self.headerLabels)-2).setToolTip('How much this element contributes to the composition of each layer.'+\
                                                                       '\nThe abundances of all elements in a layer sum up to 1')
        self.updateLayers()

    def renameElementColumn(self, elementIdx, newName):
        if len(self.elements) > elementIdx:
            self.headerLabels[elementIdx+3] = f'{newName} abundance'
            self.elements[elementIdx] = newName
        self.setHorizontalHeaderLabels(self.headerLabels)
        self.updateLayers()

    def removeElementColumn(self, elementIdx):
        columnIdx = elementIdx+3
        self.removeColumn(columnIdx)
        del(self.headerLabels[columnIdx])
        for i, row in enumerate(self.rows):
            row.removeElementCell(elementIdx)
        del(self.elements[elementIdx])
        self.setHorizontalHeaderLabels(self.headerLabels)
        self.updateLayers()

    def updateLayers(self, row=None):
        # Limit the total amount of segments
        Utility.limitSum(self.rows, self.targetSegmentsCount, Utility.FieldType.SEGMENTS)

        # Update the abundance input fields of all target layers or optionally just the given layer (=row)
        rows = self.rows if row is None else [row]
        for i, r in enumerate(rows):
            r.layerThickness.setValue(r.segmentCount.value() * self.segmentThickness)
            Utility.limitSum(r.rowWidgets[3:-1], 1.0, Utility.FieldType.OBJECT)
            Utility.setWidgetHighlight(r.segmentCount, r.segmentCount.value() == 0)

        # Highlight all abundance cells of an element if its abundance is zero in all of them
        elementIndices = []
        for i in range(len(self.elements)):
            for j,r in enumerate(self.rows):
                if r.elementCells[i].value() > 0:
                    break
                elif j == len(self.rows)-1:
                    # If we reach the last row, the whole column is zeros
                    elementIndices.append(i)
        for r in self.rows:
            for i,cell in enumerate(r.elementCells):
                Utility.setWidgetHighlight(cell, i in elementIndices)

        self.layersChanged.emit(self.elements, self.getData())

    def setTargetSegmentsCount(self, targetSegmentsCount):
        self.targetSegmentsCount = targetSegmentsCount
        for r in self.rows:
            r.segmentCount.setMaximum(self.targetSegmentsCount)
        self.resizeColumnsToContents()
        # Limit the total amount of segments
        Utility.limitSum(self.rows, self.targetSegmentsCount, Utility.FieldType.SEGMENTS)

    def setSegmentThickness(self, segmentThickness):
        self.segmentThickness = segmentThickness
        for i, row in enumerate(self.rows):
            row.segmentThickness = segmentThickness
            row.layerThickness.setValue(row.segmentCount.value() * segmentThickness)
        self.resizeColumnsToContents()