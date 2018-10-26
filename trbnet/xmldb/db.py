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

    TOP_ENTITY = 'TrbNetEntity'
    ENTITY_TAGS = ('field', 'register', 'group', 'TrbNetEntity')

    def __init__(self, folder=None):
        if folder is None:
            folder = os.environ.get('XMLDB', '.')
            folder = os.path.expanduser(folder)
        self.folder = folder
        self._cache_xml_docs = {}
        self._cache_unique_elements = {}
        self._cache_elements = {}

    def _get_xml_doc(self, entity):
        # Try to fetch xmldoc from cache and return it:
        if entity in self._cache_xml_docs:
            return self._cache_xml_docs[entity]
        # Otherwise parse the .xml file and add it to the cache:
        xml_path = os.path.join(self.folder, entity + '.xml')
        xml_doc = etree.parse(xml_path)
        ## check schema?
        #xmlschema_doc = etree.parse(xsd_path)
        #xmlschema = etree.XMLSchema(xmlschema_doc)
        #result = xmlschema.validate(xml_doc)
        self._cache_xml_docs[entity] = xml_doc
        return xml_doc

    def _get_elements_by_name_attr(self, entity, name_attr, tag='*', amount=None):
        '''
        Finds and returns elements from the entity XML tree with the attribute
        'name' having the value of this method's argument name_attr.

        Arguments:
        tag -- Can be pin the elements to search for to specific tag names. Default: wildcard
        amount -- If set to an integer {0, 2, 3, ...}, the returned list will contain this amount of elements.
        '''
        # Try to fetch the elements from the cache
        key = (entity, name_attr, tag)
        if key in self._cache_elements:
            results = self._cache_elements[key]
        # Otherwise, fetch them from the XML file:
        else:
            xml_doc = self._get_xml_doc(entity)
            results = xml_doc.findall("//"+tag+"[@name='"+name_attr+"']")
            self._cache_elements[key] = results
        # Check if we found the right amount of elements
        if amount is not None and len(results) != amount:
            fmt = "Could not find the desired amount of tags with attribute name=%s: found %d instead of %d"
            raise ValueError(fmt % (name_attr, len(results), amount))
        # Return
        return results

    def _get_unique_element_by_name_attr(self, entity, name_attr, tag='*'):
        # Try to find element in cache and return it:
        key = (entity, name_attr, tag)
        if key in self._cache_unique_elements:
            return self.unique_elements_cache[key]
        # Otherwise, search for it in the XML file:
        results = self._get_elements_by_name_attr(entity, name_attr, tag=tag)
        # Return the result if we found a single one and raise exceptions otherwise:
        if len(results) == 1:
            return results[0]
        elif len(results) == 0:
            raise ValueError("No such element found: tag '%s' with attribute name=%s" % (tag, name_attr))
        else:
            fmt = "Non-unique search for tag '%s' with attribute name=%s! XML Database Error!"
            raise ValueError(fmt % (tag, name_attr))

    def find_field(self, entity, field):
        return self._get_unique_element_by_name_attr(entity, field, tag='field')

    def get_reg_addresses(self, entity, field):
        if type(field) == str:
            field = self.find_field(entity, field)
        base_address = 0
        repeat = 1
        offset = 0
        # Determine base_address (and slices/repetitions if applicable)
        node = field.getparent()
        while node.tag in self.ENTITY_TAGS:
            base_address += int(node.get('address', '0'), 16)
            if node.tag == self.TOP_ENTITY: break
            r = int(node.get('repeat', 1))
            if r != 1:
                repeat = r
                offset = int(node.get('size', 0), 10)
            node = node.getparent()
        return [base_address + i * offset for i in range(repeat)]

    def _get_field_identifier(self, entity, fieldname, trb_address, slice=None):
        identifier = "{}-0x{:04x}-{}".format(entity, trb_address, fieldname)
        if slice is not None:
            identifier += "." + str(slice)
        return identifier

    def _get_field_hierarchy(self, entity, field):
        stack = []
        node = field
        while node.tag in self.ENTITY_TAGS:
            stack.append(node.get('name'))
            if node.tag == self.TOP_ENTITY: break
            node = node.getparent()
        return list(reversed(stack))

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
        identifier = self._get_field_identifier(entity, fieldname, trb_address, slice=slice)
        hierarchy = self._get_field_hierarchy(entity, field)
        context = {
          'address': address,
          'identifier': identifier,
          'hierarchy': hierarchy,
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
