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


import string
from PyQt5.QtCore import pyqtSignal, Qt, QSize, QEvent
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QTableWidget, QListWidget,\
    QAbstractItemView, QHBoxLayout, QVBoxLayout, QListWidgetItem
from ElementData import Element
from Styles import Styles

class HoverLabel(QLabel):
    mouseEnter = pyqtSignal(Element)
    mouseLeave = pyqtSignal()

    def enterEvent(self, e):
        self.mouseEnter.emit(self.element)

    def leaveEvent(self, e):
        self.mouseLeave.emit()

class ElementWidget(HoverLabel):
    mouseRelease = pyqtSignal(Element)
    widgetSize = 35

    sColor = 'rgba(0, 0, 255, 75)'
    pColor = 'rgba(0, 255, 0, 75)'
    dColor = 'rgba(255, 255, 0, 75)'
    fColor = 'rgba(255, 0, 0, 75)'

    def __init__(self, parent, element, elementData):
        super().__init__(parent)
        self.element = element
        self.setText(self.element.periodicTableSymbol)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(int(ElementWidget.widgetSize), int(ElementWidget.widgetSize))

        # Color the element according to its position in the periodic table
        self.setAutoFillBackground(True)
        self.color = ElementWidget.sColor
        if self.element.period > 7 or (self.element.period in [6,7] and self.element.group == 3):
            self.color = ElementWidget.fColor
        elif self.element.period > 1 and self.element.group > 12:
            self.color = ElementWidget.pColor
        elif self.element.period > 3 and self.element.group in range(3, 13):
            self.color = ElementWidget.dColor
        self.styleSheet = 'background-color: '+self.color+';'

        # Underline the element's symbol if it has multiple isotopes to choose from
        isotopes = elementData.getIsotopes(element.atomic_nr)
        if len(isotopes) > 1:
            self.styleSheet += 'text-decoration: underline;'

        self.setStyleSheet(self.styleSheet)

    def mouseReleaseEvent(self, e):
        self.mouseRelease.emit(self.element)

    def setElementSelected(self, selected):
        if selected:
            self.defaultStyle = self.styleSheet
            self.setStyleSheet(self.styleSheet+'border: 2px inset grey;')
        else:
            self.setStyleSheet(self.defaultStyle)

class IsotopeWidget(HoverLabel):
    isotopeChosen = pyqtSignal(Element)

    def __init__(self, parent, element):
        super().__init__(parent)
        self.element = element
        self.setFixedHeight(30)
        self.setMaximumWidth(parent.width())
        self.setText(f'{self.element.symbol} ({self.element.name})')

    def mouseDoubleClickEvent(self, event):
        self.isotopeChosen.emit(self.element)

class PeriodicTableDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.elementData = None
        self.disallowedElements = []
        self.lastSelectedWidget = None

        ElementWidget.widgetSize = parent.width()*0.035

        self.rowCount = 9
        self.columnCount = 18
        self.isotopeListWidth = 250

        # Set up window properties
        self.setFocusPolicy(Qt.ClickFocus)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowTitle('Select an element')
        self.initUI()

    def showEvent(self, e):
        x = self.parent().x() + self.parent().width()/2 - self.width()/2
        y = self.parent().y() + self.parent().height()/2 - self.height()/2
        self.move(int(x), int(y))
        self.searchText = ''
        self.searchResults = []
        self.searchLabel.clear()
        self.setFocus()

        if len(self.elementWidgets) > 0:
            self.updateAllowedElements()

        self.isotopeList.clear()
        if self.lastSelectedWidget != None:
            self.lastSelectedWidget.setElementSelected(False)

    def initUI(self):
        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(10)
        self.gridLayout.setContentsMargins(10, 10, 10, 10)

        self.setLayout(self.gridLayout)

        hl = QHBoxLayout()
        self.elementInfo = QLabel(self)
        hl.addWidget(self.elementInfo)
        hl.addStretch(1)
        hl.addWidget(QLabel('[ESC]: Cancel', self))
        self.gridLayout.addLayout(hl, 0, 0)

        self.elementWidgets = []

        hl = QHBoxLayout()
        # Create an empty periodic table
        self.table = QTableWidget(self.rowCount, self.columnCount, self)
        for r in range(self.rowCount):
            for c in range(self.columnCount):
                if r == 0 and c == 3:
                    self.searchLabel = QLabel(self)
                    self.searchLabel.setStyleSheet('font-size: 50px; font-style: italic')
                    self.table.setCellWidget(r, c, self.searchLabel)
                    self.table.setSpan(r, c, 3, 9)
                else:
                    self.table.setCellWidget(r, c, QLabel())

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.horizontalHeader().setMinimumSectionSize(int(ElementWidget.widgetSize))
        self.table.verticalHeader().setMinimumSectionSize(int(ElementWidget.widgetSize))
        self.table.setShowGrid(False)
        self.table.installEventFilter(self)
        hl.addWidget(self.table)

        vl = QVBoxLayout()
        vl.setSpacing(0)
        titleHl = QHBoxLayout()
        title = QLabel('Isotope list', self)
        title.setStyleSheet(Styles.subTitleStyle)
        title.setMaximumHeight(20)
        self.isotopeTitleHeight = title.height()
        titleHl.addWidget(title)
        vl.addLayout(titleHl)
        self.isotopeList = QListWidget(self)
        self.isotopeList.setMaximumWidth(self.isotopeListWidth)
        self.isotopeList.setSelectionMode(QAbstractItemView.SingleSelection)
        self.isotopeList.installEventFilter(self)
        vl.addWidget(self.isotopeList)
        hl.addLayout(vl)

        self.gridLayout.addLayout(hl, 1, 0)

        hl = QHBoxLayout()
        self.hintLabel = QLabel('The SDTrimSP folder path has not yet been set. No element data available.', self)
        self.hintLabel.setWordWrap(True)
        hl.addWidget(self.hintLabel)
        self.isotopeHintLabel = QLabel(self)
        self.isotopeHintLabel.setWordWrap(True)
        self.isotopeHintLabel.setMaximumWidth(self.isotopeListWidth)
        self.isotopeHintLabel.setAlignment(Qt.AlignRight)
        hl.addWidget(self.isotopeHintLabel)
        self.gridLayout.addLayout(hl, 2, 0)


    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        if e.isAutoRepeat() or self.elementData is None:
            return

        c = str.lower(e.text())
        if c in string.ascii_lowercase:
            if len(self.searchText) < 7:
                self.searchText += c
        elif e.key() == Qt.Key_Backspace:
            self.searchText = self.searchText[:-1]
        elif e.key() == Qt.Key_Return and self.isSearching():
            for w in self.elementWidgets:
                if not w.isEnabled():
                    continue
                if w.element.symbol in self.searchResults:
                    self.setChosenElement(w)
                    break
        self.updateSearch()

    def updateSearch(self):
        self.searchLabel.setText(self.searchText)
        if self.isSearching():
            self.searchResults = self.elementData.elementsMatching(self.searchText)
        self.updateAllowedElements()

    def eventFilter(self, obj, event):
        res = super().eventFilter(obj, event)
        if obj == self.isotopeList:
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Return:
                    selectedItems = self.isotopeList.selectedItems()
                    if len(selectedItems) > 0:
                        item = selectedItems[0]
                        widget = self.isotopeList.itemWidget(item)
                        self.dialogFinished(widget.element)
            elif event.type() == QEvent.FocusOut:
                self.setChosenElement(None)
                self.searchText = ''
                self.updateSearch()
        elif obj == self.table and event.type() == QEvent.KeyPress:
            self.keyPressEvent(event)
        return res

    def setElementData(self, elementData):
        if self.elementData is not None:
            return
        self.elementData = elementData

        fBlockCounter = 1
        for atomic_nr in range(1, 104):
            el = self.elementData.elementFromNr(atomic_nr)

            row = el.period-1
            if el.group is not None:
                column = el.group - 1
            else:
                if row == 6 and fBlockCounter == 15:
                    fBlockCounter = 1
                row += 2
                column = fBlockCounter + 2
                fBlockCounter += 1

            w = ElementWidget(self, el, self.elementData)
            self.table.setCellWidget(row, column, w)
            self.elementWidgets.append(w)

        self.hintLabel.setText('Click an element to select it.'+\
               'Type to search elements and press [Return] to select the first search result.'+\
               'Elements with multiple isotopes are underlined.')
        self.isotopeHintLabel.setText('Double click or press [Return] to choose an isotope from the list.')

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        width = self.table.horizontalHeader().length() + 2 # to fit content exactly
        height = self.table.verticalHeader().length() + 2
        self.table.setFixedSize(width, height)
        self.isotopeList.setMaximumHeight(height-self.isotopeTitleHeight)

        # table width + isotope list width + 2*10 (content margin) + 1*10 (spacing)
        width = self.table.width() + self.isotopeListWidth + 30
        # table height + 2*(label height) + 2*10 (content margin) + 3*10 (spacing)
        height = self.table.height() + self.hintLabel.height() + self.elementInfo.height() + 50
        self.setFixedSize(width, height)

        for widget in self.elementWidgets:
            widget.mouseEnter.connect(lambda element: self.elementInfo.setText(element.getInfoString()))
            widget.mouseLeave.connect(lambda: self.elementInfo.clear())
            widget.mouseRelease.connect(lambda _,w=widget: self.setChosenElement(w))

    def setChosenElement(self, elementWidget):
        self.isotopeList.clear()
        if self.lastSelectedWidget != None:
            self.lastSelectedWidget.setElementSelected(False)
        if elementWidget is None:
            return

        elementWidget.setElementSelected(True)
        self.lastSelectedWidget = elementWidget

        element = elementWidget.element
        isotopes = self.elementData.getIsotopes(element.atomic_nr)

        if len(isotopes) == 1:
            self.dialogFinished(element)
            return

        for element in isotopes:
            item = QListWidgetItem()
            self.isotopeList.addItem(item)
            widget = IsotopeWidget(self.isotopeList, element)
            widget.isotopeChosen.connect(self.dialogFinished)
            widget.mouseEnter.connect(lambda element: self.elementInfo.setText(element.getInfoString()))
            widget.mouseLeave.connect(lambda: self.elementInfo.clear())
            if element.symbol in self.disallowedElements:
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
                widget.setEnabled(False)
            else:
                item.setFlags(item.flags() | Qt.ItemIsSelectable)
                widget.setEnabled(True)
            item.setSizeHint(QSize(0, widget.height()))
            self.isotopeList.setItemWidget(item, widget)
        self.isotopeList.setFocus()
        self.isotopeList.setCurrentRow(0)

    def dialogFinished(self, element):
        self.isotope = element
        self.done(QDialog.Accepted)

    def updateAllowedElements(self):
        for w in self.elementWidgets:
            w.setEnabled(True)
            if self.isSearching() and w.element.symbol not in self.searchResults:
                w.setEnabled(False)
            # Disable used elements without multiple isotopes
            if len(self.elementData.getIsotopes(w.element.atomic_nr)) == 1 and \
                w.element.symbol in self.disallowedElements:
                w.setEnabled(False)

    def isSearching(self):
        return len(self.searchText) > 0

    def setDisallowedElements(self, elementSymbols):
        self.disallowedElements = elementSymbols
