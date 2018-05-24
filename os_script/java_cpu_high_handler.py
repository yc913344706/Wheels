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
	dump占用CPU过高的thread信息、JVM内存信息以及JVM堆栈信息到指定目录下，
	方便回溯。
参考：
	记一次线上Java程序导致服务器CPU占用率过高的问题排除过程
		https://www.jianshu.com/p/3667157d63bb
'''

import os,time

def get_java_pid():
	'''获得运行tomcat的java进程号 -> str'''
	print(">>>>" + time.strftime("%Y-%m-%d_%H_%M_%S", time.localtime()) + " get_java_pid")
	return os.popen("ps aux|grep tomcat|grep conf | grep -v grep | awk '{print $2}'").read().strip()

def get_process_cpu():
	'''获得运行tomcat的java进程所占cpu数值 -> float'''
	print(">>>>" + time.strftime("%Y-%m-%d_%H_%M_%S", time.localtime()) + " get_process_cpu")
	return float(os.popen("ps aux|grep tomcat|grep conf | grep -v grep | awk '{print $3}'").read().strip())

def get_busy_threads(java_pid, thread_cpu_limit):
	'''获得java_pid进程中占用cpu高于thread_cpu_limit的线程 -> list'''
	print(">>>>" + time.strftime("%Y-%m-%d_%H_%M_%S", time.localtime()) + " get_busy_threads")
	result_list = [s.split() for s in os.popen("ps -mp %s -o THREAD,tid,time|awk '{if ($2>%d && $8!=\"-\") {print $8,%2,%9}}'" % (java_pid, thread_cpu_limit)).read().split('\n')[:-1]]
	for index_tmp in range(0, len(result_list)):
		result_list[index_tmp][0] = "%x" % int(result_list[index_tmp][0])
	return result_list

def get_real_busy_threads(busy_threads_old, busy_threads_new):
	'''比较两组线程，返回其中重复的线程 -> list'''
	print(">>>>" + time.strftime("%Y-%m-%d_%H_%M_%S", time.localtime()) + " get_real_busy_threads")
	old_bts = [t[0] for t in busy_threads_old]
	new_bts = [t[0] for t in busy_threads_new]
	real_bts = []
	for bt in old_bts:
		if bt in new_bts:
			real_bts.append(bt)
	return real_bts

def archive_memory_info(real_busy_threads, archive_dir, thread_cpu_limit, sleep_time, java_pid):
	'''归档内存信息 -> null'''
	print(">>>>" + time.strftime("%Y-%m-%d_%H_%M_%S", time.localtime()) + " archive_memory_info")
	archive_file = os.path.join(archive_dir, "%s.log" % time.strftime("%Y-%m-%d_%H_%M_%S", time.localtime()))
	
	if not os.path.exists(os.path.dirname(archive_file)):
		os.makedirs(os.path.dirname(archive_file))
	
	str_list = []
	
	str_list.append("The threads that %d seconds to occupy cpu more than %d%%" % (sleep_time, thread_cpu_limit))
	
	for bt in real_busy_threads:
		str_list.append(bt)
		
	str_list.append("")
	str_list.append("JVM Memory Info")
	str_list.extend(os.popen("jstat -gcutil %s 2000 10" % java_pid).read().split('\n')[:-1])
	
	str_list.append("")
	str_list.append("JVM Stack Info")
	str_list.extend(os.popen("jstack %s" % java_pid).read().split('\n')[:-1])
	
	with open(archive_file, 'w') as f:
		f.write('\n'.join(str_list))

def main():
	# 获得java进程号
	java_pid = get_java_pid()
	
	# 可变variables
	process_cpu_limit = 5 # 进程cpu占用deadline
	thread_cpu_limit = 1 # 线程cpu占用deadline
	sleep_time = 1*60 # 每次检测间隔时间-s
	archive_dir = "/data01/ycfiles/cpu_high/logs" # 日志记录文件夹
	
	# flag变量
	busy_threads_old = [] 
	
	while True:
		# 获得进程CPU占用率
		process_cpu = get_process_cpu()
		# 进程CPU占用率超过deadline
		if process_cpu > process_cpu_limit:
			# 存在 busy_threads_old
			if len(busy_threads_old) > 0:
				# 获得 busy_threads_new
				busy_threads_new = get_busy_threads(java_pid, thread_cpu_limit)
				# 获得 real_busy_threads
				real_busy_threads = get_real_busy_threads(busy_threads_old, busy_threads_new)
				# 归档内存信息
				archive_memory_info(real_busy_threads, os.path.join(archive_dir, time.strftime("%Y-%m", time.localtime())), thread_cpu_limit, sleep_time, java_pid)
			# 不存在 busy_threads_old
			else:
				# 获得 busy_threads_new
				busy_threads_new = get_busy_threads(java_pid, thread_cpu_limit)
				# busy_threads_old = busy_threads_new
				busy_threads_old = busy_threads_new
		# 进程CPU占用率不超过deadline
		else:
			# 设置 flag变量
			busy_threads_old = []
		
		# sleep
		time.sleep(sleep_time)
		
main()
