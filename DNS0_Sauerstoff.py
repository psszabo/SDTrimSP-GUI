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


'''
CITE from Tridyn manual:

Note! For compounds with a very high atomic density, the atomic density of the non-principal
component may become negative according to eq. (21). This represents no problem for the
processing in TRIDYN.
---

The results here give an estimate for the needed density to match the desired composition density.
Also the calculation is actually only valid for two compound targets.

'''

class Target_Material:
    "class for targets"

    g_to_amu = 1. / 1.66  # [amu*cm^3/g*A^3]

    def __init__(self, name):
        self.name = name

    def qus_normalizer(self):
        "normalizes the target composition, which can be useful for removing C from XPS results. Therefore just set 'qu' of C (and the other unwanted like N)to zero."
        old_sum = sum(self.qus)
        self.qus = [float(i) / old_sum for i in self.qus ]
        return self.qus

    def qus_normalizer_one_fixed(self,index):
        "normalizes the target composition, but with one component 'index' keept constant, as it is needed to perform simulations with a specific ammount of projectiles in the target"
        #self.qus_copy = [(1-self.qus[index])*float(self.qus[i]) / (sum(self.qus)-self.qus[index]) for i in range(len(self.qus)) if i !=index]

        for i in range(len(self.qus)):
            if i!= index:
                self.qus[i] = (1 - self.qus[index]) * float(self.qus[i]) / (sum(self.qus) - self.qus[index])

        return self.qus


    def mean_amu(self):
        "calculates and returns mean amu per atom of the desired target"
        self.target_amu =sum([self.qus[i]*self.amus[i] for i in range(len(self.qus))])
        return self.target_amu

    def atomic_density(self):#,symbols, ratios, densities, target_density):
        "calculates the atomic density of the target material according to its composition and the density.\n density must be in g/cm^3\n"
        mean_amu = self.mean_amu()
        self.DNSO = self.density*self.g_to_amu/mean_amu
        return self.DNSO

    def mean_atomic_nonoxygendensity(self):
        "calculates a mean atomic density for the non-oxygen elements in the target"
        index = self.symbols.index("O")
        self.DNSO_nonOx = 1./((sum([self.qus[i] for i in range(len(self.qus)) if i != index])))*(sum([self.dns0[i]*self.qus[i] for i in range(len(self.qus)) if i != index]))
        return self.DNSO_nonOx

    def calculate_atomic_oxygendensity(self):
        "calculates the atomic density of oxygen in the composition for SDTrimSP"
        index = self.symbols.index("O")
        DNSO = self.atomic_density()
        DNSO_nonOx = self.mean_atomic_nonoxygendensity()
        at_ox_density = 1./((1./(self.qus[index]))* ( (1./DNSO) -  ((1-self.qus[index]) / DNSO_nonOx )))

        return at_ox_density
        #print(at_ox_density

    def atomic_density_to_sputtering(self):
        "converts atoms per A^3 to 10^15 cm^2/nm"
        try:
            converted_density = self.target_amu*self.DNSO*100
        except:
            converted_density = self.mean_amu() * self.atomic_density()* 100
        return converted_density

    def atomic_density_to_g_per_ccm(self):
        "converts resulting target density (generated from SDTrimSP!) in atoms/A^3 to g/ccm"
        try:
            converted_target_density = (self.target_density / self.g_to_amu)*self.target_amu
        except:
            converted_target_density = (self.target_density / self.g_to_amu) * self.mean_amu()
        return converted_target_density


    def dns0_all_the_same(self):
        "returns value of dns0, which is to be set for all elements to fit the required density"
        mean_amu = self.mean_amu()
        self.dnsO_forall = self.density * self.g_to_amu/ mean_amu
        return self.dnsO_forall


if __name__ == '__main__':
    symbol = ["He", "Ca", "Fe", "Mg", "Si", "O"]
    qu = [0.0, 0.0469, 0.0234, 0.081, 0.165, 0.6837]
    dns0 = [0.01878, 0.02314,  0.08491,0.04306,0.04994, 0.136]
    amus= [4.003,40.08,55.]

    elements = [[symbol[i], qu[i],dns0[i]] for i in range(len(symbol))]


    #--------------
    #Wollastonite
    #--------------

    Wo = Target_Material("Wollastonite")
    Wo.density = 3.
    Wo.symbols = [ "Ca", "Si", "O"]
    Wo.qus = [ 0.2,0.2,0.6]
    Wo.amus = [40.08,28.09,16.00]
    Wo.dns0 = [ 0.02314, 0.04994, 0.136]



    #oxygen = 0.314261308926 - result obtained with this script. is less than 10% off for density in g/ccm
    Wo.target_density=0.686951E-01    #Value generated by SDTrim, needed to calculate density SDTrim uses (compare with Wo.density, which is approx 3g/ccm

    #--------------
    #Augite (XPS Batch 1 w.o. C)
    #--------------


    Aug = Target_Material("Augite")
    Aug.density = 3.
    Aug.symbols = ["He", "Ca", "Fe", "Mg", "Si", "O"]
    Aug.qus = [0.0000000000000000, 0.0469000000000000, 0.0234000000000000, 0.0810000000000000, 0.1650000000000000, 0.6837000000000000]
    Aug.amus= [4.003,40.08,55.85,24.31,28.09,16.]
    Aug.dns0 = [0.01878, 0.02314,  0.08491,0.04306,0.04994, 0.08]

    Aug.qus_normalizer()


    #oxygen = 0.136 - comes from calculation made in my notebook. the good result was pure coincidence, as the formua was wrong.
    Aug.target_density=0.799064E-01     #Value generated by SDTrim, needed to calculate density SDTrim uses (compare with Aug.density, which is approx 3g/ccm

    #oxygen = 0.145137624332 - result obtained with this script. is less than 10% off for density in g/ccm
    Aug.target_density=0.819797E-01     #Value generated by SDTrim, needed to calculate density SDTrim uses (compare with Aug.density, which is approx 3g/ccm

    #oxygen = 0.17 - fitted density - gives 2.98990950858 g/ccm in SDTrim
    Aug.target_density=0.868870E-01


    #--------------
    #Augite (ERDA Analysis Sample Si22, noH, noC)
    #--------------


    Aug_ERD = Target_Material("Augite_ERDA")
    Aug_ERD.density = 3.
    Aug_ERD.symbols = ["He", "Ca", "Fe", "Mg", "Si", "O","H","C"]
    Aug_ERD.qus = [0.0000000000000000, 0.01810000000000, 0.06000000000000, 0.0890000000000000, 0.205000000000000, 0.60300000000000, 0.0141, 0.0107]
    Aug_ERD.amus= [4.003,40.08,55.85,24.31,28.09,16.,1.008,12.01]
    Aug_ERD.dns0 = [0.01878, 0.02314,  0.08491,0.04306,0.04994, 0.12847279715,0.04231,0.11331]

    print(Aug_ERD.qus_normalizer())


    #oxygen = 0.17 - used for XPS-nonC Augite - gives 3.15578207915 g/ccm in SDTrim
    Aug_ERD.target_density = 0.872470E-01

    #oxygen = 0.12847279715 - comes from calculation made in my notebook - gives 2.86503141624 g/ccm in SDTrim

    Aug_ERD.target_density = 0.792087E-01

    #oxygen = 0.2 - approxy for higher densities (mindat.org says 3.19-3.56 g/ccm for Augite, calculated 3.31, this value vor oxygen gives 3.31174637302 g/ccm in SDTrim
    Aug_ERD.target_density =0.915589E-01


    #--------------
    #Augite (XPS Batch 1 w.o. C), with 20% Helium
    #--------------


    Aug_wHe=Target_Material("Augite_with_Helium")
    Aug_wHe.density = 3.
    Aug_wHe.symbols = ["He", "Ca", "Fe", "Mg", "Si", "O"]
    Aug_wHe.qus = [0.2000000000000000, 0.0469000000000000, 0.0234000000000000, 0.0810000000000000, 0.1650000000000000, 0.6837000000000000]
    Aug_wHe.amus= [4.003,40.08,55.85,24.31,28.09,16.]
    Aug_wHe.dns0 = [0.01878, 0.02314,  0.08491,0.04306,0.04994, 0.08]

    Aug_wHe.qus_normalizer_one_fixed(0)
    print("Aug_qu with He:")
    print(Aug_wHe.qus)
    print("---")


    #--------------
    #Enstatite
    #--------------

    En = Target_Material("Enstatite")
    En.density = 3.3
    En.symbols = ["Mg","Si","O"]
    En.qus = [ 0.2,0.2,0.6]
    En.amus= [24.31,28.09,16.]
    En.dns0= [0.04306,0.04994, 0.08]


    #oxygen = 0.08 - gives 2.0640169751999995 g/ccm in SDTrim

    En.target_density = 0.619215E-01

    #oxygen = 0.4 - comes from calculation made in my notebook - gives 3.2841841188799994 g/ccm in SDTrim
    En.target_density = 0.985271E-01

    #--------------
    #Enstatite_Noah_Paper
    #--------------

    Enn = Target_Material("Enstatite_Noah")
    Enn.density = 3.3
    Enn.symbols = ["Mg","Si","Fe","Al","O"]
    Enn.qus = [ 0.1961,0.1891,0.0134,0.0028,0.5986]
    Enn.amus= [24.31,28.09,55.85,26.98,16.]
    Enn.dns0= [0.04306,0.04994, 0.08491 ,0.06022,0.08]


    #oxygen = 0.08 - gives 2.0640169751999995 g/ccm in SDTrim

    Enn.target_density = 0.619215E-01

    #oxygen = 0.4 - comes from calculation made in my notebook - gives 3.2841841188799994 g/ccm in SDTrim
    Enn.target_density = 0.985271E-01


    #--------------
    #Diopsit
    #--------------

    Di = Target_Material("Diopsit")
    Di.density = 3.4
    Di.symbols = ["Mg","Ca","Fe","Si","O"]
    Di.qus = [ 0.1106,0.0892,0.0068,0.1956,0.5978]
    Di.amus= [24.31,40.08,55.85,28.09,16.]
    Di.dns0= [0.04306,0.02314,0.08491,0.04994, 0.04291]


    #Di.qus_normalizer()

    #oxygen =  0.8 gives  g/ccm in SDTrim

    Di.target_density = 0.895468E-01

    #oxygen =  1.5 gives  g/ccm in SDTrim

    Di.target_density =0.924332E-01


    #oxygen =  3.0 gives  g/ccm in SDTrim

    Di.target_density =0.941677E-01

    #oxygen = - 0.5083745988811038 comes from calculation made in my notebook - gives  g/ccm in SDTrim
    #Di.target_density = 0.862367E-01


    #--------------
    #Labradorit
    #--------------

    La = Target_Material("Labradorit")
    La.density = 2.69
    La.symbols = ["Fe","Na","Ca","Al","Si","O"]
    La.qus = [0.0018,0.0244,0.0471 ,0.1235,0.1861,0.6171]
    La.amus= [55.85,22.99,40.08,26.98,28.09,16.]
    La.dns0= [0.08491,0.04306,0.02314,0.06022 ,0.04994, 0.08]



    #oxygen =  - gives  g/ccm in SDTrim

    La.target_density = 0.619215E-01

    #oxygen = - comes from calculation made in my notebook - gives  g/ccm in SDTrim
    La.target_density = 0.985271E-01



    #--------------
    #Magnesiumsulfit
    #--------------

    Ms = Target_Material("Magnesiumsulfit")
    Ms.density = 2.66
    Ms.symbols = ["Mg","S","O"]
    Ms.qus = [0.165,0.165,0.67]
    Ms.amus= [24.31,32.07,16.]
    Ms.dns0= [0.04306,0.03888,0.04291]





    #oxygen = original form SDTrimSP
    Ms.target_density =  0.422123E-01


    #oxygen = with dsn0_O = 0.15, comes from notepad
    Ms.target_density =   0.797298E-01


    #--------------
    #Magnesiumsulfit
    #--------------

    MsH = Target_Material("Magnesiumsulfit+H2O")
    MsH.density = 2.445
    MsH.symbols = ["Mg","S","H","O"]
    MsH.qus = [0.111, 0.111,  0.222,  0.556]
    MsH.amus= [24.31,32.07,1.0,16.]
    MsH.dns0= [0.04306,0.03888,0.04231,0.04291]


    #oxygen = with dsn0_O = 0.15, comes from MgSo4
    MsH.target_density =  0.695101E-01

    #oxygen = with dsn0_O = 0.2
    MsH.target_density =  0.742957E-01

    #oxygen = with dsn0_O = 10.
    MsH.target_density =  0.9315E-01


    #all dns0 egual to 0.09579047372397177 ( outcome of dns0_all_the_same())
    MsH.target_density = 0.957905E-01

    #--------------
    #Magnesiumsulfit
    #--------------

    Ms7H = Target_Material("Magnesiumsulfit+7_H2O")
    Ms7H.density = 1.68
    Ms7H.symbols = ["Mg","S","H", "O"]
    Ms7H.qus = [0.037, 0.037,  0.519,  0.407]
    Ms7H.amus= [24.31,32.07,1.0,16.]
    Ms7H.dns0= [0.04306,0.03888,0.04231,0.04291]




    #oxygen = with dsn0_O = 0.15, comes from MgSo4
    Ms7H.target_density =  0.695101E-01

    #oxygen = with dsn0 according to all the same
    Ms7H.target_density =  0.111006E+00


    #--------------
    #Sulfur Dioxide
    #--------------

    Sd = Target_Material("Sulfurdioxide")
    Sd.density = 1.92
    Sd.symbols = ["S","O"]
    Sd.qus = [0.33,0.67]
    Sd.amus= [32.07,16.]
    Sd.dns0= [0.03888,0.04291]





    #oxygen = using 0.15 like for MgSO4
    Sd.target_density =  0.824376E-01

    #oxygen = using 0.07, a bit above notepad outcome
    Sd.target_density = 0.580210E-01

    #oxygen = using 0.67, notepad outcome
    Sd.target_density = 0.566132E-01

    #oxygen = using 0.6
    Sd.target_density = 0.531056E-01


    #oxygen = using 0.63
    Sd.target_density = 0.546489E-01


    #--------------
    #Testmaterial
    # #--------------

    Test = Target_Material("Testmaterial")
    Test.density = 5.
    Test.symbols = ["He", "Ca", "Fe", "Mg", "Si", "O"]
    Test.qus = [0.0000000000000000, 0.0, 0.00000000000, 0.000000000100, 0.0, 0.99999999]
    Test.amus= [4.003,40.08,55.85,24.31,28.09,16.]
    Test.dns0 = [0.04306,0.04994, 0.08]

    Test.qus_normalizer()

    # print(Test.atomic_density()
    # print(Test.calculate_atomic_oxygendensity()
    #
    # print(Wo.atomic_density()
    # print(Wo.calculate_atomic_oxygendensity()

    print("Augit_xps")
    print(Aug.mean_amu())
    print(Aug.atomic_density())
    print(Aug.calculate_atomic_oxygendensity())

    print(Aug.atomic_density_to_sputtering())
    print(Aug.atomic_density_to_g_per_ccm())

    print("Augit_erda")

    print(Aug_ERD.mean_amu())
    print(Aug_ERD.atomic_density())
    print(Aug_ERD.calculate_atomic_oxygendensity())

    print(Aug_ERD.atomic_density_to_sputtering())
    print(Aug_ERD.atomic_density_to_g_per_ccm())

    print("\nWollastonite")
    print(Wo.calculate_atomic_oxygendensity())
    print(Wo.atomic_density_to_g_per_ccm())
    print(f'{"#"*50}')
    print(Wo.atomic_density())
    print(f'{"#"*50}')

    print("Enstatite")
    print(En.calculate_atomic_oxygendensity())
    print(En.atomic_density_to_g_per_ccm())

    print("Diopsit")
    print(Di.calculate_atomic_oxygendensity())
    print(Di.atomic_density_to_g_per_ccm())


    print("Enstatite_Noah")
    print(En.calculate_atomic_oxygendensity())
    print(En.atomic_density_to_g_per_ccm())

    print("Labradorit")
    print(La.calculate_atomic_oxygendensity())
    print(La.atomic_density_to_g_per_ccm())
    print(sum(La.qus))

    print(10*"-")

    print(Sd.name)
    print(Sd.calculate_atomic_oxygendensity())
    print(Sd.atomic_density_to_g_per_ccm())

    print(10*"-")
    print(Ms.name)
    print(Ms.calculate_atomic_oxygendensity())
    print(Ms.atomic_density_to_g_per_ccm())

    print(10*"-")
    print(MsH.name)
    print(MsH.calculate_atomic_oxygendensity())
    print(MsH.atomic_density_to_g_per_ccm())
    print(MsH.dns0_all_the_same())


    print(10*"-")
    print(Ms7H.name)
    print(Ms7H.calculate_atomic_oxygendensity())
    print(Ms7H.atomic_density_to_g_per_ccm())
    print(Ms7H.dns0_all_the_same())