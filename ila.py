#!/usr/bin/env python3
import usb
from luna.gateware.usb.devices.ila import USBIntegratedLogicAnalyzerFrontend
from luna.gateware.debug.ila       import ILACoreParameters


dev=usb.core.find(idVendor=0x1209, idProduct=0xDECA)
print(dev)

frontend = USBIntegratedLogicAnalyzerFrontend(ila=ILACoreParameters.unpickle(), idVendor=0x1209, idProduct=0xDECA, endpoint_no=3)
frontend.interactive_display()