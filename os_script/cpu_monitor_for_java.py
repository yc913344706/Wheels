# -*- coding:utf-8 -*-
#!/bin/python

'''
适用场景：
	linux + tomcat（一个tomcat进程）
可变参数：
	main()方法中的“可变variables”
功能：
	后台运行该脚本，
	可在运行tomat的java进程占用CPU过高时，
	dump占用CPU过高的thread信息、JVM内存信息以及JVM实时堆栈信息到脚本所在目录下的logs文件夹，
	方便回溯。
参考：
	记一次线上Java程序导致服务器CPU占用率过高的问题排除过程
		https://www.jianshu.com/p/3667157d63bb
	linux top命令后台执行问题
		http://www.dewen.net.cn/q/15392
	ps 和 top cpu 占用区别
		https://blog.csdn.net/beginning1126/article/details/8057527
'''

import os, time, logging, sys, inspect

def config_logger():
	"""CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTEST，默认级别为WARNING"""
	logging.basicConfig(
		level = logging.DEBUG,
		format = '%(asctime)s [%(levelname)s] at %(filename)s,%(lineno)d:%(message)s',
		datefmt = '%Y-%m-%d(%a)%H:%M:%S',
		filename = os.path.join(os.getcwd(), inspect.stack()[1][1][:-3] + '_operation.log'),
		filemode = 'w'
	)
	
	# 将大于或等于INFO级别的日志输出到StreamHandler（默认为标准错误）
	console = logging.StreamHandler()
	console.setLevel(logging.INFO)
	formatter = logging.Formatter('[%(levelname)-8s]%(message)s') # 屏显实时查看，无需时间
	
	console.setFormatter(formatter)
	logging.getLogger().addHandler(console)

def get_java_pid():
	'''获得运行tomcat的java进程号 -> str'''
	logging.info("get_java_pid")
	return os.popen("ps aux|grep tomcat|grep conf | grep -v grep | awk '{print $2}'").read().strip()

def get_sys_cpu():
	'''获得系统的实时cpu数值 -> float'''
	logging.info("get_sys_cpu")
	return float(os.popen("top -b -d 2 -n 2 | grep Cpu\(s\) | sed -n '2p' | awk '{print $2}' | awk 'BEGIN{FS=\"%\"}{print $1}'").read().strip())

def get_busy_threads(java_pid, thread_cpu_limit):
	'''获得java_pid进程中占用cpu高于thread_cpu_limit的线程 -> list'''
	logging.info("get_busy_threads")
	result_list = [s.split() for s in os.popen("ps -mp %s -o THREAD,tid,time|awk '{if ($2>%d && $8!=\"-\") {print $8,$2,$9}}'" % (java_pid, thread_cpu_limit)).read().split('\n')[:-1]]
	for index_tmp in range(0, len(result_list)):
		result_list[index_tmp][0] = "%x" % int(result_list[index_tmp][0])
	return result_list

def get_real_busy_threads(busy_threads_old, busy_threads_new):
	'''比较两组线程，返回其中重复的线程 -> list'''
	logging.info("get_real_busy_threads")
	old_bts = [t[0] for t in busy_threads_old]
	new_bts = [t[0] for t in busy_threads_new]
	real_bts = []
	for bt in old_bts:
		if bt in new_bts:
			real_bts.append(bt)
	return real_bts

def archive_memory_info(busy_threads, archive_dir, thread_cpu_limit, java_pid, sys_cpu):
	'''归档内存信息 -> null'''
	logging.info(" archive_memory_info")
	archive_file = os.path.join(archive_dir, "%s.log" % time.strftime("%Y-%m-%d_%H_%M_%S", time.localtime()))
	
	if not os.path.exists(os.path.dirname(archive_file)):
		os.makedirs(os.path.dirname(archive_file))
	
	str_list = []
	
	str_list.append("Current System CPU Occupancy rate = %s%% " % (sys_cpu))
	
	str_list.append("")
	str_list.append("The current threads'xid that occupy cpu more than %d%%" % ( thread_cpu_limit))
	
	for bt in busy_threads:
		str_list.append(bt)
		
	str_list.append("")
	str_list.append("JVM Memory Info")
	str_list.extend(os.popen("jstat -gcutil %s 2000 10" % java_pid).read().split('\n')[:-1])
	
	str_list.append("")
	str_list.append("JVM Stack Info")
	str_list.extend(os.popen("jstack %s" % java_pid).read().split('\n')[:-1])
	
	with open(archive_file, 'w') as f:
		f.write('\n'.join(["%s" % str_tmp for str_tmp in str_list]))

def main():
	
	logging.info("start main function")
	
	# 可变variables
	sys_cpu_limit = 50 # 系统cpu占用deadline
	thread_cpu_limit = 20 # 线程cpu占用deadline
	sleep_time = 3*60 # 每次检测间隔时间-s
	archive_dir = os.path.join(os.getcwd(), "logs") # 日志记录文件夹
	
#	# flag变量
#	busy_threads_old = [] 
	
	while True:
		logging.info("start while")
		
		# 获得java进程号
		java_pid = get_java_pid()
		
		# 获得系统CPU占用率
		sys_cpu = get_sys_cpu()
		logging.info("sys cpu=" + str(sys_cpu))
		
		# 系统CPU占用率超过deadline
		if sys_cpu > sys_cpu_limit:
			# 获得 busy_threads_new
			busy_threads = get_busy_threads(java_pid, thread_cpu_limit)
			# 归档内存信息
			archive_memory_info(busy_threads, os.path.join(archive_dir, time.strftime("%Y-%m", time.localtime())), thread_cpu_limit, java_pid, sys_cpu)
		
#			# 存在 busy_threads_old
#			if len(busy_threads_old) > 0:
#				# 获得 busy_threads_new
#				busy_threads_new = get_busy_threads(java_pid, thread_cpu_limit)
#				# 获得 real_busy_threads
#				real_busy_threads = get_real_busy_threads(busy_threads_old, busy_threads_new)
#				# 归档内存信息
#				archive_memory_info(real_busy_threads, os.path.join(archive_dir, time.strftime("%Y-%m", time.localtime())), thread_cpu_limit, sleep_time, java_pid)
#			# 不存在 busy_threads_old
#			else:
#				# 获得 busy_threads_new
#				busy_threads_new = get_busy_threads(java_pid, thread_cpu_limit)
#				# busy_threads_old = busy_threads_new
#				busy_threads_old = busy_threads_new
#		# 进程CPU占用率不超过deadline
#		else:
#			# 设置 flag变量
#			busy_threads_old = []
		
		# sleep
		logging.info("start sleeping...")
		time.sleep(sleep_time)
		
		logging.info("finish while")
		
try:
	config_logger()
	main()
except Exception,e:
	logging.error(e)