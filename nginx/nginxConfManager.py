# -*- coding:utf-8 -*-
class NginxConfManager(object):
	'''
	nginx配置文件管理器<br>
	目标：提供界面化nginx配置文件任一配置项的新增、修改、删除功能<br>
	2017/12/16:文件内容解析功能（返回dict）<br>
	'''
	def __init__(self, nginx_conf_file):
		self.__file = nginx_conf_file
	
	def __analysis_str(self,str,result_dict=None,sub_type_id=None):
		'''
		递归获得nginx配置文件解析结果dict
		'''
		# 文件正确性检测
		import re
		invalid_item_pattern = re.compile(r'{[\s]*}')
		invalid_item_match = invalid_item_pattern.search(str)
		if invalid_item_match != None:
			raise ValueError("invalid conf item >>> "+invalid_item_match.group())
		
		# 初始化属性
		if result_dict == None:
			result_dict = {}
		
		str_content_list = str.split(';')
		
		sub_str_list = []
		other_str_list = []
		
		# 计算start_index
		start_index = -1
		sub_type_name = ""
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
					result_dict[line_content.split()[0].strip()] = line_content.split()[1]
				else:
					result_dict[line_content.split()[0].strip()] = ' '.join(line_content.split()[1:])
			else:
				# {行--start_index
				## sub_type_name
				start_index = index
				sub_type_name = line_content.split('{')[0].lstrip('}').strip()
				### sub_type_name可以细分...
				if sub_type_name == "server":
					server_name = ""
					index_get_server_name_index = start_index+1
					while len(server_name) == 0:
						list_get_server_name_tmp = str_content_list[index_get_server_name_index].split()
						if list_get_server_name_tmp[0] == "server_name":
							server_name = list_get_server_name_tmp[1]
						index_get_server_name_index += 1
					sub_type_name = "server "+ server_name
				break
		
		# 如果有子配置项
		if start_index != -1:
			# 计算end_index
			end_index = 0
			brackets_num = 1
			for index_cal_end_index in range(start_index, len(str_content_list)):
				if index_cal_end_index == start_index :
					if str_content_list[start_index].count('{') > 1:
						brackets_num += str_content_list[start_index].count('{') - 1
				else:
					## end_index行
					### --- '[}]+' 
					### --- '[}]+.+{.+'
					if '{' in str_content_list[index_cal_end_index]:
						brackets_num += str_content_list[index_cal_end_index].count('{')
					if '}' in str_content_list[index_cal_end_index]:
						brackets_num -= str_content_list[index_cal_end_index].count('}')
						if '{' in str_content_list[index_cal_end_index] and brackets_num == 1:
							end_index = index_cal_end_index
							break
						if ( not '{' in str_content_list[index_cal_end_index] ) and ( brackets_num == 0 ):
							end_index = index_cal_end_index
							break

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
			
			
			# 添加开发者用id--__sub_type_id
			## 子type的初始id=0
			if sub_type_id == None:
				sub_type_id = 0
				
			# 递归
			result_dict[sub_type_name] = self.__analysis_str(sub_str,sub_type_id=0)
			result_dict[sub_type_name]['__sub_type_id'] = sub_type_id
			self.__analysis_str(other_str, result_dict=result_dict,sub_type_id=sub_type_id+1)
		
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
	
	@property
	def conf_dict(self):
		return self.__analysis_file()
		