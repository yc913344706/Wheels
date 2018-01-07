# Wheels
自己造的轮子
# nginx
## nginxConfManager
### 作用
nginx配置文件管理器<br/>
目标 -- 提供界面化nginx配置文件任一配置项的新增、修改、删除功能<br/>
2017/12/16 - 文件内容解析功能（返回dict）<br/>
2017/12/18 - 修正计算end_index时，如果结束行有多个{，则解析错误的情况；修正有多个同名配置项时，会被解析为一个的情况；修正无server_name时报错的情况<br/>
2018/01/07 - 增加格式化文件功能（format_file()）、添加location功能（add_location()） - 会备份并改变原本配置文件<br/>
### 使用举例
<pre>
# 假设Wheels的本地位置为'E:\yc_study\github\Wheels'
import sys
sys.path.append(r'E:\yc_study\github\Wheels')
from nginx.nginxConfManager import NginxConfManager
import json

def dict_printer(dict):
	print( json.dumps(dict,indent=4))

if __name__ == "__main__":
	nginx_conf_file = r'E:\yc_study\github\Wheels\nginx\nginx_demo.conf'
	nginx_conf_manager = NginxConfManager(nginx_conf_file)
	# 获取配置字典 - OK
	# dict_printer(nginx_conf_manager.conf_dict)
	# 格式化配置文件 - OK
	# nginx_conf_manager.format_file()
	
	# 查找存在的location - OK
	# dict_printer( nginx_conf_manager.query_location('/',server_listen=80))
	# 查找不存在的location - OK
	# dict_printer( nginx_conf_manager.query_location('^~ /isup-service-app/',server_listen=80))
	
	# 添加location - OK
	# nginx_conf_manager.add_location('^~ /isup-service-app/',server_listen=80, proxy_pass="http://127.0.0.1:88/isup-service-app/")
	# 添加已经存在的location - OK
	# nginx_conf_manager.add_location('^~ /isup-service-app/',server_listen=80, proxy_set_header="Host $host")

	
	# 删除location - OK
	# nginx_conf_manager.delete_location('^~ /isup-service-app/',server_listen=80)
	# 删除不存在的location - OK
	# nginx_conf_manager.delete_location('^~ /isup-service-basic/',server_listen=80)
	# 对已存在的location删除item - OK
	# nginx_conf_manager.delete_location('^~ /isup-service-app/',server_listen=80, location_key = "proxy_set_header")
	# nginx_conf_manager.delete_location('/',server_listen=80, location_key = ["proxy_intercept_errors", "proxy_connect_timeout"])
	
	# 修改存在的location - OK
	# nginx_conf_manager.update_location('/',server_listen=80, proxy_redirect="on")
	# nginx_conf_manager.update_location('~ .(jsp|jspx|do)?$',server_listen=80, proxy_set_header=["Host $host","X-Real-IP $remote_addr"])
	# 修改不存在的location - OK
	# nginx_conf_manager.update_location('^~ /isup-service-basic/',server_listen=80, proxy_set_header="Host $host")
</pre>
# ansible_installer
## 作用
ansible自动安装脚本 - shell<br/>
需注意，如果本机python版本低于2.7，会自动安装2.7.10<br/>
另：master版本对应rhel系列el7版本，el6版本的下载el6分支即可<br/>
## 使用
<pre>
# 假设ansible_installer的位置为/data01/software/ansible_installer
cd /data01/software/ansible_installer
chmod +x ansible_installer.sh
sh ansible_installer.sh
</pre>