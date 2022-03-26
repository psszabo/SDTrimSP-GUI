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


class Styles:
    titleStyle = '''
        qproperty-alignment: AlignCenter;
        border-top-left-radius: 15px;
        border-top-right-radius: 15px;
        background-color: #006699;
        padding: 1px 0px;
        color: #FFF;'''
        #font-size: 14px; '''

    subTitleStyle = '''
        qproperty-alignment: AlignCenter;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        background-color: #006699;
        padding: 1px 5px;
        color: #FFF;'''
        #font-size: 12px; '''

    # Note that the bracket is not closed until a color is added as well
    statusTextStyle = '''
        QLabel {
            font-size: 16px;
            font-weight: bold;'''
    green = '''color: #5fbf64; }'''
    red = '''color: #bf3e2f; }'''
    orange = '''color: #d88f20; }'''