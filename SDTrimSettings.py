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
from TableWidgets.TargetLayersTable import TargetLayerEntry
import re
from math import copysign

class InputSettings():
    # A list of all variables recognized by SDTrimSP (filled by MainWindow.py)
    allVarNames = None

    # A list of all variable names (SDTrimSP and custom GUI ones) which are recognized by the GUI
    varNames = ['ncp', 'symbol', 'dns0', 'e_surfb', 'e_displ','occurrence', 'globaldensity', 'inel0', 'nh', 'idout', 'nr_pproj', 'flc',
                'idrel', 'ipot', 'iintegral', 'isbv', 'qubeam', 'case_e0', 'e0', 'case_alpha', 'alpha0', 'number_calc',
                'qu', 'qumax', 'ttarget', 'nqx', 'iq0', 'lparticle_p', 'lparticle_r', 'lmatrices']
    # Custom variables used for the GUI only (these are always preceded by a '!' in the input file)
    customVars = ['globaldensity', 'occurrence']
    # Default values used when a value is missing in the loaded input file
    defaultValues = {'ncp': 2, 'symbol': 'H', 'dns0': None, 'e_surfb': None, 'e_displ': None, 'globaldensity': [False, 0.0], 'inel0': 3.0,
                     'nh': 1e3, 'idout': -1, 'nr_pproj': 10, 'flc': 1,
                     'idrel': 1, 'ipot': 0, 'iintegral': 2, 'isbv': 0, 'qubeam': 1 , 'case_e0': 0, 'e0': 0, 'case_alpha': 0, 'alpha0': 0, 'number_calc': 19,
                     'qu': 1, 'qumax': 1, 'ttarget': 2000, 'nqx': 0, 'iq0': 0, 'lparticle_p': False, 'lparticle_r': False, 'lmatrices': False}
    # Allowed value ranges for comboboxes
    validRange = {'inel0': (1,6), 'iintegral': (0,2), 'case_e0': (0, 6), 'case_alpha': (0, 6), 'isbv': (1,7), 'ipot': (1,6)}
    # Variables whose name starts with any of the ones in 'ignoredVars' are ignored when an input file is loaded
    ignoredVars = ['ioutput_part', 'tableinp']
    # Which of the 'varNames' are expected to be lists
    listVars = ['symbol', 'dns0', 'e_surfb', 'e_displ', 'inel0', 'qubeam', 'e0', 'alpha0', 'qu', 'qumax']
    # Which of the 'varNames' are expected to be (Fortran) booleans
    boolVars = ['lparticle_p', 'lparticle_r', 'lmatrices']
    # The 'varNames' (keys) which are the beginning of a new block and the corresponding block titles (values)
    blockStarts = {'nh': 'general', 'qubeam': 'beam', 'qu': 'target', 'lparticle_p': 'output options'}

    def setVars(self, title, ncp, symbol, dns0, e_surfb, e_displ, occurrence, globaldensity, inel0, nh, idout, nr_pproj, flc,
                 idrel, ipot, iintegral, isbv, qubeam, case_e0, e0, case_alpha, alpha0, number_calc,
                 qu, qumax, ttarget, nqx, iq0, lparticle_p, lparticle_r, lmatrices, additionalSettings=[]):
        self.title = title
        self.vars = [ncp, symbol, dns0, e_surfb, e_displ, occurrence, globaldensity, inel0, nh, idout, nr_pproj, flc,
                     idrel, ipot, iintegral, isbv, qubeam, case_e0, e0, case_alpha, alpha0, number_calc,
                     qu, qumax, ttarget, nqx, iq0, lparticle_p, lparticle_r, lmatrices]
        self.additionalSettings = additionalSettings

    def __call__(self, varName):
        if varName in InputSettings.varNames:
            return self.vars[InputSettings.varNames.index(varName)]
        return None

    '''Extract the settings variables from the given GUI elements and their user-defined properties
    and stores them in this instance's variables'''
    def extractVariables(self, symbols, beamComp, targetComp, targetLayers, title, historiesPerUpdate,
                         historiesBetweenOutputs, projectilesPerHistory, fluence, calcMethod,
                         interactPot, integrationMethod, surfaceBindingModel, kinEnergyType,
                         angleType, number_calc, targetThickness, targetSegmentsCount, enableGlobalDensity,
                         globalDensity, outputReflected, outputSputtered, outputMatrices, additionalSettings):

        customDensities = not all([entry.element.atomic_density == entry.atomicDensity for entry in beamComp+targetComp])
        customSurfBindEnergies = not all([entry.element.surface_binding_energy == entry.surfBindEnergy for entry in beamComp+targetComp])
        customDisplEnergies = not all([entry.element.displacement_energy == entry.displEnergy for entry in beamComp+targetComp])

        inel0, qubeam, e0, alpha0, qu, qumax, dns0, e_surfb, e_displ, occurrence = [], [], [], [], [], [], [], [], [], []

        # These two are needed later for creating the layers file content
        self.allAbundances = [[] for _ in range(len(targetLayers))]
        self.targetLayers = targetLayers

        for symbol in symbols:
            beamIdx = -1
            for i,b in enumerate(beamComp):
                if b.element.symbol == symbol:
                    beamIdx = i
                    break
            targetIdx = -1
            for i,t in enumerate(targetComp):
                if t.element.symbol == symbol:
                    targetIdx = i
                    break

            inBeam = beamIdx >= 0
            inTarget = targetIdx >= 0
            # Occurrence flags: 10..only beam, 01..only target, 11..both
            occurrence.append(f'{int(inBeam)}{int(inTarget)}')
            bc = beamComp[beamIdx] if inBeam else None
            tc = targetComp[targetIdx] if inTarget else None

            inel0.append(bc.inelLossModel+1 if inBeam else tc.inelLossModel+1)
            qubeam.append(bc.abundance if inBeam else 0.0)
            e0.append(bc.kinEnergy if inBeam else 0.0)
            alpha0.append(bc.angle if inBeam else 0.0)
            qumax.append(bc.maxConcentration if inBeam else tc.maxConcentration)
            qu.append(targetLayers[0].abundances[targetIdx] if inTarget else 0.0)
            if customDensities:
                dns0.append(tc.atomicDensity if inTarget else bc.atomicDensity)
            if customSurfBindEnergies:
                e_surfb.append(tc.surfBindEnergy if inTarget else bc.surfBindEnergy)
            if customDisplEnergies:
                e_displ.append(tc.displEnergy if inTarget else bc.displEnergy)

            for i,layer in enumerate(targetLayers):
                a = 0.0 if not inTarget else layer.abundances[targetIdx]
                self.allAbundances[i].append(a)

        nqx = targetSegmentsCount
        iq0 = -1 if len(targetLayers)>1 else 0

        lparticle_p = outputReflected
        lparticle_r = outputSputtered
        lmatrices = outputMatrices

        ncp = len(symbols)
        globaldensity = [enableGlobalDensity.isChecked(), globalDensity.value()]

        self.setVars(title, ncp, symbols, dns0, e_surfb, e_displ, occurrence, globaldensity, inel0, historiesPerUpdate, historiesBetweenOutputs,
                projectilesPerHistory, fluence, calcMethod, interactPot, integrationMethod,
                surfaceBindingModel, qubeam, kinEnergyType, e0, angleType, alpha0, number_calc,
                qu, qumax, targetThickness, nqx, iq0, lparticle_p, lparticle_r, lmatrices, additionalSettings)

    def checkForAdditionalSettingErrors(self):
        errors, foundDuplicates = [], {}
        for i,a in enumerate(self.additionalSettings):
            if a.count('=') != 1:
                errors.append(f'Line {i}: missing or too many "="')
            elif len(a.split('=')[1].strip()) == 0:
                errors.append(f'Line {i}: missing variable value')

            var = a.split('=')[0].strip()
            if var.count('(') != var.count(')'):
                errors.append(f'Line {i}: parentheses do not match')

            # Ignore parentheses for variable name checks
            var = var.split('(')[0].strip()
            if InputSettings.allVarNames is not None and var not in InputSettings.allVarNames:
                errors.append(f'Line {i}: unknown variable "{var}"')
        return errors

    class FileType(Enum):
        INPUT = 1
        LAYERS = 2

    def writeToFile(self, filePath, fileType):
        assert isinstance(fileType, InputSettings.FileType)
        with open(filePath, 'w') as f:
            if fileType == InputSettings.FileType.INPUT:
                content = self.getWriteInputFileString()
            elif fileType == InputSettings.FileType.LAYERS:
                content = self.getWriteLayersFileString()

            # necessary to make it work under linux
            content_split = content.split("\n")
            for line in content_split:
                f.write(line)
                f.write("\n")

    def getHeader(title):
        return f"""text='---{title}---'"""

    '''Returns the string as it will be written to the input file'''
    def getWriteInputFileString(self):
        content = f'{self.title}\n&TRI_INP'
        content += f"""\n{InputSettings.getHeader('elements')}\n"""

        for i,v in enumerate(self.vars):
            n = InputSettings.varNames[i]

            # Ignore the element atomic density or surface binding energy if it doesn't contain any values
            # i.e. the default values from table1 are used
            if n in ['dns0', 'e_surfb', 'e_displ'] and len(v) == 0:
                continue

            if n in InputSettings.blockStarts:
                header = InputSettings.getHeader(InputSettings.blockStarts[n])
                content += f'\n{header}\n'

            # adapt boolean to Fortran boolean
            if n in InputSettings.boolVars:
                if n == 'lparticle_p' and v:
                    output_part_p = int(self('nh') * self('nr_pproj')) # nh * nr_pproj --> to make sure that all reflected projectiles are written in the output file
                    content += f'\tioutput_part(2) = {output_part_p}\n'
                elif n == 'lparticle_r' and v:
                    output_part_r = int(100 * self('nh') * self('nr_pproj')) # 100 * nh * nr_pproj --> to make sure that all sputtered particles are written in the output file
                    content += f'\tioutput_part(5) = {output_part_r}\n'
                v = '.true.' if v else '.false.'

            isList = n in InputSettings.listVars
            if n in InputSettings.customVars:
                n = '!'+n # Start custom GUI variables with a comment indicator
                isList = True
            if n == 'symbol':
                v = [f'"{s}"' for s in v] # Add quotes to the element symbols
            if n == 'number_calc' and self('case_e0') != 5 and self('case_alpha') != 5:
                continue # Skip number_calc if not used
            content += f'\t{n} = {", ".join(map(str, v)) if isList else v}\n'

        if len(self.additionalSettings) > 0:
            content += f"""\n{InputSettings.getHeader('extra')}\n"""
            for l in self.additionalSettings:
                content += f'\t{l}\n'
        content += '\n/'
        return content

    def getWriteLayersFileString(self):
        layersSegments, thicknesses, layerNames = [], [], []
        for l in self.targetLayers:
            layersSegments.append(l.segmentCount)
            thicknesses.append(l.segmentThickness)
            layerNames.append(l.layerName)

        content = 'number of\tthick-\ttarget composition 2...ncp\tname of layer\n'

        ncp = self('ncp')
        elementTitles = ''.join([f'qu_{i+2}\t' for i in range(ncp-1)])
        content += f'layers\t\tness\t{elementTitles}\n'
        for i in range(len(layersSegments)):
            abundanceString = ''.join([f'{self.allAbundances[i][j]:.2f}\t' for j in range(1, ncp)])
            content += f'{layersSegments[i]:6}\t\t{thicknesses[i]:.2f}\t{abundanceString}\t{layerNames[i]}\n'

        zeros = ''.join([f'{0:.2f}\t' for _ in range(ncp-1)])
        content += f'{0:6}\t\t{0:.2f}\t{zeros}\tend'
        return content

def checkValueRange(varName, val):
    if varName not in InputSettings.validRange:
        return val, ''
    l, u = InputSettings.validRange[varName]
    if (l is not None and val < l) or (u is not None and val > u):
        if u is not None:  # Clamp to range
            val = min(u, val)
        if l is not None:
            val = max(l, val)
        return val, f'Value {val} for variable "{varName}" was clamped to allowed range [{l},{u}] (line {lineNr + 2})'
    return val, ''

def loadInputFile(filePath, elementData):
    additionalSettings = []
    alerts = []
    with open(filePath, 'r') as f:
        title = f.readline().strip()
        v = [None for _ in InputSettings.varNames] # One entry for each expected variable
        for lineNr, line in enumerate(f):
            content = [p.strip() for p in line.strip().split('=')]

            varName = content[0]
            if varName == 'text' or len(content) < 2:
                continue
            if varName[0] == '!':
                varName = varName[1:]
                if varName not in InputSettings.customVars:
                    continue
            if any(varName.startswith(var) for var in InputSettings.ignoredVars):
                continue

            # Check for parentheses with an element index
            elementIndex = None
            result = re.findall("\(\d+\)", varName)
            if len(result) > 0:
                elementIndex = int(result[0][1:-1])
            varName = varName.split('(')[0] # The variable name without possible parentheses

            unknownVar = False
            if InputSettings.allVarNames is not None:
                unknownVar = varName not in InputSettings.allVarNames + InputSettings.customVars
            if unknownVar:
                alerts.append(f'Unknown variable "{varName}" (line {lineNr+2})')
            if unknownVar or varName not in InputSettings.varNames:
                additionalSettings.append(line.strip())
                continue

            idx = InputSettings.varNames.index(varName)
            # Take the right side of the '=' until a possible '!' (comment start indicator)
            # Then split the remains into multiple values, expecting them to be separated by ','
            data = content[1].split('!')[0].split(',')
            data = [d.strip() for d in data] # Remove whitespaces
            try:
                if varName == 'occurrence':
                    v[idx] = [[int(d[0])==1, int(d[1])==1] for d in data]
                elif varName == 'globaldensity':
                    v[idx] = [data[0]=='True', float(data[1])]
                elif varName in InputSettings.listVars:
                    if v[idx] is None:
                        v[idx]= [] # Initialize the list
                    if elementIndex is not None:
                        # Add the value at the element's position in the array
                        while len(v[idx]) <= elementIndex-1:
                            v[idx].append(None)
                        if varName == 'symbol':
                            v[idx][elementIndex - 1] = data[0].replace('"', '').strip()
                            if elementData.elementFromSymbol(s) is None:
                                alerts.append(f'Element symbol "{s}" (#{elementIndex}) unknown, replaced with "H" (line {lineNr + 2})')
                                v[idx][elementIndex - 1] = 'H'
                        else:
                            v[idx][elementIndex - 1] = float(data[0])
                    elif varName == 'symbol':
                        v[idx] = [s.replace('"', '').strip() for s in data]
                        for i, s in enumerate(v[idx]):  # Check for valid element symbols
                            if elementData.elementFromSymbol(s) is None:
                                alerts.append(f'Element symbol "{s}" (#{i + 1}) unknown, replaced with "H" (line {lineNr + 2})')
                                v[idx][i] = 'H'
                    else:
                        v[idx] = [float(d) for d in data]

                    for val in v[idx]:
                        val, msg = checkValueRange(varName, val)
                        if len(msg) > 0:
                            alerts.append(msg)
                elif varName in InputSettings.boolVars:
                    v[idx] = str.lower(data[0]) == '.true.'
                else:
                    val = float(data[0])
                    if varName == 'idrel' and val != 0: # Only take the sign, since all numbers are allowed according to the docs
                        val = int(copysign(1, val))
                    elif varName == 'case_e0' and val == 4: # Prevent the unused value 4
                        alerts.append('case_e0=4 is not a valid choice - changed to 0 (line {lineNr+2})')
                        val = 0
                    val, msg = checkValueRange(varName, val)
                    if len(msg) > 0:
                        alerts.append(msg)
                    v[idx] = val
            except:
                alerts.append(f'Failed to read data for variable "{varName}" (line {lineNr+2})')
                v[idx] = None

    # Check for variables which were not found
    for idx in range(len(v)):
        varName = InputSettings.varNames[idx]
        if varName not in InputSettings.defaultValues:
            continue
        defaultVar = InputSettings.defaultValues[varName]

        if varName in InputSettings.listVars:
            if v[idx] is None: # If the variable wasn't found at all, fill it with the default value
                if varName not in ['dns0', 'e_surfb', 'e_displ']: # Don't alert for certain variables
                    alerts.append(f'Variable "{varName}" missing! Filled with default values "{defaultVar}"')
                v[idx] = [defaultVar for _ in range(int(v[0]))]
            else: # Replace None-entries with default values
                while len(v[idx]) < int(v[0]):  # Extend list to (ncp) length
                    v[idx].append(None)
                for i, val in enumerate(v[idx]):
                    if val is None:
                        # print(f'Fill "{varName}" ({v[idx]}) with {defaultVar} at index {i}')
                        v[idx][i] = defaultVar
        elif v[idx] is None: # If the variable wasn't found at all, set it to the default value
            if varName not in InputSettings.boolVars + InputSettings.customVars: # Don't alert for missing output or custom values
                # Don't alert for number_calc if it is not required
                if varName != 'number_calc' or (v[InputSettings.varNames.index('case_e0')] == 5 or v[InputSettings.varNames.index('case_alpha')] == 5):
                    alerts.append(f'Variable "{varName}" missing! Set to default value "{defaultVar}"')
            v[idx] = defaultVar

    # Check for invalid combinations
    for varName in InputSettings.boolVars:
        idx = InputSettings.varNames.index(varName)
        if not v[idx]:
            continue
        if v[InputSettings.varNames.index('case_e0')] == 5:
            alerts.append(f'{varName}=.true. not allowed for case_e0=5 - changed to .false.')
            v[idx] = False
        elif v[InputSettings.varNames.index('case_alpha')] == 5:
            alerts.append(f'{varName}=.true. not allowed for case_alpha=5 - changed to .false.')
            v[idx] = False
        if varName == 'lmatrices' and v[InputSettings.varNames.index('idrel')] == 0:
            alerts.append('lmatrices=.true. not allowed for idrel=0 - changed to .false.')
            v[idx] = False
    idx = InputSettings.varNames.index('iintegral')
    if v[idx] == 0 and InputSettings.varNames.index('ipot') > 3:
        alerts.append('iintegral=0 not allowed for ipot>3 - changed to 2')
        v[idx] = 2

    s = InputSettings()
    s.setVars(title, *v, additionalSettings)
    return s, alerts

def loadLayersFile(filePath):
    with open(filePath, 'r') as f:
        f.readline()
        ncp_sub1 = len(f.readline().split()[2:])
        splitLines = [line.strip().split() for line in f][:-1]

    targetLayers = []
    for l in splitLines:
        allAbundances = [float(v) for v in l[2:2+ncp_sub1]]
        allAbundances.insert(0, 1-sum(allAbundances)) # add the missing element's abundance
        layerEntry = TargetLayerEntry(int(l[0]), float(l[1]), allAbundances, ' '.join(l[2+ncp_sub1:]))
        targetLayers.append(layerEntry)
    return targetLayers