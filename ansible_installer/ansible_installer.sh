#!/bin/bash

current_dir=$(pwd)

# yum安装必须依赖包
sudo yum -y install xz wget gcc make gdbm-devel openssl-devel sqlite-devel zlib-devel bzip2-devel python-devel libyaml unzip libffi-devel

# 解压所有包至/usr/local/src，除过python包
for package in $(ls ${current_dir}/packages)
do
	zip_type=${package##*.}
	if [ ${zip_type} = "zip" ];then
		sudo unzip -o -d "/usr/local/src" "${current_dir}/packages/${package}"
	elif [ ${zip_type} = "gz" ];then
		sudo tar -zxvf "${current_dir}/packages/${package}" -C "/usr/local/src"
	elif [ ${zip_type} = "rpm" ];then
		sudo rpm -ivh "${current_dir}/packages/${package}"
	fi
done

# 如果python版本小于2.7，则安装2.7.10
need_install_python="false"

python_big_V=$(python -V 2>&1 | awk -F '.' '{print $1}' | awk '{print $2}')
python_sub_V=$(python -V 2>&1 | awk -F '.' '{print $2}')

python -V || need_install_python="true"

if [ ${python_big_V} -eq "2" ];then
	if [ ${python_sub_V} -lt "7" ];then
		need_install_python="true"
	fi
fi

echo "current python version is $(python -V 2>&1)" >> ${current_dir}/log.log

if [ ${need_install_python} = "true" ];then
	echo "need to install python 2.7.10" >> ${current_dir}/log.log
else
	echo "do not need to install python 2.7.10" >> ${current_dir}/log.log
fi

# 安装python2.7.10
if [ ${need_install_python} = "true" ];then
	sudo tar -zxvf "${current_dir}/packages/Python-2.7.10.tgz" -C "/usr/local/src"
	cd /usr/local/src/Python-2.7.10
	sudo ./configure --prefix=/usr/local
	sudo make -j
	sudo make install
	## 将python头文件拷贝到标准目录，以免编译ansible时，找不到所需的头文件
	sudo cp -a /usr/local/include/python2.7/* /usr/local/include/
	sudo mv /usr/bin/python /usr/bin/python.old
	sudo rm -f /usr/local/bin/python
	sudo ln -s /usr/local/bin/python2.7 /usr/local/bin/python
	sudo rm -f /usr/bin/python
	sudo cp /usr/local/bin/python2.7 /usr/bin/python
fi

# 安装ansible依赖
for package in setuptools-38.2.4 pycrypto-2.6.1 PyYAML-3.12 MarkupSafe-1.0 Jinja2-2.10 pyasn1-0.4.2 pycparser-2.18 cffi-1.11.2 six-1.11.0 PyNaCl-1.2.1 ecdsa-0.13 ipaddress-1.0.19 enum34-1.1.6 asn1crypto-0.24.0 idna-2.6 cryptography-2.1.4 bcrypt-3.1.4 paramiko-2.4.0 simplejson-3.13.2
do
	echo "---install ${package}" >> ${current_dir}/log.log
	cd /usr/local/src/${package}
	sudo python setup.py install
done

# 安装ansible
echo "---install ansible-devel" >> ${current_dir}/log.log
cd /usr/local/src/ansible-devel
sudo python setup.py install
