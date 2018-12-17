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
        self._cache_elements = {}
        self._cache_field_hierarchy = {}
        self._cache_field_info = {}

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
        results = self._get_elements_by_name_attr(entity, name_attr, tag=tag)
        # Return the result if we found a single one and raise exceptions otherwise:
        if len(results) == 1:
            return results[0]
        elif len(results) == 0:
            raise ValueError("No such element found: tag '%s' with attribute name=%s" % (tag, name_attr))
        else:
            fmt = "Non-unique search for tag '%s' with attribute name=%s! XML Database Error!"
            raise ValueError(fmt % (tag, name_attr))

    def _get_single_element_by_name_attr_prefer_field(self, entity, name_attr):
        '''
        This function will try to find a unique element:
        * First, it tries if a field' element with that name attribute exists.
          (Unique only among the 'field' elements)
        * If that fails with no result, it retries extending the search to any
          unique element (tag) with the given name attribute.
        '''
        try:
            return self._get_unique_element_by_name_attr(entity, name_attr, tag='field')
        except:
            pass
        return self._get_unique_element_by_name_attr(entity, name_attr, tag='*')

    def find_field(self, entity, field):
        return self._get_single_element_by_name_attr_prefer_field(entity, field)

    def _get_element_addressing(self, entity, element):
        '''
        Determine the addressing of an element in the database:

        * base_address: The address of the first register
        * slices: The number of slices for this (or a parent) element,
          set to None if there are no repetitions.
        * stepsize: The stepsize to determine the address for any additional slices
        * size: The size (number of elements) of the requested element

        Returns:
        tuple -- (base_address, slices, stepsize, size)
        '''
        if type(element) == str:
            element = self._get_single_element_by_name_attr_prefer_field(entity, element)
        base_address = 0
        slices = None
        size = int(element.get('size', '1'))
        stepsize = 0
        node = element
        while node.tag in self.ENTITY_TAGS:
            base_address += int(node.get('address', '0'), 16)
            if node.tag == self.TOP_ENTITY: break
            repeat = int(node.get('repeat', 1))
            if repeat != 1:
                slices = repeat
                stepsize = int(node.get('size', '0'), 10)
            node = node.getparent()
        return (base_address, slices, stepsize, size)

    def _get_all_element_addresses(self, entity, element):
        '''
        Determine all addresses of an element

        Returns:
        list -- containing all addresses of an element
        '''
        base_address, slices, stepsize, size = self._get_element_addressing(entity, element)
        return [base_address + i * stepsize for i in range(slices or 1)]

    def _contained_fields(self, entity, element):
        '''
        name specifies the 'name' attribute of a
        {<TrbNetEntity>,<group>,<register>,<field>}
        tag in the .xml file corresponding to entity.
        Returns a list of all fields contained in the element.
        '''
        if type(element) == str:
            element = self._get_single_element_by_name_attr_prefer_field(entity, element)
        if element.tag == 'field' and element.get('name'):
            return [element.get('name')]
        fields = element.findall(".//field[@name]")
        return [field.get('name') for field in fields]

    def _determine_continuous_register_blocks(self, entity, element):
        register_blocks = []
        if type(element) == str:
            element = self._get_single_element_by_name_attr_prefer_field(entity, element)
        base_address, slices, stepsize, size = self._get_element_addressing(entity, element)
        continuous = element.get('continuous', 'false') == 'true'
        #print("el:", element.get('name'), "address:", hex(base_address), "size:", size, "last (tent.):", hex(base_address+size-1) ,"continuous:", continuous, "slices:", slices or 1)
        if continuous or element.tag in ('register', 'field'):
            register_blocks += [(base_address + i*stepsize, size) for i in range(slices or 1)]
        else:
            for child in element:
                if child.tag not in self.ENTITY_TAGS:
                    continue
                register_blocks += self._determine_continuous_register_blocks(entity, child)
        return register_blocks

    def _get_field_identifier(self, entity, field_name, trb_address, slice=None):
        identifier = "{}-0x{:04x}-{}".format(entity, trb_address, field_name)
        if slice is not None:
            identifier += "." + str(slice)
        return identifier

    def _get_field_hierarchy(self, entity, field):
        # Try to fetch the field hierarchy from the cache and return it:
        key = (entity, field)
        if key in self._cache_field_hierarchy:
            return self._cache_field_hierarchy[key]
        # Otherwise, construct the hierarchy by walking up the tree from the
        # to the top level XML entity and add it to the cache:
        if type(field) == str:
            field = self.find_field(entity, field)
        stack = []
        node = field
        while node.tag in self.ENTITY_TAGS:
            stack.append(node.get('name'))
            if node.tag == self.TOP_ENTITY: break
            node = node.getparent()
        hierarchy = list(reversed(stack))
        self._cache_field_hierarchy[key] = hierarchy
        return hierarchy

    def _get_field_info(self, entity, field):
        # Try to fetch the field info from the cache and return it:
        key = (entity, field)
        if key in self._cache_field_info:
            return self._cache_field_info[key]
        # Otherwise, construct the field info by reading in its XML information
        if type(field) == str:
            field = self.find_field(entity, field)
        field_name = field.get('name')
        info = {
          'addresses': self._get_all_element_addresses(entity, field),
          'start': int(field.get('start', 0)),
          'bits': int(field.get('bits', 32)),
          'format': field.get('format', 'unsigned'),
          'unit': field.get('unit', ''),
          'scale': float(field.get('scale', 1.0)),
          'scaleoffset': float(field.get('scaleoffset', 0.0)),
          'meta': {}
          #'errorFlag': ,
          #'invertFlag': ,
        }
        if info['format'] == 'enum':
            results = field.findall("enumItem")
            choices = {}
            for result in results:
                choices[int(result.get('value'))] = result.text
            info['meta']['choices'] = choices
            DynamicEnum = enum.Enum(field_name, {v: k for k, v in choices.items()})
            info['meta']['enum'] = DynamicEnum
        self._cache_field_info[key] = info
        return info

    def convert_field(self, entity, field_name, register_word, trb_address=0xffff, slice=None):
        info = self._get_field_info(entity, field_name)
        address = info['addresses'][slice if slice is not None else 0]
        start = info['start']
        bits = info['bits']
        format = info['format']
        unit = info['unit']
        scale = info['scale']
        scaleoffset = info['scaleoffset']
        meta = info['meta']
        #errorFlag = 
        #invertFlag = 
        raw = (register_word >> start) & ((1 << bits) -1)
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
        elif format in ('integer', 'signed'):
            val = round(scale * raw + scaleoffset)
            value['python'] = val
            value['string'] = str(val)
        elif format == 'boolean':
            val = bool(raw)
            value['python'] = val
            value['string'] = str(val).lower()
        elif format == 'enum':
            DynamicEnum = meta['enum']
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
        if value['unicode'] is None:
            value['unicode'] = value['string']
        if unit:
            value['string'] += ' ' + unit
            value['unicode'] += ' ' + unit
        identifier = self._get_field_identifier(entity, field_name, trb_address, slice=slice)
        hierarchy = self._get_field_hierarchy(entity, field_name)
        context = {
          'address': address,
          'identifier': identifier,
          'hierarchy': hierarchy,
          'trb_address': trb_address,
          'field_name': field_name,
        }
        return {
            'value': value,
            'unit': unit,
            'meta': meta,
            'format': format,
            'context': context
          }
