import json

from nginxConfManager import NginxConfManager

def main():
	a=NginxConfManager('nginx_demo.conf')
	try:
		print(json.dumps(a.dict,indent=4))
	except Exception as e:
		print('+++++++++++++++++=',e.message)

main()