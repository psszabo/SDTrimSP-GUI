**SDTrimSP GUI - a graphical user interface for SDTrimSP to simulate sputtering, ion implantation and the dynamic effects of ion irradiation**

Copyright(C) 2022, Paul S. Szabo, David Weichselbaum, Herbert Biber, Christian Cupak, Andreas Mutzke, Richard A. Wilhelm, Friedrich Aumayr

The GUI is publicly available online on github (https://github.com/psszabo/SDTrimSP-GUI) and distributed under the GPLv3 license. The GUI is described in the manuscript 
P. S. Szabo, et al. Nucl. Instrum. Meth. Phys. Res. B  (2022) https://doi.org/10.1016/j.nimb.2022.04.008. One condition for free usage of the GUI program is that this manuscript is cited in any publication that presents results achieved with the GUI.

This GUI companion program for the simulation code SDTrimSP is written in Python 3 based on the PyQt5 package that implements the software  toolkit Qt for creating graphical user interfaces with Python. It has been tested under Python 3.7, 3.8, 3.9, 3.10, and 3.11 on Linux, Windows and Mac operating systems. It supports SDTrimSP versions 6.01 and newer, with 6.06 being the latest available version at the time of the publication of this article. SDTrimSP itself is not included in this repository, if you want to acquire it, please contact sdtrimsp@ipp.mpg.de.

An extended version of the GUI, called **BCA-GUIDE**, for running both SDTrimSP and TRIDYN simulations has recently been developed (available at https://github.com/atomicplasmaphysics/BCA-GUIDE, see also https://www.iap.tuwien.ac.at/www/atomic/bca-guis).

**Setup**

- 	If not already installed, download and install Python 3 (https://www.python.org/downloads/). We recommend one of the above mentioned versions 3.7, 3.8, 3.9, 3.10, or 3.11. 

-	Install following Python packages: scipy, matplotlib, numpy and PyQt5. 

**Running the GUI**

-	The GUI can be started by executing "main.py" with Python.

-	Upon first starting the GUI, the locations for the main SDTrimSP folder (which contains the subfolders "bin", "case", "doc", etc.) and the SDTrimSP binary (located f.e. "SDTrimSP_6.01/bin/linux.SEQ/") in have to be set. 

-	Following this setup, an SDTrimSP simulation can be started by setting up simulation parameters on the main	screen of the GUI and pressing the green "Play" button. The tabs below this button allow access to different views of the GUI. "Files preview" shows the text input files that are created by the GUI and that are then read by SDTrimSP to run the simulation. "SDTrimSP log" shows the console outputs of SDTrimSP and gives 	information on simulation progress and possible errors that might have occurred. "Output files" gives a preview of the text output files from the SDTrimSP simulation. Finally, "Simulation results" allows the graphical evaluation of the simulation and some quantities can already be plotted, while the simulation is still running. Furthermore, previously executed simulations can be evaluated with the GUI.
