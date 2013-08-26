"""
Created on May 24, 2012

@author: quandtan
"""
import os
from applicake.framework.keys import Keys
from applicake.applications.proteomics.tpp.searchengines.base import SearchEngine
from applicake.framework.templatehandler import BasicTemplateHandler
from applicake.utils.fileutils import FileUtils
from applicake.utils.xmlutils import XmlValidator


class Xtandem(SearchEngine):
    """
    Wrapper for the search engine X!Tandem.
    """


    def __init__(self):
        """
        Constructor
        """
        super(Xtandem, self).__init__()
        self._default_prefix = 'tandem' # default prefix, usually the name of the application        
        base = self.__class__.__name__
        self._taxonomy_file = '%s.taxonomy' % base
        self._input_file = '%s.input' % base


    def _define_score(self, info, log):
        if not info.has_key('XTANDEM_SCORE'):
            log.info('No score given, using default score')
            info['XTANDEM_SCORE'] = ''
        # for default score, no entry is allowed in template
        elif info['XTANDEM_SCORE'] == 'default':
            log.info('Using default score')
            info['XTANDEM_SCORE'] = ''
        # for k-score add special tags
        elif info['XTANDEM_SCORE'] == 'k-score':
            log.info('Using k-score')
            info['XTANDEM_SCORE'] = '<note label="scoring, algorithm" type="input">%s</note>' \
                                    '<note label="spectrum, use conditioning" type="input" >no</note>' \
                                    '<note label="scoring, minimum ion count" type="input">1</note>' % info[
                                        'XTANDEM_SCORE']
        else:
            log.warn('Using special score %s' % info['XTANDEM_SCORE'])
            info['XTANDEM_SCORE'] = '<note label="scoring, algorithm" type="input">%s</note>' % info['XTANDEM_SCORE']
        return info

    def _write_input_files(self, info, log):
        db_file = os.path.join(info[Keys.WORKDIR], info['DBASE'])
        self._taxonomy_file = os.path.join(info[Keys.WORKDIR], self._taxonomy_file)
        with open(self._taxonomy_file, "w") as sink:
            sink.write('<?xml version="1.0"?>\n')
            sink.write('<bioml>\n<taxon label="database">')
            sink.write('<file format="peptide" URL="%s"/>' % db_file)
            sink.write("</taxon>\n</bioml>")
        log.debug('Created [%s]' % self._taxonomy_file)
        self._input_file = os.path.join(info[Keys.WORKDIR], self._input_file)
        with open(self._input_file, "w") as sink:
            sink.write('<?xml version="1.0"?>\n')
            sink.write("<bioml>\n<note type='input' label='list path, default parameters'>" + info[
                Keys.TEMPLATE] + "</note>\n")
            sink.write(
                "<note type='input' label='output, xsl path' />\n<note type='input' label='output, path'>" + self._result_file + "</note>\n")
            sink.write(
                "<note type='input' label='list path, taxonomy information'>" + self._taxonomy_file + "</note>\n")
            sink.write("<note type='input' label='spectrum, path'>" + info['MZXML'] + "</note>\n")
            sink.write("<note type='input' label='protein, taxon'>database</note>\n</bioml>\n")
        log.debug('Created [%s]' % self._input_file)
        return info

    def define_enzyme(self, info, log):
        """
        See super class.
        
        For X!Tandem, the method has to additionally check for semi cleavage
        """
        info = super(Xtandem, self).define_enzyme(info, log)
        if info[Keys.ENZYME].endswith(':2'):
            info[Keys.ENZYME] = info[Keys.ENZYME][:-2]
            info['XTANDEM_SEMI_CLEAVAGE'] = 'yes'
        else:
            info['XTANDEM_SEMI_CLEAVAGE'] = 'no'
        return info

    def prepare_run(self, info, log):
        """
        See interface.
        
        - Read the template from the handler
        - Convert scoring and modifications into the specific format
        - Convert enzyme into the specific format        
        - modifies the template from the handler
        - writes the files needed to execute the program 
        
        @precondition: info object need the key [TEMPLATE]
        """
        wd = info[Keys.WORKDIR]
        log.debug('reset path of application files from current dir to work dir [%s]' % wd)
        self._template_file = os.path.join(wd, self._template_file)
        info['TEMPLATE'] = self._template_file
        self._result_file = os.path.join(wd, self._result_file)
        self._taxonomy_file = os.path.join(wd, self._taxonomy_file)
        log.debug('add key [XTANDEM_RESULT] to info')
        info['XTANDEM_RESULT'] = self._result_file

        # need to create a working copy to prevent replacement or generic definitions
        # with app specific definitions
        app_info = info.copy()
        app_info = self._define_score(app_info, log)
        log.debug('define modifications')
        app_info = self.define_mods(app_info, log)
        log.debug('define enzyme')
        app_info = self.define_enzyme(app_info, log)
        log.debug('get template handler')
        th = XtandemTemplate()
        log.debug('define score value')
        log.debug('modify template')
        _, app_info = th.modify_template(app_info, log)
        log.debug('write input files')
        app_info = self._write_input_files(app_info, log)
        prefix, app_info = self.get_prefix(app_info, log)
        
        #addin conversion
        pepxml = os.path.join(wd, 'xtandem.pep.xml')
        info[Keys.PEPXMLS] = [pepxml]
        command = '%s %s | grep -v writing && Tandem2XML %s %s ' % (prefix, self._input_file, self._result_file, pepxml)
        # update original info object with new keys from working copy
        #info = DictUtils.merge(log, info, app_info, priority='left')        
        return command, info

    def set_args(self, log, args_handler):
        """
        See interface
        """
        args_handler = super(Xtandem, self).set_args(log, args_handler)
        args_handler.add_app_args(log, 'MZXML', 'Peak list file in mzXML format')
        args_handler.add_app_args(log, 'XTANDEM_SCORE', 'Scoring algorithm used in the search.',
                                  choices=['default', 'k-score', 'c-score', 'hrk-score', ])
        return args_handler

    def validate_run(self, info, log, run_code, out_stream, err_stream):
        """
        See super class.
        
        Check the following:
        - more than 0 valid models found
        - result file is valid
        - result file is a well-formed xml
        """
        exit_code, info = super(Xtandem, self).validate_run(info, log, run_code, out_stream, err_stream)
        if 0 != run_code:
            return exit_code, info
        out_stream.seek(0)
        if 'Valid models = 0' in out_stream.read():
            log.critical('No valid model found')
            return 1, info
        if not FileUtils.is_valid_file(log, self._result_file):
            log.critical('[%s] is not valid' % self._result_file)
            return 1, info
        if not XmlValidator.is_wellformed(self._result_file):
            log.critical('[%s] is not well formed.' % self._result_file)
            return 1, info
        return 0, info


class XtandemTemplate(BasicTemplateHandler):
    """
    Template handler for Xtandem.  
    """

    def read_template(self, info, log):
        """
        See super class.
        Template carefully checked Dec 2012 by hroest, olgas & loblum 
        """
        template = """<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="tandem-input-style.xsl"?>
<bioml>

<note type="heading">Spectrum general</note>    
    <note type="input" label="spectrum, fragment monoisotopic mass error">$FRAGMASSERR</note>
    <note type="input" label="spectrum, fragment monoisotopic mass error units">$FRAGMASSUNIT</note>
    <note type="input" label="spectrum, parent monoisotopic mass isotope error">yes</note>
    <note type="input" label="spectrum, parent monoisotopic mass error plus">$PRECMASSERR</note>
    <note type="input" label="spectrum, parent monoisotopic mass error minus">$PRECMASSERR</note>
    <note type="input" label="spectrum, parent monoisotopic mass error units">$PRECMASSUNIT</note>

<note type="heading">Spectrum conditioning</note>
    <note type="input" label="spectrum, fragment mass type">monoisotopic</note>
    <note type="input" label="spectrum, dynamic range">1000.0</note>
    <note type="input" label="spectrum, total peaks">50</note>
    <note type="input" label="spectrum, maximum parent charge">5</note>
    <note type="input" label="spectrum, use noise suppression">yes</note>
    <note type="input" label="spectrum, minimum parent m+h">400.0</note>
    <note type="input" label="spectrum, maximum parent m+h">6000</note>
    <note type="input" label="spectrum, minimum fragment mz">150.0</note>
    <note type="input" label="spectrum, minimum peaks">6</note>
    <note type="input" label="spectrum, threads">$THREADS</note>

<note type="heading">Residue modification</note>
    <note type="input" label="residue, modification mass">$STATIC_MODS</note>
    <note type="input" label="residue, potential modification mass">$VARIABLE_MODS</note>
    <note type="input" label="residue, potential modification motif"></note>

<note type="heading">Protein general</note>    
    <note type="input" label="protein, taxon">no default</note>
    <note type="input" label="protein, cleavage site">$ENZYME</note>
    <note type="input" label="protein, cleavage semi">$XTANDEM_SEMI_CLEAVAGE</note>
<!--   do not add, otherwise xinteracts generates tons of confusing modification entries
    <note type="input" label="protein, cleavage C-terminal mass change">+17.00305</note>
    <note type="input" label="protein, cleavage N-terminal mass change">+1.00794</note>    
-->
    <note type="input" label="protein, N-terminal residue modification mass">0.0</note>
    <note type="input" label="protein, C-terminal residue modification mass">0.0</note>
    <note type="input" label="protein, homolog management">no</note>
    <!-- explicitly disabled -->
    <note type="input" label="protein, quick acetyl">no</note>
    <note type="input" label="protein, quick pyrolidone">no</note>

<note type="heading">Scoring</note>
    <note type="input" label="scoring, maximum missed cleavage sites">$MISSEDCLEAVAGE</note>
    <note type="input" label="scoring, x ions">no</note>
    <note type="input" label="scoring, y ions">yes</note>
    <note type="input" label="scoring, z ions">no</note>
    <note type="input" label="scoring, a ions">no</note>
    <note type="input" label="scoring, b ions">yes</note>
    <note type="input" label="scoring, c ions">no</note>
    <note type="input" label="scoring, cyclic permutation">no</note>
    <note type="input" label="scoring, include reverse">no</note>
    $XTANDEM_SCORE


<note type="heading">model refinement paramters</note>
    <note type="input" label="refine">no</note>

<note type="heading">Output</note>
    <note type="input" label="output, message">testing 1 2 3</note>
    <note type="input" label="output, path">output.xml</note>
    <note type="input" label="output, sort results by">spectrum</note>
    <note type="input" label="output, path hashing">no</note>
    <note type="input" label="output, xsl path">tandem-style.xsl</note>
    <note type="input" label="output, parameters">yes</note>
    <note type="input" label="output, performance">yes</note>
    <note type="input" label="output, spectra">yes</note>
    <note type="input" label="output, histograms">no</note>
    <note type="input" label="output, proteins">yes</note>
    <note type="input" label="output, sequences">no</note>
    <note type="input" label="output, one sequence copy">yes</note>
    <note type="input" label="output, results">all</note>
    <note type="input" label="output, maximum valid expectation value">0.1</note>
    <note type="input" label="output, histogram column width">30</note>

</bioml>
"""
        log.debug('read template from [%s]' % self.__class__.__name__)
        return template, info
