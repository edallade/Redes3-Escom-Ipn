import pygal

def print_packages_out(success,lost,name):
	pie_chart = pygal.Pie()
	pie_chart.title = name
	pie_chart.add('success '+str(success)+'%',float(success))
	pie_chart.add('lost '+str(lost)+'%',float(lost))
	pie_chart.render_to_png('static/'+name+'.png')








