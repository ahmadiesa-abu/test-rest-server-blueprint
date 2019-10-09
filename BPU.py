import os
import sys
import time
import threading
import argparse
import logging
import yaml

from cloudify_rest_client import CloudifyClient

current_milli_time = lambda: int(round(time.time() * 1000))

def _parse_command():
    parser = argparse.ArgumentParser(description='Cloudify Manager Benchmark Tool')
    parser.add_argument('--config-path', dest='config_path',
			action='store', type=str,
			required=True, help='Configuration for Manager and Rest Server')
    return parser.parse_args()

if __name__=='__main__':
	parse_args = _parse_command()
	with open(parse_args.config_path) as config_file:
        	config = yaml.load(config_file, yaml.Loader)
	client = CloudifyClient(host=config['manager_ip'],username=config['manager_username'],
				password=config['manager_password'],tenant=config['manager_tenant'])
	logging.basicConfig(level=logging.INFO)
	client.blueprints.upload('counter-blueprint/blueprint.yaml','BPUpladedFromPython')
