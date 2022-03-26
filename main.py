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



# v. 1.0 (Apr 22): version described in the original publication


import sys
from MainWindow import MainWindow
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import QPixmap
import resources

gui_version = '1.0'

if __name__ == '__main__':
    def run_app():
        app = QApplication(sys.argv)

        pixmap = QPixmap(':/icons/splash.png')
        splash = QSplashScreen(pixmap)
        splash.show()
        app.processEvents()

        mainWin = MainWindow(gui_version)
        mainWin.show()
        splash.finish(mainWin)
        app.exec_()
    run_app()