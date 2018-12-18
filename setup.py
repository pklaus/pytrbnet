# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

try:
    import pypandoc
    LDESC = open('README.md', 'r').read()
    LDESC = pypandoc.convert_text(LDESC, 'rst', format='md')
except (ImportError, IOError, RuntimeError) as e:
    print("Could not create long description:")
    print(str(e))
    LDESC = ''

setup(name='trbnet',
      version = '1.0.dev0',
      description = 'Interface to TrbNet (wrapping libtrbnet.so with ctypes)',
      long_description = LDESC,
      author = 'Philipp Klaus',
      author_email = 'klaus@physik.uni-frankfurt.de',
      url = 'https://github.com/pklaus/pytrbnet',
      license = 'GPL',
      packages = [
          'trbnet',
          'trbnet.core',
          'trbnet.xmldb',
          'trbnet.util',
          'trbnet.epics',
          ],
      entry_points = {
          'console_scripts': [
              'trbcmd.py = trbnet.util.trbcmd:cli',
          ],
      },
      include_package_data = False,
      zip_safe = True,
      platforms = 'Linux',
      install_requires = [
          "lxml",
          "click",
          "enum34", # for support of enum.IntEnum on Python < 3.4
      ],
      keywords = 'TrbNet PyTrbNet FPGA Low-latency network wrapper',
      classifiers = [
          'Development Status :: 4 - Beta',
          'Operating System :: OS Independent',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Topic :: Scientific/Engineering :: Physics',
          'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
          'Topic :: System :: Hardware :: Hardware Drivers',
      ]
)
