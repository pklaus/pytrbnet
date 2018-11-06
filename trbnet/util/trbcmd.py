#!/usr/bin/env python

import click, time, logging
from trbnet import TrbNet, TrbException, TrbError
from trbnet.xmldb import XmlDb

t = TrbNet()
logger = logging.getLogger('trbnet.util.trbcmd')

### Helpers

def _status_warning():
    if t.trb_errno() == TrbError.TRB_STATUS_WARNING:
        return "Status-Bit(s) have been set:\n" + t.trb_termstr(t.trb_term())
    else:
        return None

### Definition of a Python API to the functions later exposed by the CLI

def _r(trb_address, register):
    response = t.register_read(trb_address, register)
    for endpoint in response:
        str_data = '{:08X}'.format(response[endpoint])
        print("endpoint 0x{:08X} responded with: {}".format(endpoint, str_data))

def _rm(trb_address, register, size, mode):
    response = t.register_read_mem(trb_address, register, mode, size)
    for endpoint in response:
        str_data = ' '.join('{:08X}'.format(word) for word in response[endpoint])
        print("endpoint 0x{:08X} responded with: {}".format(endpoint, str_data))
    status_warning = _status_warning()
    if status_warning: logger.warning(status_warning)

def _xmlentry(entity, name):
    db = XmlDb()
    reg_addresses = db._get_all_element_addresses(entity, name)
    for field_name in db._contained_fields(entity, name):
        reg_addresses = db._get_all_element_addresses(entity, field_name)
        yield {'entity': entity, 'field_name': field_name, 'reg_addresses': reg_addresses}

def _xmlget(trb_address, entity, name, logger=logger):
    db = XmlDb()
    register_blocks = db._determine_continuous_register_blocks(entity, name)
    all_data = {} # dictionary with {'reg_address': {'trb_address': int, ...}, ...}
    for start, size in register_blocks:
        if size > 1:
            try:
                response = t.register_read_mem(trb_address, start, 0, size)
            except TrbException as e:
                if logger: logger.error("TRB Error happened: %s -- Continuing anyways.", repr(e))
                continue
            except Exception as e:
                if logger: logger.error("Other error happened: %s -- Continuing anyways.", repr(e))
                continue
            for response_trb_address, data in response.items():
                if not data:
                    continue
                for reg_address, word in enumerate(data, start=start):
                    if reg_address not in all_data:
                         all_data[reg_address] = {}
                    all_data[reg_address][response_trb_address] = word
        else:
            reg_address = start
            try:
                response = t.register_read(trb_address, reg_address)
            except TrbException as e:
                if logger: logger.error("TRB Error happened: %s -- Continuing anyways.", repr(e))
                continue
            except Exception as e:
                if logger: logger.error("Other error happened: %s -- Continuing anyways.", repr(e))
                continue
            for response_trb_address, word in response.items():
                if reg_address not in all_data:
                    all_data[reg_address] = {}
                all_data[reg_address][response_trb_address] = word
    for field_name in db._contained_fields(entity, name):
        reg_addresses = db._get_all_element_addresses(entity, field_name)
        slices = len(reg_addresses)
        for slice, reg_address in enumerate(reg_addresses):
            if reg_address not in all_data:
                fmt = "register missing in response: %s (addr 0x%04x)"
                if logger: logger.warning(fmt, field_name, reg_address)
                continue
            for response_trb_address, value in all_data[reg_address].items():
                data = db.convert_field(entity, field_name, value, trb_address=response_trb_address, slice=slice if slices > 1 else None)
                yield data

### Definition of the CLI with the help of the click package:

class BasedIntParamType(click.ParamType):
    name = 'integer'
    def convert(self, value, param, ctx):
        try:
            if value[:2].lower() == '0x':
                return int(value[2:], 16)
            elif value[:1] == '0':
                return int(value, 8)
            return int(value, 10)
        except ValueError:
            self.fail('%s is not a valid integer' % value, param, ctx)

BASED_INT = BasedIntParamType()

@click.group()
def cli():
    pass

@cli.command()
@click.argument('trb_address', type=BASED_INT)
@click.argument('register', type=BASED_INT)
def r(trb_address, register):
    click.echo('Reading register')
    _r(trb_address, register)

@cli.command()
@click.argument('trb_address', type=BASED_INT)
@click.argument('register', type=BASED_INT)
@click.argument('size', type=BASED_INT)
@click.argument('mode', type=BASED_INT)
def rm(trb_address, register, size, mode):
    click.echo('Reading register memory')
    _rm(trb_address, register, size, mode)

@cli.command()
@click.argument('entity')
@click.argument('name')
def xmlentry(entity, name):
    click.echo('Searching xml register entry')
    for info in _xmlentry(entity, name):
        slices = len(info['reg_addresses'])
        info['reg_addresses'] = ', '.join('0x{:04x}'.format(addr) for addr in info['reg_addresses'])
        info['slices'] = ' (%d slices)' % slices if slices > 1 else ''
        print("ENTITY: {entity:10s} FIELD: {field_name:20s} REGISTER(s): {reg_addresses} {slices}".format(**info))

@cli.command()
@click.argument('trb_address', type=BASED_INT)
@click.argument('entity')
@click.argument('name')
def xmlget(trb_address, entity, name):
    click.echo('Querying xml register entry from TrbNet')
    for data in _xmlget(trb_address, entity, name):
        print("{context[identifier]} {value[unicode]} {unit}".format(**data))

if __name__ == '__main__':
    cli()
