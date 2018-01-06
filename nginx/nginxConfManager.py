# -*- coding:utf-8 -*-
import logging
# 
# 默认情况下，logging将日志打印到屏幕，日志级别为WARNING；
# 日志级别大小关系为：CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
# logging.warning("des location already existed!!!")

class NginxConfManager(object):
	'''
	nginx配置文件管理器<br>
	目标 - 提供界面化nginx配置文件任一配置项的新增、修改、删除功能<br>
	2017/12/16 - 文件内容解析功能（返回dict）<br>
	2017/12/18 - 修正计算end_index时，如果结束行有多个{，则解析错误的情况；修正有多个同名配置项时，会被解析为一个的情况；修正无server_name时报错的情况<br>
	2018/01/07 - 增加添加location功能<br>
	'''
	def __init__(self, nginx_conf_file):
		self.__file = nginx_conf_file
	
	@property
	def conf_dict(self):
		'''
		属性 - 文件内容解析结果dict
		'''
		return self.__analysis_file()
	
	def format_file(self):
		'''
		方法 - 备份并格式化nginx文件
		'''
		self.__bakup_file()
		self.__format_file(self.conf_dict)
	
	def add_location(self, location_name, server_listen=None,server_name=None, **location_kw):
		'''
		方法 - 添加location  # 注：会备份并格式化nginx配置文件
		location_name - 要添加的location的名字。如"~ .*.(js|css)?$"、"/"
		server_listen - 该location要添加到的server的listen值，该nginx配置文件有多个server时与server_name必须选填
		server_name - 该location要添加到的server的server_name值，该nginx配置文件有多个server时与server_port必须选填
		**location_kw - 要添加的location的key-value值
		'''
		server_dict = self.__get_server_dict(server_listen,server_name)
		
		# 要添加的location已经存在
		des_key = "location {}".format(location_name)
		if des_key in server_dict:
			logging.warning('des location "{}" already existed!!!'.format(location_name))
			return
		# 添加key-value
		des_value = {}
		for i in location_kw:
			des_value[i] = location_kw[i]
		# 更新
		server_dict[des_key] = des_value
		# 写入
		conf_dict_tmp = self.conf_dict
		server_dicts_list = conf_dict_tmp['http']['server']
		# 一个server
		if isinstance(server_dicts_list, dict):
			conf_dict_tmp['http']['server'] = server_dict
		# 多个server
		else:
			for index in range(0, len(server_dicts_list)):
				server_dict_tmp = server_dicts_list[index]
				if ('__sub_type_id' in server_dict_tmp) and (server_dict_tmp['__sub_type_id'] == server_dict['__sub_type_id']):
					conf_dict_tmp['http']['server'][index] = server_dict
		self.__bakup_file()
		self.__format_file(conf_dict_tmp)
		
	def __analysis_str(self,des_str,result_dict=None):
		'''
		递归获得nginx配置文件解析结果dict
		'''
		# 文件正确性检测
		import re
		invalid_item_pattern = re.compile(r'{[\s]*}')
		invalid_item_match = invalid_item_pattern.search(des_str)
		if invalid_item_match != None:
			raise ValueError("invalid conf item >>> "+invalid_item_match.group())
		
		# 初始化属性
		if result_dict == None:
			result_dict = {}
		
		str_content_list = des_str.split(';')
		
		sub_str_list = []
		other_str_list = []
		
		# 计算start_index
		start_index = -1
		sub_type_name = ""
		if not 'single_conf_item' in result_dict:
			result_dict['single_conf_item'] = []
		for index in range(0, len(str_content_list)):
			line_content = str_content_list[index].strip()
			# 有效行判断
			if len(line_content) == 0:
				continue
			
			if not '{' in line_content:
				# 不包含{ 
				## 直接添加
				### --- key
				### --- key value
				### --- key value1 value2 ...
				item_num = len(line_content.split())
				if item_num == 1:
					result_dict['single_conf_item'].append(line_content)
				elif item_num == 2:
					# 如果该key出现多次，如server、allow，则把值存为数组
					if line_content.split()[0].strip() in result_dict:
						key_old = line_content.split()[0].strip()
						value_old = result_dict[key_old]
						if isinstance(value_old, list):
							value_old.append(line_content.split()[1])
						else:
							list_tmp = []
							list_tmp.append(value_old)
							list_tmp.append(line_content.split()[1])
							result_dict[key_old] = list_tmp
					else:
						result_dict[line_content.split()[0].strip()] = line_content.split()[1]
				else:
					# 如果该key出现多次，如server、allow，则把值存为数组
					if line_content.split()[0].strip() in result_dict:
						key_old = line_content.split()[0].strip()
						value_old = result_dict[key_old]
						if isinstance(value_old, list):
							value_old.append(' '.join(line_content.split()[1:]))
						else:
							list_tmp = []
							list_tmp.append(value_old)
							list_tmp.append(' '.join(line_content.split()[1:]))
							result_dict[key_old] = list_tmp
					else:
						result_dict[line_content.split()[0].strip()] = ' '.join(line_content.split()[1:])
			else:
				# {行--start_index
				## sub_type_name
				start_index = index
				sub_type_name = line_content.split('{')[0].lstrip('}').strip()
				### sub_type_name可以细分，以便区分，比如server...
				# server配置项以server-port为sub_type_name区分
				# if sub_type_name == "server":
					# server_port = ""
					# index_get_server_port_index = start_index
					# while len(server_port) == 0 and index_get_server_port_index < len(str_content_list):
						
						# list_get_server_port_tmp = str_content_list[index_get_server_port_index].split()
						
						# listen在第一行
						# if index_get_server_port_index == start_index:
							# if 'listen' in list_get_server_port_tmp[1]:
								# server_port = list_get_server_port_tmp[2]
						# else:
							# if list_get_server_port_tmp[0] == 'listen':
								# server_port = list_get_server_port_tmp[1]
						# index_get_server_port_index += 1
					# sub_type_name = 'server-'+server_port
				break
		
		# 如果有子配置项
		if start_index != -1:
			# 计算end_index
			end_index = 0
			start_brackets_num = 1
			end_brackets_num = 0
			for index_cal_end_index in range(start_index, len(str_content_list)):
				if index_cal_end_index == start_index :
					if str_content_list[start_index].count('{') > 1:
						start_brackets_num += str_content_list[start_index].count('{') - 1
				else:
					## end_index行
					### --- '[}]+' 
					### --- '[}]+.+{.+'
					if '}' in str_content_list[index_cal_end_index]:
						end_brackets_num += str_content_list[index_cal_end_index].count('}')
						if start_brackets_num == end_brackets_num:
							end_index = index_cal_end_index
							break
					if '{' in str_content_list[index_cal_end_index]:
						start_brackets_num += str_content_list[index_cal_end_index].count('{')

			# 计算sub_str_list
			## --- [0]: str_content_list[start_index]的第一个{之后的str(不包含{)
			## --- [-1]: str_content_list[end_index]的最后一个}之前的str(不包含})
			for index_get_sub_str_index in range(start_index,end_index+1):
				if index_get_sub_str_index == start_index:
					first_line_str = ""
					first_line_list = str_content_list[start_index].split('{')[1:]
					if len(first_line_list) > 1:
						first_line_str = '{'.join(first_line_list).strip()
					else:
						first_line_str = first_line_list[0].strip()
					sub_str_list.append(first_line_str)
					
				elif index_get_sub_str_index == end_index:
					last_line_str = ""
					last_line_list = str_content_list[index_get_sub_str_index].split('}')[:-1]
					if len(last_line_list) > 1:
						last_line_str = '}'.join(last_line_list).strip()
					else:
						last_line_str = last_line_list[0].strip()
					sub_str_list.append(last_line_str)
				else:
					sub_str_list.append(str_content_list[index_get_sub_str_index])
			
			# 如果有其他配置项
			if end_index < len(str_content_list)-1:
				# 计算other_str_list
				## --- [0]: str_content_list[end_index]的最后一个}之后的str(不包含})
				## --- [-1]: str_content_list[len(str_content_list)-1]
				for index_get_other_str_index in range(end_index,len(str_content_list)):
					if index_get_other_str_index == end_index:
						other_str_list.append(str_content_list[index_get_other_str_index].split('}')[-1].strip())
					else:
						other_str_list.append(str_content_list[index_get_other_str_index])
				
			# 最终得到的结果：sub_str,other_str
			sub_str = ';'.join(sub_str_list)
			other_str = ';'.join(other_str_list)
			
			# 递归
			# 如果该key出现多次，如server，则把值存为数组，并添加key - '__sub_type_id'
			new_result = self.__analysis_str(sub_str)
			if sub_type_name in result_dict:
				old_value = result_dict[sub_type_name]
				if isinstance(old_value, list):
					# 已经是数组，直接取出数组中最后一个'__sub_type_id'对应的值，加1运算后赋给新字典的'__sub_type_id'值，并把新字典添加进数组
					new_result['__sub_type_id'] = int(old_value[len(old_value)-1]['__sub_type_id'])+1
					old_value.append(new_result)
				else:
					# 还不是数组，要给上一个字典中添加'__sub_type_id' = 0，新字典添加'__sub_type_id' = 1，并将上一个字典和当前新字典添加进数组
					list_tmp = []
					old_value['__sub_type_id'] = 0
					new_result['__sub_type_id'] = 1
					list_tmp.append(old_value)
					list_tmp.append(new_result)
					result_dict[sub_type_name] = list_tmp
			else:
				result_dict[sub_type_name] = self.__analysis_str(sub_str)
			self.__analysis_str(other_str, result_dict=result_dict)
		if 'single_conf_item' in result_dict:
			if len(result_dict['single_conf_item']) == 0:
				result_dict.pop('single_conf_item')
		return result_dict
	
	def __analysis_file(self):
		'''
		解析nginx配置文件
		'''
		# import re
		# http_pattern = re.compile(r'http[\s]*{}')
		
		# 文件所有内容列表
		file_content_list = []
		
		# 把文件有效内容读取到文件所有内容列表中
		with open(self.__file, 'r', encoding='utf-8') as file_opened:
			for line_content in file_opened:
				if ( not line_content.startswith('#') ) and ( not len(line_content) == 0 ):
					file_content_list.append(line_content.split('#')[0].strip())
		
		return self.__analysis_str(''.join(file_content_list))
		
	def __bakup_file(self):
		'''
		备份文件
		'''
		import os, time, shutil
		# time.strftime("%Y-%m-%d-%H-%M-%S")
		des_F = os.path.join(os.path.dirname(self.__file),"{}.{}.bak".format(os.path.basename(self.__file), time.strftime("%Y_%m_%d_%H_%M")))
		try:
			shutil.copy(self.__file,des_F)
		except Exception as e:
			raise SystemError( "backup file error >>>\n{}".format(e) )
		
	def __format_file(self, des_dict):
		'''
		格式化nginx文件
		'''
		result_str = self.__get_formatter_str(des_dict)
		with open(self.__file, 'w') as formatter_F:
			formatter_F.write(result_str)
	
	def __get_formatter_str(self, des_dict, space_num=None):
		'''
		获取格式化的nginx字符串
		'''
		if space_num == None:
			space_num = 0
		else:
			space_num += 4
		result_str = ""
		# 写入result_str，\n在末尾
		for item in des_dict:
			# item是'__sub_type_id' - 忽略
			# item是'single_conf_item' - 添加
			if item == 'single_conf_item':
				for i in des_dict[item]:
					result_str = result_str + ' '*space_num + i + ';\n'
			# item是'log_format'
			if item == 'log_format':
				log_list = des_dict[item].split("''")
				result_str = result_str + ' '*space_num + "log_format {}'\n".format(log_list[0]) +"{}'".format(' '*space_num*2) + "'\n{}'".format(' '*space_num*2).join(log_list[1:]) + ';\n'
				continue
			# value是字符串 - 添加
			if isinstance(des_dict[item], str):
				result_str = result_str + ' '*space_num + '{} {}'.format(item, des_dict[item]) + ';\n'
			# value是列表
			if isinstance(des_dict[item], list):
				for i in des_dict[item]:
					## value中的每一项是字符串 - 添加
					if isinstance(i,str):
						result_str = result_str + ' '*space_num + '{} {}'.format(item, i) + ';\n'
					## value中的每一项是dict - 递归
					if isinstance(i,dict):
						# result_str = result_str + ' '*space_num  + self.__get_formatter_str(i, space_num) + ' '*space_num + '}\n'
						result_str = result_str + ' '*space_num + str(item) + '\n' + ' '*space_num + '{\n' + self.__get_formatter_str(i, space_num) + ' '*space_num + '}\n'
			# value是dict - 递归
			if isinstance(des_dict[item], dict):
				result_str = result_str + ' '*space_num + str(item) + '\n' + ' '*space_num + '{\n' + self.__get_formatter_str(des_dict[item], space_num) + ' '*space_num + '}\n'
		return result_str
		
	def __get_server_dict(self, server_listen=None, server_name=None):
		'''
		根据server_name和server_listen获得server的dict
		'''
		server_listen_need_be_judge = False if server_listen ==None else True
		server_name_need_be_judge = False if server_name ==None else True
		
		server_dicts_list = self.conf_dict['http']['server']
		if isinstance(server_dicts_list, dict):
			if server_listen_need_be_judge :
				if 'listen' not in server_dicts_list:
					logging.warning('param warning: des server no listen >{}'.format(server_listen))
				if 'ssl' in server_dicts_list['listen']:
					if '{} ssl'.format(server_listen) != server_dicts_list['listen']:
						logging.warning('param warning: you input listen is "{}",but the server listen is  "{}"'.format(server_listen,server_dicts_list['listen'][:-4]))
				elif 'SSL' in server_dicts_list['listen']:
					if '{} SSL'.format(server_listen) != server_dicts_list['listen']:
						logging.warning('param warning: you input listen is "{}",but the server listen is  "{}"'.format(server_listen,server_dicts_list['listen'][:-4]))
				else:
					if str(server_listen) != server_dicts_list['listen']:
						logging.warning('param warning: you input listen is "{}",but the server listen is  "{}"'.format(server_listen,server_dicts_list['listen']))
			return server_dicts_list
		
		# 如果没有传入server_listen或server_name并且http - server是列表，则报错
		if server_listen==None and server_name == None and isinstance(server_dicts_list,list):
			raise ValueError("params error, there are many server but no server name or server listen!!!\nyou need add sever name param or server listen param")
		
		# 只有1个server
		if (not server_listen_need_be_judge) and (not server_name_need_be_judge):
			return server_dicts_list
		# 多个server
		server_dict = {}
		for server_dict_tmp in server_dicts_list:
			server_listen_condition = False
			server_name_condition = False
			if 'listen' in server_dict_tmp and server_listen_need_be_judge:
				if str(server_listen) in server_dict_tmp['listen']:
					if 'ssl' in server_dict_tmp['listen']:
						if '{} ssl'.format(server_listen) == server_dict_tmp['listen']:
							server_listen_condition = True
					elif 'SSL' in server_dict_tmp['listen']:
						if '{} SSL'.format(server_listen) == server_dict_tmp['listen']:
							server_listen_condition = True
					else:
						if str(server_listen) == server_dict_tmp['listen']:
							server_listen_condition = True
			
			if 'server_name' in server_dict_tmp and server_name_need_be_judge:
				if server_name == server_dict_tmp['server_name']:
					server_name_condition = True
			# listen	true	true	false
			# name		true	false	true
			# 只指定了server listen
			if not server_name_need_be_judge:
				if server_listen_condition:
					if len(server_dict) != 0:
						raise ValueError("params error, there are many serve with the specified server listen!!!\nyou need add sever name param")
					server_dict = server_dict_tmp
			# 只指定了server name
			elif not server_listen_need_be_judge:
				if server_name_condition:
					if len(server_dict) != 0:
						raise ValueError("params error, there are many serve with the specified server name!!!\nyou need add sever listen param")
					server_dict = server_dict_tmp
			# server listen 和server name 同时指定
			else:
				if server_listen_condition and server_name_condition:
					if len(server_dict) != 0:
						raise ValueError("params error, there are many serve with the specified server name and server listen!!!\nyou need check your nginx conf file")
					server_dict = server_dict_tmp
		
		# 只指定了server listen
		if not server_name_need_be_judge:
			if len(server_dict) == 0:
				raise ValueError("params error, there are no serve with the specified server listen!!!")
		# 只指定了server name
		elif not server_listen_need_be_judge:
			if len(server_dict) == 0:
				raise ValueError("params error, there are no serve with the specified server name!!!")
		# server listen 和server name 同时指定
		else:
			if len(server_dict) == 0:
				raise ValueError("params error, there are no serve with the specified server listen and server name!!!")
		return server_dict
	
	