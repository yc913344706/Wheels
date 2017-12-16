# Wheels
自己造的轮子
# nginx
## nginxConfManager
### 作用
nginx配置文件管理器<br>
目标：提供界面化nginx配置文件任一配置项的新增、修改、删除功能<br>
2017/12/16:文件内容解析功能（返回dict）<br>
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