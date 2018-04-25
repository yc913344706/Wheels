import json

from nginxConfFormatter import NginxConfFormatter

def main():
	conf_file_formatter=NginxConfFormatter(r'E:\yc_study\github\Wheels\nginx\default.conf')
	try:
		# 格式化输出解析字典
		print(json.dumps(conf_file_formatter.dict,indent=4))
		# 格式化文件
		conf_file_formatter.format_file()
	except Exception as e:
		print('++++++++++++++++++',e.message)

main()