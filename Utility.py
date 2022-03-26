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
from PyQt5.QtCore import QFileInfo
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, QCheckBox,\
    QComboBox, QLineEdit, QMessageBox, QFileDialog, QGraphicsDropShadowEffect, QVBoxLayout

class inputHLayout(QHBoxLayout):
    class InputType(Enum):
        SPINBOX = 1
        COMBOBOX = 2
        LINEEDIT = 3
        DOUBLESPINBOX = 4

    def __init__(self, parent, label, inputType, defaultValue, inputRange=(0,1e8), entries=[]):
        super().__init__()
        self.label = QLabel(label, parent)
        self.addWidget(self.label)
        assert isinstance(inputType, inputHLayout.InputType)
        if inputType in [inputHLayout.InputType.SPINBOX, inputHLayout.InputType.DOUBLESPINBOX]:
            if inputType == inputHLayout.InputType.SPINBOX:
                self.input = QSpinBox(parent)
                defaultValue = int(defaultValue)
                inputRange = (int(inputRange[0]),int(inputRange[1]))
            else:
                self.input = QDoubleSpinBox(parent)
            self.input.setButtonSymbols(QSpinBox.NoButtons)
            self.input.setMinimumSize(50, 20)
            self.input.setRange(inputRange[0], inputRange[1])
            self.input.setValue(defaultValue)
        elif inputType == inputHLayout.InputType.COMBOBOX:
            self.input = QComboBox(parent)
            self.input.addItems(entries)
            self.input.setCurrentIndex(defaultValue)
        elif inputType == inputHLayout.InputType.LINEEDIT:
            self.input = QLineEdit(parent)
            self.input.setPlaceholderText(str(defaultValue))
            self.input.setMaxLength(int(inputRange))
        self.addWidget(self.input)

class VBoxTitleLayout(QVBoxLayout):
    '''
    if addStretch is a bool: addStretch(1) after title if True, else do nothing
    if addStretch is an integer: addSpacing(addStretch) after title
    '''
    def __init__(self, parent, title, titleStyle, spacing, addStretch):
        super().__init__()
        self.setSpacing(spacing)
        self.hl = QHBoxLayout()
        self.title = QLabel(title, parent)
        self.title.setStyleSheet(titleStyle)
        self.hl.addWidget(self.title)
        if type(addStretch) == bool and addStretch:
            self.hl.addStretch(1)
        elif type(addStretch) == int:
            self.hl.addSpacing(addStretch)
        self.addLayout(self.hl)

# Field types
class FieldType(Enum):
    ABUNDANCE = 1
    SEGMENTS = 2
    OBJECT = 3

"""Limits the sum of the values held by the objects' fields (defined by the fieldType)
to the given maximum. The last object's field fills up to the maximum, if possible, and is also
disabled."""
def limitSum(objects, maximum, fieldType):
    if len(objects) == 0:
        return

    total = 0
    for o in objects[:-1]:
        field = getField(o, fieldType)
        field.setEnabled(True)
        newTotal = total + field.value()
        if newTotal > maximum:
            field.setValue(maximum - total)
            total = maximum
        else:
            total = newTotal

    field = getField(objects[-1], fieldType)
    field.setEnabled(False)
    field.setValue(maximum - total)

"""Returns a property of the object or the object itself, depending on the given fieldType"""
def getField(obj, fieldType):
    assert isinstance(fieldType, FieldType)
    if fieldType == FieldType.ABUNDANCE:
        return obj.abundance
    elif fieldType == FieldType.SEGMENTS:
        return obj.segmentCount
    elif fieldType == FieldType.OBJECT:
        return obj

def selectFileDialog(parentWidget, forSaving, instruction, startDir, fileFilter):
    if forSaving:
        fullFilePath, _ = QFileDialog.getSaveFileName(parentWidget, instruction, startDir, fileFilter)
    else:
        fullFilePath, _ = QFileDialog.getOpenFileName(parentWidget, instruction, startDir, fileFilter)

    fileName = QFileInfo(fullFilePath).baseName()
    if len(fileName) == 0:
        return None
    return fullFilePath

def showMessageBox(parent, icon, windowTitle, text, infoMessage='', detailedMessage='', standardButtons=QMessageBox.Ok, checkBoxText='', expandDetails=False):
    msgBox = QMessageBox(icon, windowTitle, text, standardButtons, parent)
    font = QFont()
    font.setBold(False)
    msgBox.setFont(font)
    msgBox.setInformativeText(infoMessage)
    msgBox.setDetailedText(detailedMessage)
    if len(checkBoxText) > 0:
        msgBox.setCheckBox(QCheckBox(checkBoxText, msgBox))
    if expandDetails: # Automatically expand the details
        for b in msgBox.buttons():
            if msgBox.buttonRole(b) == QMessageBox.ActionRole:
                b.click()
                break
    return msgBox, msgBox.exec()

def setWidgetHighlight(widget, enabled, color=QColor(255,0,0,255)):
    if not enabled:
        widget.setGraphicsEffect(None)
        return
    dse = QGraphicsDropShadowEffect()
    dse.setColor(color)
    dse.setOffset(0)
    dse.setBlurRadius(10)
    widget.setGraphicsEffect(dse)