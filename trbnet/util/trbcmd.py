#!/usr/bin/env python

import click, time
from trbnet import TrbNet
from trbnet.xmldb import XmlDb

t = TrbNet()

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

def _xmlentry(entity, name):
    db = XmlDb()
    reg_addresses = db.get_reg_addresses(entity, name)
    for count, reg_address in enumerate(reg_addresses, start=1):
        print("slice", count, "address:", hex(reg_address))

def _xmlget(trb_address, entity, name):
    db = XmlDb()
    reg_addresses = db.get_reg_addresses(entity, name)
    slices = len(reg_addresses)
    for slice, reg_address in enumerate(reg_addresses):
        response = t.register_read(trb_address, reg_address)
        for response_trb_address, value in response.items():
            data = db.convert_field(entity, name, value, trb_address=response_trb_address, slice=slice if slices > 1 else None)
            #print(data)
            print("{context[identifier]} {value[unicode]} {unit}".format(**data))

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
    _xmlentry(entity, name)

@cli.command()
@click.argument('trb_address', type=BASED_INT)
@click.argument('entity')
@click.argument('name')
def xmlget(trb_address, entity, name):
    click.echo('Querying xml register entry from TrbNet')
    _xmlget(trb_address, entity, name)

if __name__ == '__main__':
    cli()
