#!/usr/bin/env python

import time, threading, logging

from trbnet.core import TrbNet, TrbException
from trbnet.xmldb import XmlDb
from trbnet.util.trbcmd import _xmlget as xmlget

from pcaspy import Driver, SimpleServer, Alarm, Severity
from pcaspy.driver import manager

from .helpers import SeenBeforeFilter

t = TrbNet()

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

    def add_subscription(self, trb_address, entity, name, responding_endpoints=None):
        self._subscriptions.append((trb_address, entity, name, responding_endpoints))

    def initialize(self):
        self._pvdb_manager = PvdbManager(self._pvdb)
        self._pvdb_manager.initialize(self._subscriptions)
        self._initialized = True

    @property
    def all_pvs(self):
        if not self._initialized:
            raise NameError("Please run .initialize() first")
        return [pv for pv in self._pvdb.keys()]

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

    def __init__(self, pvdb):
        self._pvdb = pvdb

    def initialize(self, subscriptions):
        for trb_address, entity, name, responding_endpoints in subscriptions:
            for data in xmlget(trb_address, entity, name, logger=logger):
                self._pvdb[data['context']['identifier']] = {
                  'type': TYPE_MAPPING[data['format']][0],
                  'unit': data['unit'],
                }
                if data['format'] == 'enum':
                    choices = data['meta']['choices']
                    vals = list(choices.keys())
                    min_val, max_val = min(vals), max(vals)
                    enums = []
                    for i in range(max_val+1):
                        enums.append(choices[i] if i in choices else 'n/a')
                    self._pvdb[data['context']['identifier']]['enums'] = enums
                if data['format'] == 'boolean' and TYPE_MAPPING[data['format']][0] == 'enum':
                    self._pvdb[data['context']['identifier']]['enums'] = ['false', 'true']

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
                trb_address, entity, element, responding_endpoints = subscription
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
