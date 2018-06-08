#!/usr/bin/env python

print "=== LAMA phenotyping pipeline ===\nDownloading dependencies..."


# easy_install first
import sys
import urllib
import tempfile
from os.path import join
try:
    import pip
except ImportError:
    print "setup_LAMA requires 'pip' to be installed on your system\non ubuntu try 'sudo apt install python-pip'"
    sys.exit()

dependencies = {
    'scipy': 'scipy',
    'numpy': 'numpy',
    'SimpleITK': 'SimpleITK',
    'appdirs': 'appdirs',
    'psutil': 'psutil',
    'yaml': 'pyyaml',
    'sklearn': 'sklearn',
    'matplotlib': 'matplotlib',
    'pandas': 'pandas',
    'seaborn': 'seaborn',
    'pandas': 'pandas',
    'statsmodels': 'statsmodels',
    'PIL': 'Pillow'

}

failed_installs = []

for import_name, package_name in dependencies.iteritems():

    try:
        print "Installing {0}...".format(import_name),
        mod = __import__(import_name)  # try to import module
        print " already installed.".format(import_name)

    except ImportError:
        # If it fails, try to install with pip
        result = pip.main(['install', '--user', package_name])
        if result != 0:
            failed_installs.append(package_name)

#### Download and install pyradiomics package
temp_dir = tempfile.gettempdir()
zip_loc = join(temp_dir, "pyradiomics_master.zip")

pyrad_url = 'https://github.com/Radiomics/pyradiomics/archive/master.zip'
pyrad_file = urllib.URLopener()
pyrad_file.retrieve(pyrad_url, "pyradiomics_master.zip")

import zipfile
zip_ref = zipfile.ZipFile(path_to_zip_file, 'r')
zip_ref.extractall(directory_to_extract_to)
zip_ref.close()


python -m pip install -r requirements.txt
python setup.py install

if len(failed_installs) == 0:
    print "All packages successfully installed"
else:
    print 'The following packages failed to install\n'
    for failed in failed_installs:
        print "{}\n".format(failed)




