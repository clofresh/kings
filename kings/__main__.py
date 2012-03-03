import argparse
import logging.config
from ConfigParser import ConfigParser

from .common import *
from .net import MUD

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', required=True)
    args = parser.parse_args()
    logging.config.fileConfig(args.config)
    config = ConfigParser()
    config.read(args.config)
    server = MUD.init(config)
    server.run()


if __name__ == '__main__':
    main()
