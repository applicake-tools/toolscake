#!/usr/bin/env python
from applicake.app import BasicApp
from applicake.coreutils.arguments import Argument


class PythonEcho(BasicApp):
    """
    A most simple example for a BasicApp
    prints COMMENT to stdout
    """

    def add_args(self):
        return [
            Argument("COMMENT", "String to be displayed")
        ]

    def run(self, log, info):
        print info["COMMENT"]
        return info

#use this class as executable
if __name__ == "__main__":
    PythonEcho.main()