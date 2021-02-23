#!/usr/bin/env/python3

from pysnmp.entity.rfc3413.oneliner import cmdgen

def get_system_info(gateway):
    data = {}
    cmdGen = cmdgen.CommandGenerator()

    system_name =  '1.3.6.1.2.1.1.5.0'
    system_descr = '1.3.6.1.2.1.1.1.0'
    system_loc =   '1.3.6.1.2.1.1.6.0'
    system_contact='1.3.6.1.2.1.1.4.0'

    errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
        cmdgen.CommunityData('4CM1'),
        cmdgen.UdpTransportTarget((gateway, 161)),
        system_descr,
        system_contact,
        system_name,
        system_loc
    )

    # Revisamos errores e imprimimos la salida
    if errorIndication:
        print(errorIndication)
    else:
        if errorStatus:
            print('%s en %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex)-1] or '?'
                )
            )
        else:
            for name, val in varBinds:
                key = name.prettyPrint()
                key = key[key.find('::')+2:-2]
                data[key] = str(val)

    return data

