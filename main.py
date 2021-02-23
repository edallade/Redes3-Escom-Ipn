from flask import Flask, url_for, jsonify, request, render_template, redirect
from flask.ext.sqlalchemy import SQLAlchemy
import netifaces, os
import paramiko, time, sys,socket,threading
from graphviz import Graph
from getDataSNMP import get_system_info
from getDataFa import get_fa_data
from printFaData import print_fa_data
from printPackages import print_packages_out
from os import remove

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///DatabaseRed.db'
bd = SQLAlchemy(app)
gws = []
nodos= {}
layouts={}
FastEth={}
activas = {}
listaDisp = []
FaSNMP = {}

class dispositivo (bd.Model):
	__tablename__ = 'dispositivos'
	id_host = bd.Column(bd.String(20), primary_key=True)
	sysDescr = bd.Column(bd.String(150), unique=False)
	sysContact = bd.Column(bd.String(200), unique=False)
	sysName = bd.Column(bd.String(50), unique=False)
	sysLocation = bd.Column(bd.String(200), unique=False)

	def get_url(disp):
		return url_for('get_disp', id_host=disp.id_host, _external=True)

	def get_data(disp):
		return {
			'hostname' : disp.id_host,
			'Descripcion': disp.sysDescr,
			'Contacto': disp.sysContact,
			'Name' : disp.sysName,
			'Localizacion' : disp.sysLocation
		}
	def set_data(disp, data):
		try:
			disp.id_host= data['hostname']
			disp.sysDescr = data['sysDescr'] 
			disp.sysContact = data['sysContact']
			disp.sysName = data['sysName']
			disp.sysLocation = data['sysLocation']
		except KeyError as e:
			raise ValidationError('Dispositivo invalido: missing '+e.args[0] )
		return disp


def clear_buffer(connection,buffer):
		if connection.recv_ready():
			return connection.recv(buffer)
def send_message(user,password,direction,command):
	max_buffer= 65535
	connection = paramiko.SSHClient()
	connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	try:
		connection.connect(direction,username=user,password=password,timeout=5,look_for_keys=False,allow_agent=False)
		#print('conectando a :'+ direction)
	except:
		print('ERROR INTERNO :' , sys.exc_info())
	new_connection = connection.invoke_shell()
	output = clear_buffer(new_connection,max_buffer)
	new_connection.send(command)
	time.sleep(1)
	output = new_connection.recv(max_buffer)
	response = output.decode('utf-8')
	response = response.splitlines()
	output = clear_buffer(new_connection,max_buffer)
	connection.close()
	return response
def hilo_conexion(direction):
	max_buffer=65535
	username = 'cisco'
	password = 'cisco'
	c = 'show ip ospf neighbor\n'
	aux =  send_message(username,password,direction,c)
	prompt = aux[len(aux)-1][:-1]
	ks = nodos.keys()
	if prompt not in ks:
		nodos[prompt]=[]
		layouts[prompt]=[]
		FastEth[prompt]=[]
		activas[prompt]=[]
		
		for line in aux:
		#line example : 192.168.0.25      1   FULL/BDR        00:00:37    192.168.0.18    FastEthernet1/0
			if 'FULL' in line:
				ipNieg = line[50:62].strip()
				if ipNieg not in gws:
					gws.append(ipNieg)
		c = 'show ip route list 1\n'
		lista = send_message(username,password,direction,c)
		for linea in lista:
			if linea[0:1].find('C') != -1 and linea.find('Loopback0')==-1:
				red = linea.split(' ')
				if red[7] not in nodos[prompt]:
					nodos[prompt].append(red[7])
					FastEth[prompt].append(red[11]+' '+red[7])
		c = 'show running-config | include (interface|ip address)'+'\n'
		interfaces = send_message (username,password,direction,c)
		time.sleep(1)
		print('interfaces encontradas activas  :'+ str(interfaces))
		for inter in interfaces:
			
			try:
				#interface FastEthernet0/0
 					#ip address 192.168.0.1 255.255.255.252
				if 'interface' in inter:
					name = inter[inter.index('ace')+4:]
				else:
					if 'no' not in inter:
						ip = inter[inter.index('ss')+3:]
						
						layouts[prompt].append(name+' '+ip+' ')
			except:
				continue
def imagen(gateway):
	temporal = sorted(nodos.items())
	nodos.clear()
	for i in temporal:
		nodos[i[0]]=i[1]
	#layouts interfaces reportadas en tabla route
	temp2 = sorted(layouts.items())
	layouts.clear()
	for interfaz in temp2:
		layouts[interfaz[0]]=interfaz[1]
	
	#FastEth interfaces activas incompletas
	temp2 = sorted(FastEth.items())
	FastEth.clear()
	for fa in temp2:
		FastEth[fa[0]]=fa[1]
	#Activas interfaces activas completas
	name = layouts.keys()
	for uno in name:
		for i in FastEth[uno]:
			fa = i[:i.index(' ')]
			for r in layouts[uno]:
				if fa in r:
					i=i+r[r.index(' '):]
					activas[uno].append(i)#
	temp2 = sorted(activas.items())
	activas.clear()
	for fa in temp2:
		activas[fa[0]]=fa[1]
	
	dicredes={}
	cad = ''
	grafica=Graph('red')
	grafica.node('linux mint',shape='rectangle', label='MV'+'\n'+'192.168.0.2')
	grafica.node('switch', shape='rectangle')
	grafica.edge('linux mint','switch')
	for x in nodos:
	    aux4 = activas[x]
	    for y in aux4:
	    	cad = cad + y +'\n'
	    grafica.node(x, label=x+'\n'+cad, shape='rectangle')
	    cad=''
	    redes=nodos[x]
	    for red in redes:
	        if red not in dicredes.keys():
	            dicredes[red]=[]
	            dicredes[red].append(x)
	        else:
	            dicredes[red].append(x)
	for d in dicredes:
	    if d.find('0.0')>=0:
	        for each in dicredes[d]:
	            
	            grafica.edge('switch',each,label=d)
	    if len(dicredes[d]) == 2 and d.find('192')==0:   
	        grafica.edge(dicredes[d][0],dicredes[d][1],label=d)
	grafica.format = 'png'
	grafica.render('static/red')
def monitoreo_in_out_packs(dispositivo,data):
	#data example = fa0/0 192.168.0.1
	info = data.split(' ')
	faName = info[0].replace('/','_')
	get_fa_data(faName,info[1],dispositivo)
	print_fa_data(faName,dispositivo)
		
def getCommands(nameFile):
	with open(nameFile,'r') as f:
		commands = [line for line in f.readlines()]
	return commands
def send_configuration(user,password,direction,commands):
	max_buffer= 655350
	connection = paramiko.SSHClient()
	connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	try:
		#print('conectando a :'+ direction)
		connection.connect(str(direction),username=user,password=password,timeout=5,look_for_keys=False,allow_agent=False)
		
	except:
		print('ERROR INTERNO :' , sys.exc_info())
	new_connection = connection.invoke_shell()
	N= len(commands)-2
	for i in range(N):
		output = clear_buffer(new_connection,max_buffer)
		new_connection.send(commands[i])
		time.sleep(1)
	new_connection.send(commands[len(commands)-1])
	time.sleep(15)
	output = new_connection.recv(max_buffer)
	response = output.decode('utf-8')
	response = response.splitlines()
	connection.close()
	return response


@app.route('/', methods=['POST','GET'])
def GeneraTopologia():
	aux = netifaces.gateways()
	gw = aux['default'][netifaces.AF_INET]
	gws.append(str(gw[0]))
	for g in gws: 
		hilo = threading.Thread(target=hilo_conexion,
								args=(g,))
		hilo.start()
		time.sleep(2)
	#time.sleep(5)
	imagen(gw[0])

	return redirect('/Inicio')

@app.route('/Inicio',methods=['GET'])
def showHomePage():
	return render_template('inicio.html')

@app.route('/Dispositivos', methods=['GET','POST'])
def show_disp():
	cantDisp = dispositivo.query.all()
	if len(cantDisp) == 0:
		for index in range(8):
			if index != 5:
				sysData = get_system_info(gws[index])
				prompt = sysData['sysName'][:2]
				sysData['hostname'] = prompt
				d = dispositivo()
				registro = d.set_data(sysData)
				bd.session.add(registro)
				bd.session.commit()
		for key in activas:
			for fa in activas[key]:
				#fa = 'FastEthernet0/0 192.168.0.0 192.168.0.1 255.255.255.252 '
				line = fa.split(' ')
				index = line[0].find('/')
				if key not in FaSNMP:
					FaSNMP[key] = []
					FaSNMP[key].append('fa'+line[0][index-1:index+2]+' '+line[2])
				else:
					FaSNMP[key].append('fa'+line[0][index-1:index+2]+' '+line[2])
		for disp in FaSNMP:
			for interface in FaSNMP[disp]:
				monitoreo_in_out_packs(disp,interface)


	return jsonify({'Dispositivos' : [ dispositivo.get_url()
								for dispositivo in dispositivo.query.all()]})
@app.route('/Dispositivos/<id_host>',methods=['GET'])
def get_disp(id_host):
	host_data = dispositivo.query.get_or_404(id_host).get_data()
	return render_template(id_host+'.html', info=host_data)

@app.route('/consulta',methods=['POST'])
def consultarMib():
	host_name = request.form['hostname']
	
	interfaces = FaSNMP[host_name]
	for interface in interfaces:
		# example of interface = fa0/0 192.168.0.1
		fa = interface[:interface.find(' ')]
		fa = fa.replace('/','_')

		monitoreo_in_out_packs(host_name,interface)
	return redirect('/Dispositivos/'+host_name)
	#host_data = dispositivo.query.get_or_404(host_name).get_data()
	#return render_template(host_name+'.html', info=host_data)

@app.route('/Evalua',methods=['GET'])
def showMessagesPage():
	hostnames = FaSNMP.keys()
	return render_template('LostPackages.html', hosts=hostnames)


@app.route('/sendLongPING', methods=['POST'])
def getDataLongPING():
	pointA = request.form['optA']
	pointB = request.form['optB']
	addrOrigin = FaSNMP[pointA][0]
	addrDest = FaSNMP[pointB][0]

	addrOrigin = addrOrigin.split(' ')
	addrDest = addrDest.split(' ')
	
	commands = []
	aux = getCommands('PingCommands.txt')
	for c in aux:
		c = c.replace('destiny',addrDest[1])
		c = c.replace(' ','\n')
		c = c.replace('#','\n')
		commands.append(c)
	
	answer = send_configuration('cisco','cisco',addrOrigin[1],commands)
	commands.clear()
	#answer[len(answer)-2] = 'Success rate is 100 percent (100/100), round-trip min/avg/max = 8/30/64 ms'
	print('answer'+str(answer))
	percent = answer[len(answer)-2].split(' ')
	success = int(percent[3])
	lost = 100 - success
	name = pointA+'_to_'+pointB
	print_packages_out(success,lost,name)
	message = "Perdida excesiva de paqeutes" if lost>10 else "conectividad estable"
	#hacer css para ese html
	return render_template('resultPackagesSend.html',fileN = name, m = message)

@app.route('/EditName',methods=['GET'])
def showEditNamePage():
	hostnames = FaSNMP.keys();
	return render_template('EditName.html',names=hostnames)
####################revisar funcionalidad y conexion ssh que falla en editprocces
@app.route('/EditProcces',methods=['POST'])
def EditProccesFunc():
	oldHostName = request.form['oldHostName']
	newHostName = request.form['newHostName']
	#aux = fa0/0 192.168.0.6 , for example
	aux = FaSNMP[oldHostName]
	direction = aux[0]
	d=direction[direction.find(' ')+1:]
	commands = []
	temp = getCommands('newName.txt')
	for c in temp:
		c = c.replace('nombre',newHostName)
		commands.append(c)
	#cambiar nombre router via ssh
	answer = send_configuration('cisco','cisco',str(d),commands)
	#obtener registro base de datos y cambiar nombre para 
	#sobreescribirlo en la bd
	host_data = dispositivo.query.get_or_404(oldHostName).get_data()
	#cambiar nombre en el dic temporal

	host_data['hostname'] = newHostName
	salida = host_data['Name']
	host_data['Name'] = salida.replace(oldHostName,newHostName)
	#cambiar nombre en variable global FaSNMP usado en otras funciones 
	FaSNMP[newHostName] = FaSNMP.pop(oldHostName)
	#crerr registro rn bd
	#CAMBIAR NOMBRES DE LOS KEYS PARA REG EN BD
	host_data['sysDescr'] = host_data.pop('Descripcion')
	host_data['sysContact'] = host_data.pop('Contacto')
	host_data['sysName'] = host_data.pop('Name')
	host_data['sysLocation'] = host_data.pop('Localizacion')
	disp = dispositivo()
	registro = disp.set_data(host_data)
	bd.session.add(registro)
	bd.session.commit()
	#borrar registro con nombre antiguo
	Obj_to_del = dispositivo.query.filter_by(id_host=oldHostName).first_or_404()
	bd.session.delete(Obj_to_del)
	bd.session.commit()
	os.rename('templates/'+oldHostName+'.html','templates/'+newHostName+'.html')
	return redirect('/Dispositivos')




if __name__ == '__main__':
	bd.drop_all()
	time.sleep(1)
	bd.create_all()
	app.run(host='0.0.0.0', debug=True)