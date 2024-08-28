# COPYRIGHT Ericsson AB 2020
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.

import logging
import time
import requests


class Bro():
    """ADP Backup Restore Orchestrator REST API library.

    Args:
        host (str): BRO host name or IP
        port (int): Optional port for REST API
        cert (str): Path to TLS certificate, if not specified http is used
        refresh_interval (int): Optional refresh rate for BRO objects
    """

    def __init__(self, host, port=7001, cert=False, refresh_interval=5):
        self.log = logging.getLogger(__name__)
        self.url = f'http{"s" if cert else ""}://{host}:{port}'
        self.session = requests.Session()
        self.session.verify = cert
        self.refresh_interval = refresh_interval

        self._status = None

    def create(self, name, scope='DEFAULT'):
        """Create backup.

        Args:
            name (str): Backup name
            scope (str): Optional backup scope

        Returns:
            Action: Create backup action object
        """
        return self._action('CREATE_BACKUP', scope, backupName=name)

    def restore(self, name, scope='DEFAULT'):
        """Restore backup.

        Args:
            name (str): Backup name
            scope (str): Optional backup scope

        Returns:
            Action: Restore backup action object
        """
        return self._action('RESTORE', scope, backupName=name)

    def delete(self, name, scope='DEFAULT'):
        """Delete backup.

        Args:
            name (str): Backup name
            scope (str): Optional backup scope

        Returns:
            Action: Delete backup action object
        """
        return self._action('DELETE_BACKUP', scope, backupName=name)

    def import_backup(self, name, uri, password, scope='DEFAULT'):
        """Import backup.

        Args:
            name (str): Backup name
            uri (str): URI of backup endpoint storage
            password (str): Password for backup endpoint storage
            scope (str): Optional backup scope

        Returns:
            Action: Import backup action object
       """
        return self._action(
            'IMPORT', scope, uri=f'{uri}/{scope}/{name}', password=password)

    def export_backup(self, name, uri, password, scope='DEFAULT'):
        """Export backup.

        Args:
            name (str): Backup name
            uri (str): URI of backup endpoint storage
            password (str): Password for backup endpoint storage
            scope (str): Optional backup scope

        Returns:
            Action: Export backup action object
        """
        return self._action(
            'EXPORT', scope, backupName=name, uri=uri, password=password)

    def _action(self, action, scope, **kwargs):
        self.log.debug('Requesting action %s in scope %s', action, scope)
        url = f'{self.url}/v1/backup-manager/{scope}/action'
        response = self.session.post(
            url, json={'action': action, 'payload': kwargs})
        if not response.ok:
            raise BroResponseError(url, response)
        try:
            return Action(self, scope, response.json()['id'])
        except (ValueError, KeyError):
            raise BroInvalidResponse(f'Invalid BRO respose to {url} request')

    def get_backup(self, name, scope='DEFAULT'):
        """Get backup details.

        Args:
            name (str): Backup name
            scope (str): Optional backup scope

        Returns:
            Backup: Backup instance
        """
        return Backup(self, scope, name)

    def get_scope(self, name):
        """Get scope details.

        Args:
            name (str): Scope name

        Returns:
            Scope: Scope instance
        """
        self.log.debug('Getting backup scope: %s', name)
        url = f'{self.url}/v1/backup-manager/{name}'
        res = self.session.get(url)
        if not res.ok:
            raise BroResponseError(url, res)
        try:
            return Scope(self, res.json()['id'])
        except (ValueError, KeyError):
            raise BroInvalidResponse(f'Invalid BRO respose to {url} request')

    def backups(self, scope='DEFAULT'):
        """Return list of Backup objects from BRO.

        Args:
            scope (str): Optional backup scope

        Returns:
            List[Backup]: List of Backup instances
        """
        return self._bro_items('backup', Backup, scope)

    def actions(self, scope='DEFAULT'):
        """Return list of Action objects from BRO.

        Args:
            scope (str): Optional action scope

        Returns:
            List[Action]: List of Action instances
        """
        return self._bro_items('action', Action, scope)

    def _bro_items(self, item_name, item_class, scope):
        self.log.debug('Getting {%s}s in scope %s', item_name, scope)
        url = f'{self.url}/v1/backup-manager/{scope}/{item_name}'

        res = self.session.get(url)
        if not res.ok:
            raise BroResponseError(url, res)

        try:
            items = [item_class(self, scope, item['id'])
                     for item in res.json()[item_name + 's']]
        except (ValueError, KeyError):
            raise BroInvalidResponse(f'Invalid BRO respose to {url} request')
        return items

    @property
    def scopes(self):
        """Return list of backup scopes (managers).
        """
        self.log.debug('Getting backup scopes')
        url = f'{self.url}/v1/backup-manager'
        res = self.session.get(url)
        if not res.ok:
            raise BroResponseError(url, res)
        try:
            scopes = [Scope(self, scope['id'])
                      for scope in res.json()['backupManagers']]
        except (ValueError, KeyError):
            raise BroInvalidResponse(f'Invalid BRO respose to {url} request')
        return scopes

    @property
    def status(self):
        """Return Status object representing current BRO status.
        """
        if not self._status:
            self._status = Status(self)
        return self._status


class Refreshable():
    """Refreshable BRO object base class.

    Handles automatic REST API load and refresh of BRO object classes. A GET on
    the provided URL must return a JSON response with object properties. The
    response JSON is stored in the self._json variable.

    Properties that are not static should first call self._refresh() to ensure
    the object is updated according to the refresh interval defined in the Bro
    instance. Calling self.refresh() directly forces an update regardless of
    the refresh interval.

    The class supports modifying an object with a POST request to the same URL
    using a JSON body containing one or more fields to be updated.

    Args:
        bro (Bro): Bro instance
        url (str): URL to GET for refreshes, and POST for modifications
    """

    def __init__(self, bro, url):
        self._log = bro.log
        self._url = url
        self._session = bro.session
        self._refresh_interval = bro.refresh_interval
        self._last_update = None
        self._json = None
        # Load on init
        self.refresh()

    def __str__(self):
        return str(self._json)

    def _refresh(self):
        if time.time() - self._last_update >= self._refresh_interval:
            self.refresh()

    def refresh(self):
        self._log.debug('Getting update from URL: %s', self._url)
        response = self._session.get(self._url)
        if not response.ok:
            self._log.debug('Request to url %s failed with code %s (%s %s)',
                            self._url, response.status_code, response.reason,
                            response.text)
            raise BroResponseError(self._url, response)
        try:
            self._json = response.json()
        except ValueError:
            raise BroInvalidResponse(
                f'Received invalid response from URL {self._url}')
        self._last_update = time.time()

    def _update_fields(self, **kwargs):
        self._log.debug('Updating %s with fields: %s', self._url, kwargs)
        response = self._session.post(self._url, json=kwargs)
        if not response.ok:
            self._log.debug('Update to url %s failed with code %s (%s %s)',
                            self._url, response.status_code, response.reason,
                            response.text)
            raise BroResponseError(self._url, response)
        # Force refresh
        self.refresh()


class Scope(Refreshable):
    """Represents a BRO backup manager/scope.

    Args:
        bro (Bro): Bro instance
        scope_id (str): Backup scope ID

    The backup_type and backup_domain properties are settable.
    """

    def __init__(self, bro, scope_id):
        super().__init__(bro, f'{bro.url}/v1/backup-manager/{scope_id}')

        try:
            self._id = self._json['id']
        except KeyError:
            raise BroInvalidResponse('Received invalid scope response')

    @property
    def id(self):
        return self._id

    @property
    def backup_type(self):
        self._refresh()
        return self._json['backupType']

    @backup_type.setter
    def backup_type(self, backup_type):
        self._update_fields(backupType=backup_type,
                            backupDomain=self.backup_domain)

    @property
    def backup_domain(self):
        self._refresh()
        return self._json['backupDomain']

    @backup_domain.setter
    def backup_domain(self, domain):
        self._update_fields(backupDomain=domain, backupType=self.backup_type)


class Action(Refreshable):
    """Represents a BRO action.

    Args:
        bro (Bro): Bro instance
        scope (str): Backup scope for action
        action_id (str): Action ID
    """

    def __init__(self, bro, scope, action_id):
        self._scope = scope
        super().__init__(
            bro, f'{bro.url}/v1/backup-manager/{scope}/action/{action_id}')

        try:
            self._id = self._json['id']
        except KeyError:
            raise BroInvalidResponse('Received invalid action response')

    @property
    def id(self):
        return self._id

    @property
    def scope(self):
        return self._scope

    @property
    def name(self):
        return self._json['name']

    @property
    def payload(self):
        return self._json['payload']

    @property
    def result(self):
        self._refresh()
        return self._json['result']

    @property
    def result_info(self):
        self._refresh()
        try:
            return self._json['resultInfo']
        except KeyError:
            return None

    @property
    def state(self):
        self._refresh()
        return self._json['state']

    @property
    def progress(self):
        self._refresh()
        return self._json['progressPercentage']

    @property
    def start_time(self):
        return self._json['startTime']

    @property
    def last_update_time(self):
        self._refresh()
        return self._json['lastUpdateTime']

    @property
    def completion_time(self):
        self._refresh()
        try:
            return self._json['completionTime']
        except KeyError:
            return None

    @property
    def additional_info(self):
        self._refresh()
        try:
            return self._json['additionalInfo']
        except KeyError:
            return None


class Backup(Refreshable):
    """BRO backup.

    Args:
        bro (Bro): Bro instance
        scope (str): Backup scope for action
        backup_id (str): Backup ID

    The label property is settable.
    """

    def __init__(self, bro, scope, backup_id):
        self._scope = scope
        super().__init__(
            bro, f'{bro.url}/v1/backup-manager/{scope}/backup/{backup_id}')

        try:
            self._id = self._json['id']
        except KeyError:
            raise BroInvalidResponse('Received invalid backup response')

    @property
    def id(self):
        return self._id

    @property
    def scope(self):
        return self._scope

    @property
    def name(self):
        return self._json['name']

    @property
    def status(self):
        self._refresh()
        return self._json['status']

    @property
    def label(self):
        self._refresh()
        try:
            return self._json['userLabel']
        except KeyError:
            return None

    @label.setter
    def label(self, label):
        self._update_fields(userLabel=label)

    @property
    def creation_time(self):
        return self._json['creationTime']

    @property
    def creation_type(self):
        self._refresh()
        return self._json['creationType']

    @property
    def services(self):
        self._refresh()
        return [Service(data) for data in self._json['softwareVersions']]


class Status(Refreshable):
    """BRO status.

    Args:
        bro (Bro): Bro instance
    """

    def __init__(self, bro):
        self._bro = bro
        super().__init__(bro, f'{bro.url}/v1/health')

    @property
    def health(self):
        self._refresh()
        return self._json['status']

    @property
    def availability(self):
        self._refresh()
        return self._json['availability']

    @property
    def action(self):
        self._refresh()
        action = self._json['ongoingAction']
        if action:
            try:
                return Action(
                    self._bro, action['backupManagerId'], action['actionId'])
            except KeyError:
                pass
        return None

    @property
    def agents(self):
        self._refresh()
        return self._json['registeredAgents']


class Service():
    """BRO Service (SoftwareVersion) object.

    Args:
        data (dict): Software Version data from BRO
    """

    def __init__(self, data):
        self._data = data

    @property
    def name(self):
        return self._data['productName']

    @property
    def description(self):
        return self._data['description']

    @property
    def number(self):
        return self._data['productNumber']

    @property
    def version(self):
        return self._data['productRevision']

    @property
    def date(self):
        return self._data['date']

    @property
    def type(self):
        return self._data['type']

    @property
    def agent_id(self):
        return self._data['agentId']


class BroError(Exception):
    """Base exception class for BRO API.
    """


class BroRequestError(BroError):
    """BRO request error.

    Raised when BRO REST API cannot be reached.
    """


class BroResponseError(BroError):
    """BRO response error.

    Raised when a non-successful status code is returned from the REST API.

    BRO errors return this JSON:
    {
      "statusCode": XYZ,
      "message": "error description"
    }

    The message is extracted from the response and included in the exception.
    """

    def __init__(self, url, response):
        self.url = url
        self.response = response
        try:
            self.msg = response.json()['message']
        except (ValueError, KeyError):
            self.msg = response.text
        super().__init__(self.msg)


class BroInvalidResponse(BroError):
    """Unexpected response from BRO.
    """
