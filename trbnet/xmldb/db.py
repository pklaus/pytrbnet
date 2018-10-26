import os
import enum
from datetime import datetime as dt
from lxml import etree

class XmlDb(object):

    def __init__(self, path):
        self.name = os.path.splitext(os.path.basename(path))[0]
        self.xml_doc = etree.parse(path)
        #xmlschema_doc = etree.parse(xsd_path)
        #self.xmlschema = etree.XMLSchema(xmlschema_doc)
        #result = self.xmlschema.validate(self.xml_doc)

    def find_field(self, field):
        # Find the right field entry in the xml database
        results = self.xml_doc.findall("//field[@name='"+field+"']")
        # Make sure, we only found one result and select it
        if len(results) == 1:
            return results[0]
        elif len(results) == 0:
            raise ValueError("No such field found: %s" % field)
        elif len(results) != 0:
            raise ValueError("Non-unique field name! XML Database Error!")

    def get_reg_addresses(self, field):
        if type(field) == str:
            field = self.find_field(field)
        base_address = 0
        repeat = 1
        offset = 0
        # Determine base_address (and slices/repetitions if applicable)
        node = field.getparent()
        while node.tag in ('register', 'group', 'TrbNetEntity'):
            base_address += int(node.get('address', '0'), 16)
            if node.tag == 'TrbNetEntity': break
            r = int(node.get('repeat', 1))
            if r != 1:
                repeat = r
                offset = int(node.get('size', 0), 10)
            node = node.getparent()
        return [base_address + i * offset for i in range(repeat)]

    def convert_field(self, fieldname, register_word, trb_address=0xffff, slice=None):
        field = self.find_field(fieldname)
        address = self.get_reg_addresses(field)[slice if slice is not None else 0]
        start = int(field.get('start', 0))
        bits = int(field.get('bits', 32))
        format = field.get('format', 'unsigned')
        unit = field.get('unit', '')
        scale = float(field.get('scale', 1.0))
        scaleoffset = float(field.get('scaleoffset', 0.0))
        #errorFlag = 
        #invertFlag = 
        raw = (register_word >> start) & ((1 << bits) -1)
        meta = {}
        value = {
            'raw': raw,
            'string': raw,
            'python': None,
            'unicode': None,
          }
        if format == 'unsigned':
            val = round(scale * raw + scaleoffset)
            val = val if val >= 0 else 0
            value['python'] = val
            value['string'] = str(val)
        elif format == 'float':
            val = float(raw)
            val *= scale
            val += scaleoffset
            value['python'] = val
            value['string'] = '%.2f' % val
        elif format == 'time':
            val = dt.utcfromtimestamp(raw)
            value['python'] = val
            value['string'] = val.strftime('%Y-%m-%d %H:%M')
        elif format == 'hex':
            fmt = '0x{:0%dx}' % ((bits+3)/4)
            value['python'] = raw
            value['string'] = fmt.format(raw)
        elif format == 'integer':
            val = round(scale * raw + scaleoffset)
            value['python'] = val
            value['string'] = str(val)
        elif format == 'boolean':
            val = bool(raw)
            value['python'] = val
            value['string'] = str(val).lower()
        elif format == 'enum':
            meta['choices'] = {}
            results = field.findall("enumItem")
            for result in results:
                meta['choices'][int(result.get('value'))] = result.text
            DynamicEnum = enum.Enum(fieldname, {v: k for k, v in meta['choices'].items()})
            if raw in meta['choices']:
                value['python'] = DynamicEnum(raw)
                value['string'] = meta['choices'][raw]
            else:
                value['python'] = raw
                value['string'] = str(raw)
        elif format == 'bitmask':
            fmt = '{:0%db}' % (bits)
            val = fmt.format(raw)
            value['python'] = raw
            value['string'] = val
            value['unicode'] = val.replace('0', '□').replace('1', '■')
        elif format == 'binary':
            fmt = '0b{:0%db}' % (bits)
            value['python'] = raw
            value['string'] = fmt.format(raw)
        else:
            raise NotImplementedError('format: ' + format)
        if value['unicode'] is None: value['unicode'] = value['string']
        full_name = "{}-0x{:04x}-{}".format(self.name, trb_address, fieldname)
        if slice is not None:
            full_name += "." + str(slice)
        context = {
          'address': address,
          'full_name': full_name,
          'trb_address': trb_address,
          'fieldname': fieldname,
        }
        return {
            'value': value,
            'unit': unit,
            'meta': meta,
            'format': format,
            'context': context
          }
