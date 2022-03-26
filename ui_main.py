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


from PyQt5.QtCore import Qt, QSettings, QUrl
from PyQt5.QtGui import QKeySequence, QIcon, QDesktopServices
from PyQt5.QtWidgets import QWidget, QPushButton, QTextEdit, QListWidget, QSlider,\
    QLabel, QGroupBox, QCheckBox, QVBoxLayout, QSplitter, QProgressBar,\
    QHBoxLayout, QTabWidget, QSizePolicy, QDesktopWidget, QAbstractItemView
from TableWidgets.BeamCompTable import BeamCompTable
from TableWidgets.TargetCompTable import TargetCompTable
from TableWidgets.TargetLayersTable import TargetLayersTable
from Utility import inputHLayout, VBoxTitleLayout, setWidgetHighlight
from TargetPreview import TargetPreview
from Styles import Styles
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from Dialogs import AboutDialog
import resources

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        #self.axes = self.fig.add_subplot(projection="polar")
        super(MplCanvas, self).__init__(self.fig)

class Ui_Main(object):
    def setupUi(self):
        self.setWindowIcon(QIcon(':/icons/tu_logo.png'))

        self.tabWidget = QTabWidget(self)
        settingsTabSplitter = QSplitter(self)
        settingsTabSplitter.setChildrenCollapsible(False)
        self.tabWidget.addTab(settingsTabSplitter, 'Simulation setup')

        compositionSplitter = QSplitter(self)
        compositionSplitter.setOrientation(Qt.Vertical)
        settingsTabSplitter.addWidget(compositionSplitter)
        # BEAM SETTINGS
        # settingslayout = title + settingsgroup (with its own settingsgroup layout)
        settingsLayout = VBoxTitleLayout(self, 'Beam Settings', Styles.titleStyle, 2, False)
        settingsGroupLayout = QVBoxLayout()
        settingsGroupLayout.setSpacing(5)
        settingsGroupLayout.setContentsMargins(12, 0, 12, 0)

        # General beam settings
        outerHl = QHBoxLayout()
        hl = inputHLayout(self, 'Kinetic energy [eV]:', inputHLayout.InputType.COMBOBOX, 0,
                  entries=['constant', 'energy.inp', 'Maxwell velocity distr. temp.', 'Maxwell energy distr. temp.',
                           '(unused)', 'energy sweep', 'ene_ang.inp'])
        kinEnergyToolTips = ['The energy (in eV) for each element in the beam is constant and defined in the table below',
                             'The energy distribution of the beam is read from the <i>energy.inp</i> file',
                             'The energy for each element in the beam is defined in the table below as the temperature of a Maxwellian velocity distribution  (in eV)',
                             'The energy for each element in the beam is defined in the table below as the temperature of a Maxwellian energy distribution  (in eV)',
                             '', # not used
                             'A series of calculations at different energies, with energy steps defined for each element in the table',
                             'The angle and energy distribution of the beam is read from the <i>ene_ang.inp</i> file']
        self.kinEnergyType = hl.input
        self.kinEnergyType.model().item(4, 0).setEnabled(False)

        self.kinEnergyType.setToolTip('<i>case_e0</i><br>How the energy of the projectiles in the beam is defined')
        for i in range(self.kinEnergyType.count()):
            self.kinEnergyType.setItemData(i, kinEnergyToolTips[i], Qt.ToolTipRole)

        outerHl.addLayout(hl)
        outerHl.addSpacing(20)

        hl = inputHLayout(self, 'Angle of incidence [°]:', inputHLayout.InputType.COMBOBOX, 0,
                  entries=['constant', 'random distribution',
                 'cosine distr. 1', 'cosine distr. 2', 'angle.inp', 'angle sweep', 'ene_ang.inp'])
        angleTypeTooltips = ['The angle α (in °) for each element in the beam is constant and defined in the table below',
                            'The angles α and φ are sampled from a random distribution',
                            'The angles α and φ follow a cosine distribution (1st type)',
                            'The angles α and φ follow a cosine distribution (2nd type)',
                            'The angle distribution of the beam is read from the <i>angle.inp</i> file',
                            'A series of calculations at different angles of incidence, with angle steps defined for each element in the table',
                            'The angle and energy distribution of the beam is read from the <i>ene_ang.inp</i> file']
        self.angleType = hl.input

        self.angleType.setToolTip('<i>case_alpha</i><br>How the angle of incidence of the projectiles in the beam is defined')
        for i in range(self.angleType.count()):
            self.angleType.setItemData(i, angleTypeTooltips[i], Qt.ToolTipRole)

        outerHl.addLayout(hl)
        outerHl.addSpacing(20)

        hl = inputHLayout(self, 'Sweep steps', inputHLayout.InputType.SPINBOX, 19, inputRange=(0,1e4))
        hl.input.setToolTip('<i>number_calc</i><br>How many steps will be taken (<i>number_calc</i>), starting at 0 and incrementing by the energy'+\
                            ' or angle value given in the table. <b>Note, that the sweep feature is currently (6.01) not working as'+\
                            ' it is described in the documentation!</b>')
        self.nr_calc_label = hl.label
        self.nr_calc = hl.input
        self.nr_calc_label.hide()
        self.nr_calc.hide()

        outerHl.addLayout(hl)
        outerHl.addStretch(1)
        settingsGroupLayout.addLayout(outerHl)

        # Beam composition title and composition
        vl = VBoxTitleLayout(self, 'Beam composition', Styles.subTitleStyle, 0, True)
        self.beamComp = BeamCompTable(self)
        vl.addWidget(self.beamComp)
        settingsGroupLayout.addLayout(vl)

        # Add a parent to the settingslayout and add that to the splitter
        settingsParent = QWidget(self)
        settingsGroup = QGroupBox(self)
        settingsGroup.setLayout(settingsGroupLayout)
        settingsLayout.addWidget(settingsGroup)
        settingsParent.setLayout(settingsLayout)
        compositionSplitter.addWidget(settingsParent)
        #-----------------------------------------------------------------

        # TARGET SETTINGS
        # settingslayout = title + settingsgroup (with its own settingsgroup layout)
        settingsLayout = VBoxTitleLayout(self, 'Target Settings', Styles.titleStyle, 2, False)
        settingsGroupLayout = QVBoxLayout()
        settingsGroupLayout.setSpacing(5)
        settingsGroupLayout.setContentsMargins(12, 6, 12, 6)

        # General target settings
        outerHl = QHBoxLayout()
        hl = inputHLayout(self, 'Thickness [Å]:', inputHLayout.InputType.SPINBOX, 2000, inputRange=(1, 1e8))
        self.targetThickness = hl.input
        self.targetThickness.setToolTip('<i>ttarget</i><br>Thickness of the whole target')
        hl.addSpacing(10)
        outerHl.addLayout(hl)

        hl = inputHLayout(self, 'Target segments:', inputHLayout.InputType.SPINBOX, 200, inputRange=(1,1e8))
        self.targetSegmentsCount = hl.input
        self.targetSegmentsCount.setToolTip('<i>nqx</i><br>The amount of discrete segments the target is divided into')
        hl.addSpacing(10)
        outerHl.addLayout(hl)

        hl = inputHLayout(self, 'Segment thickness [Å]:', inputHLayout.InputType.DOUBLESPINBOX,
                          self.targetThickness.value()/self.targetSegmentsCount.value(), inputRange=(1e-8,1e8))
        self.segmentThickness = hl.input
        self.segmentThickness.setEnabled(False)
        self.segmentThickness.setDecimals(4)
        self.segmentThickness.setToolTip('The resulting thickness of each segment. A value >=10Å is recommended')
        hl.addSpacing(10)
        outerHl.addLayout(hl)

        hl = inputHLayout(self, '', inputHLayout.InputType.DOUBLESPINBOX, 0.0, inputRange=(1e-8,1e8))
        hl.setSpacing(0)
        self.globalDensity = hl.input
        self.globalDensity.setDecimals(5)
        self.enableGlobalDensity = QCheckBox('Global density [g/cm³]:', self)
        self.enableGlobalDensity.setToolTip('Toggle a global density, which the individual target element densities will be calculated from.'+\
                                            '\nCan only be used if there is just one layer in the target composition')
        hl.insertWidget(0, self.enableGlobalDensity)
        hl.addStretch(1)
        outerHl.addLayout(hl)

        settingsGroupLayout.addLayout(outerHl)

        # Target composition + target layers preview
        outerHl = QHBoxLayout()

        vl = VBoxTitleLayout(self, 'Target composition', Styles.subTitleStyle, 0, True)
        self.targetComp = TargetCompTable(self)
        vl.addWidget(self.targetComp)
        outerHl.addLayout(vl)

        # Target preview
        vl = VBoxTitleLayout(self, 'Preview', Styles.subTitleStyle, 0, 50)
        self.targetPreview = TargetPreview(self)
        # Expand vertically to keep the title label compact
        self.targetPreview.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        vl.addWidget(self.targetPreview)
        outerHl.addLayout(vl)
        settingsGroupLayout.addLayout(outerHl)

        # Target layers
        vl = VBoxTitleLayout(self, 'Target structure', Styles.subTitleStyle, 0, True)
        self.targetLayers = TargetLayersTable(self, self.targetThickness.value(), self.targetSegmentsCount.value())
        vl.addWidget(self.targetLayers)
        settingsGroupLayout.addLayout(vl)

        # Add a parent to the settingslayout and add that to the splitter
        settingsParent = QWidget(self)
        settingsGroup = QGroupBox(self)
        settingsGroup.setLayout(settingsGroupLayout)
        settingsLayout.addWidget(settingsGroup)
        settingsParent.setLayout(settingsLayout)
        compositionSplitter.addWidget(settingsParent)
        #-----------------------------------------------------------------

        # SIMULATION SETTINGS
        # settingslayout = title + settingsgroup (with its own settingsgroup layout)
        settingsLayout = VBoxTitleLayout(self, 'Simulation Settings', Styles.titleStyle, 0, False)
        settingsGroupLayout = QVBoxLayout()
        settingsGroupLayout.setSpacing(5)

        hl = inputHLayout(self, 'Simulation title:', inputHLayout.InputType.LINEEDIT, 'Choose a title...', 500)
        self.simulationTitle = hl.input
        self.simulationTitle.setToolTip('The first line of the <i>tri.inp</i> file')
        settingsGroupLayout.addLayout(hl)

        hl = inputHLayout(self, 'Calculation method:', inputHLayout.InputType.COMBOBOX,
                          2, entries=['static (no recoils)', 'dynamic', 'static', ])
        calcMethodTooltips = ['Suppression of dynamic relaxation and cascades; static calculation'+\
                              '(TRIM); only projectiles (no recoils) are followed',
                              'Full dynamic calculation (TRIDYN)',
                              'Suppression of dynamic relaxation (TRIM); full static calculation']
        self.calcMethod = hl.input
        self.calcMethod.setToolTip('<i>idrel</i>')
        for i in range(self.calcMethod.count()):
            self.calcMethod.setItemData(i, calcMethodTooltips[i], Qt.ToolTipRole)
        settingsGroupLayout.addLayout(hl)

        hl = inputHLayout(self, 'Histories:', inputHLayout.InputType.SPINBOX, 1000)
        self.historiesPerUpdate = hl.input
        self.historiesPerUpdate.setToolTip('<i>nh</i><br>How many histories will be simulated')
        settingsGroupLayout.addLayout(hl)

        hl = inputHLayout(self, 'Histories between outputs:', inputHLayout.InputType.SPINBOX, 10, (-1,1e8))
        self.historiesBetweenOutputs = hl.input
        self.historiesBetweenOutputs.setToolTip('<i>idout</i><br>How many histories are simulated between two outputs.\nSet to 0 to output only after the last fluence step')
        settingsGroupLayout.addLayout(hl)

        hl = QHBoxLayout()
        hl.setAlignment(Qt.AlignRight)
        self.limitOutputs = QCheckBox('Limit to a total of 100 outputs', self)
        hl.addWidget(self.limitOutputs)
        settingsGroupLayout.addLayout(hl)

        hl = inputHLayout(self, 'Projectiles per history:', inputHLayout.InputType.SPINBOX, 100)
        self.projectilesPerHistory = hl.input
        self.projectilesPerHistory.setToolTip('<i>nr_pproj</i><br>How many projectiles will be simulated per history')
        settingsGroupLayout.addLayout(hl)

        hl = inputHLayout(self, 'Fluence [atoms/Å<sup>2</sup>]:', inputHLayout.InputType.DOUBLESPINBOX, 1.00)
        self.fluence = hl.input
        self.fluence.setEnabled(False)
        self.fluence.setToolTip('<i>flc</i><br>Fluence of incident atoms. Can only be defined for dynamic calculations')
        settingsGroupLayout.addLayout(hl)

        potentials = ['1: KrC (default)', '2: Moliere', '3: ZBL', '4: Na-Ya', '5: Si-Si', '6: power']
        hl = inputHLayout(self, 'Interaction potential:', inputHLayout.InputType.COMBOBOX, 0, entries=potentials)
        self.interactPot = hl.input
        self.interactPot.setItemData(3, 'Nakagawa-Yamamura', Qt.ToolTipRole)
        self.interactPot.setToolTip('<i>ipot</i>')
        settingsGroupLayout.addLayout(hl)

        integrationMethods = ['0: Magic', '1: Gauss-Mehler', '2: Gauss-Legendre (default)']
        magicTooltip = 'Only allowed with the following interaction potentials: KrC, Moliere, and ZBL'
        hl = inputHLayout(self, 'Integration method:', inputHLayout.InputType.COMBOBOX, 2, entries=integrationMethods)
        self.integrationMethod = hl.input
        self.integrationMethod.setItemData(0, magicTooltip, Qt.ToolTipRole)
        self.integrationMethod.setToolTip('<i>iintegral</i>')
        settingsGroupLayout.addLayout(hl)

        surfaceBindingModels = [f'{i}' for i in range(1,8)]
        surfaceBindingModels[0] = surfaceBindingModels[0] + ': element-specific (default)'
        surfaceBindingModels[1] = surfaceBindingModels[1] + ': average for all elements'
        surfaceBindingModels[2] = surfaceBindingModels[2] + ': element-pair averages'
        surfaceBindingModels[3] = surfaceBindingModels[3] + ': solid-solid compound enthalpies'
        surfaceBindingModels[4] = surfaceBindingModels[4] + ': solid-gas compound enthalpies'
        surfaceBindingModels[5] = surfaceBindingModels[5] + ': from mat_surfb.inp'
        surfaceBindingModels[6] = surfaceBindingModels[6] + ': from electronegativity'
        surfaceBindingModelTooltips = ['sbv(ip,jp)=e_surfb(jp) for ip=jp',
                    'sbv(ip,jp)=e_surfb(jp) for all ip, jp',
                    'sbv(ip,jp)=0., if e_surfb(ip)=0 or e_surfb(jp)=0'+\
                    'else: sbv(ip,jp)=0.5*(e_surfb(ip)+e_surfb(jp))',
                    'sbv(ip,jp)=f(e_surfb, qu, deltahf) for solid/solid compound',
                    'sbv(ip,jp)=f(e_surfb, qu, deltahf, deltahd) for solid/gas compound',
                    'input of given matrix of the surface-bindig-energy: "mat_surfb.inp"',
                    'calculate according to "Kudriavtsev"']
        hl = inputHLayout(self, 'Surface binding model:', inputHLayout.InputType.COMBOBOX, 0, entries=surfaceBindingModels)
        self.surfaceBindingModel = hl.input
        for i in range(self.surfaceBindingModel.count()):
            self.surfaceBindingModel.setItemData(i, surfaceBindingModelTooltips[i], Qt.ToolTipRole)
        self.surfaceBindingModel.setToolTip('<i>isbv</i>')
        settingsGroupLayout.addLayout(hl)

        # empty space before output information
        settingsGroupLayout.addSpacing(10)
        # output information header label
        settingsGroupLayout.addWidget(QLabel('Additional output options:', self))
        # checkbox: reflected ions
        self.outputReflected = QCheckBox('Reflected projectiles', self)
        self.outputReflected.setToolTip('<i>lparticle_p</i><br>Compute the angle and energy distributions of reflected projectiles and write them to output files')
        settingsGroupLayout.addWidget(self.outputReflected)
        # checkbox: sputtered atoms
        self.outputSputtered = QCheckBox('Sputtered recoil atoms', self)
        self.outputSputtered.setToolTip('<i>lparticle_r</i><br>Compute the angle and energy distributions of sputtered recoil atoms and write them to output files')
        settingsGroupLayout.addWidget(self.outputSputtered)
        # checkbox: matrices
        self.outputMatrices = QCheckBox('Matrix files', self)
        self.outputMatrices.setToolTip('<i>lmatrices</i><br>Compute and write the pre-sorted secondary particle distributions to output files')
        settingsGroupLayout.addWidget(self.outputMatrices)
        # empty space after output information
        settingsGroupLayout.addSpacing(10)

        vl = VBoxTitleLayout(self, 'Additional Settings', Styles.subTitleStyle, 0, False)
        self.checkSettings = QPushButton(QIcon(':/icons/error_check.png'), '', self)
        self.checkSettings.setMaximumWidth(50)
        self.checkSettings.setToolTip('Check the settings for validity')
        vl.hl.addWidget(self.checkSettings)
        vl.setContentsMargins(0, 0, 0, 0)
        self.additionalSettings = QTextEdit(self)
        self.additionalSettings.setPlaceholderText('Add additional settings here which will be appended to the input file'+\
                                                   ', e.g.\n\nlenergy_distr = .true.')
        self.additionalSettings.setToolTip('Additional lines of settings which are appended to the end of the created input file')
        self.additionalSettings.setAcceptRichText(False)
        vl.addWidget(self.additionalSettings)
        self.elementOrder = QLabel('Element order: ', self)
        self.elementOrder.setToolTip('The order of the elements how they will be written to the input file.\n'+\
                                    'Useful when addressing individual elements by index in certain settings')
        vl.addWidget(self.elementOrder)
        settingsGroupLayout.addLayout(vl)
        settingsGroupLayout.addStretch(1)
        settingsGroupLayout.setAlignment(Qt.AlignRight)

        # Add a parent to the settingslayout and add that to the splitter
        settingsParent = QWidget(self)
        settingsGroup = QGroupBox(self)
        settingsGroup.setLayout(settingsGroupLayout)
        settingsLayout.addWidget(settingsGroup)
        settingsParent.setLayout(settingsLayout)
        settingsTabSplitter.addWidget(settingsParent)

        # Input and layer file preview
        splitter = QSplitter()

        parentWidget = QWidget(self)
        vl = VBoxTitleLayout(self, 'tri.inp', Styles.titleStyle, 0, False)
        self.inputFilePreview = QTextEdit(self)
        self.inputFilePreview.setReadOnly(True)
        vl.addWidget(self.inputFilePreview)
        parentWidget.setLayout(vl)
        splitter.addWidget(parentWidget)

        parentWidget = QWidget(self)
        vl = VBoxTitleLayout(self, 'layer.inp', Styles.titleStyle, 0, False)
        self.layerFilePreview = QTextEdit(self)
        self.layerFilePreview.setReadOnly(True)
        vl.addWidget(self.layerFilePreview)
        parentWidget.setLayout(vl)
        splitter.addWidget(parentWidget)

        self.tabWidget.addTab(splitter, 'Files preview')

        # SDTrimSP output log
        self.SDTrimSPoutput = QTextEdit(self)
        self.SDTrimSPoutput.setAcceptRichText(False)
        self.SDTrimSPoutput.setReadOnly(True)
        self.SDTrimSPoutput.setPlaceholderText('The output of the SDTrimSP simulation process will be shown here.\n'+\
            'It is also saved to "time_run.dat", which can be viewed in the next tab, "Output files".')
        self.tabWidget.addTab(self.SDTrimSPoutput, 'SDTrimSP log')

        # SDTrimSP output files + file preview
        splitter = QSplitter()

        parentWidget = QWidget(self)
        vl = VBoxTitleLayout(self, 'List of files', Styles.titleStyle, 0, False)
        self.refreshOutputFiles = QPushButton(QIcon(':/icons/refresh.png'), '', self)
        self.refreshOutputFiles.setMaximumWidth(50)
        self.refreshOutputFiles.setToolTip('Refresh the list')
        vl.hl.addWidget(self.refreshOutputFiles)
        self.openOutputFile = QPushButton(QIcon(':/icons/open_external.png'), '', self)
        self.openOutputFile.setMaximumWidth(50)
        self.openOutputFile.setToolTip('Open the selected file with the standard text editor')
        self.openOutputFile.setEnabled(False)
        vl.hl.addWidget(self.openOutputFile)

        self.outputFilesList = QListWidget(self)
        self.outputFilesList.setSelectionMode(QAbstractItemView.SingleSelection)
        vl.addWidget(self.outputFilesList)
        parentWidget.setLayout(vl)
        splitter.addWidget(parentWidget)

        # (file preview)
        parentWidget = QWidget(self)
        vl = VBoxTitleLayout(self, 'Output file preview', Styles.titleStyle, 0, False)
        self.outputFilePreview = QTextEdit(self)
        self.outputFilePreview.setReadOnly(True)
        vl.addWidget(self.outputFilePreview)
        hl = inputHLayout(self, 'Previewed lines:', inputHLayout.InputType.SPINBOX, 100, inputRange=(-1,5e3))
        hl.label.setMaximumWidth(100)
        hl.label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        hl.input.setMaximumWidth(50)
        hl.input.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.outputFilePreviewLines = hl.input
        vl.hl.addLayout(hl)
        parentWidget.setLayout(vl)
        splitter.addWidget(parentWidget)

        self.tabWidget.addTab(splitter, 'Output files')

        # Output Data and Plots
        splitter = QSplitter()

        parentWidget = QWidget(self)
        vl = VBoxTitleLayout(self, 'Available data for plotting', Styles.titleStyle, 0, False)
        self.refreshOutputParameters = QPushButton(QIcon(':/icons/refresh.png'), '', self)
        self.refreshOutputParameters.setMaximumWidth(50)
        self.refreshOutputParameters.setToolTip('Refresh the list')
        vl.hl.addWidget(self.refreshOutputParameters)
        self.savePlot = QPushButton(QIcon(':/icons/save.png'), '', self)
        self.savePlot.setMaximumWidth(50)
        self.savePlot.setToolTip('Save the data of the selected plot')
        self.savePlot.setEnabled(False)
        vl.hl.addWidget(self.savePlot)

        self.outputParametersList = QListWidget(self)
        self.outputParametersList.setSelectionMode(QAbstractItemView.SingleSelection)
        vl.addWidget(self.outputParametersList)
        parentWidget.setLayout(vl)
        splitter.addWidget(parentWidget)

        # output plots
        parentWidget = QWidget(self)
        vl = VBoxTitleLayout(self, 'Outputs & plots', Styles.titleStyle, 0, False)
        vl.title.setMaximumHeight(20)
        self.outputPlotView = MplCanvas(self, width=4, height=8, dpi=100)
        self.outputPlotToolbar = NavigationToolbar(self.outputPlotView, self)
        vl.addWidget(self.outputPlotView)
        vl.addWidget(self.outputPlotToolbar)

        hl = QHBoxLayout()
        tooltip = 'The history step which will be plotted, from 0 to (number of histories)/(histories between outputs), or <i>nh</i>/<i>idout</i>'
        hl2 = inputHLayout(self, 'History step   ', inputHLayout.InputType.SPINBOX, 0)
        self.historyStep = hl2.input
        self.historyStep.setToolTip(tooltip)
        self.historyStep.hide()
        self.historyStepLabel = hl2.label
        self.historyStepLabel.hide()
        hl.addLayout(hl2)
        self.historyStepSlider = QSlider(Qt.Horizontal, self)
        self.historyStepSlider.setMinimumWidth(200)
        self.historyStepSlider.setMinimum(0)
        self.historyStepSlider.setToolTip(tooltip)
        self.historyStepSlider.hide()
        hl.addWidget(self.historyStepSlider)
        hl.addStretch(1)
        vl.addLayout(hl)

        parentWidget.setLayout(vl)
        splitter.addWidget(parentWidget)

        self.tabWidget.addTab(splitter, 'Simulation results')
        self.setCentralWidget(self.tabWidget)
        #-----------------------------------------------------------------

        # Create the toolbar
        self.toolBar = self.addToolBar('Toolbar')
        self.toolBar.setFloatable(False)
        self.toolBar.setMovable(False)
        self.toolBar.setContextMenuPolicy(Qt.CustomContextMenu) # Disable the context menu of the toolbar itself
        self.toolBar.toggleViewAction().setEnabled(False) # Disable the action in the context menus of the main window

        self.newAction = self.toolBar.addAction(QIcon(':/icons/new.png'), 'New')
        self.newAction.setToolTip('Reset the window and the input fields to their default states')
        self.newAction.setShortcut(QKeySequence.New)
        self.openAction = self.toolBar.addAction(QIcon(':/icons/open.png'), 'Open')
        self.openAction.setToolTip('Open an existing SDTrimSP input file')
        self.openAction.setShortcut(QKeySequence.Open)
        self.saveAction = self.toolBar.addAction(QIcon(':/icons/save.png'), 'Save')
        self.saveAction.setToolTip('Save the current settings to an SDTrimSP input file')
        self.saveAction.setShortcut(QKeySequence.Save)
        self.saveAsAction = self.toolBar.addAction(QIcon(':/icons/save_as.png'), 'Save as...')
        self.saveAsAction.setToolTip('Save the current settings under a different name and/or in a different location')
        self.saveAsAction.setShortcut(QKeySequence.SaveAs)
        self.saveAsAction.setEnabled(False)
        self.preferencesAction = self.toolBar.addAction(QIcon(':/icons/preferences.png'), 'Preferences')
        self.preferencesAction.setToolTip('Open the preferences dialog')
        self.preferencesAction.setShortcut(QKeySequence.Preferences)
        self.toolBar.addSeparator()

        self.okayPixmap = QIcon(':/icons/okay.png').pixmap(32)
        self.warningPixmap = QIcon(':/icons/warning.png').pixmap(32)
        self.errorPixmap = QIcon(':/icons/error.png').pixmap(32)
        self.runStatusIcon = QLabel('')
        self.toolBar.addWidget(self.runStatusIcon)
        self.runStatusText = QLabel('')
        self.toolBar.addWidget(self.runStatusText)
        self.toolBar.addSeparator()

        self.runAction = self.toolBar.addAction(QIcon(':/icons/play.png'), 'Run')
        self.runAction.setToolTip('Save the current settings and run SDTrimSP on the input file')
        self.runAction.setShortcut(QKeySequence(Qt.CTRL+Qt.Key_R))
        self.runProgress = QProgressBar(self)
        self.runProgress.setToolTip('The progress of the simulation')
        self.runProgress.setMinimumWidth(50)
        self.runProgress.setMaximumWidth(400)
        self.toolBar.addWidget(self.runProgress)
        self.abortAction = self.toolBar.addAction(QIcon(':/icons/abort.png'), 'Abort')
        self.abortAction.setToolTip('Abort the currently active simulation')
        self.abortAction.setShortcut(QKeySequence(Qt.CTRL+Qt.Key_P))
        self.abortAction.setEnabled(False)
        self.toolBar.addSeparator()
        self.runDetachedAction = self.toolBar.addAction(QIcon(':/icons/play_detached.png'), 'Run Detached')
        self.runDetachedAction.setToolTip('Save the current settings and run SDTrimSP on the input file in detached mode.\n'+\
                'The simulation is run in a separate window, and the GUI can even be closed')
        self.runDetachedAction.setShortcut(QKeySequence(Qt.CTRL+Qt.SHIFT+Qt.Key_R))
        self.toolBar.addSeparator()

        # Add empty space
        empty = QWidget()
        empty.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolBar.addWidget(empty)

        # open working directory button
        self.openWorkingDir = self.toolBar.addAction(QIcon(':/icons/open_workdir.png'), 'Open working directory')
        self.openWorkingDir.setToolTip('Open the working directory in the file explorer')

        # open docs button
        self.openDocsAction = self.toolBar.addAction(QIcon(':/icons/book.png'), 'SDTrimSP documentation')
        self.openDocsAction.setToolTip('Open the SDTrimSP documentation PDF with the standard PDF viewer')
        self.openDocsAction.setShortcut(QKeySequence.HelpContents)
        self.openDocsAction.setEnabled(False)
        #-----------------------------------------------------------------

        # Create the menu bar
        menu = self.menuBar()
        fileMenu = menu.addMenu('&File')
        fileMenu.setToolTipsVisible(True)
        fileMenu.addAction(self.newAction)
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.saveAsAction)
        fileMenu.addAction(self.preferencesAction)
        fileMenu.addSeparator()
        self.quitAction = fileMenu.addAction('Quit')
        self.quitAction.setToolTip('Quit the program')
        self.quitAction.setShortcut(QKeySequence.Quit)
        fileMenu.addAction(self.quitAction)

        simMenu = menu.addMenu('&Simulation')
        simMenu.setToolTipsVisible(True)
        simMenu.addAction(self.runAction)
        simMenu.addAction(self.runDetachedAction)
        simMenu.addAction(self.abortAction)

        helpMenu = menu.addMenu('&Help')
        helpMenu.setToolTipsVisible(True)
        helpMenu.addAction(self.openDocsAction)
        self.aboutAction = helpMenu.addAction('About')
        helpMenu.addAction(self.aboutAction)

        self.setMenuBar(menu)

    def setupSignals(self):
        # Enable/Disable inputs based on other settings
        self.kinEnergyType.currentIndexChanged.connect(lambda idx: self.beamTypeChanged(self.kinEnergyType, idx))
        self.angleType.currentIndexChanged.connect(lambda idx: self.beamTypeChanged(self.angleType, idx))
        self.calcMethod.currentIndexChanged.connect(self.calcMethodChanged)
        self.limitOutputs.stateChanged.connect(lambda stat: self.historiesBetweenOutputs.setEnabled(stat==0))
        self.interactPot.currentIndexChanged.connect(self.interactPotentialChanged)

        # Dis-/Enable certain inputs for elements in the beam also present in the target
        self.targetComp.rowRemoved.connect(lambda: self.beamComp.updateSyncedFields(self.targetComp.rows))
        self.targetComp.elementChanged.connect(lambda: self.beamComp.updateSyncedFields(self.targetComp.rows))
        self.beamComp.elementChanged.connect(lambda: self.beamComp.updateSyncedFields(self.targetComp.rows))

        # Update synced parameters for elements which occur both in the beam and the target
        self.targetComp.syncableValueChanged.connect(self.beamComp.updateSyncedValue)

        # Open periodic table dialog when clicking an element
        self.targetComp.elementClicked.connect(lambda row: self.openPeriodicTableDialog(row, self.targetComp))
        self.beamComp.elementClicked.connect(lambda row: self.openPeriodicTableDialog(row, self.beamComp))

        # Update the element indices
        self.beamComp.rowRemoved.connect(lambda: self.updateElementIndices())
        self.targetComp.rowRemoved.connect(lambda: self.updateElementIndices())
        self.beamComp.elementChanged.connect(lambda: self.updateElementIndices())
        self.targetComp.elementChanged.connect(lambda: self.updateElementIndices())
        self.beamComp.rowAdded.connect(self.setNewElementIndex)
        self.targetComp.rowAdded.connect(self.setNewElementIndex)

        # Have a column in the target layers table for each element in the target composition table
        self.targetComp.rowAdded.connect(self.targetLayers.addElementColumn)
        self.targetComp.rowRemoved.connect(lambda idx: self.targetLayers.removeElementColumn(idx))

        # Update target layers table limits and values based on other settings
        self.targetThickness.valueChanged.connect(lambda val: self.segmentThickness.setValue(val/self.targetSegmentsCount.value()))
        self.targetSegmentsCount.valueChanged.connect(self.targetLayers.setTargetSegmentsCount)
        self.targetSegmentsCount.valueChanged.connect(lambda val: self.segmentThickness.setValue(self.targetThickness.value()/val))
        self.segmentThickness.valueChanged.connect(lambda value: self.targetLayers.setSegmentThickness(value))
        self.segmentThickness.valueChanged.connect(lambda value: setWidgetHighlight(self.segmentThickness, value<10))

        # Update the target preview
        self.targetComp.elementChanged.connect(lambda r,el:\
               self.targetLayers.renameElementColumn(self.targetComp.rows.index(r), el.symbol))
        self.targetLayers.layersChanged.connect(self.targetPreview.setTargetInfo)

        # Open the working dir and the docs
        self.openWorkingDir.triggered.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(self.workingDir)))
        self.openDocsAction.triggered.connect(self.openDocs)

        # Run SDTrimSP
        self.runAction.triggered.connect(lambda: self.runSDTrimSP(runDetached=False))
        self.runDetachedAction.triggered.connect(lambda: self.runSDTrimSP(runDetached=True))
        self.abortAction.triggered.connect(lambda: self.process.kill())

        # Output file preview
        self.outputFilesList.itemSelectionChanged.connect(self.previewSelectedFile)
        self.outputFilePreviewLines.editingFinished.connect(self.updateOutputFilesList)
        self.refreshOutputFiles.clicked.connect(self.updateOutputFilesList)
        self.openOutputFile.clicked.connect(self.openSelectedOutputFile)

        # Set the output parameters plot
        self.outputParametersList.itemSelectionChanged.connect(self.plotSelectedOutput)
        self.refreshOutputParameters.clicked.connect(self.updateOutputParametersList)
        self.savePlot.clicked.connect(self.saveSelectedPlot)

        # Update certain tab widget contents when the active tab changes
        self.tabWidget.currentChanged.connect(self.updateTabWidget)

        # Check for errors in the additional settings
        self.checkSettings.clicked.connect(lambda: self.showAdditionalSettingsMessage(self.createSettingsObject(False)[1]))
        self.additionalSettings.textChanged.connect(lambda: setWidgetHighlight(self.additionalSettings, len(self.createSettingsObject(False)[1]) > 0))

        # Update the element densities according to the global atomic density
        self.enableGlobalDensity.stateChanged.connect(lambda state: self.setGlobalDensityEnabled(state==Qt.Checked))
        self.globalDensity.valueChanged.connect(lambda: self.updateGlobalDensity())
        self.targetLayers.layersChanged.connect(lambda: self.enableGlobalDensity.setEnabled(len(self.targetLayers.rows)==1))
        self.targetComp.rowAdded.connect(lambda: self.updateGlobalDensity())
        self.targetComp.rowRemoved.connect(lambda: self.updateGlobalDensity())
        self.targetComp.elementChanged.connect(lambda: self.updateGlobalDensity())
        self.targetLayers.layersChanged.connect(lambda: self.updateGlobalDensity())

        # Menu actions
        self.newAction.triggered.connect(lambda: self.resetSettings(createFirstRows=True))
        self.openAction.triggered.connect(lambda: self.loadFiles())
        self.saveAction.triggered.connect(lambda: self.saveFiles())
        self.saveAsAction.triggered.connect(lambda: self.saveFiles(selectFolder=True))
        self.preferencesAction.triggered.connect(lambda: self.preferences.open())
        self.quitAction.triggered.connect(self.close)
        self.aboutAction.triggered.connect(lambda: AboutDialog(self, self.gui_version).open())

        # Detect changes
        for sb in self.defSpinBoxes:
            sb.valueChanged.connect(lambda: self.setWindowModified(True))
        for cb in self.defComboBoxes:
            cb.currentIndexChanged.connect(lambda: self.setWindowModified(True))
        for cb in self.defCheckBoxes:
            cb.stateChanged.connect(lambda: self.setWindowModified(True))
        self.additionalSettings.textChanged.connect(lambda: self.setWindowModified(True))
        self.simulationTitle.textChanged.connect(lambda: self.setWindowModified(True))
        self.beamComp.contentChanged.connect(lambda: self.setWindowModified(True))
        self.targetComp.contentChanged.connect(lambda: self.setWindowModified(True))
        self.targetLayers.contentChanged.connect(lambda: self.setWindowModified(True))

        # Fluence slider
        self.historyStep.valueChanged.connect(self.historyStepSlider.setValue)
        self.historyStepSlider.valueChanged.connect(self.historyStep.setValue)
        self.historyStep.valueChanged.connect(lambda _: self.updateDepthConcPlot())
        self.historyStepSlider.valueChanged.connect(lambda _: self.updateDepthConcPlot())

    def calcMethodChanged(self, index):
        self.fluence.setEnabled(index == 1)
        #self.projectilesPerHistory.setEnabled(index == 1)
        self.beamComp.setConcentrationEditable(index == 1)
        self.targetComp.setConcentrationEditable(index == 1)
        self.outputMatrices.setEnabled(index != 1)
        if index == 1:
            self.outputMatrices.setChecked(False)

    def interactPotentialChanged(self, index):
        self.integrationMethod.model().item(0,0).setEnabled(index <= 2)
        if index > 2 and self.integrationMethod.currentIndex() == 0:
            self.integrationMethod.setCurrentIndex(2)

    def beamTypeChanged(self, beamType, newIdx):
        if beamType == self.kinEnergyType:
            self.beamComp.setKinEnergyEditable(newIdx in [0, 2, 3, 5])
            otherBeamType = self.angleType
        elif beamType == self.angleType:
            self.beamComp.setAngleEditable(newIdx in [0, 5])
            otherBeamType = self.kinEnergyType

        # Handle sweeps
        self.outputReflected.setEnabled(newIdx!=5)
        self.outputSputtered.setEnabled(newIdx!=5)
        self.outputMatrices.setEnabled(newIdx!=5)
        otherBeamType.setEnabled(newIdx!=5)
        if newIdx == 5:
            self.outputReflected.setChecked(False)
            self.outputSputtered.setChecked(False)
            self.outputMatrices.setChecked(False)
            otherBeamType.setCurrentIndex(0)
        self.nr_calc_label.setVisible(newIdx == 5)
        self.nr_calc.setVisible(newIdx == 5)
        if newIdx == 5 and beamType == self.kinEnergyType:
            self.nr_calc.setValue(18)
        elif newIdx == 5 and beamType == self.angleType:
            self.nr_calc.setValue(19)

        # Handle 'ene_ang.inp'
        if newIdx == 6:
            if otherBeamType.currentIndex() != 6:
                otherBeamType.setCurrentIndex(6)
                otherBeamType.setEnabled(False)
        elif otherBeamType.currentIndex() == 6:
            otherBeamType.setCurrentIndex(0)

    def setupWindowGeometry(self):
        settings = QSettings()
        w = settings.value('mainWindowWidth', 1100, type=int)
        h = settings.value('mainWindowHeight', 800, type=int)
        self.resize(w, h)
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
