import os
import enum
from datetime import datetime as dt
from lxml import etree

class XmlDb(object):
    '''
    XmlDb is an object representing the XML database used to describe
    registers of TrbNet systems. In this context, "XML database" means:
    a set of XML files in a single folder obeying a specific schema.

    The database folder can be provided by the environment variable
    'XMLDB' or by specifying the folder as keyword argument when
    instantiating the class:

    >>> db = XmlDb(folder='./path/to/daqtools/xml-db/database/')
    '''

    def __init__(self, folder=None):
        if folder is None:
            folder = os.environ.get('XMLDB', '.')
            folder = os.path.expanduser(folder)
        self.folder = folder
        self.xml_docs = {}

    def _get_xml_doc(self, entity):
        if entity in self.xml_docs:
            return self.xml_docs[entity]
        xml_path = os.path.join(self.folder, entity + '.xml')
        xml_doc = etree.parse(xml_path)
        ## check schema?
        #xmlschema_doc = etree.parse(xsd_path)
        #xmlschema = etree.XMLSchema(xmlschema_doc)
        #result = xmlschema.validate(xml_doc)
        self.xml_docs[entity] = xml_doc
        return xml_doc

    def find_field(self, entity, field):
        xml_doc = self._get_xml_doc(entity)
        # Find the right field entry in the xml database
        results = xml_doc.findall("//field[@name='"+field+"']")
        # Make sure, we only found one result and select it
        if len(results) == 1:
            return results[0]
        elif len(results) == 0:
            raise ValueError("No such field found: %s" % field)
        elif len(results) != 0:
            raise ValueError("Non-unique field name! XML Database Error!")

    def get_reg_addresses(self, entity, field):
        if type(field) == str:
            field = self.find_field(entity, field)
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

    def convert_field(self, entity, fieldname, register_word, trb_address=0xffff, slice=None):
        field = self.find_field(entity, fieldname)
        address = self.get_reg_addresses(entity, field)[slice if slice is not None else 0]
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
        full_name = "{}-0x{:04x}-{}".format(entity, trb_address, fieldname)
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
