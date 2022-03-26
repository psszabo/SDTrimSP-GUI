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


from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QLineEdit, QWidget,\
        QVBoxLayout, QHBoxLayout, QPushButton, QDialogButtonBox, QCheckBox, QProgressBar
from PyQt5.QtGui import QPixmap, QDesktopServices
from Utility import setWidgetHighlight
import re, resources

class AboutDialog(QDialog):
    def __init__(self, parent, gui_version):
        super().__init__(parent)

        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowTitle('About SDTrimSP GUI')
        self.initUI(gui_version)
        self.resize(parent.width() // 2, self.height())

    def initUI(self, gui_version):
        layout = QGridLayout()
        self.setLayout(layout)

        titleLabel = QLabel(f'SDTrimSP GUI v. {gui_version}', self)
        titleLabel.setStyleSheet('font-size: 16px; font-weight: bold;')
        titleLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(titleLabel, 0, 0, 1, 2)

        iapLogo = QLabel('', self)
        iapLogo.setPixmap(QPixmap(':/icons/aboutlogo_iap.png').scaled(280, 113, transformMode=Qt.SmoothTransformation))
        layout.addWidget(iapLogo, 1, 0)

        iapLabel = QLabel('David Weichselbaum <a href="mailto:weichselbaum@iap.tuwien.ac.at">weichselbaum@iap.tuwien.ac.at</a><br>'+\
                        'Paul S. Szabo <a href="mailto:szabo@iap.tuwien.ac.at">szabo@iap.tuwien.ac.at</a><br>'+ \
                        '(now at University of California, Berkeley, <a href="mailto:szabo@berkeley.edu">szabo@berkeley.edu</a>)<br>' + \
                        'Herbert Biber <a href="mailto:biber@iap.tuwien.ac.at">biber@iap.tuwien.ac.at</a><br>'+ \
                        'Christian Cupak <br>' + \
                        'Rihard A. Wilhelm <br>' + \
                        'Friedrich Aumayr <br><br>'
                          #'TITLE, AUTHORS et al (9999) <a href="https://www.duck.com">doi.org/1234/56789</a><br>'+\
                        'Licensed under the <a href="https://www.gnu.org/licenses/gpl-3.0.html">GPLv3</a> license<br><br>'+\
                        #'<a href="https://www.tuwien.at">tuwien.at</a>  '+\
                        '<a href="https://www.iap.tuwien.ac.at">https://www.iap.tuwien.ac.at</a><br>', self)
        iapLabel.setOpenExternalLinks(True)
        layout.addWidget(iapLabel, 1, 1)

        empty = QWidget(self)
        empty.setFixedHeight(75)
        layout.addWidget(empty, 2, 0, 2, 2)

        titleLabel = QLabel('SDTrimSP', self)
        titleLabel.setStyleSheet('font-size: 16px; font-weight: bold;')
        titleLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(titleLabel, 3, 0, 1, 2)

        ippLogo = QLabel('', self)
        ippLogo.setPixmap(QPixmap(':/icons/aboutlogo_ipp.png').scaled(280, 100, transformMode=Qt.SmoothTransformation))
        layout.addWidget(ippLogo, 4, 0)

        ippLabel = QLabel(#'Andreas Mutzke <a href="mailto:andreas.mutzke@ipp.mpg.de">andreas.mutzke@ipp.mpg.de</a><br><br>'+ \
                          'Andreas Mutzke <br><br>' + \
                          #'For questions regarding SDTrimSP,<br>send an email to <a href="mailto:sdtrimsp@ipp....">sdtrimsp@ipp....</a><br>'+\
                        '<a href="https://www.ipp.mpg.de">https://www.ipp.mpg.de/</a><br>', self)
        ippLabel.setOpenExternalLinks(True)
        layout.addWidget(ippLabel, 4, 1)

class MissingDocsDialog(QDialog):
    docsFileName = 'IPP_2019-02.pdf'
    def __init__(self, parent, SDTrimSPpath):
        super().__init__(parent)
        self.docsFolder = SDTrimSPpath + '/doc/'
        self.docsPath = self.docsFolder + MissingDocsDialog.docsFileName
        self.url = 'https://pure.mpg.de/pubman/item/item_3026474_4/component/file_3028154/IPP%202019-02.pdf'

        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint)
        self.setWindowTitle('Missing docs PDF')
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        text = f'The documentation PDF "{MissingDocsDialog.docsFileName}" could not be found at\n"{self.docsFolder}".'+\
               '\nYou can download it automatically'
        layout.addWidget(QLabel(text))

        hl = QHBoxLayout()
        self.downloadFile = QPushButton('Download PDF', self)
        self.downloadFile.setToolTip('Download the PDF to the SDTrimSP "/docs" folder')
        hl.addWidget(self.downloadFile)
        self.downloadProgress = QProgressBar(self)
        self.downloadProgress.setToolTip('The download progress')
        hl.addWidget(self.downloadProgress)
        self.downloadStatus = QLabel('', self)
        self.downloadStatus.setToolTip('The status of the download progress')
        hl.addWidget(self.downloadStatus)
        layout.addLayout(hl)

        text = 'Alternatively, you can manually download it from <a href="' + self.url +\
               '">pure.mpg.de</a>,<br> place it in the docs folder, and rename it to "' + MissingDocsDialog.docsFileName + '".'
        label = QLabel(text)
        label.setOpenExternalLinks(True)
        layout.addWidget(label)

        hl = QHBoxLayout()
        self.openFolder = QPushButton('Open folder', self)
        self.openFolder.setToolTip('Open the SDTrimSP "/docs" folder in the file explorer')
        hl.addWidget(self.openFolder)
        hl.addStretch(1)
        layout.addLayout(hl)

        hl = QHBoxLayout()
        hl.addStretch(1)
        self.closeDialog = QPushButton('Close', self)
        self.closeDialog.setToolTip('Close this dialog window')
        hl.addWidget(self.closeDialog)
        layout.addLayout(hl)

        self.openFolder.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(self.docsFolder)))
        self.downloadFile.clicked.connect(self.tryDownloadFile)
        self.closeDialog.clicked.connect(self.accept)

    def tryDownloadFile(self):
        try:
            import requests
            self.downloadProgress.setValue(25)
            r = requests.get(self.url, stream=True)
            self.downloadStatus.setText('Fetching file')
            self.downloadProgress.setValue(50)
            with open(self.docsPath, 'wb') as f:
                self.downloadStatus.setText('Writing PDF')
                self.downloadProgress.setValue(75)
                f.write(r.content)
                self.downloadStatus.setText('Done')
                self.downloadProgress.setValue(100)
        except:
            self.downloadStatus.setText('Error')
            self.downloadProgress.setValue(0)

class PreferencesDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.SDTrimSPpath = ''
        self.SDTrimSPbinaryPath = ''
        self.SDTrimSPversion = 'unknown'

        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint)
        self.setWindowTitle('SDTrimSP GUI Preferences')
        self.initUI()
        self.resize(parent.width() // 2, self.height())

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        hl, self.SDTrimSPpathLabel, self.setSDTrimSPfolder = \
                self.createPathSelector('SDTrimSP folder:', 'Select the main SDTrim folder',
                                'The path of the root SDTrimSP folder which contains all the SDTrimSP content')
        self.setSDTrimSPfolder.clicked.connect(lambda: self.parent().selectSDTrimSPfolder(False))
        layout.addLayout(hl)

        hl, self.SDTrimSPbinaryPathLabel, self.setSDTrimSPbinary = \
                self.createPathSelector('SDTrimSP binary:', 'Select the SDTrimSP binary',
                                'The path of the SDTrimSP executable which will be run')
        self.setSDTrimSPbinary.clicked.connect(lambda: self.parent().selectSDTrimSPbinary(False))
        layout.addLayout(hl)

        hl = QHBoxLayout()
        hl.addWidget(QLabel('SDTrimSP version:', self))
        self.SDTrimSPversionLabel = QLabel('<b></b>', self)
        self.SDTrimSPversionLabel.setToolTip('The used SDTrimSP version, extracted from "/src/SDTrimSP.F90", or alternatively the the binary name and path.'+\
                                            '\nIf all three attempts fail, the version is "unknown"')
        hl.addWidget(self.SDTrimSPversionLabel)
        hl.addStretch(1)
        layout.addLayout(hl)

        layout.addSpacing(20)
        self.skipDeleteInfoMsgBox = QCheckBox('Skip the file deletion warning when running a simulation', self)
        layout.addWidget(self.skipDeleteInfoMsgBox)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)
        layout.addWidget(buttonBox)

    def createPathSelector(self, title, placeholder, tooltip):
        hl = QHBoxLayout()
        hl.addWidget(QLabel(title, self))
        label = QLineEdit(self)
        label.setPlaceholderText(placeholder)
        label.setReadOnly(True)
        label.setMinimumWidth(300)
        label.setToolTip(tooltip)
        hl.addWidget(label)
        button = QPushButton('...', self)
        button.setMinimumSize(40, 10)
        button.setMaximumSize(40, 30)
        hl.addWidget(button)
        return hl, label, button

    def setSDTrimSPpath(self, path):
        self.SDTrimSPpath = path
        self.SDTrimSPpathLabel.setText(path)
        setWidgetHighlight(self.SDTrimSPpathLabel, len(path) == 0)

    def setSDTrimSPbinaryPath(self, path):
        self.SDTrimSPbinaryPath = path
        self.SDTrimSPbinaryPathLabel.setText(path)
        setWidgetHighlight(self.SDTrimSPbinaryPathLabel, len(path) == 0)

    def tryParseSDTrimSPversion(self):
        # Try to read the version number from the source code
        try:
            with open(self.SDTrimSPpath + '/src/SDTrimSP.F90', 'r') as f:
                for line in f:
                    if line.strip().startswith('avs0 ='):
                        result = [line.split("'")[1]] # save as array to we can ask its length
                        break
        except:
            # Try to parse it from either the SDTrimSP root folder or the binary name
            result = re.findall("\d+\.\d+", self.SDTrimSPpath + self.SDTrimSPbinaryPath)

        if len(result) > 0:
            self.SDTrimSPversion = result[0]
            style = 'b'
        else:
            self.SDTrimSPversion = 'unknown'
            style = 'i'
        self.SDTrimSPversionLabel.setText(f'<{style}>{self.SDTrimSPversion}</{style}>')