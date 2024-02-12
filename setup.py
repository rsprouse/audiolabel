#!/usr/bin/env python

from distutils.core import setup

setup(
  name = 'audiolabel',
  version='0.3.4',
  py_modules = ['audiolabel'],
  scripts = ['audiolabel_update_api'],
  classifiers = [
    'Intended Audience :: Science/Research',
    'Topic :: Scientific/Engineering',
    'Topic :: Multimedia :: Sound/Audio :: Speech'
  ],
  requires = [
    'numpy',
    'pandas'
]

)
