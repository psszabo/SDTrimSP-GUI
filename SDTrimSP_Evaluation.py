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


import os.path

import numpy as np
import scipy.optimize
import matplotlib.pyplot as plt


class SDTrimSP_Evaluation:

    def __init__(self, outputPlotView, elementData, historyStep, historyStepSlider):
        #plt.rcParams.update({'font.size': 22})
        #plt.rcParams.update({'lines.linewidth': 3})
        #plt.rcParams.update({'lines.markersize': 12})

        self.plot = outputPlotView
        self.elementData = elementData
        self.historyStep = historyStep
        self.historyStepSlider = historyStepSlider
        self.fluence_array, self.depth_array, self.conc_array = [], [], [] # For updating certain plots without reading the file again

        # Define labels for plot outputs (fluence dependent)
        self.fluence_yields = 'Sputtering yields'
        self.fluence_yield_total = 'Total sputtering yield (atoms/ion)'
        self.fluence_yield_total_amu = 'Net mass removal (amu/ion)'
        self.fluence_reflection = 'Reflection coefficients'
        self.fluence_reemission = 'Reemission coefficients'
        self.fluence_surf_conc = 'Surface concentrations'
        self.fluence_surf_level = 'Surface level'
        self.fluence_depth_conc = 'Concentrations over depth'
        self.fluence_labels = [self.fluence_yields, self.fluence_yield_total, self.fluence_yield_total_amu,
                              self.fluence_reflection, self.fluence_reemission, self.fluence_surf_conc,
                              self.fluence_surf_level, self.fluence_depth_conc]

        self.depth_proj_impl = 'Implantation depth'
        self.depth_proj_eloss = 'Projectile energy loss'
        self.depth_recoil = 'Ion-induced damages'

        self.ang_yield = 'Angular dependence of sputtering yields (atoms/ion)'
        self.ang_mass = 'Angular dependence of sputtered mass (amu/ion)'
        self.ang_refl = 'Angular dependence of reflection coefficients'
        self.ang_depth = 'Angular dependence of implantation depth'

        self.en_yield = 'Energy dependence of sputtering yields (atoms/ion)'
        self.en_mass = 'Energy dependence of sputtered mass (amu/ion)'
        self.en_refl = 'Energy dependence of reflection coefficients'
        self.en_depth = 'Energy dependence of implantation depth'

        self.polar_ions = 'Polar angles of backscattered ions'
        self.polar_recoils = 'Polar angles of backsputtered recoils'
        self.energy_ions = 'Energy of backscattered ions'
        self.energy_recoils = 'Energy of backsputtered recoils'

        self.plot_labels = self.fluence_labels + [self.depth_proj_impl, self.depth_proj_eloss, self.depth_recoil,
                            self.ang_yield, self.ang_mass, self.ang_refl, self.ang_depth,
                            self.en_yield, self.en_mass, self.en_refl, self.en_depth,
                            self.polar_ions, self.polar_recoils, self.energy_ions, self.energy_recoils]

        # Initial definition of particle data arrays for polar poots
        self.resetPolarData()

    def resetPolarData(self):
        self.partic_back_p_data = []
        self.partic_back_r_data = []

    def updateData(self, workingDir, infoFile):
        self.workingDir = workingDir

        # updateData is only called if infoFile exists, so no need to check
        with open(infoFile) as content_file:
            for i in range(4):
                content_file.readline()
            self.ncp = int(content_file.readline().split()[2])
            self.elements = content_file.readline().split()
        self.masses = [self.elementData.elementFromSymbol(e).atomic_mass for e in self.elements]

        # colors: assign first color to total/amu-plots
        self.colors = []
        pyplot_colors = [plt.get_cmap('tab10').colors[i] for i in [1,2,0,3,4,7,6,8,9,5]] #plt.rcParams['axes.prop_cycle'].by_key()['color']
        nr_of_pyplot_colors = len(pyplot_colors)
        for i in range(len(self.elements)):
            color_index = i%(nr_of_pyplot_colors-1)+1
            #color_index = i % nr_of_pyplot_colors
            self.colors.append(pyplot_colors[color_index])
        self.first_color = pyplot_colors[0]



    def get_element_index(self, input_element):
        return_index = 0
        for i, element in enumerate(self.elements):
            if input_element == element:
                return_index = i
        return return_index


    # returns elemental sputtering yields + amu sputtering yield as array
    def get_output_file_data(self):
        # output.dat is guaranteed to exist here
        with open(self.workingDir + '/output.dat', 'r') as content_file:
            content = content_file.readlines()

        # Look for "MAXHIST" in file to determine ncp
        content_len = len(content)
        # for j in range(0, content_len):
        #     if len(content[j].split()) != 0 and content[j].split()[0] == 'MAXHIST':
        #         ncp =  int(content[j+1].split()[2])
        # #print 'ncp', ncp
        #

        #print('ncp', ncp)
        #print('Elements:', elements)

        # determine atomic masses
        masses = np.zeros(self.ncp)
        for j in range(0, content_len):
            #print(content[j].split(), len(content[j].split()))
            if len(content[j].split()) != 0 and content[j].split()[0] == 'CPT':
                for k in range(0, self.ncp):
                    masses[k] = float(content[j + k + 1].split()[3])
                break
        #print('Atomic masses', masses)

        # determine total number of particles
        for j in range(0, content_len):
            if len(content[j].split()) != 0 and content[j].split()[0] == 'NH':
                try:
                    nr_calc_total = int(content[j+1].split()[0]) * int(content[j+1].split()[1])
                except:
                    nr_calc_total = 1

                #print("nr_calc", nr_calc_total, content[j+1].split())
                break

        # determine beam ratios for different elements
        beam_comp = np.ones(self.ncp)/self.ncp
        for j in range(0, content_len):
            if len(content[j].split()) > 2 and content[j].split()[2] == 'Q-BEAM':
                for k in range(self.ncp):
                    try:
                        beam_comp[k] = float(content[j+1+k].split()[2])
                    except:
                        pass
                #print("beam comp", beam_comp)


        # Read simulation results
        yields = np.zeros(self.ncp)
        energy_loss_nucl = np.zeros(self.ncp)
        energy_loss_elec = np.zeros(self.ncp)
        implantation_depth = np.zeros(self.ncp)
        refl_coefficients = np.zeros(self.ncp)
        transm_coefficients = np.zeros(self.ncp)
        transm_sputt_yields = np.zeros(self.ncp)

        for j in range(0, content_len):
            # read projectile energy loss
            if len(content[j].split()) != 0 and content[j].strip().startswith("ENERGY LOSSES (PROJECTILES:"):
                for k in range(self.ncp):
                    if beam_comp[k] == 0.:
                        continue
                    if len(content[j+3+k].split()) != 0:
                        try:
                            # energy loss per calculated projectile
                            energy_loss_nucl[k] = float(content[j+k+3].split()[1]) / nr_calc_total / beam_comp[k]
                            energy_loss_elec[k] = float(content[j + k+3].split()[2]) / nr_calc_total / beam_comp [k]
                        except:
                            pass

                #print("energy losses", energy_loss_nucl, energy_loss_elec)

            # read projectile implantation depth
            if len(content[j].split()) != 0 and content[j].strip().startswith("IMPLANTATION DATA (Projectiles"):
                for k in range(self.ncp):
                    if len(content[j+k+4].split()) != 0:
                        try:
                            implantation_depth[k] = float(content[j+k+4].split()[1])
                        except:
                            pass

                #print("implantation depths", implantation_depth)

            # read reflection coefficients
            if len(content[j].split()) != 0 and content[j].strip().startswith("REFLECTION DATA (BACKSC"):
                # check if no reflection at all occurs, then the output looks as follows:
                #  REFLECTION DATA (BACKSCATTERING):
                #  no backscattering
                if content[j + 1].strip().startswith('no') == False:
                    for k in range(self.ncp):
                        if len(content[j + k + 4].split()) != 0 and content[j + k + 4].split()[0] != "all":
                            try:
                                refl_coefficients[k] = float(content[j + k + 4].split()[1])
                            except:
                                pass
                #print("reflection coefficients", refl_coefficients)

            # read sputtering yields
            if len(content[j].split()) != 0 and content[j].split()[0] == 'SPUTTERING':
                # check if no sputtering at all occurs, then the output looks as follows:
                #  SPUTTERING DATA (BACKWARD SPUTTERING):
                #  no backward sputtering
                #
                if content[j + 1].strip().startswith('no') == False:
                    for k in range(0, self.ncp):
                        temp = content[j + k + 4].split()[1]
                        if str(temp).startswith('n'):  # set 0.0 when it say 'no backwards sputtering'
                            yields[k] = 0.0
                        else:
                            yields[k] = float(temp)


            # read transmission sputtering yields
            if len(content[j].split()) != 0 and content[j].strip().startswith("TRANSMISSION SPUTTERING"):
                # check if no sputtering at all occurs, then the output looks as follows:
                #   TRANSMISSION SPUTTERING DATA:
                #  no transmission sputtering
                #
                if content[j+1].strip().startswith('no') == False:
                    for k in range(0, self.ncp):
                        temp = content[j + k + 4].split()[1]
                        if str(temp).startswith('n'):  # set 0.0 when it say 'no backwards sputtering'
                            transm_sputt_yields[k] = 0.0
                        else:
                            transm_sputt_yields[k] = float(temp)

            # read transmission coefficients
            if len(content[j].split()) != 0 and content[j].strip().startswith("TRANSMISSION DATA"):
                # check if no reflection at all occurs, then the output looks as follows:
                #  REFLECTION DATA (BACKSCATTERING):
                #  no backscattering
                if content[j + 1].strip().startswith('no') == False:
                    for k in range(self.ncp):
                        if len(content[j + k + 4].split()) != 0 and content[j + k + 4].split()[0] != "all":
                            try:
                                transm_coefficients[k] = float(content[j + k + 4].split()[1])
                            except:
                                pass
                # print("reflection coefficients", refl_coefficients)




        total_yield = np.sum(yields)
        total_transm_sputt_yield = np.sum(transm_sputt_yields)

        # calculate amu yield
        amu_yield = np.dot(masses, yields)
        amu_transm_sputt_yield = np.dot(masses, transm_sputt_yields)
        #print('Yield [amu/ion]: ' + str(amu_yield))
        return yields, total_yield, amu_yield,  energy_loss_nucl, energy_loss_elec, implantation_depth, refl_coefficients, transm_sputt_yields, total_transm_sputt_yield, amu_transm_sputt_yield, transm_coefficients

    def get_data_from_E031target(self):
        if not os.path.exists(self.workingDir + '/E0_31_target.dat'):
            return None
        f = open(self.workingDir + '/E0_31_target.dat', 'r')

        # skip version header and name of simulation
        f.readline()
        f.readline()

        # read global parameter headers
        for i in range(0, 10):
            temp = f.readline()
            if len(temp) != 0:
                if temp.split()[0] == "nh":
                    break
        global_pars = f.readline().split()
        maxhist = int(global_pars[0])
        nqx = int(global_pars[1])
        ihist_out = int(global_pars[3])
        ncp = int(global_pars[2])

        # skip element symbols and history step headers
        for i in range(17):
            f.readline()

        # for loop over history steps, set up variables that will be plotted
        max_hist_step = int(maxhist / ihist_out) + 1

        fluence_array = np.zeros(max_hist_step)  # fluence
        surf = np.zeros(max_hist_step)  # surface minimum
        surface_conc = np.zeros((max_hist_step, ncp))
        nr_projectiles_array = np.zeros(max_hist_step)  # number of projectiles
        nr_projectiles_array_per_element = np.zeros((max_hist_step, ncp)) # number of projectiles per element
        nr_reflected = np.zeros((max_hist_step, ncp))  # number of reflected
        nr_sputtered = np.zeros((max_hist_step, ncp))  # number of backsputtered
        nr_reemitted = np.zeros((max_hist_step, ncp))  # number of reemitted projectiles
        conc_array = np.zeros((max_hist_step, ncp, nqx)) # concentration over depth of each element for each history step

        for hist_counter in range(0, max_hist_step):
            #print('History ' + str(hist_counter+1) + ' of ' +  str(max_hist_step))
            # read fluence, surface_min, surface_max
            hist_pars = f.readline().split()[0:2]

            if len(hist_pars) == 0:
                max_hist_step = hist_counter  # adjust max_hist_step
                # cut arrays for plotting
                fluence_array = fluence_array[:max_hist_step]
                surf = surf[:max_hist_step]
                surface_conc = surface_conc[:max_hist_step]
                conc_array = conc_array[:max_hist_step]
                break

            fluence_array[hist_counter] = float(hist_pars[0])
            surf[hist_counter] = float(hist_pars[1])

            # read surface atomic fractions
            surface_conc[hist_counter, :] = np.array(f.readline().split()[0:ncp]).astype(np.float)
            if np.sum(surface_conc[hist_counter]) < 1.:
                surface_conc[hist_counter,0] = 1. - np.sum(surface_conc[hist_counter])

            # skip Momente and areal densitites
            f.readline()
            f.readline()

            # read number of projectiles
            nr_projectiles_array_per_element[hist_counter, :] = np.array(f.readline().split()[0:ncp]).astype(np.float)
            nr_projectiles_array[hist_counter] = np.sum(nr_projectiles_array_per_element[hist_counter,:])

            # read number of backscattered particles
            nr_reflected[hist_counter, :] = np.array(f.readline().split()[0:ncp]).astype(np.float)

            # skip energy of backscattered particles, and number and energy of transmitted projectiles
            for i in range(3):
                f.readline()

            # read number of backsputtered particles
            nr_sputtered[hist_counter, :] = np.array( f.readline().split()[0:ncp]).astype(np.float)

            # skip energy of backsputtered particles , and number, energy of transmitted sputtered particles, energy of all projectiles
            for i in range(4):
                f.readline()

            # read number of reemitted atoms
            nr_reemitted[hist_counter, :] = np.array(f.readline().split()[0:ncp]).astype(np.float)

            # chemical erosion --> not recorded further
            f.readline()

            # read two header lines + depth dependent concentrations
            if hist_counter == 0:
                for i in range(0, 2):
                    f.readline()

            depth_array = np.zeros(nqx)

            for i in range(0, nqx):
                #f.readline()
                layer_line = np.array(f.readline().split()).astype(np.float)
                depth_array[i] = layer_line[0]
                # read layer concentrations for all ncp elements
                for j in range(0, ncp):
                    conc_array[hist_counter, j, i] = layer_line[j + 2]

            # if fluence_array[hist_counter] != 0.0:
            #     print
            #     fluence_array[hist_counter], '\t', '\t'.join(map(str, (
            #                 nr_sputtered[hist_counter] - nr_sputtered[hist_counter - 1]) / (
            #                                                                  nr_projectiles_array[hist_counter] -
            #                                                                  nr_projectiles_array[
            #                                                                      hist_counter - 1]))), '\t', (
            #                 nr_reflected[hist_counter, 0] - nr_reflected[hist_counter - 1, 0]) / (
            #                 nr_projectiles_array[hist_counter] - nr_projectiles_array[hist_counter - 1])

        f.close()

        # calculate yields
        reflected_yield = np.zeros((max_hist_step, ncp))  # number of reflected
        sputtered_yield = np.zeros((max_hist_step, ncp))  # number of backsputtered
        reemitted_yield = np.zeros((max_hist_step, ncp))  # number of backsputtered
        projectile_yield = np.zeros((max_hist_step, ncp))  # number of backsputtered
        amu_yield = np.zeros((max_hist_step))  # mass change per ion over fluence
        # netto_implanted_yield = np.zeros((max_hist_step - 1))  # netto implanted ions per incoming ion
        for i in range(1, max_hist_step):
            for j in range(0, ncp):
                if nr_projectiles_array_per_element[i,j] != nr_projectiles_array_per_element[i - 1,j]:
                    reflected_yield[i, j] = (nr_reflected[i, j] - nr_reflected[i - 1, j]) / (
                                nr_projectiles_array_per_element[i,j] - nr_projectiles_array_per_element[i - 1,j])

            sputtered_yield[i, :] = (nr_sputtered[i, :] - nr_sputtered[i - 1, :]) / (
                    nr_projectiles_array[i] - nr_projectiles_array[i - 1])
            reemitted_yield[i, :] = (nr_reemitted[i, :] - nr_reemitted[i - 1, :]) / (
                    nr_projectiles_array[i] - nr_projectiles_array[i - 1])
            projectile_yield[i, :] = (nr_projectiles_array_per_element[i, :] - nr_projectiles_array_per_element[i - 1, :]) / (
                    nr_projectiles_array[i] - nr_projectiles_array[i - 1])


            for j in range(0, ncp):
                #amu_yield[i] += self.masses[j] * (sputtered_yield[i,j] + reemitted_yield[i,j] + reflected_yield[i,j] - projectile_yield[i,j])
                amu_yield[i] += self.masses[j] * (
                            sputtered_yield[i, j] + reemitted_yield[i, j] + reflected_yield[i, j]*projectile_yield[i,j] - projectile_yield[
                        i, j])
        return [fluence_array, sputtered_yield, amu_yield, reflected_yield, reemitted_yield, surface_conc, surf, depth_array, conc_array]

    def plot_output(self, plot_label):
        self.plot.fig.clf()
        self.plot.axes = self.plot.fig.add_subplot(projection="rectilinear")

        # All the fluence plots need data from the E031target file
        if plot_label in self.fluence_labels:
            E031data = self.get_data_from_E031target()
            if E031data is None: # Abort if the E031target file is missing
                self.plot.fig.canvas.draw_idle()
                return [], []
            fluence_array, sputtered_yield, amu_yield, reflected_yield,\
                reemitted_yield, surface_conc, surf, depth_array, conc_array = E031data

            # Store the data for plot updates where the file is not read again
            self.fluence_array, self.depth_array, self.conc_array = fluence_array, depth_array, conc_array

            if plot_label == self.fluence_yields:
                return self.plot_sputtering_yields(fluence_array, sputtered_yield)
            elif plot_label == self.fluence_yield_total:
                return self.plot_sputtering_yield_total(fluence_array, sputtered_yield)
            elif plot_label == self.fluence_yield_total_amu:
                return self.plot_sputtering_yield_total_amu(fluence_array, amu_yield)
            elif plot_label == self.fluence_reflection:
                return self.plot_reflection_coefficient(fluence_array, reflected_yield)
            elif plot_label == self.fluence_reemission:
                return self.plot_reemission_coefficient(fluence_array, reemitted_yield)
            elif plot_label == self.fluence_surf_conc:
                return self.plot_surface_concentrations(fluence_array, surface_conc)
            elif plot_label == self.fluence_surf_level:
                return self.plot_surface_level(fluence_array, surf)
            elif plot_label == self.fluence_depth_conc:
                return self.update_depth_conc(setToMax=True)
        else:
            if plot_label == self.depth_proj_impl:
                return self.plot_proj_stops_over_depth()
            elif plot_label == self.depth_proj_eloss:
                return self.plot_proj_energy_loss_over_depth()
            elif plot_label == self.depth_recoil:
                return self.plot_vacancies_over_depth()
            elif plot_label == self.ang_yield:
                return self.plot_ang_dep_sputter_yields()
            elif plot_label == self.ang_mass:
                return self.plot_ang_dep_mass_yields()
            elif plot_label == self.ang_refl:
                return self.plot_ang_dep_refl_coeff()
            elif plot_label == self.ang_depth:
                return self.plot_ang_dep_mean_depth()
            elif plot_label == self.en_yield:
                return self.plot_en_dep_sputter_yields()
            elif plot_label == self.en_mass:
                return self.plot_en_dep_mass_yields()
            elif plot_label == self.en_refl:
                return self.plot_en_dep_refl_coeff()
            elif plot_label == self.en_depth:
                return self.plot_en_dep_mean_depth()
            elif plot_label == self.polar_ions:
                return self.plot_particles_over_polar_angle("p")
            elif plot_label == self.polar_recoils:
                return self.plot_particles_over_polar_angle("r")
            elif plot_label == self.energy_ions:
                return self.plot_particles_over_energy("p")
            elif plot_label == self.energy_recoils:
                return self.plot_particles_over_energy("r")

    def update_depth_conc(self, setToMax=False):
        max_hist = self.conc_array.shape[0]-1
        if max_hist < 0:
            return [], []
        self.historyStep.setMaximum(max_hist)
        self.historyStepSlider.setMaximum(max_hist)
        if setToMax:
            self.historyStep.setValue(self.historyStep.maximum())
        return self.plot_depth_concentrations(self.fluence_array, self.depth_array, self.conc_array, self.historyStep.value())

    def plot_sputtering_yields(self, fluence_array, sputtered_yield):
        data = []
        plotLabels = ["Fluence[10^20 ions/m^2]"]
        data.append(fluence_array[1:])
        for i, element in enumerate(self.elements):
            self.plot.axes.plot(fluence_array[1:], sputtered_yield[1:, i], label=element, color=self.colors[i])
            data.append(sputtered_yield[1:, i])
            plotLabels.append(element)

        self.plot.axes.set_xlabel("Fluence [$10^{20}$ ions/m$^2$]")
        self.plot.axes.set_ylabel("Sputtering Yield Y [atoms/ion]")
        self.plot.axes.set_ylim(ymin=0.)
        self.plot.axes.legend()
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()
        return data, plotLabels

    def plot_sputtering_yield_total(self, fluence_array, sputtered_yield):
        data = []
        data.append(fluence_array[1:])
        data.append(np.sum(sputtered_yield[1:, :], axis=1))
        self.plot.axes.plot(fluence_array[1:], np.sum(sputtered_yield[1:, :], axis=1), color=self.first_color)
        self.plot.axes.set_xlabel("Fluence [$10^{20}$ ions/m$^2$]")
        self.plot.axes.set_ylabel("Sputtering Yield Y [atoms/ion]")
        self.plot.axes.set_ylim(ymin=0.)
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()
        return data, ["Fluence[10^20 ions/m^2]", "Y [atoms/ion]"]

    def plot_sputtering_yield_total_amu(self, fluence_array, amu_yield):
        data = []
        data.append(fluence_array[1:])
        data.append(amu_yield[1:])
        self.plot.axes.plot(fluence_array[1:], amu_yield[1:], color=self.first_color)
        self.plot.axes.set_xlabel("Fluence [$10^{20}$ ions/m$^2$]")
        self.plot.axes.set_ylabel("Net Mass Removal y [amu/ion]")
        #self.plot.axes.set_ylim(ymin=np.min([0.,np.min(amu_yield[1:])]))
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()
        return data, ["Fluence[10^20 ions/m^2]", "y [amu/ion]"]

    def plot_reflection_coefficient(self, fluence_array, reflected_yield):
        data = []
        data.append(fluence_array[1:])
        plotLabels = ["Fluence[10^20 ions/m^2]"]
        for i, element in enumerate(self.elements):
            self.plot.axes.plot(fluence_array[1:], reflected_yield[1:, i], label=element, color=self.colors[i])
            data.append(reflected_yield[1:, i])
            plotLabels.append(element)
        self.plot.axes.set_xlabel("Fluence [$10^{20}$ ions/m$^2$]")
        self.plot.axes.set_ylabel("Reflection Coefficient R [atoms/ion]")
        self.plot.axes.set_ylim(ymin=0., ymax=1.)
        self.plot.axes.legend()
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()
        return data, plotLabels

    def plot_reemission_coefficient(self, fluence_array, reemitted_yield):
        data = []
        data.append(fluence_array[1:])
        plotLabels = ["Fluence[10^20 ions/m^2]"]
        for i, element in enumerate(self.elements):
            self.plot.axes.plot(fluence_array[1:], reemitted_yield[1:, i], label=element, color=self.colors[i])
            data.append(reemitted_yield[1:, i])
            plotLabels.append(element)
        self.plot.axes.set_xlabel("Fluence [$10^{20}$ ions/m$^2$]")
        self.plot.axes.set_ylabel("Reemission Coefficient [atoms/ion]")
        self.plot.axes.set_ylim(ymin=0., ymax=1.)
        self.plot.axes.legend()
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()
        return data, plotLabels

    def plot_surface_concentrations(self, fluence_array, surface_conc):
        data = []
        data.append(fluence_array[1:])
        plotLabels = ["Fluence[10^20 ions/m^2]"]
        for i, element in enumerate(self.elements):
            self.plot.axes.plot(fluence_array[1:], surface_conc[1:, i], label=element, color=self.colors[i])
            data.append(surface_conc[1:, i])
            plotLabels.append(element)
        self.plot.axes.set_xlabel("Fluence [$10^{20}$ ions/m$^2$]")
        self.plot.axes.set_ylabel("Surface Concentration")
        self.plot.axes.set_ylim(ymin=0., ymax=1.)
        self.plot.axes.legend()
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()
        return data, plotLabels

    def plot_surface_level(self, fluence_array, surf):
        data = []
        data.append(fluence_array[1:])
        data.append(surf[1:])
        self.plot.axes.plot(fluence_array[1:], surf[1:], color=self.first_color)
        self.plot.axes.set_xlabel("Fluence [$10^{20}$ ions/m$^2$]")
        self.plot.axes.set_ylabel("Surface Erosion [Å]")
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()
        return data, ["Fluence[10^20 ions/m^2]", "Surface Erosion [Å]"]

    def plot_depth_concentrations(self, fluence_array, depth_array, conc_array, history_step):
        self.plot.fig.clf()
        self.plot.axes = self.plot.fig.add_subplot(projection="rectilinear")

        data = []
        data.append(depth_array)
        plotLabels = ["Depth [Å]"]
        for k in range(0, self.ncp):
            #self.plot.axes.plot((depth_array) * 0.1, conc_array[k, :], linewidth=2, label=self.elements[k], color=self.colors[i])  # plot in nm
            self.plot.axes.plot(depth_array, conc_array[history_step, k, :], linewidth=2,
                                label=self.elements[k], color=self.colors[k])  # plot in A
            data.append(conc_array[history_step, k, :])
            plotLabels.append(self.elements[k])
        # plt.plot(conc_array[k, hist_counter, :], linewidth=2)
        # plt.ylim([-0.1, 1.1])
        self.plot.axes.set_ylim(ymin=0.0, ymax=1.0)
        self.plot.axes.legend()
        self.plot.axes.set_xlabel("Depth [Å]")
        self.plot.axes.set_ylabel("Concentrations")
        self.plot.axes.set_title("Fluence: "+ str(fluence_array[history_step]) + "$ \\times 10^{20}$/m$^2$")
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()
        return data, plotLabels

    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------

    def get_data_from_particle_files(self, proj_or_rec):
        old_data_len = len(self.partic_back_p_data) if proj_or_rec == "p" else len(self.partic_back_r_data)
        
        try:
            forheader = open(self.workingDir + f'/partic_back_{proj_or_rec}.dat')
            for line in range(5):
                headerline = forheader.readline()
            headerline = headerline.split()
            self.cosp = headerline.index('cosp')
            self.cosa = headerline.index('cosa')        
            self.energyindex = headerline.index('end-energy')  
        except:
            self.cosp = 13 #standard values, if no reduced dataset
            self.cosa = 14 #standard values, if no reduced dataset
            self.energyindex = 3  #standard values, if no reduced dataset

        try:
            new_particle_file_data = np.genfromtxt(self.workingDir + f'/partic_back_{proj_or_rec}.dat', skip_header=5+old_data_len, skip_footer=2)
        except:
            return []

        if len(new_particle_file_data) > 0:
            if new_particle_file_data.ndim == 1: # Fix the data shape if just a single line was read
                new_particle_file_data = new_particle_file_data[np.newaxis, ...]

            new_particle_file_data = np.ndarray.tolist(new_particle_file_data)
            if proj_or_rec == "p":
                self.partic_back_p_data.extend(new_particle_file_data)
            else:
                self.partic_back_r_data.extend(new_particle_file_data)

        particle_file_data = np.array(self.partic_back_p_data) if proj_or_rec == "p" else np.array(self.partic_back_r_data)
        if len(particle_file_data) == 0:
            return []

        particle_file_data_per_element = []
        for number in range(0, self.ncp):
            mask = particle_file_data[:, 0] == number+1
            species_data = particle_file_data[mask, :]
            particle_file_data_per_element.append(species_data)
        return particle_file_data_per_element

    def plot_polar(self, plot_element, proj_or_rec):
        self.plot.fig.clf()
        self.plot.axes = self.plot.fig.add_subplot(projection="polar")

        data = []
        plotLabels = []


        particle_file_data_per_element = self.get_data_from_particle_files(proj_or_rec=proj_or_rec)
        if len(particle_file_data_per_element) == 0:
            self.plot.axes.set_title('No data found')
            self.plot.fig.tight_layout()
            self.plot.fig.canvas.draw_idle()
            return data, plotLabels

        # get index of the element that should be plotted
        plot_element_index = 0
        for i in range(0, self.ncp):
            if plot_element == self.elements[i]:
                plot_element_index = i

        plot_data = particle_file_data_per_element[plot_element_index]
        if len(plot_data) == 0:
            self.plot.axes.set_title('No data found')
            self.plot.fig.tight_layout()
            self.plot.fig.canvas.draw_idle()
            return data, plotLabels

        deg_from_rad = 180. / np.pi
        # deg_from_rad = 1.

        # usual plot, not polar
        #####

        phi_intermed = np.arccos(plot_data[:, self.cosa]) #cosa
        phi_intermed_neg = -np.arccos(plot_data[:, self.cosa])
        phi = np.hstack((phi_intermed, phi_intermed_neg))


        #print("number of atoms plotted:", len(phi))

        theta_intermed = np.arccos(plot_data[:, self.cosp]) #cosp
        theta = np.hstack((theta_intermed, theta_intermed))

        #phi = phi_intermed
        #theta = theta_intermed

        polarplot_sinbin = True

        lowerlimit = 0

        # np.arrange(0,N_bins+1 results in 0... pi/2). scaling of
        N_bins = 30

        if polarplot_sinbin:
            # define binning
            # rbins = np.linspace(0,0.5*np.pi, 30)
            # abins = np.linspace(0,2*np.pi, 60)
            spacing = np.arange(lowerlimit, N_bins + 1)
            rbins = np.arccos(1 - spacing / N_bins)
            #rbins = np.arange(0, np.pi/2, np.pi/2/N_bins)

            abins = np.linspace(-np.pi, np.pi, 4 * N_bins)
            #print(abins)

            # calculate histogram
            # hist, _, _ = np.histogram2d(np.pi-1*np.arccos(element[:,3]),deg_from_rad*np.arccos(element[:,2]), weights = 1./np.sin(np.arccos(element[:,2])), bins=(abins, rbins))
            # hist, _, _ = np.histogram2d(phi,deg_from_rad*theta, weights = 1./np.sin(theta), bins=(abins, rbins))
            # hist, _, _ = np.histogram2d(phi,deg_from_rad*theta, bins=(abins, rbins))
            # hist, _, _ = np.histogram2d(phi[::100], theta[::100], bins=(abins, rbins))
            hist, _, _ = np.histogram2d(phi, theta, bins=(abins, rbins))
            hist *= 0.5 # 0.5 corrects for the extension to the full 2*pi azimuthal space, so that particles are not counted twice
            hist /= np.sum(hist) # normalize for number of particles

            total_nr_of_bins = hist.size
            #print("hist size", hist.size)
            bin_area = np.pi*2. /total_nr_of_bins
            hist /= bin_area

            # hist, _, _ = np.histogram2d(np.pi-1*np.arccos(element[:,3]),deg_from_rad*np.arccos(element[:,2]), bins=(abins, rbins))
            A, R = np.meshgrid(abins, rbins)

            # plot
            # fig, ax = plt.subplots(subplot_kw=dict(projection="polar"))
            # fig.canvas.set_window_title(filename)


            self.plot.axes.set_thetamin(0)
            self.plot.axes.set_thetamax(360)
            self.plot.axes.set_theta_direction(-1)
            self.plot.axes.set_theta_zero_location("E")
            self.plot.axes.set_yticklabels([])
            #        ax.plot([np.pi], [int(sdtrim_data.angle)], 'o', color = "red")
            #        ax.plot([0], [int(sdtrim_data.angle)], 'o', color = "blue")
            pc = self.plot.axes.pcolormesh(A, R, hist.T, cmap="viridis", zorder=-1, vmin=0.)
            cb = self.plot.fig.colorbar(pc)
            cb.set_label('Distribution of Particles [1/sr]', rotation=90)

            #data.append(A)
            #data.append(R)
            plotLabels.append("Rows: polar angles [°], columns: azimuthal angles [°], distribution of particles in [1/sr], first row/column gives the respective angle (center of the bin of the histogram), polar bins are chosen so that all bins have the same solid angle")

            delta_rbins = rbins[1:] - rbins[:-1]
            rbins_center = rbins[:-1] + 0.5 * delta_rbins

            delta_abins = abins[1:] - abins[:-1]
            abins_center = abins[:-1] + 0.5 * delta_abins

            data.append(np.append(0.,np.round(rbins_center/np.pi*180.,2)))
            for i in range(len(hist)):
                if abins_center[i] < 0:
                    continue
                data.append(np.append(np.mod(np.round(abins_center[i]/np.pi*180.,2), 360.),hist[i]))
            for i in range(len(hist)):
                if abins_center[i] > 0:
                    continue
                data.append(np.append(np.mod(np.round(abins_center[i]/np.pi*180.,2), 360.),hist[i]))


        if proj_or_rec == 'p':
            title = f'Angular distribution of backscattered {plot_element} projectiles'
        else:
            title = f'Angular distribution of backsputtered {plot_element} recoil atoms'
        self.plot.axes.set_title(title)
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()

        return data, plotLabels


    def plot_particles_over_energy(self, proj_or_rec):
        self.plot.fig.clf()
        self.plot.axes = self.plot.fig.add_subplot(projection="rectilinear")

        data = []
        plotLabels = []

        particle_file_data_per_element = self.get_data_from_particle_files(proj_or_rec=proj_or_rec)
        #print(particle_file_data_per_element)
        if len(particle_file_data_per_element) == 0:
            self.plot.axes.set_title('No data found')
            self.plot.fig.tight_layout()
            self.plot.fig.canvas.draw_idle()
            return data, plotLabels

        plot_counter = 0
        for i in range(self.ncp):
            plot_data = particle_file_data_per_element[i]
            energies = plot_data[:, self.energyindex]
            if len(energies) == 0:
                continue
            if proj_or_rec == 'p':
                hist, bin_edges = np.histogram(energies, density=True, bins=100)
            else: # use very fine resolution in binning for sputtered atoms because lower energies are of more interest
                hist, bin_edges = np.histogram(energies, density=True, bins=int(np.max(energies)/0.2))
            #delta_bin_edges = bin_edges[1] - bin_edges[0]
            bin_edges_new = 0.5*(bin_edges[:-1] + bin_edges[1:])
            self.plot.axes.plot(bin_edges_new, hist, label=self.elements[i],linewidth=2., color=self.colors[i])

            data.append(bin_edges_new)
            plotLabels.append(f"Energy ({self.elements[i]}) [eV]")
            data.append(hist)
            plotLabels.append(f"Probability ({self.elements[i]}) [1/eV]")

            plot_counter += 1

        self.plot.axes.set_xlabel("Energy [eV]")
        if proj_or_rec == 'p':
            self.plot.axes.set_ylabel("Reflected ions [1/eV]")
        else:
            self.plot.axes.set_ylabel("Sputtered atoms [1/eV]")
        self.plot.axes.set_ylim(ymin=0.)
        self.plot.axes.set_xlim(xmin=0.)
        self.plot.axes.legend()
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()

        return data, plotLabels


    def plot_particles_over_polar_angle(self, proj_or_rec):
        self.plot.fig.clf()
        self.plot.axes = self.plot.fig.add_subplot(projection="polar")

        data = []
        plotLabels = []

        particle_file_data_per_element = self.get_data_from_particle_files(proj_or_rec=proj_or_rec)
        #print(particle_file_data_per_element)
        if len(particle_file_data_per_element) == 0:
            self.plot.axes.set_title('No data found')
            self.plot.fig.tight_layout()
            self.plot.fig.canvas.draw_idle()
            return data, plotLabels



        plot_counter = 0
        for i in range(self.ncp):
            plot_data = particle_file_data_per_element[i]
            cos_polar = plot_data[:, self.cosp]
            cos_azimuth = plot_data[:, self.cosa]
            polar_angles = np.arccos(np.asarray(cos_polar)) * np.sign(cos_azimuth)

            if len(cos_polar) == 0:
                continue

            # adapt variable bins from the angular distribution polar color plots
            #N_bins = 18
            #spacing = np.arange(0, N_bins + 1)
            #bins = np.arccos(1 - spacing / N_bins)
            #bins = np.append(-1*np.flip(bins[1:]), bins)
            #print(bins)

            hist, bin_edges = np.histogram(polar_angles, density=True, bins=72, range=(-np.pi/2, np.pi/2))
            #hist, bin_edges = np.histogram(polar_angles, bins=bins)
            #delta_bin_edges = bin_edges[1] - bin_edges[0]
            bin_edges_new = 0.5*(bin_edges[:-1] + bin_edges[1:])
            polar_plot_norm = np.absolute(np.cos(bin_edges[:-1]) - np.cos(bin_edges[1:]))/np.sum(np.absolute(
                np.cos(bin_edges[:-1]) - np.cos(bin_edges[1:])))
            plot_data = 0.5 * np.pi/180. * np.divide(hist, np.absolute(polar_plot_norm)) # 0.5 ... normalization because both + and - polar angle are shown, np.pi/180. for conversion from 1/rad to 1/deg
            self.plot.axes.plot(bin_edges_new, plot_data,
                                label=self.elements[i], linewidth=2., color=self.colors[i])

            if plot_counter == 0:
                data.append(bin_edges_new/np.pi*180.)
                plotLabels.append(f"Polar Angle [°]")
            data.append(plot_data)
            plotLabels.append(f"Probability ({self.elements[i]}) [1/°]")

            plot_counter += 1

        if proj_or_rec == 'p':
            self.plot.axes.set_title("Backscattered projectiles over polar angle")
        else:
            self.plot.axes.set_title("Sputtered recoils over polar angle")

        self.plot.axes.set_xlabel("Probability [1/°]")
        self.plot.axes.grid(True)
        self.plot.axes.set_thetagrids((-90, -80, -70, -60, -50, -40, -30, -20, -10, 0, 10, 20, 30, 40, 50, 60, 70, 80, 90))
        self.plot.axes.set_thetamin(-90)
        self.plot.axes.set_thetamax(90)
        self.plot.axes.set_theta_offset(np.pi / 2)
        self.plot.axes.set_theta_direction(-1)
        self.plot.axes.tick_params(axis='y', labelrotation=45, pad=4, labelsize=8)

        self.plot.axes.legend()
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()
        return data, plotLabels


    ##
    ##
    def get_data_from_serie_file(self):

        with open(self.workingDir + f'/serie.dat', 'r') as content_file:
            # read first line
            content_file.readline()

            # read ncp and ncp_proj
            line = content_file.readline().split()
            ncp = int(line[0])
            ncp_proj = int(line[1])
            #print("ncp", ncp)

            # read version
            content_file.readline()

            # read elements
            elements = content_file.readline().split()[-ncp:]
            #print("elements", elements)

            # read element header and masses
            content_file.readline()
            masses = np.zeros(ncp)
            for i in range(ncp):
                masses[i] = float(content_file.readline().split()[2])
            #print("masses", masses)

            # read skip line as long as there are '!'
            while True:
                line = content_file.readline()
                if line.strip().startswith('!') == False:
                    break


            # read number of calculations
            #nr_energies = int(content_file.readline().split()[0])
            nr_energies = int(line.split()[0])
            #print("nr_energies", nr_energies)
            nr_angles = int(content_file.readline().split()[0])
            #print("nr_angles", nr_angles)
            nr_total = nr_angles*nr_energies
            #print("nr_total", nr_total)

            # read remaining number lines and headers
            for i in range(4):
                content_file.readline()

            # read element columns to define elements of projectiles
            line_elements = content_file.readline().split()
            #print(line_elements)
            elements_proj = []
            for i in range(ncp_proj):
                elements_proj.append(line_elements[2*i])
            #print("Elements_proj", elements_proj)


            # read all calculation results
            energies = np.zeros(nr_total)
            angles = np.zeros(nr_total)
            mean_depth = np.zeros(nr_total)
            refl_coeff = np.zeros((nr_total,ncp_proj))
            energ_refl_coeff = np.zeros((nr_total, ncp_proj))
            sputt_coeff = np.zeros((nr_total, ncp))
            energ_sputt_coeff = np.zeros((nr_total, ncp))

            # number of expected elements per calculation: energy, alpha, mean_depth, 2*ncp_proj reflection coefficients, 2 * ncp sputter coefficients
            # 3 + 2*ncp_proj + 2*ncp
            expected_line_elements = 3 + 2*ncp_proj + 2*ncp


            for i in range(0, nr_total):
                try:
                    line = content_file.readline().split()
                    #print(line)

                    if len(line) == 0:
                        break

                    while len(line) < expected_line_elements:
                        line.extend(content_file.readline().split())
                    #print("Line", line)
                    energies[i] = line[0]
                    angles[i] = line[1]
                    mean_depth[i] = line[2]

                    for j in range(ncp_proj):
                        refl_coeff[i,j] = line[3 + 2*j]
                        energ_refl_coeff[i, j] = line[3 + 2 * j + 1]
                    for j in range(ncp):
                        sputt_coeff[i,j] = line[3 + 2*ncp_proj + 2*j]
                        energ_sputt_coeff[i, j] = line[3 + 2 * ncp_proj + 2 * j + 1]
                except:
                    break
            #print("i at the end", i)

            #print(sputt_coeff)

            return ncp, ncp_proj, elements, elements_proj, masses, nr_energies, nr_angles, nr_total, energies, angles, mean_depth, refl_coeff, energ_refl_coeff, sputt_coeff, energ_sputt_coeff, i


    def plot_ang_dep_sputter_yields(self):
        ncp, ncp_proj, elements, elements_proj, masses, nr_energies, nr_angles, nr_total, energies, angles, mean_depth, refl_coeff, energ_refl_coeff, sputt_coeff, energ_sputt_coeff, last_index = self.get_data_from_serie_file()
        if last_index > nr_total:
            last_index = nr_total

        self.plot.fig.clf()
        self.plot.axes = self.plot.fig.add_subplot(projection="rectilinear")

        data = []
        plotLabels = []

        total_yield = np.sum(sputt_coeff, axis=1)
        angle_distance_weights = np.ones(nr_total)

        # fit total yield with Eckstein fit
        # fit yield with eckstein formula
        fit_params_string = ''
        if last_index >= 5:
            try:
                for i in range(0, last_index-1):
                    angle_distance_weights[i] = 1./(angles[i+1]-angles[i])
                popt, pcov = scipy.optimize.curve_fit(self.eckstein_angle_fit, angles[:last_index], total_yield[:last_index],
                                                      p0=[total_yield[0], 90., 1., 1., 1.6], sigma=angle_distance_weights[:last_index],
                                                      bounds=(0., [np.max(total_yield), 90., 10., 1., 10.]))
                angles_fit = np.arange(0., 90., 0.1)
                #angles_fit = np.arange(0., np.min([90., popt[1]**popt[3]]), 0.1)
                self.plot.axes.plot(angles_fit, self.eckstein_angle_fit(angles_fit, *popt), 'k--', label=f'Eckstein Fit',
                                    linewidth=1.)
                self.plot.axes.set_title(f'Fit: Y$_0$ = {np.round(popt[0], 3)} atoms/ion, $\\alpha_0$ = {np.round(popt[1], 3)}°, b = {np.round(popt[2], 3)}, c = {np.round(popt[3],3)}, f = {np.round(popt[4],3)}')
                fit_params_string = f'Fit: Y0 = {np.round(popt[0], 3)} atoms/ion, alpha0 = {np.round(popt[1], 3)}°, b = {np.round(popt[2], 3)}, c = {np.round(popt[3],3)}, f = {np.round(popt[4],3)}'
            except:
                pass

        #ydata = []
        #plotLabels = ["Angle of Incidence $\\alpha$ [°]"]
        plot_counter = 0
        for i, element in enumerate(elements):
            if np.max(sputt_coeff[:,i]) > 0.:
                self.plot.axes.plot(angles[:last_index], sputt_coeff[:last_index,i], 'o', label=element, color=self.colors[self.get_element_index(element)])

                if plot_counter == 0:
                    data.append(angles[:last_index])
                    plotLabels.append("Angle of Incidence [°]")
                data.append(sputt_coeff[:last_index,i])
                plotLabels.append(element)

                plot_counter += 1


        if plot_counter > 1:
            self.plot.axes.plot(angles[:last_index], total_yield[:last_index], 'o', label="Total", color=self.first_color)
            data.append(total_yield[:last_index])
            plotLabels.append("Total")
            plotLabels.append(fit_params_string)

        self.plot.axes.set_xlabel("Angle of Incidence $\\alpha$ [°]")
        self.plot.axes.set_ylabel("Sputtering Yield Y [atoms/ion]")
        self.plot.axes.set_ylim(ymin=0.)
        self.plot.axes.set_xlim(xmin=-5., xmax=90.)
        self.plot.axes.legend()
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()

        return data, plotLabels


    def plot_ang_dep_mass_yields(self):
        ncp, ncp_proj, elements, elements_proj, masses, nr_energies, nr_angles, nr_total, energies, angles, mean_depth, refl_coeff, energ_refl_coeff, sputt_coeff, energ_sputt_coeff, last_index = self.get_data_from_serie_file()
        if last_index > nr_total:
            last_index = nr_total

        self.plot.fig.clf()
        self.plot.axes = self.plot.fig.add_subplot(projection="rectilinear")

        amu_yield = np.dot(sputt_coeff,masses)
            #ydata.append(sputt_coeff[:, i])
            #plotLabels.append(element)

        # fit yield with eckstein formula
        fit_params_string = ''
        if last_index >= 5:
            try:
                angle_distance_weights = np.ones(nr_total)
                for i in range(0, last_index-1):
                    angle_distance_weights[i] = 1./(angles[i+1]-angles[i])

                popt, pcov = scipy.optimize.curve_fit(self.eckstein_angle_fit, angles[:last_index], amu_yield[:last_index], sigma=angle_distance_weights[:last_index], p0=[amu_yield[0], 90., 1., 1., 1.6], bounds=(0., [np.max(amu_yield), 90., 10., 1., 10.]))
                angles_fit = np.arange(0.,90.,0.1)
                self.plot.axes.plot(angles_fit, self.eckstein_angle_fit(angles_fit, *popt), 'k--', label=f'Eckstein Fit', linewidth=1.)
                self.plot.axes.set_title(f'Fit: Y$_0$ = {np.round(popt[0], 3)} amu/ion, $\\alpha_0$ = {np.round(popt[1], 3)}°, b = {np.round(popt[2], 3)}, c = {np.round(popt[3], 3)}, f = {np.round(popt[4], 3)}')
                fit_params_string = f'Fit: Y0 = {np.round(popt[0], 3)} amu/ion, alpha0 = {np.round(popt[1], 3)}°, b = {np.round(popt[2], 3)}, c = {np.round(popt[3], 3)}, f = {np.round(popt[4], 3)}'

            except:
                pass

        self.plot.axes.plot(angles[:last_index], amu_yield[:last_index], 'o', label="SDTrimSP", color=self.first_color)

        data = []
        plotLabels = []

        if last_index > 0:
            data.append(angles[:last_index])
            data.append(amu_yield[:last_index])
            plotLabels.append("Angle of Incidence [°]")
            plotLabels.append("y [amu/ion]")
            plotLabels.append(fit_params_string)

        self.plot.axes.set_xlabel("Angle of Incidence $\\alpha$ [°]")
        self.plot.axes.set_ylabel("Sputtering Yield y [amu/ion]")
        self.plot.axes.set_ylim(ymin=0.)
        self.plot.axes.set_xlim(xmin=-5., xmax=90.)
        self.plot.axes.legend()
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()
        return data, plotLabels


    def eckstein_angle_fit(self, angles, Y0, alpha0, b, c, f):
        out_value = np.zeros(len(angles))
        #alpha0 = 90.

        for i, alpha in enumerate(angles):
            if alpha == 0.:
                out_value[i] = Y0
            else:
                out_value[i] = Y0 * np.cos((alpha/alpha0*np.pi/2)**c)**(-f)*np.exp(b*(1-1/np.cos((alpha/alpha0*np.pi/2)**c)))

        return out_value

    def plot_ang_dep_refl_coeff(self):
        ncp, ncp_proj, elements, elements_proj, masses, nr_energies, nr_angles, nr_total, energies, angles, mean_depth, refl_coeff, energ_refl_coeff, sputt_coeff, energ_sputt_coeff, last_index = self.get_data_from_serie_file()
        if last_index > nr_total:
            last_index = nr_total

        self.plot.fig.clf()
        self.plot.axes = self.plot.fig.add_subplot(projection="rectilinear")

        total_yield = np.sum(refl_coeff, axis=1)

        data = []
        plotLabels = []

        plot_counter = 0
        for i, element in enumerate(elements_proj):
            if np.max(refl_coeff[:, i]) > 0.:
                self.plot.axes.plot(angles[:last_index], refl_coeff[:last_index, i], 'o', label=element, color=self.colors[self.get_element_index(element)])

                if plot_counter == 0:
                    data.append(angles[:last_index])
                    plotLabels.append("Angle of Incidence [°]")
                data.append(refl_coeff[:last_index,i])
                plotLabels.append(element)

                plot_counter += 1
        if plot_counter > 1:
            self.plot.axes.plot(angles[:last_index], total_yield[:last_index], 'o', label="Total", color=self.first_color)

        self.plot.axes.set_xlabel("Angle of Incidence $\\alpha$ [°]")
        self.plot.axes.set_ylabel("Reflection Coefficient R")
        self.plot.axes.set_ylim(ymin=0.)
        self.plot.axes.set_xlim(xmin=-5., xmax=90.)
        self.plot.axes.legend()
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()
        return data, plotLabels


    def plot_ang_dep_mean_depth(self):
        ncp, ncp_proj, elements, elements_proj, masses, nr_energies, nr_angles, nr_total, energies, angles, mean_depth, refl_coeff, energ_refl_coeff, sputt_coeff, energ_sputt_coeff, last_index = self.get_data_from_serie_file()
        #print(mean_depth)
        if last_index > nr_total:
            last_index = nr_total

        self.plot.fig.clf()
        self.plot.axes = self.plot.fig.add_subplot(projection="rectilinear")

        self.plot.axes.plot(angles[:last_index], mean_depth[:last_index], 'o', label="Implantation Depth", color=self.first_color)

        data = []
        plotLabels = []

        if last_index > 0:
            data.append(angles[:last_index])
            data.append(mean_depth[:last_index])
            plotLabels.append("Angle of Incidence [°]")
            plotLabels.append("Implantation Depth [Å]")

        self.plot.axes.set_xlabel("Angle of Incidence $\\alpha$ [°]")
        self.plot.axes.set_ylabel("Implantation Depth [Å]")
        self.plot.axes.set_ylim(ymin=0.)
        self.plot.axes.set_xlim(xmin=-5., xmax=90.)
        #self.plot.axes.legend()
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()
        return data, plotLabels

    def plot_en_dep_sputter_yields(self):
        ncp, ncp_proj, elements, elements_proj, masses, nr_energies, nr_angles, nr_total, energies, angles, mean_depth, refl_coeff, energ_refl_coeff, sputt_coeff, energ_sputt_coeff, last_index = self.get_data_from_serie_file()
        if last_index > nr_total:
            last_index = nr_total

        self.plot.fig.clf()
        self.plot.axes = self.plot.fig.add_subplot(projection="rectilinear")

        data = []
        plotLabels = []

        total_yield = np.sum(sputt_coeff, axis=1)
        energy_distance_weights = np.ones(nr_total)

        # fit total yield with Eckstein fit
        # fit yield with eckstein formula
        # if last_index >= 5:
        #     try:
        #         for i in range(0, last_index-1):
        #             energy_distance_weights[i] = 1./(energies[i+1]-energies[i])
        #         popt, pcov = scipy.optimize.curve_fit(self.eckstein_energy_fit, energies[:last_index], total_yield[:last_index])
        #         energies_fit = np.arange(0., np.max(energies), 1.)
        #         self.plot.axes.plot(energies_fit, self.eckstein_energy_fit(energies_fit, *popt), 'k--', label=f'Eckstein Fit',
        #                             linewidth=1.)
        #         self.plot.axes.set_title(f'Fit: Q = {np.round(popt[0], 3)}, $\\mu$ = {np.round(popt[1], 3)}, $\\lambda$ = {np.round(popt[2],3)}, E$_t$$_h$ = {np.round(popt[3],3)} eV, $\\epsilon_L$ = {np.round(popt[4],3)}')
        #     except:
        #         pass

        plot_counter = 0
        for i, element in enumerate(elements):
            if np.max(sputt_coeff[:,i]) > 0.:
                self.plot.axes.plot(energies[:last_index], sputt_coeff[:last_index,i], 'o', label=element, color=self.colors[self.get_element_index(element)])

                if plot_counter == 0:
                    data.append(energies[:last_index])
                    plotLabels.append("Kinetic Energy [eV]")
                data.append(sputt_coeff[:last_index,i])
                plotLabels.append(element)

                plot_counter += 1


        if plot_counter > 1:
            self.plot.axes.plot(energies[:last_index], total_yield[:last_index], 'o', label="Total", color=self.first_color)
            data.append(total_yield[:last_index])
            plotLabels.append("Total")

        self.plot.axes.set_xlabel("Kinetic Energy E [eV]")
        self.plot.axes.set_ylabel("Sputtering Yield Y [atoms/ion]")
        self.plot.axes.set_yscale("log")
        self.plot.axes.set_xscale("log")
        self.plot.axes.legend()
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()

        return data, plotLabels


    def plot_en_dep_mass_yields(self):
        ncp, ncp_proj, elements, elements_proj, masses, nr_energies, nr_angles, nr_total, energies, angles, mean_depth, refl_coeff, energ_refl_coeff, sputt_coeff, energ_sputt_coeff, last_index = self.get_data_from_serie_file()
        if last_index > nr_total:
            last_index = nr_total

        self.plot.fig.clf()
        self.plot.axes = self.plot.fig.add_subplot(projection="rectilinear")

        amu_yield = np.dot(sputt_coeff,masses)
            #ydata.append(sputt_coeff[:, i])
            #plotLabels.append(element)

        # fit yield with eckstein formula
        # if last_index >= 5:
        #     try:
        #         energy_distance_weights = np.ones(nr_total)
        #         for i in range(0, last_index-1):
        #             energy_distance_weights[i] = 1./(energies[i+1]-energies[i])
        #
        #         popt, pcov = scipy.optimize.curve_fit(self.eckstein_energy_fit, energies[:last_index], amu_yield[:last_index], sigma=energy_distance_weights[:last_index], bounds=(0., 1000.))
        #         energies_fit = np.arange(0.,np.max(energies),1.)
        #         self.plot.axes.plot(energies_fit, self.eckstein_energy_fit(energies_fit, *popt), 'k--', label=f'Eckstein Fit', linewidth=1.)
        #         self.plot.axes.set_title(f'Fit: Q = {np.round(popt[0], 3)}, $\\mu$ = {np.round(popt[1], 3)}, $\\lambda$ = {np.round(popt[2],3)}, E$_t$$_h$ = {np.round(popt[3],3)} eV, $\\epsilon_L$ = {np.round(popt[4],3)}')
        #     except:
        #         pass

        self.plot.axes.plot(energies[:last_index], amu_yield[:last_index], 'o', label="SDTrimSP", color=self.first_color)

        data = []
        plotLabels = []

        if last_index > 0:
            data.append(energies[:last_index])
            data.append(amu_yield[:last_index])
            plotLabels.append("Kinetic Energy [eV]")
            plotLabels.append("y [amu/ion]")

        self.plot.axes.set_xlabel("Kinetic Energy E [eV]")
        self.plot.axes.set_ylabel("Sputtering Yield y [amu/ion]")
        self.plot.axes.set_yscale("log")
        self.plot.axes.set_xscale("log")
        self.plot.axes.legend()
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()
        return data, plotLabels


    def eckstein_energy_fit(self, en, q, mu, lam, Eth, eps_l):
        eps = en * eps_l
        s_n_krc = 0.5 * np.log(1 + 1.2288 * eps) / (eps + 0.1728 * np.sqrt(eps) + 0.008 * eps ** 0.1504)
        out_value = q * s_n_krc * (en / Eth - 1) ** mu / (lam + (en / Eth - 1) ** mu)
        return out_value

    # def eckstein_energy_fit(self, en, m1, m2, z1, z2, q, mu, lam, Eth):
    #     a = (9*np.pi**2/128.)**(1./3.) * 5.292e-11 * (z1**(2./3.) + z2**(2./3.))**(-0.5)
    #     eps = en * m2/(m1+m2) * a / z1/z2 /(1.602e-19)**2
    #     s_n_krc = 0.5 * np.log(1 + 1.2288 * eps) / (eps + 0.1728 * np.sqrt(eps) + 0.008 * eps ** 0.1504)
    #     out_value = q * s_n_krc * (en / Eth - 1) ** mu / (lam + (en / Eth - 1) ** mu)
    #     return out_value

    def plot_en_dep_refl_coeff(self):
        ncp, ncp_proj, elements, elements_proj, masses, nr_energies, nr_angles, nr_total, energies, angles, mean_depth, refl_coeff, energ_refl_coeff, sputt_coeff, energ_sputt_coeff, last_index = self.get_data_from_serie_file()
        if last_index > nr_total:
            last_index = nr_total

        self.plot.fig.clf()
        self.plot.axes = self.plot.fig.add_subplot(projection="rectilinear")

        total_yield = np.sum(refl_coeff, axis=1)

        data = []
        plotLabels = []

        plot_counter = 0
        for i, element in enumerate(elements_proj):
            if np.max(refl_coeff[:, i]) > 0.:
                self.plot.axes.plot(energies[:last_index], refl_coeff[:last_index, i], 'o', label=element, color=self.colors[self.get_element_index(element)])

                if plot_counter == 0:
                    data.append(energies[:last_index])
                    plotLabels.append("Kinetic Energy [eV]")
                data.append(refl_coeff[:last_index,i])
                plotLabels.append(element)

                plot_counter += 1
        if plot_counter > 1:
            self.plot.axes.plot(energies[:last_index], total_yield[:last_index], 'o', label="Total", color=self.first_color)

        self.plot.axes.set_xlabel("Kinetic Energy E [eV]")
        self.plot.axes.set_ylabel("Reflection Coefficient R")
        self.plot.axes.set_yscale("log")
        self.plot.axes.set_xscale("log")
        self.plot.axes.legend()
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()
        return data, plotLabels


    def plot_en_dep_mean_depth(self):
        ncp, ncp_proj, elements, elements_proj, masses, nr_energies, nr_angles, nr_total, energies, angles, mean_depth, refl_coeff, energ_refl_coeff, sputt_coeff, energ_sputt_coeff, last_index = self.get_data_from_serie_file()
        #print(mean_depth)
        if last_index > nr_total:
            last_index = nr_total

        self.plot.fig.clf()
        self.plot.axes = self.plot.fig.add_subplot(projection="rectilinear")

        self.plot.axes.plot(energies[:last_index], mean_depth[:last_index], 'o', label="Implantation Depth", color=self.first_color)

        data = []
        plotLabels = []

        if last_index > 0:
            data.append(energies[:last_index])
            data.append(mean_depth[:last_index])
            plotLabels.append("Kinetic Energy [eV]")
            plotLabels.append("Implantation Depth [Å]")

        self.plot.axes.set_xlabel("Kinetic Energy E [eV]")
        self.plot.axes.set_ylabel("Implantation Depth [Å]")
        self.plot.axes.set_yscale("log")
        self.plot.axes.set_xscale("log")
        self.plot.fig.tight_layout()
        #self.plot.axes.legend()
        self.plot.fig.canvas.draw_idle()
        return data, plotLabels

    def get_data_from_depth_file(self, filename):

        # read depth file
        # skip empty lines, this allows consistency for files with multiple elements between SDTrimSP 6.01 and 6.06 or newer
        with open(self.workingDir + "/" + filename, 'r') as content_file:
            content = [line for line in content_file.readlines() if line.strip()]

	    # read version of SDtrimSP for file
        version = content[0].split()[2]
	
	    # set linenumber between blocks of informatin according to version
	    
        if version == "6.03":
            addintional_lines = 9
        else:
            addintional_lines = 5



        # read number of elements
        file_ncp = int(content[2].split()[0])

        # get number of depth distributions
        nr_of_depth_steps = np.zeros(file_ncp, dtype=int)
        nr_of_projectiles = np.zeros(file_ncp, dtype=int)
        data_start_line = np.zeros(file_ncp, dtype=int)

        last_nr_of_depth_steps =0
        depth_step_index = 4
        for i in range(file_ncp):
            depth_step_index = depth_step_index + bool(i)*addintional_lines+last_nr_of_depth_steps
            data_start_line[i] = depth_step_index+3
            nr_of_depth_steps[i] = int(content[depth_step_index].split()[0])
            nr_of_projectiles[i] = int(float(content[depth_step_index].split()[1]))
            
            last_nr_of_depth_steps = nr_of_depth_steps[i]
        #print("nr of depth steps", nr_of_depth_steps)

        # get elements
        file_elements = []
        for i in range(file_ncp):
            element_line_index = int(2 + i* (4 + 1) + np.sum(nr_of_depth_steps[:i]) + 1)
            file_elements.append(content[element_line_index].split()[-1])

        max_nr_depth_steps = np.max(nr_of_depth_steps)
        nr_of_columns = len(content[data_start_line[0]].split())
        depth_data = np.zeros((file_ncp, max_nr_depth_steps, nr_of_columns))

        for i in range(file_ncp):
            for j in range(nr_of_depth_steps[i]):
                line = content[data_start_line[i] + j].split()
                for k in range(nr_of_columns):
                    depth_data[i, j, k] = float(line[k])

        return file_ncp, file_elements, nr_of_depth_steps, max_nr_depth_steps, nr_of_projectiles, depth_data

    def get_data_from_depth_damage_file(self, filename):
        with open(self.workingDir + "/" + filename, 'r') as content_file:
            content = content_file.readlines()


        # read number of elements
        file_ncp = int(content[2].split()[0])
        nr_of_projectiles = int(float(content[2].split()[1]))

        # get number of depth distributions
        nr_of_depth_steps = np.zeros(file_ncp, dtype=int)
        #nr_of_projectiles = np.zeros(file_ncp, dtype=int)
        data_start_line = np.zeros(file_ncp, dtype=int)
        for i in range(file_ncp):
            depth_step_index = int(3 + i* (4 + 1 + 5) + np.sum(nr_of_depth_steps[:i]) + 1)
            data_start_line[i] = depth_step_index + 3
            nr_of_depth_steps[i] = int(content[depth_step_index].split()[0])
            #nr_of_projectiles[i] = int(float(content[depth_step_index].split()[1]))
        #print("nr of depth steps", nr_of_depth_steps)

        # get elements
        file_elements = []
        for i in range(file_ncp):
            element_line_index = int(2 + i* (4 + 1 + 5) + np.sum(nr_of_depth_steps[:i]) + 1)
            file_elements.append(content[element_line_index].split()[-1])

        max_nr_depth_steps = np.max(nr_of_depth_steps)
        nr_of_columns = len(content[data_start_line[0]].split())
        depth_data = np.zeros((file_ncp, max_nr_depth_steps, nr_of_columns))

        for i in range(file_ncp):
            for j in range(nr_of_depth_steps[i]):
                line = content[data_start_line[i] + j].split()
                for k in range(nr_of_columns):
                    depth_data[i, j, k] = float(line[k])

        return file_ncp, file_elements, nr_of_depth_steps, max_nr_depth_steps, nr_of_projectiles, depth_data

    def plot_proj_stops_over_depth(self):
        file_ncp, file_elements, nr_of_depth_steps, max_nr_depth_steps, nr_of_projectiles, depth_data = self.get_data_from_depth_file("depth_proj.dat")

        self.plot.fig.clf()
        self.plot.axes = self.plot.fig.add_subplot(projection="rectilinear")

        depth_x_values = depth_data[:, :, 0]
        depth_delta = depth_x_values[:, 1] - depth_x_values[:, 0]
        stops = depth_data[:, :, 1]

        data = []
        plotLabels = []

        for k in range(file_ncp):
            if np.max(stops[k]) > 0. and nr_of_projectiles[k] != 0:
                self.plot.axes.plot(depth_x_values[k, :nr_of_depth_steps[k]], stops[k,:nr_of_depth_steps[k]]/np.sum(stops[k,:nr_of_depth_steps[k]])/depth_delta[k], label=file_elements[k], linewidth=2, color=self.colors[self.get_element_index(file_elements[k])]) # normalize for stopped projectiles and depth interval
                data.append(depth_x_values[k, :])
                data.append(stops[k,:]/np.sum(stops[k,:nr_of_depth_steps[k]])/depth_delta[k])
                plotLabels.append(f"Depth ({self.elements[k]}) [Å]")
                plotLabels.append(f"Stopping Probability ({self.elements[k]}) [1/Å]")
        # plt.plot(conc_array[k, hist_counter, :], linewidth=2)
        # plt.ylim([-0.1, 1.1])
        self.plot.axes.set_ylim(ymin=0.0)
        self.plot.axes.set_xlim(xmin=0.0)
        self.plot.axes.legend()
        self.plot.axes.set_ylabel("Stopping Probability [1/Å]")
        self.plot.axes.set_xlabel("Depth [Å]")
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()

        return data, plotLabels

    def plot_proj_energy_loss_over_depth(self):
        file_ncp, file_elements, nr_of_depth_steps, max_nr_depth_steps, nr_of_projectiles, depth_data = self.get_data_from_depth_file("depth_proj.dat")

        self.plot.fig.clf()
        self.plot.axes = self.plot.fig.add_subplot(projection="rectilinear")

        depth_x_values = depth_data[:, :, 0]
        depth_delta = depth_x_values[:, 1] - depth_x_values[:, 0]
        nucl_loss = depth_data[:, :, 3] * 1e6 # convert from MeV to eV
        elec_loss = depth_data[:, :, 4] * 1e6 # convert from MeV to eV
        total_loss = nucl_loss + elec_loss

        data = []
        plotLabels = []
        for k in range(file_ncp):
            if (np.max(nucl_loss[k]) > 0. or np.max(elec_loss[k]) > 0.) and nr_of_projectiles[k] != 0:
                nucl_plot, = self.plot.axes.plot(depth_x_values[k, :nr_of_depth_steps[k]], nucl_loss[k,:nr_of_depth_steps[k]]/nr_of_projectiles[k]/ depth_delta[k], linestyle= '--', label=file_elements[k]+' (nuclear)', linewidth=2, color=self.colors[self.get_element_index(file_elements[k])])
                self.plot.axes.plot(depth_x_values[k, :nr_of_depth_steps[k]],
                                    elec_loss[k, :nr_of_depth_steps[k]] / nr_of_projectiles[k] / depth_delta[k], linestyle= ':', color=nucl_plot.get_color(),
                                    label=file_elements[k] + ' (electronic)', linewidth=2) # normalize for number of projectiles and depth interval
                self.plot.axes.plot(depth_x_values[k, :nr_of_depth_steps[k]],
                                    total_loss[k, :nr_of_depth_steps[k]] / nr_of_projectiles[k]/ depth_delta[k], linestyle= '-', color=nucl_plot.get_color(),
                                    label=file_elements[k] + ' (total)', linewidth=2)
                data.append(depth_x_values[k, :])
                data.append(nucl_loss[k,:]/nr_of_projectiles[k]/ depth_delta[k])
                data.append(elec_loss[k, :] / nr_of_projectiles[k] / depth_delta[k])
                data.append(total_loss[k, :] / nr_of_projectiles[k] / depth_delta[k])
                plotLabels.append(f"Depth ({self.elements[k]}) [Å]")
                plotLabels.append(f"Energy Loss (normalized) ({self.elements[k]}, nuclear) [eV/Å]")
                plotLabels.append(f"Energy Loss (normalized) ({self.elements[k]}, electronic) [eV/Å]")
                plotLabels.append(f"Energy Loss (normalized) ({self.elements[k]}, total) [eV/Å]")
        # plt.plot(conc_array[k, hist_counter, :], linewidth=2)
        # plt.ylim([-0.1, 1.1])
        self.plot.axes.set_ylim(ymin=0.0)
        self.plot.axes.set_xlim(xmin=0.0)
        self.plot.axes.legend()
        self.plot.axes.set_ylabel("Energy Loss (normalized) [eV/Å]")
        self.plot.axes.set_xlabel("Depth [Å]")
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()
        return data, plotLabels

    def plot_vacancies_over_depth(self):
        # check for existence of 'depth_damage.dat' (contains damage information in versions 6.05 or newer)
        # --> use this file for vacancy calculations if it exists, otherwise 'depth_recoil.dat'
        use_depth_damage = False

        if os.path.exists(f'{self.workingDir}/depth_damage.dat'):
            use_depth_damage = True

        if use_depth_damage:
            file_ncp, file_elements, nr_of_depth_steps, max_nr_depth_steps, nr_of_projectiles, depth_data = self.get_data_from_depth_damage_file(
                "depth_damage.dat")
        else:
            file_ncp, file_elements, nr_of_depth_steps, max_nr_depth_steps, nr_of_projectiles, depth_data = self.get_data_from_depth_file("depth_recoil.dat")

        self.plot.fig.clf()
        self.plot.axes = self.plot.fig.add_subplot(projection="rectilinear")

        depth_x_values = depth_data[:, :, 0]
        depth_delta = depth_x_values[:, 1] - depth_x_values[:, 0]
        #print("depth_delta", depth_delta[0])
        if use_depth_damage:
            vacancies = depth_data[:, :, -1]
        else:
            vacancies = depth_data[:, :, 7]
            nr_of_projectiles = nr_of_projectiles[0]

        data = []
        plotLabels = []
        nr_of_plots = 0
        for k in range(file_ncp):
            #if np.max(vacancies[k]) > 0. and nr_of_projectiles[k] != 0:
            if np.max(vacancies[k]) > 0.:
                nr_of_plots += 1
                self.plot.axes.plot(depth_x_values[k, :nr_of_depth_steps[k]],
                                    vacancies[k, :nr_of_depth_steps[k]] / nr_of_projectiles / depth_delta[k], label=file_elements[k],
                                    linewidth=2, color=self.colors[self.get_element_index(file_elements[k])])  # normalize for all projectiles and depth interval
                data.append(depth_x_values[k, :])
                data.append(vacancies[k, :] / nr_of_projectiles / depth_delta[k])
                plotLabels.append(f"Depth ({self.elements[k]}) [Å]")
                plotLabels.append(f"Vacancies ({self.elements[k]}) [1/Å/ion]")
        # plot total vacancies if more than one element is plotted and all depth deltas are the same
        if nr_of_plots > 1 and all(x == depth_delta[0] for x in depth_delta):
            self.plot.axes.plot(depth_x_values[np.argmax(nr_of_depth_steps), :max_nr_depth_steps],
                                np.sum(vacancies[:, :max_nr_depth_steps],axis=0) / nr_of_projectiles / depth_delta[0],
                                label=f"Total",
                                linewidth=2, color=self.first_color)

            data.append(depth_x_values[np.argmax(nr_of_depth_steps), :])
            data.append(np.sum(vacancies[:, :max_nr_depth_steps],axis=0) / nr_of_projectiles / depth_delta[0])
            plotLabels.append(f"Depth (Total) [Å]")
            plotLabels.append(f"Vacancies (Total) [1/Å/ion]")
        # plt.plot(conc_array[k, hist_counter, :], linewidth=2)
        # plt.ylim([-0.1, 1.1])
        self.plot.axes.set_ylim(ymin=0.0)
        self.plot.axes.set_xlim(xmin=0.0)
        self.plot.axes.legend()
        self.plot.axes.set_ylabel("Vacancies [1/Å/ion]")
        self.plot.axes.set_xlabel("Depth [Å]")

        self.plot.axes.set_title(f'Total Vacancies: {np.round(np.sum(vacancies)/ nr_of_projectiles, 2)} / Ion')
        self.plot.fig.tight_layout()
        self.plot.fig.canvas.draw_idle()
        return data, plotLabels
