from distutils.core import setup

setup(name='illuminaPipeline',
      url='http://www.awblocker.com',
      version='0.1',
      description='Data processing tools to take raw Illumina output to useable data',
      author='Alexander W Blocker',
      author_email='ablocker@gmail.com',
      py_modules=['libPipeline'],
      scripts=['pipeline-gui.py', 'convertToFASTQ.py', 'parseBowtieOutput.py',
               'parseSAMOutput.py', 'readsToChromCounts.py',
               'buildReadLengthDist.py'],
      requires=['numpy(>=1.1)', 'wx']
      )
