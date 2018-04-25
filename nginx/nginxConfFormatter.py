# -*- coding:utf-8 -*-
import logging

'''
配置文件
	nginx配置文件主要分为全局块、events块、http块 - 3
	http块中分为http全局块、server块、upstream块 - 2
	server块中分为server全局块、location块、if块 - 1
	location块中又分为location全局块、if块、limit_except块 - 0
思路
	将配置文件以字典形式存于内存，以对字典的增删改查，实现对配置文件的增删改查
	由于添加的模块级别不同，形式不同，故不在编写增删改查功能，只提供格式化功能
问题
	1.注释问题
		由于为字典形式，所以每个key录入value时，检测上一行即上2/3/4...行是否是注释，是，则该key对应的value为元组("value",["comment1","comment",...])，不是，则为str
	1.1注释问题新解决办法
		{
			key:{
				"value":"",
				"id":1,
				"backend_comment":""
				"before_comments":[]
			}
		}
		全局再加一个"last_comment"属性
	2.模块化配置文件问题
		定义解析单元方法，返回
		{
			"globals":["key1":"value1","key2":("value2","comment2"),...],
			"blocks":[
				{
					"block_type":"",
					"block_content_list":[],
					"block_comment":["comment1","comment2"...]
				},
				...
			]
		}
	2.1.不同程度模块化
		根据解析出来的配置文件中的模块配置层级，决定可使用的方法
		"http"、"events" > "server"、"upstream" > "location" > "if"、"limit_except"
		3 > 2 > 1 > 0
		# {"events", "http", "upstream", "server"} - 继续
		# { "if", "limit_except", "location"} - 报错
	3.尾行注释问题
		添加"last_comment"属性
'''

class NginxConfFormatter(object):
	'''
	nginx配置文件管理器<br/>
	目标 - 提供界面化nginx配置文件任一配置项的新增、修改、删除功能<br/>
	2017/12/16 - 文件内容解析功能（返回dict）<br/>
	2017/12/18 - 修正计算end_index时，如果结束行有多个{，则解析错误的情况；修正有多个同名配置项时，会被解析为一个的情况；修正无server_name时报错的情况<br/>
	2018/01/07 - 增加 http> server> location 的增删改查功能<br/>
	2018/01/08 - 增加格式化时候的排序<br/>
	'''
	
	################################ 类属性 start ################################
	
	TIPS_DICT = {
		"FILE_MODULATE_ERROR":"FAILED >>> You took your config file too small to analyze !!!",
		"FILE_MODULATE_WARNING":"WARNING >>> You took your config file a little small to analyze !!!",
		
		"LIMIT_EXCEPT_MODULE_ANALYSIS_WARNING":"WARNING >>> Analysis limit_except module warning !!!",
		"IF_MODULE_ANALYSIS_WARNING":"WARNING >>> Analysis if module warning !!!",
		"LOCATION_MODULE_ANALYSIS_WARNING":"WARNING >>> Analysis location module warning !!!",
		"SERVER_MODULE_ANALYSIS_WARNING":"WARNING >>> Analysis server module warning !!!",
		"UPSTREAM_MODULE_ANALYSIS_WARNING":"WARNING >>> Analysis upstream module warning !!!",
		"HTTP_MODULE_ANALYSIS_WARNING":"WARNING >>> Analysis http module warning !!!",
		"EVENTS_MODULE_ANALYSIS_WARNING":"WARNING >>> Analysis events module warning !!!",
	}
	
	# block等级字典
	MODULATE_LEVEL_DICT = {
		"http" : 3,
		"events" : 3,
		"server" : 2,
		"upstream" : 2,
		"location" : 1,
		"if" : 0,
		"limit_except" : 0,
	}
	
	################################ 类属性 start ################################
	
	################################ 内部方法 start ################################
	
	# 解析 events 块 -> events 解析结果字典
	def __analysis_events_list(self, events_list, event_comment, event_block_prefix):
		# {
			# "comments":[],
			# "globals":{},
			# "last_comment":last_comment,
		# }
		print('start analyze events', event_block_prefix)
		# print('events_list', '>>>\n', events_list)
		# print('event_comment', '>>>\n', event_comment)
		# print('event_block_prefix', '>>>\n', event_block_prefix)
		
		globals, blocks, last_comment = self.__analysis_unit(events_list)
		if event_block_prefix.strip().lower() != "events":
			raise YcException(NginxConfFormatter.TIPS_DICT["EVENTS_MODULE_ANALYSIS_WARNING"] + '\n>>> events prefix error!!!\n>>>' + event_block_prefix)
		
		if blocks != None:
			raise YcException(NginxConfFormatter.TIPS_DICT["EVENTS_MODULE_ANALYSIS_WARNING"] + '\n>>> events have sub blocks !!!\n>>>' + blocks)
		
		print('finish analyze events')
		return {
			"comments":event_comment,
			"globals":globals,
			"last_comment":last_comment,
		}
	
	# 解析 http 块 -> http 解析结果字典
	def __analysis_http_list(self, http_list, http_comment, http_block_prefix):
		# {
			# "comments":[],
			# "globals":{},
			# "upstreams":[],
			# "servers":[],
			# "last_comment":last_comment,
		# }
		print('start analyze http', http_block_prefix)
		# print('http_list', '>>>\n', http_list)
		# print('http_comment', '>>>\n', http_comment)
		# print('http_block_prefix', '>>>\n', http_block_prefix)
		
		globals, blocks, last_comment = self.__analysis_unit(http_list)
		# print('======',blocks)
		if http_block_prefix.strip().lower() != "http":
			raise YcException(NginxConfFormatter.TIPS_DICT["HTTP_MODULE_ANALYSIS_WARNING"] + '\n>>> http prefix error!!!\n>>>'+ http_block_prefix)
		upstreams = None
		servers = None
		if blocks != None:
			for block in blocks:
				# print('===========', block["block_type"])
				if ( not block["block_type"].strip().lower().startswith("upstream ") ) and ( block["block_type"] != "server" ):
					raise YcException(NginxConfFormatter.TIPS_DICT["HTTP_MODULE_ANALYSIS_WARNING"] + '\n>>> http\' subblock is\'t upstream or server !!!\n>>>' +block["block_type"])
				if block["block_type"].strip().lower().startswith("upstream "):
					if upstreams == None:
						upstreams = []
					upstreams.append((block["id"], self.__analysis_upstream_list(block["block_content_list"], block["block_comment"], block["block_type"])))
				if block["block_type"] == "server":
					if servers == None:
						servers = []
					servers.append((block["id"], self.__analysis_server_list(block["block_content_list"], block["block_comment"], block["block_type"])))
					
		print('finish analyze http')
		return {
			"comments":http_comment,
			"globals":globals,
			"upstreams":upstreams,
			"servers":servers,
			"last_comment":last_comment,
		}
	
	# 解析 upstream 块 -> upstream 解析结果字典
	def __analysis_upstream_list(self, upstream_list, upstream_comment, upstream_block_prefix):
		# {
			# "comments":[],
			# "name":"",
			# "globals":{},
			# "last_comment":last_comment,
		# }
		print('start analyze upstream', upstream_block_prefix)
		# print('upstream_list', '>>>\n', upstream_list)
		# print('upstream_comment', '>>>\n', upstream_comment)
		# print('upstream_block_prefix', '>>>\n', upstream_block_prefix)
		
		globals, blocks, last_comment = self.__analysis_unit(upstream_list)
		if not upstream_block_prefix.strip().lower().startswith("upstream "):
			raise YcException(NginxConfFormatter.TIPS_DICT["UPSTREAM_MODULE_ANALYSIS_WARNING"] + '\n>>> upstream prefix error!!!\n>>>' + upstream_block_prefix)
		
		if blocks != None:
			raise YcException(NginxConfFormatter.TIPS_DICT["UPSTREAM_MODULE_ANALYSIS_WARNING"] + '\n>>> upstream have sub blocks !!!\n>>>' + blocks)
		
		print('finish analyze upstream')
		return {
			"comments":upstream_comment,
			"name":upstream_block_prefix[9:].strip(),
			"globals":globals,
			"last_comment":last_comment,
		}
	
	# 解析 server 块 -> server 解析结果字典
	def __analysis_server_list(self, server_list, server_comment, server_block_prefix):
		# {
			# "comments":[],
			# "globals":{"listen":"listen_content", "server_name":"server_name_content",...},
			# "ifs":[],
			# "locations":[],
			# "last_comment":last_comment,
		# }
		print('start analyze server', server_block_prefix)
		# print('server_list', '>>>\n', server_list)
		# print('server_comment', '>>>\n', server_comment)
		# print('server_block_prefix', '>>>\n', server_block_prefix)
		
		globals, blocks, last_comment = self.__analysis_unit(server_list)
		if server_block_prefix.strip().lower() != "server":
			raise YcException(NginxConfFormatter.TIPS_DICT["SERVER_MODULE_ANALYSIS_WARNING"] + '\n>>> server prefix error!!!\n>>>' + server_block_prefix)
		ifs = None
		locations = None
		if blocks != None:
			for block in blocks:
				if ( not block["block_type"].strip().lower().startswith("if ") ) and ( not block["block_type"].startswith("location ") ):
					raise YcException(NginxConfFormatter.TIPS_DICT["SERVER_MODULE_ANALYSIS_WARNING"] + '\n>>> server\' subblock is\'t if or location !!!\n>>>' + block["block_type"])
				if block["block_type"].strip().lower().startswith("if "):
					if ifs == None:
						ifs = []
					ifs.append((block["id"], self.__analysis_if_list(block["block_content_list"], block["block_comment"], block["block_type"])))
				if block["block_type"].strip().lower().startswith("location "):
					if locations == None:
						locations = []
					locations.append((block["id"], self.__analysis_location_list(block["block_content_list"], block["block_comment"], block["block_type"])))
		
		print('finish analyze server')
		return {
			"comments":server_comment,
			"globals":globals,
			"ifs":ifs,
			"locations":locations,
			"last_comment":last_comment,
		}
	
	# 解析 location 块 -> location 解析结果字典
	def __analysis_location_list(self, location_list, location_comment, location_block_prefix):
		# {
			# "comments":[],
			# "name":"",
			# "globals":{},
			# "ifs":[],
			# "limit_excepts":[],
			# "last_comment":last_comment,
		# }
		print('start analyze location', location_block_prefix)
		# print('location_list', '>>>\n', location_list)
		# print('location_comment', '>>>\n', location_comment)
		# print('location_block_prefix', '>>>\n', location_block_prefix)
		
		globals, blocks, last_comment = self.__analysis_unit(location_list)
		if not location_block_prefix.strip().lower().startswith("location "):
			raise YcException(NginxConfFormatter.TIPS_DICT["LOCATION_MODULE_ANALYSIS_WARNING"] + '\n>>> location prefix error!!!\n>>>'+ location_block_prefix)
		ifs = None
		limit_excepts = None
		if blocks != None:
			for block in blocks:
				# if not block["block_type"].strip().lower().startswith("if "):
				if ( not block["block_type"].strip().lower().startswith("if ") ) and ( not block["block_type"].startswith("limit_except ") ):
					raise YcException(NginxConfFormatter.TIPS_DICT["LOCATION_MODULE_ANALYSIS_WARNING"] + '\n>>> location\' subblock is\'t if or limit_except!!!\n>>>' + block["block_type"])
				# ifs.append({block["id"]:self.__analysis_if_list(block["block_content_list"], block["block_comment"], block["block_type"])})
				if block["block_type"].strip().lower().startswith("if "):
					if ifs == None:
						ifs = []
					ifs.append((block["id"], self.__analysis_if_list(block["block_content_list"], block["block_comment"], block["block_type"])))
				if block["block_type"].strip().lower().startswith("limit_except "):
					if limit_excepts == None:
						limit_excepts = []
					limit_excepts.append((block["id"], self.__analysis_limit_except_list(block["block_content_list"], block["block_comment"], block["block_type"])))
		
		print('finish analyze location')
		return {
			"comments":location_comment,
			"name":location_block_prefix[9:].strip(),
			"globals":globals,
			"ifs":ifs,
			"limit_excepts":limit_excepts,
			"last_comment":last_comment,
		}
	
	# 解析 if 块 -> if 解析结果字典
	def __analysis_if_list(self, if_list, if_comment, if_block_prefix):
		# {
			# "comments":[],
			# "condition":"",
			# "globals":{},
			# "last_comment":last_comment,
		# }
		print('start analyze if', if_block_prefix)
		# print('if_list', '>>>\n', if_list)
		# print('if_comment', '>>>\n', if_comment)
		# print('if_block_prefix', '>>>\n', if_block_prefix)
		
		globals, blocks, last_comment = self.__analysis_unit(if_list)
		if not if_block_prefix.strip().lower().startswith("if "):
			raise YcException(NginxConfFormatter.TIPS_DICT["IF_MODULE_ANALYSIS_WARNING"] + '\n>>> if prefix error!!!\n>>>' + if_block_prefix)
		
		if blocks != None:
			raise YcException(NginxConfFormatter.TIPS_DICT["IF_MODULE_ANALYSIS_WARNING"] + '\n>>> if have sub blocks !!!\n>>>' + blocks)
		
		print('finish analyze if')
		return {
			"comments":if_comment,
			"condition":if_block_prefix[3:].strip(),
			"globals":globals,
			"last_comment":last_comment,
		}
	
	# 解析 limit_except 块 -> limit_except 解析结果字典
	def __analysis_limit_except_list(self, limit_except_list, limit_except_comment, limit_except_block_prefix):
		# {
			# "comments":[],
			# "condition":"",
			# "globals":{},
			# "last_comment":last_comment,
		# }
		print('start analyze limit_except', limit_except_block_prefix)
		# print('limit_except_list', '>>>\n', limit_except_list)
		# print('limit_except_comment', '>>>\n', limit_except_comment)
		# print('limit_except_block_prefix', '>>>\n', limit_except_block_prefix)
		
		globals, blocks, last_comment = self.__analysis_unit(limit_except_list)
		if not limit_except_block_prefix.strip().lower().startswith("limit_except "):
			raise YcException(NginxConfFormatter.TIPS_DICT["LIMIT_EXCEPT_MODULE_ANALYSIS_WARNING"] + '\n>>> limit_except prefix error!!!\n>>>' + limit_except_block_prefix)
		
		if blocks != None:
			raise YcException(NginxConfFormatter.TIPS_DICT["LIMIT_EXCEPT_MODULE_ANALYSIS_WARNING"] + '\n>>> limit_except have sub blocks !!!\n>>>' + blocks)
		
		print('finish analyze limit_except')
		return {
			"comments":limit_except_comment,
			"condition":limit_except_block_prefix[13:].strip(),
			"globals":globals,
			"last_comment":last_comment,
		}
	
	# 解析传入的list（不以"{"开头）-> 包含全局配置与子模块的字典
	def __analysis_unit(self, contents_list):
		# {
			# "globals":[
				# 1:{"key":"", "value":"", "comments":(before_comments, backend_comment)},
				# 2:{"key":"", "value":"", "comments":None},
				# ...
			# ],
			# "last_comment":"",
			# "blocks":[
				# {
					# "id":x,
					# "block_type":"",
					# "block_content_list":[],
					# "block_comment":(before_comments, backend_comment)]
				# },
				# ...
			# ]
		# }
		
		globals = {}
		
		last_comment = []
		last_comment_flag = True
		
		before_comments = []
		backend_comment = None
		has_comment = False
		
		blocks = []
		block_dict_tmp = {"id":None,"block_content_list":None,"block_type":None,"block_comment":None}
		bracket_num = 0
		
		# 多行flag
		multi_line = False
		log_format_line = False
		
		for index_content, content in enumerate(contents_list):
			# bracket_num记录花括号，标识该行是否属于block内容
			# block_list_tmp记录block内容
			# comment_list_tmp记录每一个key/block的注释内容
			
			# print(index_content, '>>>', content)
			# print('>>>', last_comment_flag)
			
			
			
			# 准备comment
			# 单行注释
			if content.startswith('#') and bracket_num == 0:
				# print('type > line comment')
				has_comment = True
				last_comment_index = index_content +1
				while last_comment_index < len(contents_list):
					if not contents_list[last_comment_index].startswith('#'):
						last_comment_flag = False
						break
					last_comment_index += 1
				if last_comment_flag == True:
					last_comment.append(content)
				else:
					before_comments.append(content)
				continue
			
			# ====此后，每一个continue之前，应该清空comment_list_tmp============
			# 设置 last_comment_flag = True，
			last_comment_flag = True
			last_comment = []
			
			# 末尾注释
			if '#' in content and bracket_num == 0:
				# print('type > comment in the end')
				has_comment = True
				backend_comment = '#' + '#'.join(content.split('#')[1:])
				content = content.split('#')[0].strip()
			
			# 是否有注释标识
			# has_comment = True if len(before_comments) != 0 else False
			
			# 计算该行是否为外层块结束行
			bracket_num_tmp = bracket_num
			is_block_over_line = False
			if ('{' in content ) or ( '}' in content):
				for word_tmp in content:
					if word_tmp == "{":
						bracket_num += 1
					if word_tmp == "}":
						bracket_num -=1
						if bracket_num == 0:
							# 说明该行为最外层块的结束行
							is_block_over_line = True
			# 如果不是结束行，并且处理到该行时，brack_num不等于0，说明依然为外层块内容，添加到块即可
			if bracket_num_tmp != 0 and ( not is_block_over_line ) :
				# print('type > block','bracket num > ',bracket_num_tmp)
				if block_dict_tmp["block_content_list"] != None:
					block_dict_tmp["block_content_list"].append(content)
				continue
			bracket_num = bracket_num_tmp
			
			# 多行location | if - 不会有末尾注释
			if ( content.startswith("location ") or content.startswith("if ") ) and ( '{' not in content ):
				multi_line = True
				block_dict_tmp["block_type"] = content.strip()
				continue
			
			if multi_line and ( '{' not in content ):
				block_dict_tmp["block_type"] += "\n" + content.strip()
				continue
			# if block_dict_tmp["block_type"] != None and ( '{' not in content ):
				# block_dict_tmp["block_type"] += "\n" + content.strip()
				# continue
			
			# 首行/末行
			if ('{' in content ) or ( '}' in content):
				# print('type > { or }')
				# block刚开始
				if block_dict_tmp["block_content_list"] == None:
					# print('type > block start')
					# 初始化block_dict_tmp
					block_dict_tmp["block_content_list"] = []
					# 获得block type
					if content.startswith('{'):
						block_dict_tmp["id"] = len(blocks)+1
						if block_dict_tmp["block_type"] != None:
							# block_dict_tmp["block_type"] +=  "\n" + content.split('{')[0].strip()
							multi_line = False
						else:
							block_dict_tmp["block_type"] = contents_list[index_content-1].split('}')[-1].split('#')[0].strip()
					else:
						before_words = content.split('{')[0].strip()
						if ';' in before_words:
							items = content.split(';')
							# analyze item
							for index_item, item in enumerate(items):
								if index_item == len(items)-1:
									block_dict_tmp["id"] = len(blocks)+1
									block_dict_tmp["block_type"] = item.strip() if block_dict_tmp["block_type"] == None else block_dict_tmp["block_type"] + "\n" + item.strip()
								else:
									key_tmp = item.split()[0]
									value_tmp = ' '.join(item.split()[1:])
									if len(before_comments) == 0:
										before_comments = None
									globals[len(globals)+1] = { "key":key_tmp, "value":value_tmp, "comments":(before_comments, backend_comment)}
									before_comments = []
									backend_comment = None
									has_comment = False
									# if index_item == 0:
										# if has_comment:
											# globals[key_tmp] = (value_tmp, before_comments)
										# before_comments = []
										# backend_comment = None
										# has_comment = False
										# else:
											# globals[key_tmp] = value_tmp
									# if index_item > 0:
										# globals[key_tmp] = value_tmp
						else:
							block_dict_tmp["id"] = len(blocks)+1
							block_dict_tmp["block_type"] = before_words if block_dict_tmp["block_type"] == None else block_dict_tmp["block_type"] + "\n" + before_words
					# 获得block comment
					if has_comment:
						if len(before_comments) == 0:
							before_comments = None
						block_dict_tmp["block_comment"] = ( before_comments,backend_comment )
						before_comments = []
						backend_comment = None
						has_comment = False
				
				
				
				# 获得首行/末行内容
				for index_word_tmp, word_tmp in enumerate(content):
					# 首行
					## bracket_num ++
					## 添加内容到 block_dict_tmp
					if word_tmp == "{":
						bracket_num += 1
						content = content[index_word_tmp+1:].strip()
						# if len(content)-1 > index_word_tmp:
							# block_dict_tmp["block_content_list"].append(content[index_word_tmp+1:].strip())
					# 末行
					## bracket_num --
					## 如果block结束，添加内容到 block_dict_tmp
					## 添加 block_dict_tmp到 blocks
					## 清空 block_dict_tmp
					
					## 将'}'之后的所有内容插到file_list中
					if word_tmp == '}':
						bracket_num -= 1
						if bracket_num == 0:
							forward_words_tmp = content[:index_word_tmp].strip()
							if len(forward_words_tmp) != 0:
								block_dict_tmp["block_content_list"].append(forward_words_tmp)
							# print('===============',block_dict_tmp)
							blocks.append(block_dict_tmp)
							block_dict_tmp = {"id":None,"block_content_list":None,"block_type":None,"block_comment":None}
							# last_comment_flag = 1
							# print('====',content, len(content))
							content = content[index_word_tmp+1:].strip()
							# print('====',content, len(content))
							# after_words = content[index_word_tmp+1:].strip()
							# file_list.insert(index_content+1, after_words)
				# before_comments = []
				# continue
			
			# block内容
			if bracket_num != 0:
				# print('type > block','bracket num > ',bracket_num)
				if len(content) != 0:
					block_dict_tmp["block_content_list"].append(content)
				continue
			
			# log_format - 不会有末尾注释
			if content.startswith("log_format "):
				log_format_line = True
				
				if len(before_comments) == 0:
					before_comments = None
				# if content.endswith(";"):
					# globals[len(globals)+1] = { "key":"log_format", "value":content[11:-1].strip(), "comments":(before_comments, None)}
				# else:
					# globals[len(globals)+1] = { "key":"log_format", "value":content[11:].strip(), "comments":(before_comments, None)}
				globals[len(globals)+1] = { "key":"log_format", "value":content[11:-1].strip(), "comments":(before_comments, None)} if content.endswith(";") else { "key":"log_format", "value":content[11:].strip(), "comments":(before_comments, None)}
				before_comments = []
				backend_comment = None
				has_comment = False
				
				if content.endswith(";"):
					log_format_line = False
				continue
			
			if log_format_line:
				for global_id in globals:
					if globals[global_id]["key"] == "log_format":
						globals[global_id]["value"] += '\n' + (content[:-1].strip()) if content.endswith(";") else '\n' + content.strip()
						if len(before_comments) != 0:
							for comment_tmp in before_comments:
								globals[global_id]["comments"][0].append(comment_tmp)
							before_comments = []
							backend_comment = None
							has_comment = False
			
			if log_format_line and content.endswith(';'):
				log_format_line = False
			
			# 子模块名行
			if ';' not in content:
				# print('type > block type single line')
				continue
			
			# 正常全局配置项
			# print('type > globals')
			items = content.split(';')
			if len(items[-1]) == 0:
				items.pop(-1)
			# analyze item
			for index_item, item in enumerate(items):
				key_tmp = item.split()[0]
				value_tmp = ' '.join(item.split()[1:])
				
				if len(before_comments) == 0:
					before_comments = None
				globals[len(globals)+1] = { "key":key_tmp, "value":value_tmp, "comments":(before_comments, backend_comment)}
				before_comments = []
				backend_comment = None
				has_comment = False
				# if index_item == 0:
					# if has_comment:
						# globals[key_tmp] = (value_tmp, before_comments)
						# before_comments = []
					# if len(before_comments) == 0:
						# before_comments = None
					# globals[len(globals)+1] = { "key":key_tmp, "value":value_tmp, "comments":(before_comments, backend_comment)}
					# before_comments = []
					# backend_comment = None
					# has_comment = False
						
						# has_comment = False
					# else:
						# globals[key_tmp] = value_tmp
				# if index_item > 0:
					# globals[key_tmp] = value_tmp
		if len(globals) == 0:
			globals = None
		if len(blocks) == 0:
			blocks = None
		if len(last_comment) == 0:
			last_comment = None
		return (globals, blocks, last_comment)
	
	# 根据传入的block_type通过查询block等级字典确定该block的级别，如http - 3
	def __match_modulate_level(self, block_type):
		return NginxConfFormatter.MODULATE_LEVEL_DICT[block_type]
	
	# 解析文件 -> 文件解析结果字典
	def __analysis_file_list(self, file_list):
		dict_tmp = {
			"globals":None,
			"events":None,
			"http":{
				"comments":None,
				"globals":None,
				"upstreams":None,
				"servers":None,
			}, 
			"last_comment":None,
		}
		
		globals, blocks, last_comment = self.__analysis_unit(file_list)
		
		# print('===============',blocks)
		
		
		# {"events", "http", "upstream", "server"} - 继续
		# { "if", "limit_except", "location"} - 报错
		
		block_types_set = set()
		if blocks != None:
			for block in blocks:
				if block["block_type"].lower().strip().startswith('location '):
					block_types_set.add("location")
					continue
				if block["block_type"].lower().strip().startswith('limit_except '):
					block_types_set.add("limit_except")
					continue
				if block["block_type"].lower().strip().startswith('if '):
					block_types_set.add("if")
					continue
				if block["block_type"].lower().strip().startswith('upstream '):
					block_types_set.add("upstream")
					continue
				block_types_set.add(block["block_type"])
		print('================', block_types_set)
		self.__modulate_level = max(map(self.__match_modulate_level, block_types_set))
		# print('===============',self.__modulate_level)
		if self.__modulate_level == 0:
			raise YcException(NginxConfFormatter.TIPS_DICT['FILE_MODULATE_ERROR'])
		
		if self.__modulate_level == 1:
			raise YcException(NginxConfFormatter.TIPS_DICT['FILE_MODULATE_ERROR'])
		
		if self.__modulate_level == 2:
			dict_tmp["globals"] = None
			dict_tmp["events"] = None
			dict_tmp["http"]["globals"] = globals
			dict_tmp["http"]["last_comment"] = last_comment
			for block in blocks:
				if block["block_type"].startswith("upstream "):
					if dict_tmp["http"]["upstreams"] == None:
						dict_tmp["http"]["upstreams"] = []
					dict_tmp["http"]["upstreams"].append((block["id"], self.__analysis_upstream_list(block["block_content_list"], block["block_comment"], block["block_type"])))
				if block["block_type"] == "server":
					if dict_tmp["http"]["servers"] == None:
						dict_tmp["http"]["servers"] = []
					dict_tmp["http"]["servers"].append((block["id"], self.__analysis_server_list(block["block_content_list"], block["block_comment"], block["block_type"])))
		
		if self.__modulate_level == 3:
			dict_tmp["globals"] = globals
			dict_tmp["last_comment"] = last_comment
			for block in blocks:
				if block["block_type"] == "events":
					dict_tmp["events"] = self.__analysis_events_list(block["block_content_list"], block["block_comment"], block["block_type"])
					dict_tmp["events"]["id"] = block["id"]
				if block["block_type"] == "http":
					dict_tmp["http"] = self.__analysis_http_list(block["block_content_list"], block["block_comment"], block["block_type"])
					dict_tmp["http"]["id"] = block["id"]
				
		return dict_tmp
	
	# 重新加载并解析初始化时指定的文件 -> 文件解析结果字典
	def __reload_file(self):
		file_list = []
		with open(self.__file, 'r', encoding="utf-8") as f_tmp:
			for line in f_tmp:
				line_tmp = line.strip()
				if len(line_tmp) != 0:
					file_list.append(line_tmp)
		return self.__analysis_file_list(file_list)
	
	# 备份文件
	def __bakup_file(self):
		import os, time, shutil
		# time.strftime("%Y-%m-%d-%H-%M-%S")
		des_F = os.path.join(os.path.dirname(self.__file),"{}.{}.bak".format(os.path.basename(self.__file), time.strftime("%Y_%m_%d_%H_%M")))
		try:
			shutil.copy(self.__file,des_F)
		except Exception as e:
			raise SystemError( "backup file error >>>\n{}".format(e) )
	
	# 格式化nginx配置文件
	def __format_file(self, des_dict):
		result_str_list = self.__get_formatter_str_list(des_dict)
		with open(self.__file, 'w', encoding="utf-8") as formatter_F:
			for str_tmp in result_str_list:
				formatter_F.write(str_tmp+'\n')
	
	def __get_events_list(self, events_dict, space_num):
		# {
			# "comments":[],
			# "globals":{},
			# "last_comment":last_comment,
		# }
		result_list = []
		
		root_space_str = ' ' * space_num
		sub_space_str = ' ' * ( space_num + 4 )
		
		# before_comments
		if ( events_dict["comments"] != None ) and ( events_dict["comments"][0] != None ):
			for comment_tmp in events_dict["comments"][0]:
				result_list.append(root_space_str + comment_tmp)
		
		# events line & events backend_comment
		events_line_str = "events " + "{"
		if ( events_dict["comments"] != None ) and ( events_dict["comments"][1] != None ):
			events_line_str += events_dict["comments"][1]
		result_list.append(root_space_str + events_line_str)
		
		# global
		if events_dict["globals"] != None:
			result_list.extend(self.__get_global_item_list(events_dict["globals"], space_num+4))
		
		# "}"
		result_list.append(root_space_str + "}")
		
		# last_comment
		if events_dict["last_comment"] != None:
			for comment_tmp in events_dict["last_comment"]:
				result_list.append(root_space_str + comment_tmp)
		
		return result_list
	
	def __get_http_list(self, http_dict, space_num, need_http_start_line=True):
		# {
			# "comments":[],
			# "globals":{},
			# "upstreams":[],
			# "servers":[],
			# "last_comment":last_comment,
		# }
		result_list = []
		
		root_space_str = ' ' * space_num
		sub_space_str = ' ' * ( space_num + 4 )
		
		if need_http_start_line:
			# before_comments
			if ( http_dict["comments"] != None ) and ( http_dict["comments"][0] != None ):
				for comment_tmp in http_dict["comments"][0]:
					result_list.append(root_space_str + comment_tmp)
			
			# http line & http backend_comment
			http_line_str = "http " + "{"
			if ( http_dict["comments"] != None ) and ( http_dict["comments"][1] != None ):
				http_line_str += http_dict["comments"][1]
			result_list.append(root_space_str + http_line_str)
		
		# global
		if http_dict["globals"] != None:
			result_list.extend(self.__get_global_item_list(http_dict["globals"], space_num+4))
		
		# upstreams、servers
		# 得按照upstream_dict与server_dict的key来决定先后顺序
		sub_block_num = 0
		if http_dict["upstreams"] != None:
			sub_block_num += len(http_dict["upstreams"])
		if http_dict["servers"] != None:
			sub_block_num += len(http_dict["servers"])
		for sub_block_id in range(1, sub_block_num+1):
			if http_dict["upstreams"] != None:
				for upstream_id, upstream_dict in http_dict["upstreams"]:
					if sub_block_id == int(upstream_id):
						if need_http_start_line:
							result_list.extend(self.__get_upstream_list(upstream_dict, space_num+4))
						else:
							result_list.extend(self.__get_upstream_list(upstream_dict, space_num))
						break
			if http_dict["servers"] != None:
				for server_id, server_dict in http_dict["servers"]:
					if sub_block_id == int(server_id):
						if need_http_start_line:
							result_list.extend(self.__get_server_list(server_dict, space_num+4))
						else:
							result_list.extend(self.__get_server_list(server_dict, space_num))
						break
		
		if need_http_start_line:
			# "}"
			result_list.append(root_space_str + "}")
		
		# last_comment
		if http_dict["last_comment"] != None:
			for comment_tmp in http_dict["last_comment"]:
				result_list.append(root_space_str + comment_tmp)
		
		return result_list
	
	def __get_upstream_list(self, upstream_dict, space_num):
		# {
			# "comments":[],
			# "name":"",
			# "globals":{},
			# "last_comment":last_comment,
		# }
		result_list = []
		
		root_space_str = ' ' * space_num
		sub_space_str = ' ' * ( space_num + 4 )
		
		# before_comments
		if ( upstream_dict["comments"] != None ) and ( upstream_dict["comments"][0] != None ):
			for comment_tmp in upstream_dict["comments"][0]:
				result_list.append(root_space_str + comment_tmp)
		
		# upstream line & upstream backend_comment
		upstream_line_str = "upstream " + upstream_dict["name"] + " {"
		if ( upstream_dict["comments"] != None ) and ( upstream_dict["comments"][1] != None ):
			upstream_line_str += upstream_dict["comments"][1]
		result_list.append(root_space_str + upstream_line_str)
		
		# global
		if upstream_dict["globals"] != None:
			result_list.extend(self.__get_global_item_list(upstream_dict["globals"], space_num+4))
		
		# "}"
		result_list.append(root_space_str + "}")
		
		# last_comment
		if upstream_dict["last_comment"] != None:
			for comment_tmp in upstream_dict["last_comment"]:
				result_list.append(root_space_str + comment_tmp)
		
		return result_list
	
	def __get_server_list(self, server_dict, space_num):
		# {
			# "comments":[],
			# "globals":{"listen":"listen_content", "server_name":"server_name_content",...},
			# "ifs":[],
			# "locations":[],
			# "last_comment":last_comment,
		# }
		result_list = []
		
		root_space_str = ' ' * space_num
		sub_space_str = ' ' * ( space_num + 4 )
		
		# before_comments
		if ( server_dict["comments"] != None ) and ( server_dict["comments"][0] != None ):
			for comment_tmp in server_dict["comments"][0]:
				result_list.append(root_space_str + comment_tmp)
		
		# server line & server backend_comment
		server_line_str = "server " + "{"
		if ( server_dict["comments"] != None ) and ( server_dict["comments"][1] != None ):
			server_line_str += server_dict["comments"][1]
		result_list.append(root_space_str + server_line_str)
		
		# global
		if server_dict["globals"] != None:
			result_list.extend(self.__get_global_item_list(server_dict["globals"], space_num+4))
		
		# ifs、locations
		# 得按照if_dict与limit_except_dict的key来决定先后顺序
		sub_block_num = 0
		if server_dict["ifs"] != None:
			sub_block_num += len(server_dict["ifs"])
		if server_dict["locations"] != None:
			sub_block_num += len(server_dict["locations"])
		for sub_block_id in range(1, sub_block_num+1):
			if server_dict["ifs"] != None:
				for if_id, if_dict in server_dict["ifs"]:
					if sub_block_id == int(if_id):
						result_list.extend(self.__get_if_list(if_dict, space_num+4))
						break
			if server_dict["locations"] != None:
				for location_id, location_dict in server_dict["locations"]:
					if sub_block_id == int(location_id):
						result_list.extend(self.__get_location_list(location_dict, space_num+4))
						break
		
		# "}"
		result_list.append(root_space_str + "}")
		
		# last_comment
		if server_dict["last_comment"] != None:
			for comment_tmp in server_dict["last_comment"]:
				result_list.append(root_space_str + comment_tmp)
		
		return result_list
	
	def __get_location_list(self, location_dict, space_num):
		# {
			# "comments":[],
			# "name":"",
			# "globals":{},
			# "ifs":[],
			# "limit_excepts":[],
			# "last_comment":last_comment,
		# }
		result_list = []
		
		root_space_str = ' ' * space_num
		sub_space_str = ' ' * ( space_num + 4 )
		
		# before_comments
		if ( location_dict["comments"] != None ) and ( location_dict["comments"][0] != None ):
			for comment_tmp in location_dict["comments"][0]:
				result_list.append(root_space_str + comment_tmp)
		
		# location line & location backend_comment
		location_line_str = "location " + location_dict["name"] + " {"
		if ( location_dict["comments"] != None ) and ( location_dict["comments"][1] != None ):
			location_line_str += location_dict["comments"][1]
		result_list.append(root_space_str + location_line_str)
		
		# global
		if location_dict["globals"] != None:
			result_list.extend(self.__get_global_item_list(location_dict["globals"], space_num+4))
		
		# ifs、limit_excepts
		# 得按照if_dict与limit_except_dict的key来决定先后顺序
		sub_block_num = 0
		if location_dict["ifs"] != None:
			sub_block_num += len(location_dict["ifs"])
		if location_dict["limit_excepts"] != None:
			sub_block_num += len(location_dict["limit_excepts"])
		for sub_block_id in range(1, sub_block_num+1):
			if location_dict["ifs"] != None:
				for if_id, if_dict in location_dict["ifs"]:
					if sub_block_id == int(if_id):
						result_list.extend(self.__get_if_list(if_dict, space_num+4))
						break
			if location_dict["limit_excepts"] != None:
				for limit_except_id, limit_except_dict in location_dict["limit_excepts"]:
					if sub_block_id == int(limit_except_id):
						result_list.extend(self.__get_limit_except_list(limit_except_dict, space_num+4))
						break
		
		# "}"
		result_list.append(root_space_str + "}")
		
		# last_comment
		if location_dict["last_comment"] != None:
			for comment_tmp in location_dict["last_comment"]:
				result_list.append(root_space_str + comment_tmp)
		
		return result_list
	
	def __get_limit_except_list(self, limit_except_dict, space_num):
		# {
			# "comments":[],
			# "condition":"",
			# "globals":{},
			# "last_comment":last_comment,
		# }
		result_list = []
		
		root_space_str = ' ' * space_num
		sub_space_str = ' ' * ( space_num + 4 )
		
		# before_comments
		if ( limit_except_dict["comments"] != None ) and ( limit_except_dict["comments"][0] != None ):
			for comment_tmp in limit_except_dict["comments"][0]:
				result_list.append(root_space_str + comment_tmp)
		
		# limit_except line & limit_except backend_comment
		limit_except_line_str = "limit_except " + limit_except_dict["condition"] + " {"
		if ( limit_except_dict["comments"] != None ) and ( limit_except_dict["comments"][1] != None ):
			limit_except_line_str += limit_except_dict["comments"][1]
		result_list.append(root_space_str + limit_except_line_str)
		
		# global
		if limit_except_dict["globals"] != None:
			result_list.extend(self.__get_global_item_list(limit_except_dict["globals"], space_num+4))
		
		# "}"
		result_list.append(root_space_str + "}")
		
		# last_comment
		if limit_except_dict["last_comment"] != None:
			for comment_tmp in limit_except_dict["last_comment"]:
				result_list.append(root_space_str + comment_tmp)
		
		return result_list
	
	def __get_if_list(self, if_dict, space_num):
		# {
			# "comments":[],
			# "condition":"",
			# "globals":{},
			# "last_comment":last_comment,
		# }
		# "globals":{
				# 1:{"key":"", "value":"", "comments":(before_comments, backend_comment)},
				# 2:{"key":"", "value":"", "comments":None},
				# ...
			# },
		result_list = []
		
		root_space_str = ' ' * space_num
		sub_space_str = ' ' * ( space_num + 4 )
		
		# before_comments
		if ( if_dict["comments"] != None ) and ( if_dict["comments"][0] != None ):
			for comment_tmp in if_dict["comments"][0]:
				result_list.append(root_space_str + comment_tmp)
		
		# if line & if backend_comment
		if_line_str = "if " + if_dict["condition"] + " {"
		if ( if_dict["comments"] != None ) and ( if_dict["comments"][1] != None ):
			if_line_str += if_dict["comments"][1]
		result_list.append(root_space_str + if_line_str)
		
		# global
		if if_dict["globals"] != None:
			result_list.extend(self.__get_global_item_list(if_dict["globals"], space_num+4))
		
		# "}"
		result_list.append(root_space_str + "}")
		
		# last_comment
		if if_dict["last_comment"] != None:
			for comment_tmp in if_dict["last_comment"]:
				result_list.append(root_space_str + comment_tmp)
		
		return result_list
	
	def __get_global_item_list(self, globals, space_num):
		result_list = []
		
		root_space_str = ' ' * space_num
		# sub_space_str = ' ' * ( space_num + 4 )
		
		global_num = len(globals)
		# print(globals)
		for global_id in range(1, global_num+1):
			# global before comment
			if globals[global_id]["comments"] != None and globals[global_id]["comments"][0] != None:
				for comment_tmp in globals[global_id]["comments"][0]:
					result_list.append(root_space_str + comment_tmp)
			# global_str & global backend_comment
			global_str = globals[global_id]["key"] + ' ' + globals[global_id]["value"] + ";" 
			if globals[global_id]["comments"] != None and globals[global_id]["comments"][1] != None:
				global_str += globals[global_id]["comments"][1]
			result_list.append(root_space_str + global_str)
		return result_list
	
	# 获取格式化的nginx字符串 -> 格式化后的str组成的list
	def __get_formatter_str_list(self, des_dict):
		# dict_tmp = {
			# "globals":{},
			# "events":{},
			# "http":{
				# "comments":None,
				# "globals":None,
				# "upstreams":[],
				# "servers":[],
			# }, 
			# "last_comment":None,
		# }
		
		
		result_list = []
		
		space_num = 0
		root_space_str = ' ' * space_num
		# sub_space_str = ' ' * ( space_num + 4 )
		
		if des_dict["globals"] != None:
			result_list.extend(self.__get_global_item_list(des_dict["globals"], space_num))
		
		if des_dict["events"] != None:
			result_list.extend(self.__get_events_list(des_dict["events"], space_num))
		
		if des_dict["http"] != None:
			if self.__modulate_level <= 2:
				result_list.extend(self.__get_http_list(des_dict["http"], space_num, need_http_start_line=False))
			if self.__modulate_level == 3:
				result_list.extend(self.__get_http_list(des_dict["http"], space_num))
		
		if des_dict["last_comment"] != None:
			for comment_tmp in des_dict["last_comment"]:
				result_list.append(root_space_str + comment_tmp)
		
		return result_list
	
	################################ 内部方法 finish ################################
	
	################################ init start ################################
	
	def __init__(self, nginx_conf_file):
		self.__file = nginx_conf_file
	
	################################ init finish ################################
	
	################################ 属性 start ################################
	
	# 文件内容解析结果dict - 只读
	@property
	def dict(self):
		return self.__reload_file()
	
	################################ 属性 finish ################################
	
	################################ 方法 start ################################
	
	# 备份并格式化nginx文件
	def format_file(self):
		self.__bakup_file()
		self.__format_file(self.dict)
	
	################################ 方法 finish ################################
	
	def add_location(self, location_name, server_listen=None,server_name=None, **location_kw):
		'''
		方法 - 添加location  # 注：会备份并格式化nginx配置文件
		location_name - 要添加的location的名字。如"~ .*.(js|css)?$"、"/"
		server_listen - 该location所在的server的listen值，该nginx配置文件有多个server时与server_name必须选填
		server_name - 该location所在的server的server_name值，该nginx配置文件有多个server时与server_port必须选填
		**location_kw - 要添加的location的key-value值
		'''
		server_dict = self.__get_server_dict(server_listen,server_name)
		
		# 要添加的location已经存在
		des_key = "location {}".format(location_name)
		if des_key in server_dict:
			logging.warning('des location "{}" already existed!!!\nif you want add or update location\'s item,you can try update_location'.format(location_name))
			return
		# 添加key-value
		server_dict[des_key] = {}
		for i in location_kw:
			server_dict[des_key][i] = location_kw[i]
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
	
	def delete_location(self, location_name, server_listen=None,server_name=None, location_key=None):
		'''
		方法 - 删除location  # 注：会备份并格式化nginx配置文件
		location_name - type:str 要删除的location的名字。如"~ .*.(js|css)?$"、"/"
		server_listen - type:int/str 该location所在的server的listen值，该nginx配置文件有多个server时与server_name必须选填
		server_name - type:str 该location所在的server的server_name值，该nginx配置文件有多个server时与server_port必须选填
		location_key - type:str/list 如果不是要删除location，只是要删除location中的一个或多个key，则传入此key或key组成的list
		'''
		server_dict = self.__get_server_dict(server_listen,server_name)
		
		# 要删除的location不存在
		des_key = "location {}".format(location_name)
		if not des_key in server_dict:
			logging.warning('des location "{}" non existed!!!'.format(location_name))
			return
		# 删除/修改location
		if location_key == None:
			server_dict.pop(des_key)
		else:
			if isinstance(location_key, str):
				if location_key not in server_dict[des_key]:
					raise ValueError('des location key "{}" not in des location "{}"'.format(location_key, des_key))
				server_dict[des_key].pop(location_key)
			elif isinstance(location_key, list):
				for i in location_key:
					if i not in server_dict[des_key]:
						raise ValueError('des location key "{}" not in des location "{}"'.format(i, des_key))
					server_dict[des_key].pop(i)
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
	
	def update_location(self, location_name, server_listen=None,server_name=None, **location_kw):
		'''
		方法 - 修改location  # 注：会备份并格式化nginx配置文件，不存在的key-value会新增
		location_name - 要修改的location的名字。如"~ .*.(js|css)?$"、"/"
		server_listen - 该location所在的server的listen值，该nginx配置文件有多个server时与server_name必须选填
		server_name - 该location所在的server的server_name值，该nginx配置文件有多个server时与server_port必须选填
		**location_kw - 要修改的location的key-value值，不存在的key-value会新增
		'''
		server_dict = self.__get_server_dict(server_listen,server_name)
		
		# 要修改的location不存在
		des_key = "location {}".format(location_name)
		if not des_key in server_dict:
			logging.warning('des location "{}" non existed!!!\nplease add that first'.format(location_name))
			return
			
		len_before_add = len(server_dict[des_key])
		# 修改location - 不存在的key-value会新增
		for i in location_kw:
			server_dict[des_key][i] = location_kw[i]
		len_after_add = len(server_dict[des_key])
		if len_after_add == len_before_add:
			params_list = []
			for i in location_kw:
				params_list.append(i)
			logging.warning('all des location\'s key "{}" already existed in "{}"!!!'.format(params_list,location_name))
		
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
	
	def query_location(self, location_name, server_listen=None,server_name=None):
		'''
		方法 - 查询location  # 注：会备份并格式化nginx配置文件
		location_name - 要查询的location的名字。如"~ .*.(js|css)?$"、"/"
		server_listen - 该location所在的server的listen值，该nginx配置文件有多个server时与server_name必须选填
		server_name - 该location所在的server的server_name值，该nginx配置文件有多个server时与server_port必须选填
		'''
		server_dict = self.__get_server_dict(server_listen,server_name)
		
		# 要修改的location不存在
		des_key = "location {}".format(location_name)
		if not des_key in server_dict:
			logging.warning('des location "{}" non existed!!!\nplease add that first'.format(location_name))
			return
		# 修改location - 不存在的key-value会新增
		return {des_key:server_dict[des_key]}
	
class YcException(Exception):
	def __init__(self, exception_type):
		super(YcException,self).__init__()
		self.message=exception_type