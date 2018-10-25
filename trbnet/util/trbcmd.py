#!/usr/bin/env python

import click, time
from trbnet import TrbNet
from trbnet.xmldb import XmlDb

t = TrbNet()

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
    response = t.register_read(trb_address, register)
    for endpoint in response:
        str_data = '{:08X}'.format(response[endpoint])
        print("endpoint 0x{:08X} responded with: {}".format(endpoint, str_data))

@cli.command()
@click.argument('trb_address', type=BASED_INT)
@click.argument('register', type=BASED_INT)
@click.argument('size', type=BASED_INT)
@click.argument('mode', type=BASED_INT)
def rm(trb_address, register, size, mode):
    click.echo('Reading register memory')
    response = t.register_read_mem(trb_address, register, mode, size)
    for endpoint in response:
        str_data = ' '.join('{:08X}'.format(word) for word in response[endpoint])
        print("endpoint 0x{:08X} responded with: {}".format(endpoint, str_data))

@cli.command()
@click.argument('xml_name')
@click.argument('xml_path')
@click.argument('entity')
def xmlentry(xml_name, xml_path, entity):
    db = XmlDb(xml_name, xml_path)
    reg_addresses = db.get_reg_addresses(entity)
    for count, reg_address in enumerate(reg_addresses, start=1):
        print("slice", count, "address:", hex(reg_address))

@cli.command()
@click.argument('xml_name')
@click.argument('xml_path')
@click.argument('trb_address', type=BASED_INT)
@click.argument('entity')
def xmlget(xml_name, xml_path, trb_address, entity):
    db = XmlDb(xml_name, xml_path)
    reg_addresses = db.get_reg_addresses(entity)
    slices = len(reg_addresses)
    for slice, reg_address in enumerate(reg_addresses):
        response = t.register_read(trb_address, reg_address)
        for response_trb_address, value in response.items():
            data = db.convert_field(entity, value, trb_address=response_trb_address, slice=slice if slices > 1 else None)
            #print(data)
            print("{context[full_name]} {value[unicode]} {unit}".format(**data))

if __name__ == '__main__':
    cli()
