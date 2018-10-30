#!/usr/bin/env python

import time, sys, threading, subprocess, shlex, math

from trbnet.core import TrbNet
from trbnet.xmldb import XmlDb

from pcaspy import Driver, SimpleServer, Alarm, Severity
from pcaspy.driver import manager

t = TrbNet()

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
            for data in xmlget(trb_address, entity, name):
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
                for data in xmlget(trb_address, entity, element):
                    reason = data['context']['identifier']
                    try:
                        self.pvDB[reason].mask = 0
                        self.setParamStatus(reason, Alarm.NO_ALARM, Severity.NO_ALARM)
                        self.setParam(reason, data['value'][TYPE_MAPPING[data['format']][1]])
                        manager.pvs[self.port][reason].updateValue(self.pvDB[reason])
                    except Exception as e:
                        print("ERROR: " + str(e))

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

def xmlget(trb_address, entity, name):
    db = XmlDb()
    register_blocks = db._determine_continuous_register_blocks(entity, name)
    all_data = {} # dictionary with {'reg_address': {'trb_address': int, ...}, ...}
    for start, size in register_blocks:
        if size > 1:
            response = t.register_read_mem(trb_address, start, 0, size)
            for response_trb_address, data in response.items():
                if not data:
                    continue
                for reg_address, word in enumerate(data, start=start):
                    if reg_address not in all_data:
                         all_data[reg_address] = {}
                    all_data[reg_address][response_trb_address] = word
        else:
            reg_address = start
            response = t.register_read(trb_address, reg_address)
            for response_trb_address, word in response.items():
                if reg_address not in all_data:
                    all_data[reg_address] = {}
                all_data[reg_address][response_trb_address] = word
    for field_name in db._contained_fields(entity, name):
        reg_addresses = db._get_all_element_addresses(entity, field_name)
        slices = len(reg_addresses)
        for slice, reg_address in enumerate(reg_addresses):
            if reg_address not in all_data:
                print("Error:  field_name:", field_name, "with register address:", reg_address, "not found in fetched data")
                continue
            for response_trb_address, value in all_data[reg_address].items():
                data = db.convert_field(entity, field_name, value, trb_address=response_trb_address, slice=slice if slices > 1 else None)
                yield data
