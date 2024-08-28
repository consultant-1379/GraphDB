#!/usr/bin/env python3
import signal
import sys
import time
import logging
from prometheus_client import start_http_server, Gauge
from neo4jlib.client.session import Neo4jSession


def sigterm_handler(signal, frame):
    print("Received SIGTERM, shutting down immediately")
    sys.exit(0)


signal.signal(signal.SIGTERM, sigterm_handler)

neo4j_availability_metric = \
    Gauge('neo4j_availability', 'Neo4j cluster availability status')
neo4j_lag_metric = Gauge('neo4j_lag', 'Neo4j instance lag status')
neo4j_local_instance_metric = Gauge('neo4j_local_instance',
                                    'Neo4j local instance status')
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
start_http_server(3004)


def monitor_neo4j_cluster_availability():
    with Neo4jSession() as shell:
        while True:
            try:
                check_neo4j_availability(shell)
            except Exception as exc:
                logging.error("Exception occurred:", exc_info=True)
            finally:
                time.sleep(10)


def check_neo4j_availability(shell):
    neo4j_availability_check = 1 if shell.cluster.is_well_formed() \
        else 0
    local_instance_check = 1 if shell.host.ping() else 0

    alert_cluster_down = neo4j_availability_check or local_instance_check

    neo4j_availability_metric.set(alert_cluster_down)
    neo4j_local_instance_metric.set(local_instance_check)
    neo4j_lag_threshold = 50000
    neo4j_lag = max(i.lag for i in shell.cluster.instances)
    neo4j_lag_status = 1 if neo4j_lag <= neo4j_lag_threshold else 0
    neo4j_lag_metric.set(neo4j_lag_status)


time.sleep(300)
if __name__ == '__main__':
    monitor_neo4j_cluster_availability()
