'''
Created on Apr 14, 2012

@author: loblum
'''

from applicake.framework.interfaces import IApplication


class EmptyKeyRemover(IApplication):
 
    def main(self,info,log):

        for key,value in info.items():
            if value == None or value == "":
                log.debug("Removing empty key %s" % key)
                del info[key]
            else:
                print "%s = %s" % key,value

        return (0,info)
    
    def set_args(self,log,args_handler):
        return args_handler

