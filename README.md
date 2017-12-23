# Wheels
自己造的轮子
# nginx
## nginxConfManager
### 作用
nginx配置文件管理器<br>
目标 -- 提供界面化nginx配置文件任一配置项的新增、修改、删除功能<br>
2017/12/16 -- 文件内容解析功能（返回dict）<br>
2017/12/18 - 修正计算end_index时，如果结束行有多个{，则解析错误的情况；修正有多个同名配置项时，会被解析为一个的情况；修正无server_name时报错的情况<br>
### 使用举例
<pre>
# 假设Wheels的本地位置为'D:\Wheels'
import sys
sys.path.append(r'D:\Wheels')
from nginx.nginxConfManager import NginxConfManager
import json

def dict_printer(dict):
	print( json.dumps(dict,indent=4))

if __name__ == "__main__":
	nginx_conf_file = r'D:\nginx\nginx.conf'
	nginx_conf_manager = NginxConfManager(nginx_conf_file)
	dict_printer(nginx_conf_manager.conf_dict)
</pre>
# ansible_installer
## 作用
ansible自动安装脚本 - shell
需注意，如果本机python版本低于2.7，会自动安装2.7.10
另：master版本对应rhel系列el7版本，el6版本的下载el6分支即可
## 使用
<pre>
# 假设ansible_installer的位置为/data01/software/ansible_installer
cd /data01/software/ansible_installer
chmod +x ansible_installer.sh
sh ansible_installer.sh
</pre>