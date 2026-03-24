#! /usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time   :2020/12/10 16:04
# @Auther :yanjie.li
# @Email  :381347268@qq.com
# @File   :main.py


import configparser
import os
import time
from GetItems import Zabbix
from SaveToExcel import WriteExcel


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read(os.path.join(os.getcwd(), 'config.ini'), encoding='utf-8')
    # 实例化一个zabbix对象
    zabbix =  Zabbix(
        config.get('zabbix', 'api_url'),
        config.get('zabbix', 'user'),
        config.get('zabbix', 'password')
    )
    # 调用GetItemValue方法获取每台监控主机的监控数据
    zabbix_data = zabbix.GetItemValue()
    if len(zabbix_data) == 2:
        print(zabbix_data['errmsg'])
    else:
        date_time = time.strftime('%Y-%m-%d_%H-%M-%S')
        file_name = os.path.join(os.getcwd(), config.get('excel', 'file_name') + date_time + '.xlsx')
        WriteExcel(file_name, zabbix_data)












