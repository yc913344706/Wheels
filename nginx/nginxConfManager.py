# -*- coding:utf-8 -*-
class NginxConfManager(object):
	'''
	nginx配置文件管理器<br>
	目标 - 提供界面化nginx配置文件任一配置项的新增、修改、删除功能<br>
	2017/12/16 - 文件内容解析功能（返回dict）<br>
	2017/12/18 - 修正计算end_index时，如果结束行有多个{，则解析错误的情况；修正有多个同名配置项时，会被解析为一个的情况；修正无server_name时报错的情况<br>
	'''
	def __init__(self, nginx_conf_file):
		self.__file = nginx_conf_file
	
	@property
	def conf_dict(self):
		'''
		属性 - 文件内容解析结果dict
		'''
		return self.__analysis_file()
	
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