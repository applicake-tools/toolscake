'''
Created on Oct 24, 2012

@author: lorenz
'''

import os
from applicake.framework.interfaces import IWrapper
from applicake.framework.templatehandler import BasicTemplateHandler

class mProphet(IWrapper):
    
    def __init__(self):
        """
        Constructor
        """
        base = self.__class__.__name__
        self._result_base = base # result produced by the application  
            
    def get_template_handler(self):
        """
        See interface
        """
        return mProphetTemplate()
    
    
    def prepare_run(self,info,log):
        
        wd = info[self.WORKDIR]
        info['RESULTBASE'] = os.path.join(wd,self._result_base)

        log.debug('get template handler')
        th = self.get_template_handler()
        log.debug('modify template')
        mod_template,info = th.modify_template(info, log)

        prefix = 'R'
        command = '%s %s' % (prefix,mod_template)
        return command,info

    def set_args(self,log,args_handler):
        """
        See interface
        """
        args_handler.add_app_args(log, 'MPROPHET_BINDIR', 'mprophet binaries folder')
        args_handler.add_app_args(log, 'MPR_NUM_XVAL', 'help')
        args_handler.add_app_args(log, 'WRITE_ALL_PG', 'help')
        args_handler.add_app_args(log, 'WRITE_CLASSIFIER', 'help')

        return args_handler

    def validate_run(self,info,log, run_code,out_stream, err_stream):
        if run_code != 0:            
            return(run_code,info)
        return run_code,info

        
class mProphetTemplate(BasicTemplateHandler):
    """
    Template handler for mprophet.
    """

    def read_template(self, info, log):
        """
        See super class.
        """
        template =  'R --slave -f $MPROPHET_BINDIR/mProphet.R --args bin_dir=$MPROPHET_BINDIR ' \
                    'run_log=FALSE workflow=LABEL_FREE help=0' \
                    'num_xval=$MPR_NUM_XVAL write_classifier=$WRITE_CLASSIFIER write_all_pg=$WRITE_ALL_PG  ' \
                    'project=$RESULTBASE mquest=$OUTBASE_combined.short_format.csv > $RESULTBASE.mProphet'
        return template,info    
    