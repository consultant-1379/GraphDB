#!/usr/bin/python3
from logging import FileHandler
from logging.handlers import RotatingFileHandler

from lib.conf.template import Neo4jConfTemplate
from pyu.os.shell.session import ShellSession
from pyu.log import log
from pyu.os.fs.units import Size


def main():
    with ShellSession() as shell:
        file_size = int(Size('20M').bytes)
        log_handler = RotatingFileHandler('/var/tmp/generate_conf.log',
                                          maxBytes=file_size,
                                          backupCount=50)
        log.setup_log(log_handler, 'generate_conf.py', verbose=True)
        log.info('Generate neo4j.conf started')
        conf_template = Neo4jConfTemplate(shell)
        conf_template.generate_neo4j_conf()
        log.info('Generate neo4j.conf finished successfully')


if __name__ == '__main__':
    main()
