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


class Element:
    def __init__(self, symbol, periodicTableSymbol, atomic_nr, atomic_mass, mass_density,
                         atomic_density, surface_binding_enery, displacement_energy,
                         cutoff_energy, dissociation_heat, melt_enthalpy, vaporization_energy,
                         formation_enthalpy, name, period, group):
        self.symbol = symbol
        self.periodicTableSymbol = periodicTableSymbol
        self.atomic_nr = atomic_nr
        self.atomic_mass = atomic_mass
        self.mass_density = mass_density
        self.atomic_density = atomic_density
        self.surface_binding_energy = surface_binding_enery
        self.displacement_energy = displacement_energy
        self.cutoff_energy = cutoff_energy
        self.dissociation_heat = dissociation_heat
        self.melt_enthalpy = melt_enthalpy
        self.vaporization_energy = vaporization_energy
        self.formation_enthalpy = formation_enthalpy
        self.name = name
        self.period = period
        self.group = group

    """The information string displayed in the periodic table dialog when hovering over the element"""
    def getInfoString(self):
        return f'{self.name} ({self.symbol}, #{self.atomic_nr}, period {self.period}, group {self.group})'+\
            f', {self.atomic_mass} atomic mass, {self.atomic_density} atomic density'

class SDTrimElementData:
    def __init__(self):
        self.elements = []
        self.periodIncrease = [3, 11, 19, 37, 55, 87]

    def tryLoadElementTable(self, table1Path):
        self.elements = []
        period = 1
        try:
            f = open(table1Path, 'r', encoding='cp1250')
        except:
            return False
        content = '!'
        while content == '!':
            last_pos = f.tell()
            content = f.readline()[0]
        f.seek(last_pos) # Go back to the previous line after the comment section is over
        group, lastAtomicNr = 0, 0
        symbol = ''
        while symbol != 'Lr':
            l = [x.strip() for x in f.readline().split()]
            if len(l) == 0:
                continue

            symbol = l[0]
            # How the element's symbol will be shown in the periodic table
            periodicTableSymbol = l[0].split('_')[0][:2]
            atomicNr = int(l[1])

            # Skip the weird elements
            if atomicNr > lastAtomicNr + 1:
                continue

            # Francium is missing a decimal point in its vaporization energy
            if symbol == 'Fr':
                l[10:12] = [l[10]+'.'+l[11]]
            # Polonium and astatine are missing a decimal point in their formation enthalpy
            elif symbol in ['Po', 'At']:
                l[11:13] = [l[11]+'.'+l[12]]

            l[2:11] = [float(v) for v in l[2:11]]

            name = str.capitalize(' '.join(l[17:]))
            if '_' in name: # Build a nice name for versions 6.05 onward
                parts = name.split('_')
                name = str.capitalize(' '.join(parts[1:])) + ' (' + parts[0] + ')'
            if len(name.strip()) == 0: # fallback for older version
                name = str.capitalize(' '.join(l[16:]))

            if atomicNr != lastAtomicNr:
                group += 1
            if atomicNr in self.periodIncrease:
                period += 1
                group = 1

            if atomicNr == 2: # H -> He
                group = 18
            elif atomicNr in [5, 13]: #Be/Mg -> B/Al
                group = 13
            elif atomicNr in [57, 89]: # show Lantha/Acti two rows down
                period += 2
            elif atomicNr in [71, 103]: # go back up after Lantha/Acti
                period -= 2
                group = 3

            # Note that the period also defines the element's position in the periodic table
            # in case you want to correct the period of Lantha/Acti elements
            e = Element(symbol, periodicTableSymbol, atomicNr, l[2], l[3], l[4], l[5], l[6], l[7],
                        l[8], l[9], l[10], l[11], name, period, group)
            lastAtomicNr = atomicNr

            # Since He3 appears first, add He before it
            if symbol == 'He':
                self.elements.insert(-1, e)
            else:
                self.elements.append(e)
        f.close()
        return True

    def elementFromNr(self, atomic_nr):
        for e in self.elements:
            if e.atomic_nr == atomic_nr:
                return e
        return None

    def elementFromSymbol(self, symbol):
        for e in self.elements:
            if e.symbol == symbol:
                return e
        return None

    def getIsotopes(self, atomic_nr):
        return [e for e in self.elements if e.atomic_nr == atomic_nr]

    def elementsMatching(self, text):
        text = str.lower(text)
        results = []
        for e in self.elements:
            symbol = str.lower(e.symbol)
            name = str.lower(e.name)
            if text in symbol or text in name:
                results.append(e.symbol)
        return results