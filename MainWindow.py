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


import os.path, subprocess, platform
from os import chdir
from enum import Enum
from PyQt5.QtCore import QCoreApplication, QSettings, QTimer, QDir, QProcess,\
    QFileInfo, QIODevice, QFile, QUrl, QCommandLineParser, QDateTime
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QCheckBox,\
    QFileDialog, QComboBox, QAbstractSpinBox, QListWidgetItem
from PyQt5.QtGui import QDesktopServices, QColor, QFont
from TableWidgets.CompTable import CompEntry
from TableWidgets.CompTable import CompTable
from TableWidgets.BeamCompTable import BeamCompEntry
from TableWidgets.TargetLayersTable import TargetLayerEntry
from SDTrimSettings import InputSettings, loadInputFile, loadLayersFile
from Utility import showMessageBox, selectFileDialog
from PeriodicTable import PeriodicTableDialog
from Dialogs import PreferencesDialog, MissingDocsDialog
from ElementData import SDTrimElementData
from ui_main import Ui_Main
from Styles import Styles
from DNS0_Sauerstoff import Target_Material
from SDTrimSP_Evaluation import SDTrimSP_Evaluation
import numpy as np

class MainWindow(QMainWindow, Ui_Main):

    def __init__(self, gui_version):
        super(MainWindow, self).__init__()
        QCoreApplication.setOrganizationName('TUWien')
        QCoreApplication.setOrganizationDomain('www.tuwien.at')
        QCoreApplication.setApplicationName('SDTrimSPgui')

        # set gui version
        self.gui_version = gui_version

        # ui_main.py: create the UI
        self.setupUi()

        # Store the input fields and their default values
        self.defSpinBoxes = self.findChildren(QAbstractSpinBox)
        self.defSpinBoxes.remove(self.outputFilePreviewLines)
        self.defSpinBoxes.remove(self.historyStep)
        self.defSpinBoxValues = [sb.value() for sb in self.defSpinBoxes]
        self.defComboBoxes = self.findChildren(QComboBox)
        self.defComboBoxValues = [cb.currentIndex() for cb in self.defComboBoxes]
        self.defCheckBoxes = self.findChildren(QCheckBox)
        self.defCheckBoxValues = [cb.isChecked() for cb in self.defCheckBoxes]

        # ui_main.py: setup window
        self.setupSignals()
        self.setupWindowGeometry()

        # The process for running SDTrimSP
        self.process = QProcess(self)
        self.process.started.connect(self.processStarted)
        self.process.readyRead.connect(self.processReadyRead)
        self.process.errorOccurred.connect(self.processError)
        self.process.finished.connect(self.processFinished)
        # The object which will hold the SDTrimSP element data
        self.elementData = SDTrimElementData()
        # The (empty) periodic table dialog window
        self.periodicTableDialog = PeriodicTableDialog(self)
        self.periodicTableDialog.finished.connect(self.periodicTableDialogClosed)
        # The object for the output evaluation
        self.outputEval = SDTrimSP_Evaluation(self.outputPlotView, self.elementData, self.historyStep, self.historyStepSlider)

        # The tooltips for output files, which are imported from the SDTrimSP docs
        self.outputFileToolTips = {'meagb_p.dat': 'output of backscattered particles',
                      'meagb_s.dat': 'output of all backsputtered particles',
                      'meagt_p.dat': 'output of all transmitted scattered particles',
                      'meagt_s.dat': 'output of all transmitted sputtered particles'}

        # Set up the preferences dialog
        self.preferences = PreferencesDialog(self)
        settings = QSettings()
        self.preferences.setSDTrimSPpath(settings.value('SDTrimSPpath', ''))
        self.preferences.setSDTrimSPbinaryPath(settings.value('SDTrimSPbinaryPath', ''))
        self.preferences.skipDeleteInfoMsgBox.setChecked(settings.value('skipDeleteFilesInfo', False, type=bool))

        # Check whether the SDTrimSP paths are still valid, otherwise reset them
        if not os.path.exists(self.preferences.SDTrimSPpath):
            self.preferences.setSDTrimSPpath('')
        if not os.path.exists(self.preferences.SDTrimSPbinaryPath):
            self.preferences.setSDTrimSPbinaryPath('')

        self.preferences.tryParseSDTrimSPversion()

        # Reset the whole window and fill the tables with their first entry each
        self.resetSettings(True)

        # An input file can be passed as an argument
        # Either through the console or if a file is opened via right click->open with->.exe
        parser = QCommandLineParser()
        parser.parse(QCoreApplication.arguments())
        args = parser.positionalArguments()

        # Try to load the required SDTrimSP data from the SDTrimSP path
        success = self.tryLoadSDTrimSPData()

        # If a file name is given as argument, just try and load it. If the SDTrimSP path is not set up
        # the user will be asked to set it, and then the given files are loaded afterwards
        if len(args)>0:
            QTimer.singleShot(500, lambda: self.loadFiles(args[0]))
        # If no file was passed and loading the element data failed, the paths have to be set again
        elif not success:
            QTimer.singleShot(500, lambda: self.selectSDTrimSPfolder(True))

    def closeEvent(self, e):
        if self.process.state() != QProcess.NotRunning:
            showMessageBox(self, QMessageBox.Critical, 'Warning', 'Process still running',
                    'The SDTrimSP process is still running. \nIf you really want to quit, abort the process first.')
            e.ignore()
            return

        if self.isWindowModified() and not self.showUnsavedChangesWarning():
            e.ignore()
            return

        settings = QSettings()
        settings.setValue('mainWindowWidth', self.width())
        settings.setValue('mainWindowHeight', self.height())
        settings.setValue('SDTrimSPpath', self.preferences.SDTrimSPpath)
        settings.setValue('SDTrimSPbinaryPath', self.preferences.SDTrimSPbinaryPath)
        settings.setValue('skipDeleteFilesInfo', self.preferences.skipDeleteInfoMsgBox.isChecked())
        settings.sync()
        e.accept()

    def showUnsavedChangesWarning(self):
        _, res = showMessageBox(self, QMessageBox.Warning, 'Warning!', 'The document has been modified',
                                infoMessage='Do you want to save your changes?',
                                standardButtons=QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        # If the saving is aborted, also cancel the close event
        if res == QMessageBox.Cancel or (res == QMessageBox.Save and not self.saveFiles()):
            return False
        return True

    def resetSettings(self, createFirstRows):
        # Only warn about unsaved changes if the first rows are added, i.e. a blank window is created
        if createFirstRows and self.isWindowModified() and not self.showUnsavedChangesWarning():
            return

        self.workingDir = QDir.currentPath()
        self.setWindowTitle(f'{self.workingDir}/untitled[*] - SDTrimSP GUI v. {self.gui_version} (SDTrimSP v. {self.preferences.SDTrimSPversion})')

        self.beamComp.resetTable()
        self.targetComp.resetTable()
        self.targetLayers.resetTable()

        # Restore default values
        self.simulationTitle.setText(f'SDTrimSP - {QDateTime.currentDateTime().toString()}')
        for i,s in enumerate(self.defSpinBoxes):
            s.setValue(self.defSpinBoxValues[i])
        for i,c in enumerate(self.defComboBoxes):
            c.setCurrentIndex(self.defComboBoxValues[i])
        for i,c in enumerate(self.defCheckBoxes):
            c.setChecked(self.defCheckBoxValues[i])
        self.additionalSettings.clear()

        # Clear text outputs and lists
        self.SDTrimSPoutput.clear()
        self.outputFilesList.clear()
        self.outputFilePreview.clear()

        self.statusBar().clearMessage()
        self.runProgress.setValue(0)

        if len(self.preferences.SDTrimSPpath) > 0 and len(self.preferences.SDTrimSPbinaryPath) > 0:
            self.setRunStatus(MainWindow.RunStatus.READY)
        else:
            self.setRunStatus(MainWindow.RunStatus.MISSING_PATHS)
        self.openDocsAction.setEnabled(len(self.preferences.SDTrimSPpath) > 0)
        self.saveAsAction.setEnabled(False)

        if createFirstRows:
            self.beamComp.addRow()
            self.targetComp.addRow()
            self.targetLayers.addRow()

        self.setWindowModified(False)
        self.updateTabWidget()

    class RunStatus(Enum):
        READY = 1
        RUNNING = 2
        DONE = 3
        MISSING_PATHS = 4
        ABORTED = 5
        ERROR = 6

    def setRunStatus(self, status):
        assert isinstance(status, MainWindow.RunStatus)
        if status in [MainWindow.RunStatus.READY, MainWindow.RunStatus.RUNNING, MainWindow.RunStatus.DONE]:
            if status == MainWindow.RunStatus.READY:
                text = 'Ready!'
                tooltip = 'Everything is set up and ready for the simulation'
            elif status == MainWindow.RunStatus.RUNNING:
                text = 'Running...'
                tooltip = 'The simulation is currently running'
            elif status == MainWindow.RunStatus.DONE:
                text = 'Done!'
                tooltip = 'The simulation has successfully finished'
            pixmap = self.okayPixmap
            colorStyle = Styles.green
        elif status == MainWindow.RunStatus.MISSING_PATHS:
            text = 'Missing paths'
            pixmap = self.warningPixmap
            colorStyle = Styles.orange
            tooltip = 'One or more of the following paths are not set up:'+\
                '\n  - SDTrimSP root directory\n  - SDTrimSP binary'
        elif status == MainWindow.RunStatus.ABORTED:
            text = 'Aborted'
            pixmap = self.errorPixmap
            colorStyle = Styles.red
            tooltip = 'The process was aborted on purpose'
        elif status == MainWindow.RunStatus.ERROR:
            text = 'ERROR'
            pixmap = self.errorPixmap
            colorStyle = Styles.red
            tooltip = 'Something went wrong with the simulation\nCheck the "SDTrimSP log" tab for more info'

        self.runStatusText.setText(text)
        self.runStatusIcon.setPixmap(pixmap)
        self.runStatusText.setStyleSheet(Styles.statusTextStyle + colorStyle)
        self.runStatusText.setToolTip(tooltip)

    def getNextElementIndex(self):
        return max([r.elementIndex.value() for r in self.beamComp.rows + self.targetComp.rows])+1

    def setNewElementIndex(self, row):
        row.elementIndex.setValue(self.getNextElementIndex())
        self.updateElementOrder()

    def updateElementOrder(self):
        symbols = self.getOrderedElements()
        elementOrder = 'Element order: '
        if len(symbols) == 0:
            elementOrder += '<none defined>'
        else:
            for i,s in enumerate(symbols):
                elementOrder += f'{s}({i+1}), '
            elementOrder = elementOrder[:-2]
        self.elementOrder.setText(elementOrder)

    def getOrderedElements(self):
        rows = [r for r in (self.beamComp.rows + self.targetComp.rows) if r.element is not None]
        rows.sort(key=lambda r: r.elementIndex.value())
        symbols = [r.element.symbol for r in rows]
        symbols = list(dict.fromkeys(symbols)) # Remove duplicates
        return symbols

    def updateElementIndices(self):
        # If the synchronization of two entries has ended, a new index has to be found for the beam entry
        for r in self.beamComp.rows:
            if r.elementIndex.value() <= 0:
                r.elementIndex.setValue(self.getNextElementIndex())

        allRows = self.beamComp.rows + self.targetComp.rows

        # Gather a list of unique symbols and an empty entry for each undefined element
        symbols = []
        for r in allRows:
            if r.element is None:
                symbols.append('')
            elif r.element.symbol not in symbols:
                symbols.append(r.element.symbol)

        # Assure that all composition entry indices range from 1 to the maximum number
        curIdx = 1
        while curIdx <= len(symbols):
            foundNothing = True
            for r in allRows:
                if r.elementIndex.value() == curIdx:
                    curIdx += 1
                    foundNothing = False
                    break
            if foundNothing:
                for row in allRows:
                    v = row.elementIndex.value()
                    if v > curIdx:
                        row.elementIndex.setValue(v-1)
        self.updateElementOrder()

    def openPeriodicTableDialog(self, row, compTableOrigin):
        disallowedElements = [r.element.symbol for r in compTableOrigin.rows if r.element is not None]
        if row.element is not None: # Allow selecting the same element again
            disallowedElements.remove(row.element.symbol)
        self.periodicTableDialog.setDisallowedElements(disallowedElements)
        self.dialogSourceRow = row
        self.periodicTableDialog.open()

    def periodicTableDialogClosed(self, returnValue):
        if returnValue > 0:
            self.dialogSourceRow.setElement(self.periodicTableDialog.isotope)

    def updateTabWidget(self):
        tabIndex = self.tabWidget.currentIndex()

        if tabIndex == 1:
            s, _ = self.createSettingsObject()
            c = s.getWriteInputFileString()
            self.inputFilePreview.setPlainText(c.replace('\t',' '*4))
            if s('iq0') < 0:
                c = s.getWriteLayersFileString()
            else:
                c = '(--FILE WILL NOT BE CREATED--)'
            self.layerFilePreview.setPlainText(c.replace('\t', ' '*4))
        elif tabIndex == 3:
            self.updateOutputFilesList()
        elif tabIndex == 4:
            self.updateOutputParametersList()

        # Store the tab index as the previous one for the next tab change
        self.previousTabIndex = tabIndex

    def setGlobalDensityEnabled(self, enabled):
        self.targetLayers.addButton.setEnabled(not enabled)
        self.updateGlobalDensity(enabled)

    # If the update happens through toggling the checkbox, its state is passed as argument
    # For updates due to composition changes, nothing must be passed
    def updateGlobalDensity(self, globalDensityEnabled=None):
        globalDensityToggled = True
        if globalDensityEnabled is None:
            globalDensityToggled = False
            globalDensityEnabled = self.enableGlobalDensity.isChecked()

        if globalDensityEnabled:
            targetComp = self.targetComp.getData()
            if len(targetComp) == 0:
                return
            targetLayers = self.targetLayers.getData()
            mat = Target_Material('mat')
            mat.density = self.globalDensity.value()
            mat.symbols = [entry.element.symbol for entry in targetComp]
            mat.qus = [targetLayers[0].abundances[i] for i in range(len(targetComp))]
            mat.amus = [entry.element.atomic_mass for entry in targetComp]
            mat.dns0 = [entry.element.atomic_density for entry in targetComp]
            newDensity = mat.atomic_density()

        for row in self.targetComp.rows:
            row.atomicDensity.setEnabled(not globalDensityEnabled)
            if globalDensityEnabled:
                row.atomicDensity.setValue(newDensity)
                # If the atomic density is manually set to the global density and afterwards, global density is enabled, then the widget stays highlit
                # because the value did not change --> no signal is emitted. Thus, we force an update of the atomic density highlight here.
                row.updateHighlight(CompTable.SyncedValue.ATOMICDENSITY)
            elif globalDensityToggled:
                # Revert back to the default atomic density, if possible
                newDensity = 0
                if row.element is not None:
                    newDensity = row.element.atomic_density
                row.atomicDensity.setValue(newDensity)

    def selectSDTrimSPfolder(self, showWarningWindow):
        if showWarningWindow:
            showMessageBox(self, QMessageBox.Warning, 'Warning', 'Missing SDTrimSP folder location',
                        'The main SDTrimSP folder, which contains the "bin", "doc", etc. subfolders, has not yet been defined. \n'+\
                        'You can do that either in the preferences or using the window which opens after pressing "OK".')

        startDir = self.preferences.SDTrimSPpath if len(self.preferences.SDTrimSPpath) > 0 else QDir.currentPath()
        folderDir = QFileDialog.getExistingDirectory(self, 'Select the main SDTrimSP folder', startDir)
        if len(folderDir) == 0:
            self.statusBar().showMessage('SDTrimSP folder selection aborted', 3000)
            return False

        # Set the chosen folder and try to load the SDTrimSP data
        self.preferences.setSDTrimSPpath(folderDir)
        success = self.tryLoadSDTrimSPData()
        if success:
            msg = 'SDTrimSP folder successfully set up'
            self.openDocsAction.setEnabled(True)
            self.preferences.tryParseSDTrimSPversion()
            self.setWindowTitle(self.windowTitle().split('SDTrimSP v.')[0] + f'SDTrimSP v. {self.preferences.SDTrimSPversion})')
            if len(self.preferences.SDTrimSPbinaryPath) > 0:
                self.setRunStatus(MainWindow.RunStatus.READY)
        else:
            msg = 'Could not load element data from SDTrimSP directory. Did you select the correct folder?'
            print(msg)
            self.preferences.setSDTrimSPpath('')
            self.setRunStatus(MainWindow.RunStatus.MISSING_PATHS)
            self.openDocsAction.setEnabled(False)
        self.statusBar().showMessage(msg, 3000)
        return success

    def selectSDTrimSPbinary(self, showWarningWindow):
        if showWarningWindow:
            showMessageBox(self, QMessageBox.Warning, 'Warning', 'Missing SDTrimSP binary location',
                    'The SDTrimSP binary has not yet been defined. \n'+\
                    'You can do that either in the preferences or using the window which opens after pressing "OK".')

        if len(self.preferences.SDTrimSPbinaryPath) > 0:
            startDir = self.preferences.SDTrimSPbinaryPath
        elif len(self.preferences.SDTrimSPpath) > 0:
            startDir = self.preferences.SDTrimSPpath
        else:
            startDir = QDir.currentPath()
        filePath = selectFileDialog(self, False, 'Select SDTrimSP binary', startDir, 'Executable File (*.exe)')
        if filePath is None:
            self.statusBar().showMessage('SDTrimSP binary selection aborted', 3000)
            return False

        self.preferences.setSDTrimSPbinaryPath(filePath)
        self.preferences.tryParseSDTrimSPversion()
        self.setWindowTitle(self.windowTitle().split('SDTrimSP v.')[0] + f'SDTrimSP v. {self.preferences.SDTrimSPversion})')
        self.statusBar().showMessage('SDTrimSP binary successfully located', 3000)
        if len(self.preferences.SDTrimSPpath) > 0:
            self.setRunStatus(MainWindow.RunStatus.READY)
        return True

    def tryLoadSDTrimSPData(self):
        # Try to load the element data table and populate the periodic table
        if not self.elementData.tryLoadElementTable(self.preferences.SDTrimSPpath + '/tables/table1'):
            print('/tables/table1 does not exist! Cannot fetch the element data, which is problematic!')
            return False
        self.periodicTableDialog.setElementData(self.elementData)

        # Load a list of all possible variable names
        variableNamesDoc = self.preferences.SDTrimSPpath + '/doc/tri.inp.txt'
        if os.path.exists(variableNamesDoc):
            with open(variableNamesDoc, 'r') as f:
                while f.readline().strip() != 'variable in tri.inp:':
                    pass
                content = f.readline() # skip column headers
                inputVariables = []
                for line in f:
                    content = line.strip()
                    if len(content) == 0: # After the last variable, there's an empty line
                        break
                    var = content.split()[0].split('(')[0].split('=')[0].split('.')[0]
                    inputVariables.append(var)

                # custom add of variable that are not in 'tri.inp.txt
                inputVariables.append('qu_int')
                InputSettings.allVarNames = inputVariables
        else:
            print('/doc/tri.inp.txt does not exist! Cannot fetch a list of all possible variable names')

        # Load output file descriptions from the docs
        outputFilesDoc = self.preferences.SDTrimSPpath + '/doc/output_files.txt'
        if os.path.exists(outputFilesDoc):
            with open(outputFilesDoc, 'r') as f:
                for line in f:
                    content = line.split('.dat')
                    if len(content) <= 1:
                        continue
                    fileName = f'{content[0].strip()}.dat'
                    self.outputFileToolTips[fileName] = content[1].strip()
        else:
            print('/doc/output_files.txt does not exist! Output file tooltips will be missing.')

        self.statusBar().showMessage('SDTrimSP data loaded successfully', 3000)
        return True

    def processStarted(self):
        self.statusBar().showMessage('SDTrimSP simulation running...')
        self.setRunStatus(MainWindow.RunStatus.RUNNING)

    def processReadyRead(self):
        readText = str(self.process.readAll(), 'utf-8')
        self.SDTrimSPoutput.append(readText.rstrip()) # Remove trailing newlines

    def processError(self, e):
        errors = {0: 'QProcess::FailedToStart', 1: 'QProcess::Crashed', 2: 'QProcess::Timedout',
                  3: 'QProcess::WriteError', 4: 'QProcess::ReadError', 5: 'QProcess::UnknownError'}
        self.statusBar().showMessage(f'SDTrimSP ERROR: {errors[e]}')
        print(f'SDTrimSP ERROR: {errors[e]}')
        self.SDTrimSPoutput.append(f'<i>An error occurred: {errors[e]}</i>')
        self.setRunStatus(MainWindow.RunStatus.ERROR)
        self.setProcessWidgetsEnabled(True)
        self.stopSimulationTimer()

    def processFinished(self, exitCode, exitStatus):
        if exitStatus == 0:
            result = 'finished'
            status = MainWindow.RunStatus.DONE
        else:
            result = 'aborted'
            status = MainWindow.RunStatus.ABORTED
        self.statusBar().showMessage('SDTrimSP simulation ' + result, 3000)
        self.setRunStatus(status)
        self.setProcessWidgetsEnabled(True)
        self.stopSimulationTimer()

    """En-/Disable actions which depend on the state of the process"""
    def setProcessWidgetsEnabled(self, enabled):
        self.newAction.setEnabled(enabled)
        self.openAction.setEnabled(enabled)
        self.saveAction.setEnabled(enabled)
        self.saveAsAction.setEnabled(enabled)
        self.runAction.setEnabled(enabled)
        self.runDetachedAction.setEnabled(enabled)
        self.abortAction.setEnabled(not enabled)

    def stopSimulationTimer(self):
        self.updateSimulationData.stop()
        self.updateProgress()
        self.updateOutputFilesList()
        self.updateOutputParametersList()

    def updateProgress(self):
        percent = self.runProgress.value()
        try:
            with open(f'{self.workingDir}/time_run.dat', 'r') as f:
                for line in f:
                    data = line.split(' %')
                    if len(data) == 2 and data[0][0] not in ['I', 'W']:
                        percent = int(data[0][-3:])
        except:
            pass
        self.runProgress.setValue(percent)

    def updateOutputFilesList(self):
        # Only update if the tab is actually visible
        if self.tabWidget.currentIndex() != 3:
            return
        # Save the currently selected entry of the output list
        self.selectedOutputFile = None
        selectedItems = self.outputFilesList.selectedItems()
        if len(selectedItems) > 0:
            self.selectedOutputFile = selectedItems[0].text()
            self.previousScrollPos = self.outputFilePreview.verticalScrollBar().value()

        self.outputFilesList.clear()

        # Get all .dat files in working directory
        allDatFileInfos = QDir(self.workingDir).entryInfoList(['*.dat'], QDir.Files, QDir.Name)
        for fileInfo in allDatFileInfos:
            if fileInfo.fileName() == 'ausdat.dat':
                continue # Skip the temporary help file
            self.outputFilesList.addItem(fileInfo.fileName())
            item = self.outputFilesList.item(self.outputFilesList.count()-1)
            if fileInfo.fileName() in self.outputFileToolTips:
                item.setToolTip(self.outputFileToolTips[fileInfo.fileName()])
            # Keep the previous selection
            if item.text() == self.selectedOutputFile:
                self.outputFilesList.setCurrentItem(item)

    def previewSelectedFile(self):
        selectedItems = self.outputFilesList.selectedItems()
        if len(selectedItems) == 0:
            self.openOutputFile.setEnabled(False)
            self.outputFilePreview.clear()
            return

        filePath = f'{self.workingDir}/{selectedItems[0].text()}'
        file = QFile(filePath)
        if not file.open(QIODevice.ReadOnly | QIODevice.Text):
            self.outputFilePreview.clear()
            self.statusBar().showMessage(f'Failed to preview file "{filePath}"', 3000)
            print(f'Failed to preview file "{filePath}"')
            self.openOutputFile.setEnabled(False)
            return

        fileContent = str(file.readAll(), 'utf-8')
        lineLimit = self.outputFilePreviewLines.value()
        if len(fileContent) == 0:
            fileContent = '(--EMPTY FILE--)'
        elif lineLimit >= 0: # Limit the maximum lines in the preview to the set number
            fileContent = fileContent.split('\n')
            lineCount = len(fileContent)
            fileContent = '\n'.join(fileContent[:lineLimit])
            if lineCount > lineLimit:
                fileContent += '\n\n(--END OF PREVIEW--)'
        self.outputFilePreview.setPlainText(fileContent)
        if self.selectedOutputFile == selectedItems[0].text():
            self.outputFilePreview.verticalScrollBar().setValue(self.previousScrollPos)
        self.openOutputFile.setEnabled(True)

    def openSelectedOutputFile(self):
        filePath = f'{self.workingDir}/{self.outputFilesList.selectedItems()[0].text()}'
        if not os.path.exists(filePath) or not QDesktopServices.openUrl(QUrl.fromUserInput(filePath)):
            self.statusBar().showMessage(f'Failed to open file "{filePath}"', 3000)
            print(f'Failed to open file "{filePath}"')

    def updateOutputParametersList(self):
        # Only update if the tab is actually visible
        if self.tabWidget.currentIndex() != 4:
            return

        # Save the currently selected entry of the list
        self.selectedOutputParameter = None
        selectedItems = self.outputParametersList.selectedItems()
        if len(selectedItems) > 0:
            self.selectedOutputParameter = selectedItems[0].text()

        self.outputParametersList.clear()
        self.clearPlotWindow()

        infoFile = f'{self.workingDir}/E0_31_target.dat'
        if not os.path.exists(infoFile):
            infoFile = f'{self.workingDir}/E0_31_target001.dat'
            if not os.path.exists(infoFile):
                return

        # Update the output evaluation data
        self.outputEval.updateData(self.workingDir, infoFile)

        # Check if calculation in output files is dynamic (=IDREL parameter)
        with open(infoFile, 'r') as content_file:
            for i in range(4):
                content_file.readline()
            output_dynamic = int(content_file.readline().split()[-1]) == 0

        # static simulations
        # For static simulations, read simulation results from output.dat for all elements
        if output_dynamic == False and os.path.exists(f'{self.workingDir}/output.dat'):
            #try:
                item = QListWidgetItem('Results overview:')
                item_font = item.font()
                item_font.setWeight(QFont.Bold)
                item.setFont(item_font)
                self.outputParametersList.addItem(item)

                yields, total_yield, amu_yield, energy_loss_nucl, energy_loss_elec, implantation_depth, refl_coefficients, transm_sputt_yields, total_transm_sputt_yield, amu_transm_sputt_yield, transm_coefficients = self.outputEval.get_output_file_data()
                energy_loss_total = energy_loss_nucl + energy_loss_elec

                transmission_happening = (np.sum(transm_coefficients) + np.sum(transm_sputt_yields)) > 0

                self.outputParametersList.addItem('\tSputtering yields:')
                for i, element in enumerate(self.outputEval.elements):
                    if yields[i] != 0.:
                        if yields[i] >= 1.e-3:
                            self.outputParametersList.addItem(f'\t\t{element}\t{yields[i]:.3f}  atoms/ion')
                        else:
                            self.outputParametersList.addItem(f'\t\t{element}\t{yields[i]:.2e}  atoms/ion')
                if np.sum(yields) == 0.:
                    self.outputParametersList.addItem('\t\tNo sputtering occured.')
                else:
                    self.outputParametersList.addItem('')
                    if total_yield >= 1.e-3:
                        self.outputParametersList.addItem(f'\t\tTotal\t{total_yield:.3f}  atoms/ion')
                    else:
                        self.outputParametersList.addItem(f'\t\tTotal\t{total_yield:.2e}  atoms/ion')
                    if amu_yield >= 1.e-3:
                        self.outputParametersList.addItem(f'\t\t\t{amu_yield:.3f}  amu/ion')
                    else:
                        self.outputParametersList.addItem(f'\t\t\t{amu_yield:.2e}  amu/ion')

                # only show transmission sputtering data, if it actually occurs
                if transmission_happening:
                    self.outputParametersList.addItem('')
                    self.outputParametersList.addItem('\tTransmission sputtering yields:')
                    for i, element in enumerate(self.outputEval.elements):
                        if transm_sputt_yields[i] != 0.:
                            if transm_sputt_yields[i] >= 1.e-3:
                                self.outputParametersList.addItem(f'\t\t{element}\t{transm_sputt_yields[i]:.3f}  atoms/ion')
                            else:
                                self.outputParametersList.addItem(f'\t\t{element}\t{transm_sputt_yields[i]:.2e}  atoms/ion')
                    if np.sum(transm_sputt_yields) == 0.:
                        self.outputParametersList.addItem('\t\tNo transmission sputtering occured.')
                    else:
                        self.outputParametersList.addItem('')
                        if total_transm_sputt_yield >= 1.e-3:
                            self.outputParametersList.addItem(f'\t\tTotal\t{total_transm_sputt_yield:.3f}  atoms/ion')
                        else:
                            self.outputParametersList.addItem(f'\t\tTotal\t{total_transm_sputt_yield:.2e}  atoms/ion')
                        if amu_transm_sputt_yield >= 1.e-3:
                            self.outputParametersList.addItem(f'\t\t\t{amu_transm_sputt_yield:.3f}  amu/ion')
                        else:
                            self.outputParametersList.addItem(f'\t\t\t{amu_transm_sputt_yield:.2e}  amu/ion')

                self.outputParametersList.addItem('')
                self.outputParametersList.addItem('\tReflection coefficients:')
                for i, element in enumerate(self.outputEval.elements):
                    if refl_coefficients[i] != 0.:
                        if refl_coefficients[i] > 1.e-3:
                            self.outputParametersList.addItem(f'\t\t{element}\t{refl_coefficients[i]:.3f}')
                        else:
                            self.outputParametersList.addItem(f'\t\t{element}\t{refl_coefficients[i]:.2e}')
                if np.sum(refl_coefficients) == 0.:
                    self.outputParametersList.addItem('\t\tNo projectile reflection occured.')

                # only show transmission sputtering data, if it actually occurs
                if transmission_happening:
                    self.outputParametersList.addItem('')
                    self.outputParametersList.addItem('\tTransmission coefficients:')
                    for i, element in enumerate(self.outputEval.elements):
                        if transm_coefficients[i] != 0.:
                            if transm_coefficients[i] >= 1.e-3:
                                self.outputParametersList.addItem(f'\t\t{element}\t{transm_coefficients[i]:.3f}')
                            else:
                                self.outputParametersList.addItem(f'\t\t{element}\t{transm_coefficients[i]:.2e}')
                    if np.sum(transm_coefficients) == 0.:
                        self.outputParametersList.addItem('\t\tNo projectile transmission occured.')
                else:
                    self.outputParametersList.addItem('')
                    self.outputParametersList.addItem('\tNo transmission effects occured.')

                self.outputParametersList.addItem('')
                self.outputParametersList.addItem('\tMean implantation depth:')
                for i, element in enumerate(self.outputEval.elements):
                    if implantation_depth[i] != 0.:
                        self.outputParametersList.addItem(f'\t\t{element}\t{implantation_depth[i]:.3f} Å')
                if np.sum(implantation_depth) == 0.:
                    self.outputParametersList.addItem('\t\tNo projectile implantation occured.')

                self.outputParametersList.addItem('')
                self.outputParametersList.addItem('\tMean projectile energy loss:')
                self.outputParametersList.addItem('\t\t\tNuclear\tElectronic\tTotal')
                for i, element in enumerate(self.outputEval.elements):
                    if energy_loss_nucl[i] != 0. or energy_loss_elec[i] != 0.:
                        self.outputParametersList.addItem(
                            f'\t\t{element}\t{energy_loss_nucl[i]:.3f} eV\t{energy_loss_elec[i]:.3f} eV\t{energy_loss_total[i]:.3f} eV')
                self.outputParametersList.addItem('')
            #except:
            #    self.outputParametersList.addItem('')
        else:
            item = QListWidgetItem('Results overview (only for finished static simulations)')
            item.setForeground(QColor('#888888'))
            self.outputParametersList.addItem(item)
            self.outputParametersList.addItem('')



        # For static simulations, plot depth information of stopped projectiles, damages, ...
        depth_proj_exists = os.path.exists(f'{self.workingDir}/depth_proj.dat')
        depth_recoil_exists = os.path.exists(f'{self.workingDir}/depth_recoil.dat')
        depth_damage_exists = os.path.exists(f'{self.workingDir}/depth_damage.dat')

        if depth_proj_exists or depth_recoil_exists or depth_damage_exists:
            item = QListWidgetItem('Plot depth statistics:')
            item_font = item.font()
            item_font.setWeight(QFont.Bold)
            item.setFont(item_font)
            self.outputParametersList.addItem(item)

            if depth_proj_exists:
                self.outputParametersList.addItem(f'\t{self.outputEval.depth_proj_impl}')
                self.outputParametersList.addItem(f'\t{self.outputEval.depth_proj_eloss}')

            if depth_recoil_exists or depth_damage_exists:
                self.outputParametersList.addItem(f'\t{self.outputEval.depth_recoil}')

            self.outputParametersList.addItem('')
        else:
            item = QListWidgetItem('Plot depth statistics (only for finished static simulations)')
            item.setForeground(QColor('#888888'))
            self.outputParametersList.addItem(item)
            self.outputParametersList.addItem('')

        # For dynamic simulations, show options for plotting fluence dependent quantities (yield, concentrations)
        if output_dynamic:
            item = QListWidgetItem('Plot over fluence:')
            item_font = item.font()
            item_font.setWeight(QFont.Bold)
            item.setFont(item_font)
            self.outputParametersList.addItem(item)

            for label in self.outputEval.fluence_labels:
                self.outputParametersList.addItem('\t' + label)
            self.outputParametersList.addItem('')
        else:
            item = QListWidgetItem('Plot over fluence (only for dynamic simulations)')
            item.setForeground(QColor('#888888'))
            self.outputParametersList.addItem(item)
            self.outputParametersList.addItem('')

        # For static angular dependence calculations (case_alpha = 5) plot the angular dependence of sputtering yields from "serie.dat"
        nr_energies = 0
        nr_angles = 0
        if os.path.exists(f'{self.workingDir}/serie.dat'):
            # read serie.dat file and check for energy or angle sweep by number of unique angles or energies
            ncp, ncp_proj, elements, elements_proj, masses, nr_energies, nr_angles,  nr_total, energies, angles, mean_depth, refl_coeff, energ_refl_coeff, sputt_coeff, energ_sputt_coeff, i = self.outputEval.get_data_from_serie_file()
        if nr_angles > 1:
            item = QListWidgetItem('Plot angular dependence:')
            item_font = item.font()
            item_font.setWeight(QFont.Bold)
            item.setFont(item_font)
            self.outputParametersList.addItem(item)

            self.outputParametersList.addItem(f'\t{self.outputEval.ang_yield}')
            self.outputParametersList.addItem(f'\t{self.outputEval.ang_mass}')
            self.outputParametersList.addItem(f'\t{self.outputEval.ang_refl}')
            self.outputParametersList.addItem(f'\t{self.outputEval.ang_depth}')
            self.outputParametersList.addItem('')
        else:
            item = QListWidgetItem('Plot angular dependence (only for "angle sweep")')
            item.setForeground(QColor('#888888'))
            self.outputParametersList.addItem(item)
            self.outputParametersList.addItem('')

        if nr_energies > 1:
            item = QListWidgetItem('Plot energy dependence:')
            item_font = item.font()
            item_font.setWeight(QFont.Bold)
            item.setFont(item_font)
            self.outputParametersList.addItem(item)

            self.outputParametersList.addItem(f'\t{self.outputEval.en_yield}')
            self.outputParametersList.addItem(f'\t{self.outputEval.en_mass}')
            self.outputParametersList.addItem(f'\t{self.outputEval.en_refl}')
            self.outputParametersList.addItem(f'\t{self.outputEval.en_depth}')
            self.outputParametersList.addItem('')
        else:
            item = QListWidgetItem('Plot energy dependence (only for "energy sweep")')
            item.setForeground(QColor('#888888'))
            self.outputParametersList.addItem(item)
            self.outputParametersList.addItem('')

        # allow plotting of reflected projectiles and sputtered recoils
        back_p_exists = os.path.exists(f'{self.workingDir}/partic_back_p.dat')
        back_r_exists = os.path.exists(f'{self.workingDir}/partic_back_r.dat')
        if back_p_exists or back_r_exists:
            item = QListWidgetItem('Plot secondary particle distributions:')
            item_font = item.font()
            item_font.setWeight(QFont.Bold)
            item.setFont(item_font)
            self.outputParametersList.addItem(item)

            for i, element in enumerate(self.outputEval.elements):
                if back_p_exists:
                    self.outputParametersList.addItem(f'\t Backscattered {element} ions')
                if back_r_exists:
                    self.outputParametersList.addItem(f'\t Backsputtered {element} recoil atoms')

            self.outputParametersList.addItem('')
            if back_p_exists:
                self.outputParametersList.addItem(f'\t{self.outputEval.polar_ions}')
            if back_r_exists:
                self.outputParametersList.addItem(f'\t{self.outputEval.polar_recoils}')

            self.outputParametersList.addItem('')
            if back_p_exists:
                self.outputParametersList.addItem(f'\t{self.outputEval.energy_ions}')
            if back_r_exists:
                self.outputParametersList.addItem(f'\t{self.outputEval.energy_recoils}')

            self.outputParametersList.addItem('')
        else:
            item = QListWidgetItem('Plot secondary particle distributions (only with additional output options)')
            item.setForeground(QColor('#888888'))
            self.outputParametersList.addItem(item)
            self.outputParametersList.addItem('')

        # Keep the previous selection
        for i in range(self.outputParametersList.count()):
            item = self.outputParametersList.item(i)
            if item.text() == self.selectedOutputParameter:
                self.outputParametersList.setCurrentItem(item)
                break

    def clearPlotWindow(self):
        self.savePlot.setEnabled(False)
        self.outputPlotView.fig.clf()
        self.outputPlotView.axes = self.outputPlotView.fig.add_subplot(projection="rectilinear")
        self.outputPlotView.fig.canvas.draw_idle()

    def plotSelectedOutput(self):
        selectedItems = self.outputParametersList.selectedItems()
        if len(selectedItems) == 0 or len(selectedItems[0].text().strip()) == 0:
            self.clearPlotWindow()
        else:
            plot_label = selectedItems[0].text().strip()

            if plot_label in self.outputEval.plot_labels:
                inputVisible = plot_label == self.outputEval.fluence_depth_conc
                self.historyStep.setVisible(inputVisible)
                self.historyStepSlider.setVisible(inputVisible)
                self.historyStepLabel.setVisible(inputVisible)
                self.data, self.plotLabels = self.outputEval.plot_output(plot_label)
                self.savePlot.setEnabled(len(self.data)+len(self.plotLabels) > 0)
            elif plot_label.startswith('Backscattered'):
                self.data, self.plotLabels = self.outputEval.plot_polar(plot_label.split()[1], 'p')
                self.savePlot.setEnabled(len(self.data) + len(self.plotLabels) > 0)
            elif plot_label.startswith('Backsputtered'):
                self.data, self.plotLabels = self.outputEval.plot_polar(plot_label.split()[1], 'r')
                self.savePlot.setEnabled(len(self.data) + len(self.plotLabels) > 0)
            else:
                self.clearPlotWindow()

    def updateDepthConcPlot(self):
        self.data, self.plotLabels = self.outputEval.update_depth_conc()
        self.savePlot.setEnabled(len(self.data)+len(self.plotLabels) > 0)

    def saveSelectedPlot(self):
        selectedItems = self.outputParametersList.selectedItems()
        if len(selectedItems) == 0:
            return

        # Use the displayed plot name minus the content in parentheses as default name
        text = '_'.join(selectedItems[0].text().strip().split('(')[0].split())
        filePath = selectFileDialog(self, True, 'Save plot data as...', f'{self.workingDir}/{text}.txt', 'Text files (*.txt)')
        if filePath is None:
            self.statusBar().showMessage('No file selected - aborted', 3000)
            return

        with open(filePath, 'w') as file:
            file.write('\t'.join(self.plotLabels)+'\n')
            for i in range(len(self.data[0])):
                data = ''
                for j in range(len(self.data)):
                    data += f'{self.data[j][i]}\t'
                file.write(f'{data}\n')

        self.statusBar().showMessage(f'Plot data saved as "{filePath}"', 3000)

    def openDocs(self):
        filePath = self.preferences.SDTrimSPpath + '/doc/' + MissingDocsDialog.docsFileName
        if not os.path.exists(filePath) or not QDesktopServices.openUrl(QUrl.fromUserInput(filePath)):
            dialog = MissingDocsDialog(self, self.preferences.SDTrimSPpath)
            dialog.open()

    def runSDTrimSP(self, runDetached):
        if (len(self.preferences.SDTrimSPpath) == 0 or not os.path.exists(self.preferences.SDTrimSPpath)) and not self.selectSDTrimSPfolder(True):
            self.statusBar().showMessage('SDTrimSP folder not set up - simulation aborted', 3000)
            return

        if (len(self.preferences.SDTrimSPbinaryPath) == 0 or not os.path.exists(self.preferences.SDTrimSPbinaryPath)) and not self.selectSDTrimSPbinary(True):
            self.statusBar().showMessage('SDTrimSP binary not set up - simulation aborted', 3000)
            return

        # The working directory has to exist
        if not os.path.exists(self.workingDir):
            showMessageBox(self, QMessageBox.Critical, 'Warning', 'Missing working directory', 'To set it, either save or load an input file')
            self.statusBar().showMessage('Working directory missing - simulation aborted', 3000)
            return

        # Try to save the current status of the input file
        if not self.saveFiles():
            self.statusBar().showMessage('Could not save input file - simulation aborted', 3000)
            return

        # Find all *.dat files in the working directory
        allDatFileInfos = QDir(self.workingDir).entryInfoList(['*.dat'], QDir.Files, QDir.Name)

        # If necessary, inform the user that all *.dat files in the working directory will be deleted
        if not self.preferences.skipDeleteInfoMsgBox.isChecked() and len(allDatFileInfos) > 0:
            infoMsg = 'In order to run the simulation, all <b>*.dat</b> files in the working directory<br><br>'+self.workingDir+'<br><br>will be deleted automatically.'
            detailMsg = 'Affected files:\n\n'+'\n'.join([fileInfo.fileName() for fileInfo in allDatFileInfos])
            msgBox, result = showMessageBox(self, QMessageBox.Information, 'Attention!', 'Files in the working directory will be deleted',
                           infoMessage=infoMsg, detailedMessage=detailMsg, standardButtons=QMessageBox.Ok | QMessageBox.Cancel, checkBoxText='Do not show again')
            if result == QMessageBox.Cancel:
                return
            self.preferences.skipDeleteInfoMsgBox.setChecked(msgBox.checkBox().isChecked())

        # Delete all found *.dat files
        for fileInfo in allDatFileInfos:
            QFile(fileInfo.filePath()).remove()

        chdir(self.workingDir)

        self.SDTrimSPoutput.clear()
        self.outputFilesList.clear()
        self.outputParametersList.clear()
        self.outputEval.resetPolarData()

        if not runDetached:
            self.setProcessWidgetsEnabled(False)
            self.runProgress.setValue(0)

            self.updateSimulationData = QTimer(self)
            self.updateSimulationData.timeout.connect(self.updateProgress)
            self.updateSimulationData.timeout.connect(self.updateOutputFilesList)
            self.updateSimulationData.timeout.connect(self.updateOutputParametersList)
            self.updateSimulationData.start(1000)

            self.process.start(f'"{self.preferences.SDTrimSPbinaryPath}"')
        else:
            if platform.system() == 'Windows':
                cmd = f'start /wait {self.preferences.SDTrimSPbinaryPath}'
                subprocess.Popen(cmd, shell=True)
            elif platform.system() in ['Linux', 'Darwin']:
                cmd = self.preferences.SDTrimSPbinaryPath

                if 'GNOME' in os.popen("echo $XDG_CURRENT_DESKTOP").read():
                    #cmd = "'" + cmd + "; exec bash'"
                    #cmd = "gnome-terminal -- bash -c " + cmd
                    cmd = f"gnome-terminal -- bash -c '{cmd}; exec bash'"

                    os.system(cmd)
                else:
                    subprocess.Popen(cmd, shell=True)
            else:
                return

            #subprocess.Popen(cmd, shell=True)
            self.statusBar().showMessage('SDTrimSP detached simulation started', 3000)

    def saveFiles(self, selectFolder=None):
        if not all([r.containsData() for r in self.beamComp.rows]) or not all([r.containsData() for r in self.targetComp.rows]):
            showMessageBox(self, QMessageBox.Warning, 'Warning!', 'All elements must be defined in order to save the input file', standardButtons=QMessageBox.Ok)
            self.statusBar().showMessage('Not all elements defined - saving aborted', 3000)
            return False

        # For 'Save as...', existing .dat files will be copied to the new directory
        copyFiles = selectFolder

        # If the working directory is missing, ask for a new save directory
        if not os.path.exists(self.workingDir):
            self.workingDir = QDir.currentPath()
            selectFolder = True

        # If the argument is not given, select a folder if the file hasn't been saved yet (i.e. the "Save as..." action is disabled)
        if selectFolder is None:
            selectFolder = not self.saveAsAction.isEnabled()

        folder = self.workingDir
        if selectFolder:
            res = None
            while res != QMessageBox.Yes:
                folder = QFileDialog.getExistingDirectory(self, 'Select the folder where the files will be saved', self.workingDir)
                if len(folder) == 0:
                    self.statusBar().showMessage('Saving aborted', 3000)
                    return False
                if not QFileInfo.exists(folder + '/tri.inp'):
                    break
                _, res = showMessageBox(self, QMessageBox.Warning, 'Warning!', 'This folder already contains an input file',
                            infoMessage=f'Do you want to overwrite the file in\n"{folder}/"?', standardButtons=QMessageBox.Yes | QMessageBox.No)

            # Copy all .dat files in the current working directory to the new one
            if copyFiles:
                allDatFileInfos = QDir(self.workingDir).entryInfoList(['*.dat'], QDir.Files, QDir.Name)
                for fileInfo in allDatFileInfos:
                    QFile.copy(fileInfo.canonicalFilePath(), folder + '/' + fileInfo.fileName())

            # Update to the new working directory
            self.workingDir = folder
            self.saveAsAction.setEnabled(True)

        s, _ = self.createSettingsObject()
        s.writeToFile(folder + '/tri.inp', InputSettings.FileType.INPUT)

        # Create the layer.inp file if necessary. Otherwise remove it if it exists
        layerFileName = f'{self.workingDir}/layer.inp'
        if s('iq0') < 0:
            s.writeToFile(layerFileName, InputSettings.FileType.LAYERS)
        elif os.path.exists(layerFileName):
            QFile(layerFileName).remove()

        self.updateTabWidget()
        self.setWindowTitle(f'{folder}/tri.inp[*] - SDTrimSP GUI (SDTrimSP v. {self.preferences.SDTrimSPversion})')
        self.setWindowModified(False)
        self.statusBar().showMessage(f'Saved to "{folder}/"', 3000)
        return True

    def createSettingsObject(self, showErrorsMessageBox=True):
        settings = InputSettings()
        additionalSettingsText = self.additionalSettings.toPlainText()
        # Always add the path to the SDTrimSP tables folder as additional setting
        additionalSettings = [f'tableinp = "{self.preferences.SDTrimSPpath}/tables"']
        if len(additionalSettingsText.strip()) > 0:
            additionalSettings.extend(additionalSettingsText.split('\n'))

        # if simulation Title is empty, set to default value to prevent errors with missing title
        if len(self.simulationTitle.text().strip()) == 0:
            self.simulationTitle.setText(f'SDTrimSP - {QDateTime.currentDateTime().toString()}')

        # Sort the occurring symbols by their respective element index
        symbols = self.getOrderedElements()
        settings.extractVariables(symbols, self.beamComp.getData(), self.targetComp.getData(), self.targetLayers.getData(),
                self.simulationTitle.text(), self.historiesPerUpdate.value(),
                -1 if self.limitOutputs.isChecked() else self.historiesBetweenOutputs.value(),
                self.projectilesPerHistory.value(), self.fluence.value(), self.calcMethod.currentIndex()-1,
                self.interactPot.currentIndex()+1, self.integrationMethod.currentIndex(),
                self.surfaceBindingModel.currentIndex()+1, self.kinEnergyType.currentIndex(),
                self.angleType.currentIndex(), self.nr_calc.value(), self.targetThickness.value(), self.targetSegmentsCount.value(),
                self.enableGlobalDensity, self.globalDensity, self.outputReflected.isChecked(), self.outputSputtered.isChecked(), self.outputMatrices.isChecked(),
                additionalSettings)
        errors = settings.checkForAdditionalSettingErrors()
        if len(errors) > 0 and showErrorsMessageBox:
            self.showAdditionalSettingsMessage(errors, False)
        return settings, errors

    def showAdditionalSettingsMessage(self, errors, showIfValid=True):
        if len(errors) > 0:
            showMessageBox(self, QMessageBox.Warning, 'Warning!', 'Problems with settings detected',
                        infoMessage='Some settings appear multiple times, or there are unknown or invalid ones.\n'+
                                    'Note that multiple occurring settings overwrite previous ones.',
                        detailedMessage='\n'.join(errors), expandDetails=True)
        elif showIfValid:
            showMessageBox(self, QMessageBox.Information, 'Valid!', 'No problems with the settings detected')

    def loadFiles(self, inputFilePath=''):
        if len(self.preferences.SDTrimSPpath) == 0 and not self.selectSDTrimSPfolder(True):
            self.statusBar().showMessage('SDTrimSP folder not set up - loading aborted', 3000)
            return

        if self.isWindowModified() and not self.showUnsavedChangesWarning():
            return

        if len(inputFilePath) == 0:
            inputFilePath = selectFileDialog(self, False, 'Load input file', self.workingDir, 'Input Files (*.inp)')
            if inputFilePath is None:
                self.statusBar().showMessage('Loading aborted', 3000)
                return
        elif not os.path.exists(inputFilePath):
            showMessageBox(self, QMessageBox.Warning, 'Error', 'Invalid file path', 'Input file "' + inputFilePath + '" does not exist')
            return

        try:
            s, alerts = loadInputFile(inputFilePath, self.elementData)
        except:
            showMessageBox(self, QMessageBox.Critical, 'Error', 'Error while loading input file "' + inputFilePath + '"')
            return
        if len(alerts) > 0:
            showMessageBox(self, QMessageBox.Warning, 'Warning', 'Problems while loading input file',
                            infoMessage=f'The following problems occurred while trying to load "{inputFilePath}"',
                            detailedMessage='\n'.join(alerts), expandDetails=True)

        nqx, qu, symbols = s('nqx'), s('qu'), s('symbol')
        targetThickness = s('ttarget')

        # Check whether the elements' occurrence in the target is explicitly given by the custom variable
        occurrence = s('occurrence')
        if occurrence is not None:
            elementInTarget = [o[1] for o in occurrence]

        folder = QFileInfo(inputFilePath).canonicalPath()
        if s('iq0') < 0:
            layersFilePath = folder + '/layer.inp'
            try:
                targetLayers = loadLayersFile(layersFilePath)
            except:
                showMessageBox(self, QMessageBox.Critical, 'Error', 'Failed to load required layers file "' + layersFilePath + '"')
                return
            # If the occurrences are not explicitly given, figure them out via the abundances
            if occurrence is None:
                elementInTarget = [any(l.abundances[i]>0 for l in targetLayers) for i in range(len(symbols))]
        else:
            targetLayers = [TargetLayerEntry(nqx, targetThickness/nqx, qu, 'Layer1')]
            if occurrence is None:
                elementInTarget = [a>0 for a in qu]

        self.resetSettings(False)
        self.workingDir = folder
        self.saveAsAction.setEnabled(True)

        self.simulationTitle.setText(s.title)
        self.kinEnergyType.setCurrentIndex(int(s('case_e0')))
        self.angleType.setCurrentIndex(int(s('case_alpha')))
        self.nr_calc.setValue(int(s('number_calc')))
        self.targetThickness.setValue(int(targetThickness))
        self.targetSegmentsCount.setValue(int(nqx))
        self.historiesPerUpdate.setValue(int(s('nh')))
        idout = s('idout')
        self.historiesBetweenOutputs.setValue(1000 if idout == -1 else int(idout))
        self.limitOutputs.setChecked(idout == -1)
        self.projectilesPerHistory.setValue(int(s('nr_pproj')))
        self.fluence.setValue(s('flc'))
        self.calcMethod.setCurrentIndex(int(s('idrel')+1))
        self.interactPot.setCurrentIndex(int(s('ipot'))-1)
        self.integrationMethod.setCurrentIndex(int(s('iintegral')))
        self.surfaceBindingModel.setCurrentIndex(int(s('isbv'))-1)
        self.outputReflected.setChecked(s('lparticle_p'))
        self.outputSputtered.setChecked(s('lparticle_r'))
        self.outputMatrices.setChecked(s('lmatrices'))
        self.additionalSettings.setPlainText('\n'.join(s.additionalSettings))

        qubeam, e0, alpha0, qumax = s('qubeam'), s('e0'), s('alpha0'), s('qumax')
        inel0, dns0, e_surfb, e_displ = s('inel0'), s('dns0'), s('e_surfb'), s('e_displ')
        defaultDens = dns0 is None
        defaultSurfBindEnergy = e_surfb is None
        defaultDisplEnergy = e_displ is None

        # Create the beam and target composition table entries.
        # Also, remove elements, which are not in the target, from the abundances lists
        beamEntries, targetEntries = [], []
        for i in range(len(symbols)-1, -1, -1):
            element = self.elementData.elementFromSymbol(symbols[i])
            dns = element.atomic_density if (defaultDens or dns0[i] is None) else dns0[i]
            surfBindEnergy = element.surface_binding_energy if (defaultSurfBindEnergy or e_surfb[i] is None) else e_surfb[i]
            displEnergy = element.displacement_energy if (defaultDisplEnergy or e_displ[i] is None) else e_displ[i]
            # Whether the element occurs in the beam is either given by the custom GUI occurrence variable
            # or otherwise inferred from the beam abundances
            if (occurrence is not None and occurrence[i][0]) or qubeam[i] > 0:
                entry = BeamCompEntry(element, qubeam[i], e0[i], alpha0[i], qumax[i], dns, surfBindEnergy, displEnergy, inel0[i]-1)
                beamEntries.insert(0, entry)
            if elementInTarget[i]:
                entry = CompEntry(element, qumax[i], dns, surfBindEnergy, displEnergy, inel0[i]-1)
                targetEntries.insert(0, entry)
            else: # Remove the element from the target layer abundances
                for layer in targetLayers:
                    layer.abundances = layer.abundances[:i] + layer.abundances[i+1:]

        self.beamComp.addRows(beamEntries)
        self.targetComp.addRows(targetEntries)
        self.targetLayers.addRows(targetLayers)

        # Set the element order to the loaded one
        for r in self.beamComp.rows + self.targetComp.rows:
            r.elementIndex.setValue(symbols.index(r.element.symbol)+1)
        self.updateElementOrder()

        enabled, value = s('globaldensity')
        self.globalDensity.setValue(value)
        self.enableGlobalDensity.setChecked(enabled)

        self.updateTabWidget()
        self.setWindowTitle(f'{folder}/tri.inp[*] - SDTrimSP GUI (SDTrimSP v. {self.preferences.SDTrimSPversion})')
        self.setWindowModified(False)
        self.statusBar().showMessage(f'Loaded from "{folder}/"', 3000)