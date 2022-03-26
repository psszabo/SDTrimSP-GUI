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


from PyQt5.QtCore import pyqtSignal, QSize, QObject
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QTableWidget, QSpinBox, QPushButton, QAbstractItemView,\
    QHeaderView, QHBoxLayout, QWidget
import resources

class CustomRow(QObject):
    contentChanged = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.createWidgets()
        self.initWidgets()

    def createWidgets(self):
        self.remove = QPushButton(QIcon(':/icons/delete.png'), '')
        # Center the remove button by surrounding it with two stretches inside a horizontal layout
        removeButtonParent = QWidget()
        hl = QHBoxLayout()
        hl.setSpacing(0)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addStretch(1)
        hl.addWidget(self.remove)
        hl.addStretch(1)
        removeButtonParent.setLayout(hl)
        self.rowWidgets = [removeButtonParent]

    def initWidgets(self):
        self.remove.setFixedSize(30, 30)
        for w in self.rowWidgets:
            try: w.setButtonSymbols(QSpinBox.NoButtons)
            except: pass

    def selectRowInput(self):
        raise NotImplementedError('Must override selectRowInput()')

    def containsData(self):
        return True

    def getRowData(self):
        raise NotImplementedError('Must override getRowData()')

class CustomTable(QTableWidget):
    contentChanged = pyqtSignal()
    def __init__(self, rowCount, headerLabels, parent):
        self.headerLabels = [''] + headerLabels
        super().__init__(rowCount, len(self.headerLabels), parent)
        self.rows = []

        self.setMinimumSize(QSize(50, 50))
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.verticalHeader().setVisible(False)
        self.setHorizontalHeaderLabels(self.headerLabels)
        for i in range(self.columnCount()):
            mode = QHeaderView.Fixed if i == 0 else QHeaderView.ResizeToContents
            self.horizontalHeader().setSectionResizeMode(i, mode)
        self.createAddButton()

    def createAddButton(self):
        self.insertRow(0)
        self.addButton = QPushButton(QIcon(':/icons/add.png'), '')
        self.addButton.setFixedSize(30, 30)
        self.setCellWidget(0, 0, self.addButton)
        self.setSpan(0, 0, 1, 10)
        self.addButton.clicked.connect(self.addRow)

    def createRow(self, rowIdx):
        raise NotImplementedError('Must override createRow()')

    def addRow(self):
        rowIdx = self.rowCount()-1 # add it before the '+'-button-row
        row = self.createRow()
        row.remove.clicked.connect(lambda: self.removeCustomRow(self.rows.index(row)))
        self.insertRow(rowIdx)
        self.rows.append(row)
        self.updateCellWidgets(rowIdx)
        self.resizeColumnsToContents()
        self.updateRemoveButtons()
        row.selectRowInput()
        self.contentChanged.emit()
        row.contentChanged.connect(self.contentChanged.emit)
        return row

    def removeCustomRow(self, rowIdx):
        self.removeRow(rowIdx)
        del(self.rows[rowIdx])
        self.updateRemoveButtons()
        self.contentChanged.emit()

    def updateRemoveButtons(self):
        for i, r in enumerate(self.rows):
            r.remove.setEnabled(True)
        if len(self.rows) == 1:
            self.rows[0].remove.setEnabled(False)

    def updateCellWidgets(self, rowIdx):
        for i, w in enumerate(self.rows[rowIdx].rowWidgets):
            self.setCellWidget(rowIdx, i, w)

    def getTableEntry(self):
        raise NotImplementedError('Must override getTableEntry()')

    """Returns a list of custom 'entry'-objects (depending on the table type)
    containing the table's rows' data, if the row contains data"""
    def getData(self):
        return [row.getRowData() for row in self.rows if row.containsData()]

    def resetTable(self):
        while len(self.rows) > 0:
            self.removeCustomRow(0)