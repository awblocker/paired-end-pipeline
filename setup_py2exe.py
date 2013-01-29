from distutils.core import setup
from glob import glob
import sys
import py2exe

# Fix for MSVCR90.dll
dirPattern = r'C:\Windows\winsxs\x86_microsoft.vc90.crt*9.0.21022.8*'
dir = glob(dirPattern)[0]
sys.path.append(dir)
pattern = dir + '\\*.*'
data_files = [("Microsoft.VC90.CRT", glob(pattern))]

setup(name='illuminaPipeline',
      url='http://www.awblocker.com',
      version='0.1',
      description='Data processing tools to take raw Illumina output to usable data',
      author='Alexander W Blocker',
      author_email='ablocker@gmail.com',
      py_modules=['libPipeline'],
      console=['convertToFASTQ.py','parseBowtieOutput.py',
               'readsToChromCounts.py','buildReadLengthDist.py'],
      windows=["pipeline-gui.py"],
      requires=['numpy(>=1.1)','wx'],
      data_files=data_files
      )