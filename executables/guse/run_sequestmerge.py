#!/usr/bin/env python
'''
Created on Jul 6, 2012

@author: loblum
'''

import sys
from applicake.framework.runner import ApplicationRunner
from applicake.applications.proteomics.sequest.merger import SequestMerger

runner = ApplicationRunner()
application = SequestMerger()
exit_code = runner(sys.argv,application)
print exit_code
sys.exit(exit_code)