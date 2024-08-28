from decimal import Decimal
from logging import getLogger, DEBUG, Formatter
from logging.handlers import RotatingFileHandler

from lib.probe.base import ProbeBase
from lib.probe.egress import ExitCode
from pyu.decor.misc import set_timeout
from pyu.os.fs.units import Size
from pyu.tools.timing import MINUTE
from pyu.decor.misc import FunctionTimeout
from pyu.log import log
from neo4jlib.client.auth.credentials import credentials
import re

class ServiceProbe(ProbeBase):
    name = 'service'
    failure_msg = 'Neo4j is not running!'
    failure_exit_code = ExitCode.not_running
    successful_msg = 'Neo4j service is running.'

    @property
    def complete_successful_msg(self):
        return 'Neo4j service is running on pid %s.' % \
               self.shell.deployment.service.process.pid

    def is_ok(self):
        return self.shell.deployment.service.is_running()


class PortsListeningProbe(ProbeBase):
    name = 'listening'
    failure_exit_code = ExitCode.not_listening
    failure_msg = 'Neo4j port is not responding.'
    successful_msg = 'Neo4j port check passed.'

    def is_ok(self):
        neo4j_instance = self.shell.instance
        return neo4j_instance.is_listening(stdout=self.stdout)


class Neo4jPingProbe(ProbeBase):
    name = 'ping'
    failure_exit_code = ExitCode.not_pinging
    failure_msg = 'Neo4j ping failed.'
    successful_msg = 'Neo4j ping check passed.'

    def is_ok(self):
        neo4j_instance = self.shell.instance
        neo4j_pinged = neo4j_instance.ping(credential=credentials.admin)
        if not neo4j_pinged:
            # if there is a checkpoint ongoing, then we ignore and return True
            try:
                is_checkpoint_ongoing = set_timeout(3 * MINUTE)(
                    neo4j_instance.is_checkpoint_ongoing)()
            except FunctionTimeout as err:
                log.warning('Timed out while checking the checkpoint ongoing '
                            'method: %s' % err,
                            stdout=self.stdout)
                return False
            if is_checkpoint_ongoing:
                log.warning('Neo4j ping failed and checkpoint is ongoing. '
                            'Considering as a successful Health Check anyway.',
                            stdout=self.stdout)
            return is_checkpoint_ongoing
        return True


class RoutingTableProbe(ProbeBase):
    name = 'routing'
    failure_exit_code = ExitCode.no_consistent_routing
    failure_msg = 'Neo4j routing table is inconsistent.'
    successful_msg = 'Neo4j routing table is fine.'

    def is_ok(self):
        # Checking "'bragent' not in str(i.host)" below as sometimes
        # instance.role cannot be retrieved making "i.is_replica()" become
        # False although the instance is still a read-replica.
        other_instances = [i for i in self.shell.cluster.other_instances
                             if not i.is_replica() and
                            'bragent' not in str(i.host)]
        self_routing_table = self.shell.instance.routing_table
        if self_routing_table is None:
            return False
        route_servers_length = len(self_routing_table.route_servers)
        if route_servers_length <= 1:
            if route_servers_length == 1:
                log.warning('Routing table has only 1 server: %s' %
                            self_routing_table, self.stdout)
            else:
                log.warning('Routing table has no servers: %s' %
                            self_routing_table, self.stdout)
            # ping ips
            ip_pings = [(i.host, i.host.ping()) for i in other_instances]
            log.info('Other neo4j instances ip ping: %s' %
                     ', '.join(["%s: %s" % (h, p) for h, p in ip_pings]),
                     self.stdout)
            if not any([i[1] for i in ip_pings]):
                log.info('It is not possible to ping the ip of the other '
                         'neo4j instances, so the routing table info seems ok',
                         self.stdout)
                return True
            neo4j_pings = [(i.host, i.ping()) for i in other_instances]
            log.info('Other neo4j instances neo4j ping: %s' %
                     ', '.join(["%s: %s" % (h, p) for h, p in neo4j_pings]),
                     self.stdout)
            if not any([i[1] for i in neo4j_pings]):
                log.info('It is not possible to ping(200) the other neo4j '
                         'instances, so the routing table info seems ok',
                         self.stdout)
                return True
            if all([i[1] for i in neo4j_pings]):
                log.info('The other neo4j instances are responding to '
                         'ping(200), however the current routing table has '
                         'size %s. Health check failed.' %
                         route_servers_length, self.stdout)
                return False
            return True
        other_routing_tables = [(i.host, i.routing_table)
                                for i in other_instances]
        other_routing_tables = dict([i for i in other_routing_tables if i[1]])
        other_tables_str = 'Other routing tables: %s' % \
                           ', '.join(["(%s): %s" % (h, r)
                                      for h, r in
                                      other_routing_tables.items()])
        failed_routing_tables = [h for h, r in other_routing_tables.items()
                                 if r is None]
        if failed_routing_tables:
            log.info(other_tables_str, self.stdout)
            # query failed somehow: connectivity?
            log.info('Routing table from the local instance: %s' %
                     self_routing_table, self.stdout)
            log.info('Could not retrieve the routing table from the other '
                     'instance(s): %s' %
                     ', '.join(map(str, failed_routing_tables)), self.stdout)
            # ping ips
            ip_pings = [(i.host, i.host.ping()) for i in other_instances]
            log.info('Other neo4j instances ip ping: %s' %
                     ', '.join(["%s: %s" % (h, p) for h, p in ip_pings]),
                     self.stdout)
            neo4j_pings = [(i.host, i.ping()) for i in other_instances]
            log.info('Other neo4j instances neo4j ping: %s' %
                     ', '.join(["%s: %s" % (h, p) for h, p in neo4j_pings]),
                     self.stdout)
            if len(other_instances) <= 2:
                log.info('Returning a successful health check as there are '
                         'not enough instances of neo4j to compare the '
                         'routing tables', self.stdout)
                return True

        if all([r == self_routing_table
                for r in other_routing_tables.values()]):
            log.info('All neo4j instances routing tables are identical',
                     self.stdout)
            return True
        log.info('Routing table from the local instance: %s' %
                 self_routing_table, self.stdout)
        log.error('Neo4j routing tables are different. Self routing table is '
                  '(%s): %s. The other instances routing tables: %s' %
                  (self.shell.host, self_routing_table, other_tables_str),
                  self.stdout)
        return False


CPU_USAGE_FILE = '/data/logs/cpu_usage.log'
CPU_THRESHOLD = 60

class CpuThresholdProbe(ProbeBase):
    name = 'cpu'
    failure_exit_code = ExitCode.cpu_exhausted
    failure_msg = 'Neo4j CPU is high for too long.'
    successful_msg = 'Neo4j CPU usage is fine.'

    def is_ok(self):
        cpu_loggger = getLogger('cpu_usage')
        cpu_loggger.setLevel(DEBUG)
        handler = RotatingFileHandler(CPU_USAGE_FILE,
                                      maxBytes=Size('20M').bytes,
                                      backupCount=50)
        handler.setLevel(DEBUG)
        handler.setFormatter(Formatter('%(asctime)s: %(message)s'))
        cpu_loggger.addHandler(handler)

        output = self.shell.rune('top -b -d1 -n1|grep -i "Cpu(s)"')
        try:
            total_cpu = float(re.findall("\d+\.\d+", output)[0])
        except Exception:
            log.warning('Neo4j CPU calculation regex error from %s ' % output)
            return True
        cpu_loggger.info(output)

        msg = 'Neo4j is running with %s%% of CPU' % total_cpu
        if total_cpu > CPU_THRESHOLD:
            log.warning(msg)
            return False
        log.info(msg)
        return True
