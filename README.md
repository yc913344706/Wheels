# Wheels
自己造的轮子
# nginx
## 环境：python 3.6.3
## nginxConfManager
### 作用
nginx配置文件管理器<br/>
目标 - 提供界面化nginx配置文件任一配置项的新增、修改、删除功能<br/>
当前功能 - 对nginx配置文件自动格式化 - 2018/04/22
### 注意
```
对模块化到location/if/limit_except的配置文件，会报错
对配置文件进行格式化或增删改查时，__不会删除掉文件中的注释！！！__
且在源位置有备份 :blush:
```
### 使用举例
```Python
# 假设Wheels的本地位置为'E:\yc_study\github\Wheels'
import sys, json
sys.path.append(r'E:\yc_study\github\Wheels')
from nginx.nginxConfManager import NginxConfManager

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
```

# ansible_installer
## 环境：CentOS 7.3 :bash
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