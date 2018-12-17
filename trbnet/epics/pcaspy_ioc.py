#!/usr/bin/env python

import time, threading, logging

from trbnet.core import TrbNet, TrbException
from trbnet.xmldb import XmlDb
from trbnet.util.trbcmd import _xmlget as xmlget, _xmlentry as xmlentry

from pcaspy import Driver, SimpleServer, Alarm, Severity
from pcaspy.driver import manager

from .helpers import SeenBeforeFilter

t = TrbNet()
db = XmlDb()

logger = logging.getLogger('trbnet.epics.pcaspy_ioc')
logging.basicConfig(
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
restr_func = lambda log: log[2].startswith('register missing')
logger.addFilter(SeenBeforeFilter(restriction_func=restr_func))


class TrbNetIOC(object):

    def __init__(self):
        self.prefix = ''
        self._initialized = False
        self._subscriptions = []
        self._pvdb = {}
        self._pvdb_manager = None
        self._expected_trb_addresses = {}

    def before_initialization(func):
       def func_wrapper(self, *args, **kwargs):
           if self._initialized:
               raise NameError('Cannot use the method .%s() after running .initialize().' % func.__name__)
           return func(self, *args, **kwargs)
       return func_wrapper

    @before_initialization
    def add_subscription(self, trb_address, entity, name):
        self._subscriptions.append((trb_address, entity, name))

    @before_initialization
    def add_expected_trb_addresses(self, send_to_trb_address, answer_from_trb_addresses):
        self._expected_trb_addresses[send_to_trb_address] = answer_from_trb_addresses

    def initialize(self):
        self._pvdb_manager = PvdbManager(self._pvdb, self._expected_trb_addresses)
        self._pvdb_manager.initialize(self._subscriptions)
        self._initialized = True

    @property
    def all_pvs(self):
        if not self._initialized:
            raise NameError("Please run .initialize() first")
        return [self.prefix + pv for pv in self._pvdb.keys()]

    def run(self):
        if not self._initialized:
            self.initialize()

        server = SimpleServer()
        server.createPV(self.prefix, self._pvdb)
        driver = TrbNetIocDriver(self._subscriptions, self._pvdb_manager)

        while True:
            # process CA transactions
            server.process(0.1)


class PvdbManager(object):

    def __init__(self, pvdb, expected_trb_addresses):
        self._pvdb = pvdb
        self._expected_trb_addresses = expected_trb_addresses

    def _add(self, identifier, definition):
        self._pvdb[identifier] = {
          'type': TYPE_MAPPING[definition['format']][0],
          'unit': definition['unit'],
        }
        if definition['format'] == 'enum':
            choices = definition['meta']['choices']
            vals = list(choices.keys())
            min_val, max_val = min(vals), max(vals)
            enums = []
            for i in range(max_val+1):
                enums.append(choices[i] if i in choices else 'n/a')
            self._pvdb[identifier]['enums'] = enums
        if definition['format'] == 'boolean' and TYPE_MAPPING[definition['format']][0] == 'enum':
            self._pvdb[identifier]['enums'] = ['false', 'true']

    def initialize(self, subscriptions):
        for trb_address, entity, name in subscriptions:
            if trb_address in self._expected_trb_addresses:
                answer_from_trb_addresses = self._expected_trb_addresses[trb_address]
                for info in xmlentry(entity, name):
                    slices = len(info['reg_addresses'])
                    for slice in range(slices):
                        slice = slice if slices > 1 else None
                        for answer_from_trb_address in answer_from_trb_addresses:
                            identifier = db._get_field_identifier(entity, info['field_name'], answer_from_trb_address, slice=slice)
                            definition = db._get_field_info(entity, info['field_name'])
                            self._add(identifier, definition)
            else:
                for data in xmlget(trb_address, entity, name, logger=logger):
                    self._add(data['context']['identifier'], data)

class TrbNetIocDriver(Driver):

    def __init__(self, subscriptions, scan_period=1.0):
        Driver.__init__(self)
        self.scan_period = 1.0
        self.subscriptions = subscriptions
        self.start()

    def start(self):
        if self.scan_period > 0:
            self.tid = threading.Thread(target=self.scan_all)
            self.tid.setDaemon(True)
            self.tid.start()

    def scan_all(self):
        last_time = time.time()
        while True:
            for subscription in self.subscriptions:
                trb_address, entity, element = subscription
                for data in xmlget(trb_address, entity, element, logger=logger):
                    reason = data['context']['identifier']
                    try:
                        self.pvDB[reason].mask = 0
                        self.setParamStatus(reason, Alarm.NO_ALARM, Severity.NO_ALARM)
                        self.setParam(reason, data['value'][TYPE_MAPPING[data['format']][1]])
                        manager.pvs[self.port][reason].updateValue(self.pvDB[reason])
                    except Exception as e:
                        logger.error(str(e))

            # if the process was suspended, reset last_time:
            if time.time() - last_time > self.scan_period:
                last_time = time.time()

            time.sleep(max(0.0, self.scan_period - (time.time() - last_time)))
            last_time += self.scan_period

TYPE_MAPPING = {
    # pcaspy types: 'enum', 'string', 'char', 'float' or 'int'
    'unsigned': ('int', 'python'),
    'integer': ('int', 'python'),
    'signed': ('int', 'python'),
    'hex': ('int', 'python'),
    'boolean': ('enum', 'raw'),
    'bitmask': ('int', 'raw'),
    'enum': ('enum', 'raw'),
    'float': ('float', 'python'),
    #'time': ('char', 'string'),
    'time': ('int', 'raw'),
    #'binary': ('char', 'string'),
    'binary': ('int', 'raw'),
}
