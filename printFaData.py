#!/usr/bin/env python3

import pygal

def print_fa_data(fa,name):
	x_time = []
	out_octets = []
	out_packets = []
	in_octets = []
	in_packets = []
	with open('static/'+name+fa+'.txt', 'r') as f:
	    for line in f.readlines():
	        # eval(line) lee cada linea como diccionario no como cadena
	        line = eval(line)
	        t = line['time']
	        x_time.append(t[-15:-5])
	        out_packets.append(float(line['fa_out_uPackets']))
	        out_octets.append(float(line['fa_out_oct']))
	        in_packets.append(float(line['fa_in_uPackets']))
	        in_octets.append(float(line['fa_in_oct']))

	line_chart = pygal.Line()
	line_chart.title = name +' '+fa
	line_chart.x_labels = x_time
	line_chart.add('Oct. salida', out_octets)
	line_chart.add('Paq. salida', out_packets)
	line_chart.add('Oct. entrada', in_octets)
	line_chart.add('Paq. entrada', in_packets)
	line_chart.render_to_png('static/'+name+fa+'img.png')



