#!/usr/bin/env python3


import re

from bottle import get, post, request, run, SimpleTemplate, static_file
from os import kill, listdir
from psutil import process_iter
from signal import SIGKILL 
from subprocess import Popen


photo_dir = '/home/pi/Photos'


base = '''
<html>
	<head>
		<style>
			body{{
				font-size: 5vh;
			}}
			input[type="submit"]{{
				font-size: 300%;
				width: 90%;
				height: 35%;
			}} 
			input[type="number"]{{
				font-size:100%;
				width: 20%;
			}}
			img{{
				width: 90%;
			}}
		</style>
	</head>
	<body>
		{body}
	</body>
</html>
'''


start = '''
	<br />
	<form action="/" method="post">
		<input name="action" value="Start" type="submit" /><br /><br />
			<input name="interval" type="number" /> &mdash; interval<br /><br />
			<input name="frames" type="number" /> &mdash; number of frames<br /><br />
	</form>
'''

stop = '''
	<br />
	<form action="/" method="post">
		<input name="action" value="Stop" type="submit" /><br />
	</form>

	<br /><div id="lastphoto"></div>

	<script>
		var last = ""
		setInterval( function(){
			var r = new XMLHttpRequest();
			r.open( "GET", "/lastphoto/?last="+last, false );
			r.send( null );
			if ( r.status == 200 ){
				if ( ! /^$/.test(r.responseText) ){
					last = r.responseText;
					// document.write("<br /><img src='/Photos/"+last+".jpg' />");
					document.getElementById("lastphoto").innerHTML = "<br /><img src='/Photos/" + last + ".jpg' /><br />" + document.getElementById("lastphoto").innerHTML;
				}
			}
		}, 250);
	</script>
'''


def find_process():
	for p in process_iter():
		for cmd in p.cmdline():
			if re.search('gphoto2', cmd):
				return p
	return None


@get('/')
def index_get():
	if find_process():
		return base.format( body = stop ) 
	else:
		return base.format( body = start )


@post('/')
def index_post():
	action = request.forms.get('action')
	if action == 'Stop':
		p = find_process()
		if p:
			kill(p.pid, SIGKILL)	
	if action == 'Start':
		interval = request.forms.get('interval') or 4
		frames = request.forms.get('frames') or 0
		Popen( ['gphoto2', '--set-config', '/main/capturesettings/imagequality=4', '--capture-image-and-download', '--filename', '{}/%Y%m%d%H%M%S.%C'.format(photo_dir), '-I{}'.format(interval), '-F{}'.format(frames) ] )

	return ( index_get() )


@get('/lastphoto/')
def lastphoto_get():
	last = request.query.last or ''
	files = listdir(photo_dir)
	files.sort(reverse=True)
	for f in files:
		rem = re.match("^(.+)\.jpg$", f)
		if rem:
			fileroot = rem.group(1)
			if ( fileroot != last ):
				return (fileroot)
			else:
				break
	return ('')


@post('/timelapse/')
def timelapse_post():
	interval = request.forms.get('interval') or 4
	frames = request.forms.get('frames') or 0
	Popen( ['gphoto2', '--set-config', '/main/capturesettings/imagequality=4', '--capture-image-and-download', '--filename', '{}/%Y%m%d%H%M%S.%C'.format(photo_dir), '-I{}'.format(interval), '-F{}'.format(frames) ] )
	return ( timelapse_get() )


@get('/Photos/<filename>')
def Photos(filename):
	return ( static_file(filename, root=photo_dir) )


## ## ## ## ##


run(host='0.0.0.0', port=8080, debug=True)
