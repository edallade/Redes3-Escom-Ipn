#!/usr/bin/python3
from pysnmp.entity.rfc3413.oneliner import cmdgen
import datetime

cmdGen = cmdgen.CommandGenerator()
community = '4CM1'
result = {}
OIDS = {
'interface_name' :'1.3.6.1.2.1.2.2.1.2.',
'fa_in_oct' : '1.3.6.1.2.1.2.2.1.10.',
'fa_in_uPackets' :'1.3.6.1.2.1.2.2.1.11.',
'fa_out_oct' :'1.3.6.1.2.1.2.2.1.16.',
'fa_out_uPackets': '1.3.6.1.2.1.2.2.1.17.'
}
transFa = {'fa0_0':'1','fa1_0':'2','fa1_1':'3'}
def get_fa_data(fa,host,name):
    for oid in OIDS:
        oid_out = OIDS[oid]+transFa[fa]
        result[oid]= snmp_query(host,community,oid_out)
    result['time']= datetime.datetime.utcnow().isoformat()
    with open('static/'+name+fa+'.txt', 'a') as f:
        f.write(str(result))
        f.write('\n')

def snmp_query(host, community, oid):
    errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
        cmdgen.CommunityData(community),
        cmdgen.UdpTransportTarget((host, 161)),
        oid
    )
    
    # Revisamos errores e imprimimos resultados
    if errorIndication:
        print(errorIndication)
    else:
        if errorStatus:
            print('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex)-1] or '?'
                )
            )
        else:
            for name, val in varBinds:
                return(str(val))



