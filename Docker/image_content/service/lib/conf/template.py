import os
import re

BASE_PATH = os.path.abspath(os.path.dirname(__file__))
CONF_TEMPLATE_PATH = os.path.join(BASE_PATH, 'neo4j.conf.template')
CORE_ID_REGEXES = [re.compile(r'^neo4j-(\d+).*'),
                   re.compile(r'^neo4j-(bragent-\d+).*'),
                   re.compile(r'^eric-data-graph-database-nj-(\d+).*'),
                   re.compile(r'^eric-data-graph-database-nj-(bragent-\d+).*')]


class Neo4jConfTemplate(object):

    def __init__(self, shell, template_path=CONF_TEMPLATE_PATH):
        self.shell = shell
        self.template_file = shell.os.fs.get(template_path)

    @property
    def template_dict(self):
        data = {}
        for line in self.template_file.read_lines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, value = line.split('=', 1)
            data.setdefault(key, []).append(value)
        return data

    def _prepare_env(self):
        fqdn = next(iter(self.shell.host.fqdns), None)
        if not fqdn:
            raise Exception('Failed to get hostname')
        match = None
        for regex in CORE_ID_REGEXES:
            match = regex.match(fqdn)
            if match:
                break
        if not match:
            raise Exception('Failed to parse neo4j core id from hostname %s' %
                            repr(fqdn))
        core_id = match.group(1)
        env = os.environ.copy()
        env.update(dict(
            CORE_ID=core_id,
            HOSTNAME=fqdn,
        ))
        discovery_host = "%(NEO4J_SERVICE_NAME)s-discovery-%(CORE_ID)s." \
                         "%(RELEASE_NAMESPACE)s.svc.cluster.local" % env
        env['DISCOVERY_HOST'] = discovery_host
        return env

    def generate_neo4j_conf(self):
        env = self._prepare_env()
        lines = []
        param_names = []
        for key, value in env.items():
            if not key.startswith('NEO4J_'):
                continue
            param = key.replace('NEO4J_', '') \
                       .replace('NEO4j_', '') \
                       .replace('__', '|') \
                       .replace('_', '.') \
                       .replace('|', '_')
            if param.isupper():
                continue
            lines.append("%s=%s" % (param, value))
            param_names.append(param)
        for key, values in self.template_dict.items():
            if key in param_names:
                # do not override from global env "NEO4J_parameter..."
                continue
            for value in values:
                lines.append("%s=%s" % (key, value % env))
        conf_contents = '\n'.join(sorted(set(lines)))
        conf_path = '/etc/neo4j/neo4j.conf'
        with self.shell.os.fs.open(conf_path, 'w') as conf_file:
            conf_file.write(conf_contents + '\n')
