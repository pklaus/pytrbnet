# PyTrbNet

This is a Python package wrapping libtrbnet.so.
It allows accessing trbnet registers from Python.

The package comes with two additional features:

* XmlDb support. Allows to query registers by their
  name as specified in the corresponding xml file.
* PCASpy-based EPICS IOC providing TrbNet register
  status information to the EPICS detector control
  system.

### Installation

This package can be installed from the Python Package
Index via:

    pip install trbnet

### Configuration / Setup

As this Python package depends on the shared library
libtrbnet.so for the communication with TrbNet,
its location needs to be provided.
This can be done by setting the environment variable
`LIBTRBNET`.

libtrbnet.so in turn requires the environment variables
`DAQOPSERVER` (if talking to TrbNet via a trbnetd daemon)
or the IP of a TRB Board: `TRB3_SERVER` (if talking to
TrbNet directly).

A fourth environment variable `XMLDB` comes into play,
if the xmldb capabilities of this Python package are
to be used. It should point to the location of the
xml-db for your system.

Those environment variables can also be set from within
Python with their lowercase variants
`libtrbnet`, `daqopserver`, and `trb3_server` upon
instantiating the TrbNet() class.

Examples:


    # Using environment variables
    export LIBTRBNET=/local/gitrepos/trbnettools/trbnetd/libtrbnet.so
    export DAQOPSERVER=jspc55.x-matter.uni-frankfurt.de:1
    export XMLDB=~/phd/workrepos/daqtools/xml-db/database

    # example call to get the value in the compile time
    # register for all reachable TRBs:
    trbcmd.py xmlget 0xffff TrbNet CompileTime

    # Here, you could also run some Python code and
    # and instantiate TrbNet() without any keyword arguments.

or by setting the variables from within Python:

```python
import os
from trbnet import TrbNet

lib = '/local/gitrepos/trbnettools/trbnetd/libtrbnet.so'
host = 'trbnetd_host:8888'
t = TrbNet(libtrbnet=lib, daqopserver=host)
# 0x40 is the register address of CompileTime
t.register_read(0xffff, 0x40)
```

### Usage with Python

To read the content of the register address 0x0 for all
connected TrbNet boards (broadcast address 0xffff), do:

```python
import os
from trbnet import TrbNet

t = TrbNet()

response = t.register_read(0xffff, 0x0)
for endpoint in response:
    print("endpoint 0x{:08X} responded with: 0x{:08X}".format(endpoint, response[endpoint]))
```

The TrbNet() class has the following methods:

* `register_read(trb_address, reg_address)`
* `register_write(trb_address, reg_address, value)`
* `register_read_mem(trb_address, reg_address, option, size)`
* `read_uid(trb_address)`
* `trb_set_address(uid, endpoint, trb_address)`
* and some more less frequently used methods (found in the source code of [trbnet/core/lowlevel.py](trbnet/core/lowlevel.py)).

### Usage of the Terminal Utility trbcmd.py

The package comes with a simple command line utility called `trbcmd.py`.
It is a Python counterpart for the trbcmd utility provided
by trbnettools.

What it can do:

**read register values**

```
trbcmd.py r 0xffff 0x0
```

**read memory (subsequent register addresses)**

Read three registers starting at 0x8005 from all boards:
```
trbcmd.py rm 0xffff 0x8005 0x3 0x0
```

**xml-db queries**

Ask all TrbNet nodes (broadcast 0xffff) for the register value of CompileTime as set in TrbNet.xml:

```
trbcmd.py xmlget 0xffff TrbNet       CompileTime
```

### Resources

* [The TRB Website](http://trb.gsi.de)
* [TrbNet Manual](http://jspc29.x-matter.uni-frankfurt.de/docu/trbnetdocu.pdf)
