#!/usr/bin/env python
'''
Created on Apr 23, 2012

@author: quandtan
'''

import sys
from applicake.framework.runner import CollectorRunner
from applicake.applications.commons.collector import SimpleCollector


runner = CollectorRunner()
application = SimpleCollector()
exit_code = runner(sys.argv,application)
print exit_code
sys.exit(exit_code)