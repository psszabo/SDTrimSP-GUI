# https://py2app.readthedocs.io/en/latest/options.html
# https://py2app.readthedocs.io/en/latest/tweaking.html -> plist things (for example supported file types)
#
# This file was created with and manually adapted afterwards
#     py2applet --make-setup main.py icons/tu_logo.icns
# Create standalone .app file with
#     python3 setup_py2app.py py2app
# For testing, use the -A/--alias flag when running the setup script
#
# REMOVE ANY "build" or "dist" folders before running this!
#

from setuptools import setup

OPTIONS = {'iconfile': '../icons/tu_logo.icns'}

setup(
    name="SDTrimSP-GUI",
    version="0.0.1",
    url = "http://www.iap.tuwien.ac.at",
    app=['../main.py'],
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)