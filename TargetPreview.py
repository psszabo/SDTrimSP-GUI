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


from PyQt5.QtCore import QSize, QRect, Qt
from PyQt5.QtGui import QPen, QPalette, QPainter, QColor
from PyQt5.QtWidgets import QWidget

class TargetPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.antialised = True
        self.setBackgroundRole(QPalette.Base)
        self.setAutoFillBackground(True)
        self.pen = QPen(QColor(0, 0, 0))

        self.layers, self.elements = [], []
        self.totalSegments = 0
        self.elementCount = 0

        self.legendSize = 15
        self.legendLabelWidth = 20

    def minimumSizeHint(self):
        return QSize(150, 100)

    def setTargetInfo(self, elements, layers):
        self.elements = elements
        self.elementCount = len(elements)
        self.layers = []
        self.totalSegments = 0
        for row in layers:
            self.layers.append([row.segmentCount, row.layerName, row.abundances])
            self.totalSegments += row.segmentCount
        self.update()

    def resizeEvent(self, event):
        self.targetHeight = self.height()*0.75
        self.targetWidth = self.width()*0.8
        self.yMargin = self.height()*0.2
        self.xMargin = (self.width()-self.targetWidth)/2
        self.legendY = self.yMargin*0.2

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(self.pen)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Draw elements legend
        if self.elementCount > 0:
            legendEntryWidth = self.targetWidth/self.elementCount
            for i in range(self.elementCount):
                rect = QRect(int(self.xMargin + i*legendEntryWidth), int(self.legendY), int(self.legendSize), int(self.legendSize))
                painter.fillRect(rect, QColor.fromHsv(int(i*359/self.elementCount), 255, 255, 127))
                rect.translate(self.legendSize, 0)
                rect.setSize(QSize(self.legendLabelWidth, self.legendSize))
                painter.drawText(rect, Qt.AlignCenter, f'{self.elements[i]}')

        # Draw the target layers
        lastLayerY = self.yMargin
        for i,l in enumerate(self.layers):
            layerHeight = self.targetHeight * l[0]/self.totalSegments
            rect = QRect(int(self.xMargin), int(lastLayerY), int(self.targetWidth), int(layerHeight))
            painter.drawRect(rect)

            # Color the layer depending on composition
            lastX = self.xMargin
            for j in range(self.elementCount):
                w = self.targetWidth*l[2][j]
                rect2 = QRect(int(lastX), int(lastLayerY), int(w), int(layerHeight))
                painter.fillRect(rect2, QColor.fromHsv(int(j*359/self.elementCount), 255, 255, 127))
                lastX += w

            painter.drawText(rect, Qt.AlignCenter, f'{l[1]}')
            lastLayerY += layerHeight

        painter.drawRect(QRect(0, 0, int(self.width()-1), int(self.height()-1)))