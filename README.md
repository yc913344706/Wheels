# Wheels
自己造的轮子
# nginx
## 环境：Win 7 : Python 3.6.3
## NginxConfFormatter
### 作用
nginx配置文件格式化工具<br/>
功能 - `对nginx配置文件自动格式化`<br/>
~~由于添加的模块级别不同，形式不同，故不在编写增删改查功能，只提供格式化功能~~
### 注意
```
1. 对模块化到location/if/limit_except的配置文件，会报错
2. 对配置文件进行格式化时，不会删除掉文件中的注释！！！
3. 且在源位置有备份
```
### 使用举例
```Python
# 假设Wheels的本地位置为'E:\yc_study\github\Wheels'
import sys, json
sys.path.append(r'E:\yc_study\github\Wheels')
from nginx.NginxConfFormatter import NginxConfFormatter

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
```

# ansible_installer
## 环境：CentOS 7.3 : Bash
## 作用
ansible自动安装脚本 - shell脚本<br/>
需注意，如果本机python版本低于2.7，会自动安装2.7.10<br/>
另：master版本对应rhel系列el7版本，el6版本的下载el6分支即可<br/>
## 使用
```Bash
# 假设ansible_installer的位置为/data01/software/ansible_installer
cd /data01/software/ansible_installer
chmod +x ansible_installer.sh
sh ansible_installer.sh
```