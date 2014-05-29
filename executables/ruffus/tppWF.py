#!/usr/bin/env python
import os
import shutil
import sys
import subprocess

from ruffus import *


basepath = os.path.dirname(__file__) + '/../../'


def setup():
    if len(sys.argv) > 1 and sys.argv[1] == 'cont':
        print 'Continuing with existing input.ini (Ruffus should skip to the right place automatically)'
    else:
        print 'Starting from scratch by creating new input.ini'
        subprocess.call("rm *ini* *.log", shell=True)
        with open("input.ini", 'w+') as f:
            f.write("""DATASET_CODE = 20120320163951515-361883, 20120320163653755-361882, 20120320164249179-361886
PRECMASSERR = 25
DATASET_DIR = /cluster/scratch_xl/shareholder/imsb_ra/datasets
STORAGE = unchanged
PEPTIDEFDR = 0.01
RUNTANDEM = True
PRECMASSUNIT = ppm
COMMENT = TPP of UPS1 ruffus
RUNMYRIMATCH = True
LOG_LEVEL = DEBUG
MISSEDCLEAVAGE = 1
FRAGMASSERR = 0.2
WORKFLOW = TPP_ruffus
DB_SOURCE = PersonalDB
DBASE = PDB-BEHULLAR-LOBLUM_UPS1-20130912113123
DROPBOX = /cluster/scratch_xl/shareholder/imsb_ra/drop-box_prot_ident
XTANDEM_SCORE = k-score
SPACE = LOBLUM
DECOY_STRING = DECOY_
BASEDIR = /cluster/scratch_xl/shareholder/imsb_ra/workflows/
PROJECT = JUNK
STATIC_MODS = Carbamidomethyl (C)
VARIABLE_MODS =
FRAGMASSUNIT = Da
ENZYME = Trypsin
RUNOMSSA = True
RUNCOMET = False
RUNTPP2VIEWER = fast""")


@follows(setup)
@files("input.ini", "biopersdb.ini")
def biopersdb(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/openbis/biopersdb.py',
                           '--INPUT', infile, '--OUTPUT', outfile])


@follows(biopersdb)
@split("biopersdb.ini", "split.ini_*")
def split_dataset(infile, unused_outfile):
    subprocess.check_call(['python', basepath + 'appliapps/flow/split.py',
                           '--INPUT', infile, '--SPLIT', 'split.ini', '--SPLIT_KEY', 'DATASET_CODE'])


@transform(split_dataset, regex("split.ini_"), "dss.ini_")
def dss(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/openbis/dss.py',
                           '--INPUT', infile, '--OUTPUT', outfile, '--EXECUTABLE', 'getmsdata'])
    print "WARNING: NOT A CONDITIONAL WORKFLOW, WILL EXECUTE ALL BRANCHES!!!"


##################################################################################

@transform(dss, regex("dss.ini_"), "rawtandem.ini_")
def tandem(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/tpp/searchengines/xtandem.py',
                           '--INPUT', infile, '--OUTPUT', outfile, '--THREADS', '4'])


@transform(tandem, regex("rawtandem.ini_"), "tandem.ini_")
def pepprotandem(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/tpp/peptideprophet.py',
                           '--INPUT', infile, '--OUTPUT', outfile, '--NAME', 'peptandem'])


##################################################################################

@transform(dss, regex("dss.ini_"), "rawomssa.ini_")
def omssa(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/tpp/searchengines/omssa.py',
                           '--INPUT', infile, '--OUTPUT', outfile, '--THREADS', '4'])


@transform(omssa, regex("rawomssa.ini_"), "omssa.ini_")
def pepproomssa(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/tpp/peptideprophet.py',
                           '--INPUT', infile, '--OUTPUT', outfile, '--NAME', 'pepomssa'])


###################################################################################


@transform(dss, regex("dss.ini_"), "rawmyri.ini_")
def myri(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/tpp/searchengines/myrimatch.py',
                           '--INPUT', infile, '--OUTPUT', outfile, '--THREADS', '4'])


@transform(myri, regex("rawmyri.ini_"), "myrimatch.ini_")
def peppromyri(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/tpp/peptideprophet.py',
                           '--INPUT', infile, '--OUTPUT', outfile, '--NAME', 'pepmyri'])


###################################################################################


@transform(dss, regex("dss.ini_"), "rawcomet.ini_")
def comet(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/tpp/searchengines/comet.py',
                           '--INPUT', infile, '--OUTPUT', outfile, '--THREADS', '4'])


@transform(comet, regex("rawcomet.ini_"), "comet.ini_")
def pepprocomet(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/tpp/peptideprophet.py',
                           '--INPUT', infile, '--OUTPUT', outfile, '--NAME', 'pepcomet', '--MODULE', 'tpp/4.7.0'])


############################# MERGE SEARCH ENGINE RESULTS ##################################
#In guse version conditional branching is used which requires collate to be a full collector to work
#thus enginecollate is a collector/generator node in guse and simulated in ruffus with a merge/fake_split
@merge([pepprotandem,pepproomssa,peppromyri], "ecollate.ini")
def collateengines(infiles, outfiles):
    subprocess.check_call(['python', basepath + 'appliapps/tpp/enginecollate.py',
                           '--INPUT','biopersdb.ini','--OUTPUT','ecollate.ini','--MERGED', 'mergeengine.ini',
                           '--ENGINES', 'tandem', '--ENGINES', 'myrimatch', '--ENGINES', 'omssa', '--ENGINES', 'comet'])

@split(collateengines,"mergeengine.ini_*")
def fake_split(infile,outfiles):
    pass

@transform(fake_split, regex("mergeengine.ini_"), "engineiprophet.ini_")
def engineiprophet(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/tpp/interprophet.py',
                           '--INPUT', infile, '--OUTPUT', outfile, '--NAME', 'engineiprophet', "--MODULE", "imsbtools"])


############################# TAIL: PARAMGENERATE ##################################   

@merge(engineiprophet, "mergedatasets.ini")
def merge_datasets(unused_infiles, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/flow/merge.py',
                           '--MERGE', 'engineiprophet.ini', '--MERGED', outfile])


@follows(merge_datasets)
@files("mergedatasets.ini_0", "datasetiprophet.ini")
def datasetiprophet(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/tpp/interprophet.py',
                           '--INPUT', infile, '--OUTPUT', outfile])


@follows(datasetiprophet)
@files("datasetiprophet.ini", "proteinprophet.ini")
def proteinprophet(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/tpp/proteinprophet.py',
                           '--INPUT', infile, '--OUTPUT', outfile])

@follows(proteinprophet)
@files("proteinprophet.ini", "protxml2openbis.ini")
def protxml2openbis(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/tpp/protxml2openbis.py',
                           '--INPUT', infile, '--OUTPUT', outfile])

@follows(protxml2openbis)
@files("protxml2openbis.ini", "copy2dropbox.ini")
def copy2dropbox(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/tpp/dropbox.py',
                           '--INPUT', infile, '--OUTPUT', outfile])

@follows(copy2dropbox)
@files("copy2dropbox.ini", "tpp2viewer.ini")
def tpp2viewer(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/tpp/tpp2viewer.py',
                           '--INPUT', infile, '--OUTPUT', outfile])


pipeline_run([tpp2viewer], multiprocess=3)

#pipeline_printout_graph ('flowchart.png','png',[copy2dropbox],no_key_legend = False) #svg