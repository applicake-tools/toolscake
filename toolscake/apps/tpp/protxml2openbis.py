#!/usr/bin/env python
import os

from applicake.base.app import WrappedApp
from applicake.base.apputils import validation
from applicake.base.coreutils.arguments import Argument
from applicake.base.coreutils.keys import Keys, KeyHelp


class ProtXml2OpenbisSequence(WrappedApp):
    """
    Wrapper for SyBIT-tools protxml2openbis made by lucia.
    """

    def add_args(self):
        return [
            Argument(Keys.WORKDIR, KeyHelp.WORKDIR),
            Argument(Keys.EXECUTABLE, KeyHelp.EXECUTABLE),
            Argument(Keys.PEPXML, KeyHelp.PEPXML),
            Argument('PROTXML', 'Path to a file in protXML format'),
            Argument('DBASE', 'Sequence database file with target/decoy entries'),
            Argument('IPROB','Use same iprob cutoff as used in ProteinProphet (before).')
        ]

    def prepare_run(self, log, info):
        wd = info[Keys.WORKDIR]

        info['PEPCSV'] = os.path.join(wd, 'peptides.tsv')
        countprotxml = os.path.join(wd, 'spectralcount.prot.xml')
        modprotxml = os.path.join(wd, 'modifications.prot.xml')
        bisprotxml = os.path.join(wd, 'protxml2openbis.prot.xml')

        command = """pepxml2csv -IPROPHET -header -cP=%s -OUT=%s %s &&
        protxml2spectralcount -CSV=%s -OUT=%s %s &&
        protxml2modifications -CSV=%s -OUT=%s %s &&
        protxml2openbis -DB=%s -OUT=%s %s""" % (
            info['IPROB'], info['PEPCSV'], info[Keys.PEPXML],
            info['PEPCSV'], countprotxml, info['PROTXML'],
            info['PEPCSV'], modprotxml, countprotxml,
            info['DBASE'], bisprotxml, modprotxml )

        info['PROTXML'] = bisprotxml

        return info, command


    def validate_run(self, log, info, exit_code, stdout):
        validation.check_exitcode(log, exit_code)
        validation.check_xml(log, info['PROTXML'])
        return info


if __name__ == "__main__":
    ProtXml2OpenbisSequence.main()