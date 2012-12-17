#!/usr/bin/env python
'''
Created on Dez 20, 2012

@author: lorenz
'''

from applicake.framework.interfaces import IWrapper
from applicake.utils.fileutils import FileUtils

class Gzip(IWrapper):
    """
    Performs gzip, checks outfile  
    """
    
    def set_args(self,log,args_handler):
        args_handler.add_app_args(log, 'COMPRESS', 'File(s) to compress')
        return args_handler
    
    def prepare_run(self, info, log):
        """
        See super class.
        
        @precondition: 'info' object has to contain 'COMPRESS'
        """
        if not isinstance(info['COMPRESS'],list):
            info['COMPRESS'] = [info['COMPRESS']]

        param = ""
        outs = []
        for file in info['COMPRESS']:
            param = param + ' ' + file
            outs.append(file + '.gz')
             
        command = "gzip -v %s" % param
        
        self._result_files = outs
        return command,info
           
    def validate_run(self,info,log, run_code,out_stream, err_stream): 
        if 0 == run_code:
            #run code 1 might also be OK if file was already zipped 
            #(job rescue), thus rather check file than exitcode
            for file in self._result_files:
                if not FileUtils.is_valid_file(log, file):
                    log.critical('[%s] is not valid' %file)
                    return 1,info 
            info['COMPRESS_OUT'] = self._result_files
            return 0,info
        elif 1 == run_code:
            log.warn('gzip failed, checking if file was already zipped (rescued job)...')
            for file in self._result_files:
                if FileUtils.is_valid_file(log, file):
                    log.warn('Lucky you: File was already zipped. Continuing...' %file)
                else:
                    log.fatal('Gzip output file is invalid!')  
                    return 1,info
            info['COMPRESS_OUT'] = self._result_files
            return 0,info
        else:
            return run_code,info
