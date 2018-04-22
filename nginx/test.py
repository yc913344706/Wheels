import json

from nginxConfManager import NginxConfManager

def main():
	conf_file=NginxConfManager(r'E:\yc_study\github\Wheels\nginx\nginx_demo.conf')
	try:
		# 格式化输出解析字典
		print(json.dumps(conf_file.dict,indent=4))
		# 格式化文件
		conf_file.format_file()
	except Exception as e:
		print('++++++++++++++++++',e.message)

main()