#!/usr/bin/env python
# -*- coding:utf-8 -*-

from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.event import RotateEvent, FormatDescriptionEvent
from pymysqlreplication.row_event import UpdateRowsEvent
from pymysqlreplication.row_event import WriteRowsEvent
from pymysqlreplication.row_event import DeleteRowsEvent
import pymysql
import time,datetime
import argparse
# import simplejson as json
import json
import sys
import signal
import traceback
'''
MySQL表信息统计小工具

基本使用

[root@centos7 tmp]# python mysql_binlog_stat.py --help
usage: mysql_binlog_stat.py [-h] [--host HOST] [--port PORT]
                            [--username USERNAME] [--password PASSWORD]
                            [--log-file binlog-file-name]
                            [--log-pos binlog-file-pos]
                            [--server-id server-id] [--slave-uuid slave-uuid]
                            [--blocking False/True] [--start-time start-time]
                            [--sorted-by insert/update/delete]

Description: The script parse MySQL binlog and statistic column.

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           Connect MySQL host
  --port PORT           Connect MySQL port
  --username USERNAME   Connect MySQL username
  --password PASSWORD   Connect MySQL password
  --log-file binlog-file-name
                        Specify a binlog name
  --log-pos binlog-file-pos
                        Specify a binlog file pos
  --server-id server-id
                        Specify a slave server server-id
  --slave-uuid slave-uuid
                        Specify a slave server uuid
  --blocking False/True
                        Specify is bloking and parse, default False
  --start-time start-time
                        Specify is start parse timestamp, default None,
                        example: 2016-11-01 00:00:00
  --sorted-by insert/update/delete
                        Specify show statistic sort by, default: insert
主要参数介绍:

--log-file: binlog 文件名称

--log-pos: binlog 文件位置(从哪个位置开始解析)

--blocking: 是否需要使用阻塞的方式进行解析始终为 False 就好(默认就是False)

--start-time: 从什么时间开始解析

--sorted-by: 展示的结果通过什么来排序, 默认是通过 insert 的行数的多少降序排列, 设置的值有 insert/update/delete

解析binlog并统计

root@(none) 09:17:12>show binary logs;
+------------------+-----------+
| Log_name         | File_size |
+------------------+-----------+
| mysql-bin.000012 | 437066170 |
| mysql-bin.000013 | 536884582 |
| mysql-bin.000014 | 537032563 |
| mysql-bin.000015 | 536950457 |
| mysql-bin.000016 |  87791004 |
| mysql-bin.000017 |       143 |
| mysql-bin.000018 |       143 |
| mysql-bin.000019 |       143 |
| mysql-bin.000020 |       143 |
| mysql-bin.000021 |      1426 |
+------------------+-----------+
10 rows in set (0.01 sec)

[root@centos7 tmp]# time python mysql_binlog_stat.py --log-file=mysql-bin.000012 --log-pos=120 --username=root --password=root --sorted-by='insert' 
[
    {
        "app_db.business_item_sku_detail": {
            "row_insert_count": {
                "market_price": 273453,
                "sku_id": 273453,
                "weight": 273453,
                "sku_info": 273453,
                "created": 273453,
                "pre_sale_stock": 273453,
                "price": 273453,
                "sku_name": 273453,
                "limit_sale_time": 273453,
                "sku_no": 273453,
                "limit_sale_num": 273453,
                "business_item_id": 273453,
                "channel_sku_lowest_price": 273453,
                "tmall_shop_id": 273453,
                "guid": 273453,
                "pic_url": 273453,
                "stock": 273453
            },
            "table_dml_count": {
                "insert": 273453,
                "update": 0,
                "delete": 0
            },
            "row_update_count": {}
        }
    },
    {
        "app_db.business_item_sku_property": {
            "row_insert_count": {
                "sku_id": 273112,
                "created": 273112,
                "property_value_id": 273112,
                "business_item_id": 273112,
                "record_id": 273112,
                "property_id": 273112
            },
            "table_dml_count": {
                "insert": 273112,
                "update": 0,
                "delete": 0
            },
            "row_update_count": {}
        }
    },
    {
        "app_db.business_item_pic": {
            "row_insert_count": {
                "created": 270993,
                "business_item_id": 270993,
                "pic_id": 270993,
                "pic_no": 270993,
                "tmall_shop_id": 270993,
                "pic_url": 270993
            },
            "table_dml_count": {
                "insert": 270993,
                "update": 0,
                "delete": 0
            },
            "row_update_count": {}
        }
    },
    {
        "app_db.business_item": {
            "row_insert_count": {
                "guide_commission": 264803,
                "commission_type": 264803,
                "pstatus": 264803,
                "num_iid": 264803,
                "limit_sale_time": 264803,
                "sell_point": 264803,
                "abbreviation": 264803,
                "distribution_time": 264803,
                "view_num": 264803,
                "tariff_rate": 264803,
                "tmall_shop_id": 264803,
                "is_pre_sale": 264803,
                "pic_url": 264803,
                "pre_sale_begin_time": 264803,
                "business_item_id": 264803,
                "sale_tax": 264803,
                "guid": 264803,
                "recommend_time": 264803,
                "is_top_newgood": 264803,
                "is_delete": 264803,
                "is_open_item_property": 264803,
                "mstatus": 264803,
                "pre_sale_end_time": 264803,
                "top_time": 264803,
                "country_id": 264803,
                "vir_sales_num": 264803,
                "content": 264803,
                "commission": 264803,
                "wholesale_sales_num": 264803,
                "is_associated_type": 264803,
                "recommend": 264803,
                "is_cross_border": 264803,
                "sales_num": 264803,
                "custom_discount_type": 264803,
                "use_item_type_tax_rate": 264803,
                "one_type_id": 264803,
                "new_good_time": 264803,
                "ship_time": 264803,
                "value_add_tax": 264803,
                "new_good_words": 264803,
                "top_time_newgood": 264803,
                "bar_code": 264803,
                "price": 264803,
                "business_no": 264803,
                "limit_sale_num": 264803,
                "is_top_hot_sell": 264803,
                "discount_type": 264803,
                "is_top": 264803,
                "tax_rate": 264803,
                "hot_sell_time": 264803,
                "is_taobao_item": 264803,
                "business_item_brand_id": 264803,
                "logistics_costs": 264803,
                "business_type": 264803,
                "guide_commission_type": 264803,
                "is_top_recommend": 264803,
                "created": 264803,
                "pre_sale_stock": 264803,
                "title": 264803,
                "two_type_id": 264803,
                "new_good_flag": 264803,
                "custom_clear_type": 264803,
                "top_time_recommend": 264803,
                "store_commission_type": 264803,
                "store_commission": 264803,
                "is_hot_sell": 264803,
                "like_num": 264803,
                "distribution": 264803,
                "stock": 264803,
                "channel_item_lowest_price": 264803,
                "top_time_hot_sell": 264803
            },
            "table_dml_count": {
                "insert": 264803,
                "update": 0,
                "delete": 0
            },
            "row_update_count": {}
        }
    },
    {
        "test.t_binlog_event": {
            "row_insert_count": {
                "auto_id": 5926,
                "dml_sql": 5926,
                "dml_start_time": 5926,
                "dml_end_time": 5926,
                "start_log_pos": 5926,
                "db_name": 5926,
                "binlog_name": 5926,
                "undo_sql": 5926,
                "table_name": 5926,
                "end_log_pos": 5926
            },
            "table_dml_count": {
                "insert": 5926,
                "update": 0,
                "delete": 4017
            },
            "row_update_count": {}
        }
    },
    {
        "test.ord_order": {
            "row_insert_count": {
                "order_id": 184,
                "pay_type": 181,
                "amount": 184,
                "create_time": 184,
                "serial_num": 181
            },
            "table_dml_count": {
                "insert": 184,
                "update": 0,
                "delete": 0
            },
            "row_update_count": {}
        }
    },
    {
        "test.t1": {
            "row_insert_count": {
                "id": 7,
                "name": 7
            },
            "table_dml_count": {
                "insert": 7,
                "update": 2,
                "delete": 2
            },
            "row_update_count": {
                "name": 2
            }
        }
    },
    {
        "test.area": {
            "row_insert_count": {},
            "table_dml_count": {
                "insert": 0,
                "update": 0,
                "delete": 0
            },
            "row_update_count": {}
        }
    }
]

real    5m42.982s
user    5m26.080s
sys     0m8.958s
'''

class MySQLBinlogStat(object):
    """对MySQL Binlog Event进行解析,获得对MySQL操作的统计"""

    _stream = None
    _table_stat_info = {}

    def __init__(self, connectionSettings, startFile=None, startPos=None, endFile=None, endPos=None, startTime=None,
                 stopTime=None, only_schemas=None, only_tables=None, nopk=False, flashback=False, only_events=[UpdateRowsEvent, WriteRowsEvent, DeleteRowsEvent],
                 stopnever=False,countnum=10):

        if not startFile:
            raise ValueError('lack of parameter,startFile.')
        self.countnum = countnum
        self.only_events = only_events
        self.connectionSettings = connectionSettings
        self.startFile = startFile
        self.startPos = startPos if startPos else 4  # use binlog v4
        self.endFile = endFile if endFile else startFile
        self.endPos = endPos
        self.startTime = datetime.datetime.strptime(startTime,
                                                    "%Y-%m-%d %H:%M:%S") if startTime else datetime.datetime.strptime(
            '1970-01-01 00:00:00', "%Y-%m-%d %H:%M:%S")
        self.stopTime = datetime.datetime.strptime(stopTime,
                                                   "%Y-%m-%d %H:%M:%S") if stopTime else datetime.datetime.strptime(
            '2999-12-31 00:00:00', "%Y-%m-%d %H:%M:%S")

        self.only_schemas = only_schemas if only_schemas else None
        self.only_tables = only_tables if only_tables else None
        self.nopk, self.flashback, self.stopnever = (nopk, flashback, stopnever)
        self.sqllist = []
        self.binlogList = []
        self.connection = pymysql.connect(**self.connectionSettings)
        try:
            cur = self.connection.cursor()
            cur.execute("SHOW MASTER STATUS")
            self.eofFile, self.eofPos = cur.fetchone()[:2]
            cur.execute("SHOW MASTER LOGS")
            binIndex = [row[0] for row in cur.fetchall()]
            if self.startFile not in binIndex:
                raise ValueError('parameter error: startFile %s not in mysql server' % self.startFile)
            binlog2i = lambda x: x.split('.')[1]
            for bin in binIndex:
                if binlog2i(bin) >= binlog2i(self.startFile) and binlog2i(bin) <= binlog2i(self.endFile):
                    self.binlogList.append(bin)

            cur.execute("SELECT @@server_id")
            self.serverId = cur.fetchone()[0]
            if not self.serverId:
                raise ValueError('need set server_id in mysql server %s:%s' % (
                self.connectionSettings['host'], self.connectionSettings['port']))

        finally:
            if 'cur' in locals():
                cur.close()

    @property
    def stream(self):
        """stream 是一个属性 - getter 方法"""
        return self._stream

    @stream.setter
    def stream(self, value):
        """stream属性的 setter 方法"""
        self._stream = value

    @property
    def table_stat_info(self):
        """table_stat_info 是一个属性 - getter 方法"""
        return self._table_stat_info

    @table_stat_info.setter
    def table_stat_info(self, value):
        """table_stat_info属性的 setter 方法"""
        self._table_stat_info = value

    def init_schema_stat_struct(self, schema=None):
        """初始化记录表统计信息的数据库基本结构
        Args:
            schema: 数据库名称
        Return: None
        Raise: None
        Table stat info struct:
            _table_stat_info = {
                'test': { # 数据库名称
                }
            }
        """

        if schema not in self.table_stat_info:  # 初始化 数据库
            self.table_stat_info[schema] = {}

    def init_table_stat_struct(self, schema=None, table=None):
        """初始化记录表统计信息的表的基本结构
        Args:
            schema: 数据库名称
            table: 表名称
        Return: None
        Raise: None
        Table stat info struct:
            _table_stat_info['test'] = {
                't1': { # 表名称
                    'table_dml_count': { # 统计表 DML 次数的变量
                        'insert': 0,
                        'update': 0,
                        'delete': 0,
                    },
                    'row_insert_count': {}, # 统计表的字段插入数
                    'row_update_count': {}, # 统计表的字段更新数
                }
            }
        """

        if table not in self.table_stat_info[schema]:  # 初始化表
            self.table_stat_info[schema][table] = {
                'table_dml_count': {  # 统计表 DML 次数的变量
                    'insert': 0,
                    'update': 0,
                    'delete': 0,
                },
                'row_insert_count': {},  # 统计表的字段插入数
                'row_update_count': {},  # 统计表的字段更新数
            }

    def init_insert_col_stat_struct(self, schema=None, table=None, col=None):
        """初始化插入字段统计结构
        Args:
            schema: 数据库
            table: 表
            col: 字段
        Return: None
        Raise: None
        """

        self.table_stat_info[schema][table]['row_insert_count'][col] = 0

    def init_update_col_stat_struct(self, schema=None, table=None, col=None):
        """初始化更新字段统计结构
        Args:
            schema: 数据库
            table: 表
            col: 字段
        Return: None
        Raise: None
        """

        self.table_stat_info[schema][table]['row_update_count'][col] = 0

    def schema_exist(self, schema=None):
        """判断schema是否存在
        Args:
            schema: 数据库
        Return: True/False
        Raise: None
        """

        if schema in self.table_stat_info:
            return True
        else:
            return False

    def table_exist(self, schema=None, table=None):
        """判断表是否存在
        Args:
            schema: 数据库
            table: 表
        Return: True/False
        Raise: None
        """

        if table in self.table_stat_info[schema]:
            return True
        else:
            return False

    def insert_col_exist(self, schema=None, table=None, col=None):
        """判断插入的字段是否存在
        Args:
            schema: 数据库
            table: 表
            col: 字段名
        Return: True/False
        Raise: None
        """

        if col in self.table_stat_info[schema][table]['row_insert_count']:
            return True
        else:
            return False

    def update_col_exist(self, schema=None, table=None, col=None):
        """判断更新的字段是否存在
        Args:
            schema: 数据库
            table: 表
            col: 字段名
        Return: True/False
        Raise: None
        """

        if col in self.table_stat_info[schema][table]['row_update_count']:
            return True
        else:
            return False

    def add_insert_count(self, schema=None, table=None, count=0):
        """添加insert执行的行数
        Args:
            schema: 数据库
            table: 表
            count: 行数
        """

        self.table_stat_info[schema][table] \
            ['table_dml_count']['insert'] += count

    def add_update_count(self, schema=None, table=None, count=0):
        """添加update执行的行数
        Args:
            schema: 数据库
            table: 表
            count: 行数
        """

        self.table_stat_info[schema][table] \
            ['table_dml_count']['update'] += count

    def add_delete_count(self, schema=None, table=None, count=0):
        """添加delete执行的行数
        Args:
            schema: 数据库
            table: 表
            count: 行数
        """

        self.table_stat_info[schema][table] \
            ['table_dml_count']['delete'] += count

    def add_insert_row_col_count(self, schema=None, table=None,
                                 col=None, count=0):
        """添加insert语句列的插入次数
        Args:
            schema: 数据库
            table: 表
            col: 列名
            count: 更新新次数
        """

        self.table_stat_info[schema][table] \
            ['row_insert_count'][col] += count

    def add_update_row_col_count(self, schema=None, table=None,
                                 col=None, count=0):
        """添加insert语句列的插入次数
        Args:
            schema: 数据库
            table: 表
            col: 列名
            count: 更新新次数
        """

        self.table_stat_info[schema][table] \
            ['row_update_count'][col] += count

    def insert_row_stat(self, binlogevent=None):
        """对WriteRowsEvent事件进行分析统计
        Args:
            binlogevent: binlog 事件对象
        Return: None
        Raise: None
        """

        # 判断之前是否存在该表的统计信息, 不存在则初始化一个
        schema = binlogevent.schema
        table = binlogevent.table

        if not self.schema_exist(schema=schema):  # 初始化 schema
            self.init_schema_stat_struct(schema=schema)

        if not self.table_exist(schema=schema, table=table):  # 初始化 table
            self.init_table_stat_struct(schema=schema, table=table)

        self.add_insert_count(schema=schema, table=table,
                              count=len(binlogevent.rows))  # 添加 INSERT 行数

    def update_row_stat(self, binlogevent=None):
        """对UpdateRowsEvent事件进行分析统计
        Args:
            binlogevent: binlog 事件对象
        Return: None
        Raise: None
        """

        # 判断之前是否存在该表的统计信息, 不存在则初始化一个
        schema = binlogevent.schema
        table = binlogevent.table

        if not self.schema_exist(schema=schema):  # 初始化 schema
            self.init_schema_stat_struct(schema=schema)

        if not self.table_exist(schema=schema, table=table):  # 初始化 table
            self.init_table_stat_struct(schema=schema, table=table)

        self.add_update_count(schema=schema, table=table,
                              count=len(binlogevent.rows))  # 添加 INSERT 行数

    def delete_row_stat(self, binlogevent=None):
        """对DeleteRowsEvent事件进行分析统计
        Args:
            binlogevent: binlog 事件对象
        Return: None
        Raise: None
        """

        # 判断之前是否存在该表的统计信息, 不存在则初始化一个
        schema = binlogevent.schema
        table = binlogevent.table

        if not self.schema_exist(schema=schema):  # 初始化 schema
            self.init_schema_stat_struct(schema=schema)

        if not self.table_exist(schema=schema, table=table):  # 初始化 table
            self.init_table_stat_struct(schema=schema, table=table)

        self.add_delete_count(schema=schema, table=table,
                              count=len(binlogevent.rows))  # 添加 DELETE 行数

    def insert_row_col_stat(self, binlogevent):
        """统计insert某列的值"""

        schema = binlogevent.schema
        table = binlogevent.table
        row_size = len(binlogevent.rows)

        for column in binlogevent.columns:
            # 初始化列的统计
            if not self.insert_col_exist(schema=schema, table=table,
                                         col=column.name):
                self.init_insert_col_stat_struct(schema=schema,
                                                 table=table,
                                                 col=column.name)
            self.add_insert_row_col_count(schema=schema, table=table,
                                          col=column.name, count=row_size)

    def update_row_col_stat(self, binlogevent):
        """统计update某列的值"""

        schema = binlogevent.schema
        table = binlogevent.table

        for row in binlogevent.rows:
            for column in binlogevent.columns:
                if column.is_primary:  # 是主键则不处理
                    continue

                # 前后的值相等则不处理
                if (row['before_values'][column.name] ==
                        row['after_values'][column.name]):
                    continue

                # 初始化更新列统计
                if not self.update_col_exist(schema=schema, table=table,
                                             col=column.name):
                    self.init_update_col_stat_struct(schema=schema,
                                                     table=table,
                                                     col=column.name)

                # 添加某列更行1次
                self.add_update_row_col_count(schema=schema, table=table,
                                              col=column.name, count=1)

    def run_parse(self):
        self.stream = BinLogStreamReader(connection_settings=self.connectionSettings, server_id=self.serverId,
                                    log_file=self.startFile, log_pos=self.startPos, only_schemas=self.only_schemas, only_events=self.only_events,
                                    only_tables=self.only_tables, resume_stream=True)

        """循环解析并统计"""

        for binlogevent in self.stream:
            count = 0
            print datetime.datetime.fromtimestamp(binlogevent.timestamp).strftime('%Y-%m-%d %H:%M:%S') ,self.stream.log_file,self.stream.log_pos
            if count >= self.countnum:
                break
            if not self.stopnever:
                if (self.stream.log_file == self.endFile and self.stream.log_pos == self.endPos) or (
                                self.stream.log_file == self.eofFile and self.stream.log_pos == self.eofPos):
                    flagLastEvent = True

                elif datetime.datetime.fromtimestamp(binlogevent.timestamp) < self.startTime:
                    if not (isinstance(binlogevent, RotateEvent) or isinstance(binlogevent, FormatDescriptionEvent)):
                        lastPos = binlogevent.packet.log_pos
                    continue
                elif (self.stream.log_file not in self.binlogList) or (
                        self.endPos and self.stream.log_file == self.endFile and self.stream.log_pos > self.endPos) or (
                                self.stream.log_file == self.eofFile and self.stream.log_pos > self.eofPos) or (
                    datetime.datetime.fromtimestamp(binlogevent.timestamp) >= self.stopTime):
                    break

            if binlogevent.event_type in [23, 30]:  # WriteRowsEvent(WRITE_ROWS_EVENT)
                self.insert_row_stat(binlogevent)
                self.insert_row_col_stat(binlogevent)
            elif binlogevent.event_type in [24, 31]:  # UpdateRowsEvent(UPDATE_ROWS_EVENT)
                self.update_row_stat(binlogevent)
                self.update_row_col_stat(binlogevent)
                pass
            elif binlogevent.event_type in [25, 32]:  # DeleteRowsEvent(DELETE_ROWS_EVENT)
                self.delete_row_stat(binlogevent)

    def print_format(self, content):
        print json.dumps(content, encoding='utf-8', ensure_ascii=False, indent=4)

    def print_sort_stat(self, by='insert'):
        """排序打印统计结果"""

        by = by.lower()  # 一律转化为小写

        # 对统计进行排序
        stat = self.iter_table_stat_format()
        sorted_stat = sorted(
            self.iter_table_stat_format(),
            key=lambda stat: stat.values()[0]['table_dml_count'][by],
            reverse=True,
        )
        self.print_format(sorted_stat)

    def iter_table_stat_format(self):
        """格式化每个表的统计的dict
        Format: {'schema.table': xxx}
        """

        for schema, tables in self.table_stat_info.iteritems():
            for table, stat in tables.iteritems():
                key = '{schema}.{table}'.format(schema=schema, table=table)
                yield {key: stat}


def parse_args():
    """解析命令行传入参数"""
    usage = """
        Description:
            The script parse MySQL binlog and statistic column.
    """

    # 创建解析对象并传入描述
    parser = argparse.ArgumentParser(description=usage)
    # 添加 MySQL Host 参数
    parser.add_argument('--host', dest='host', action='store',
                        default='127.0.0.1', help='Connect MySQL host',
                        metavar='HOST')
    # 添加 MySQL Port 参数
    parser.add_argument('--port', dest='port', action='store',
                        default=3306, help='Connect MySQL port',
                        metavar='PORT', type=int)
    # 添加 MySQL username 参数
    parser.add_argument('--username', dest='username', action='store',
                        default='root', help='Connect MySQL username',
                        metavar='USERNAME')
    # 添加 MySQL password 参数
    parser.add_argument('--password', dest='password', action='store',
                        default='root', help='Connect MySQL password',
                        metavar='PASSWORD')
    # 添加 MySQL binlog file 参数
    parser.add_argument('--log-file', dest='log_file', action='store',
                        default=None, help='Specify a binlog name',
                        metavar='binlog-file-name')
    # 添加 MySQL binlog file pos 参数
    parser.add_argument('--log-pos', dest='log_pos', action='store',
                        default=None, help='Specify a binlog file pos',
                        metavar='binlog-file-pos', type=int)
    # 添加 slave server id 参数
    parser.add_argument('--server-id', dest='server_id', action='store',
                        default=99999, help='Specify a slave server server-id',
                        metavar='server-id', type=int)
    # 添加 slave uuid 参数
    parser.add_argument('--slave-uuid', dest='slave_uuid', action='store',
                        default='ca1e2b93-5d2f-11e6-b758-0800277643c8',
                        help='Specify a slave server uuid', metavar='slave-uuid')
    # 添加 是否以阻塞的方式进行解析 参数
    parser.add_argument('--blocking', dest='blocking', action='store',
                        default=False, help='Specify is bloking and parse, default False',
                        metavar='False/True')
    # 添加指定以什么时间戳开始进行解析
    help = 'Specify is start parse timestamp, default None, example: 2016-11-01 00:00:00'
    parser.add_argument('--start-time', dest='start_time', action='store',
                        default=None, help=help, metavar='start-time')
    # 添加 是否以阻塞的方式进行解析 参数
    parser.add_argument('--sorted-by', dest='sorted_by', action='store',
                        default='insert', help='Specify show statistic sort by, default: insert',
                        metavar='insert/update/delete')

    args = parser.parse_args()

    return args


def kill_sign_op(signum, frame):
    """当接收到kill 信号执行关闭流打印输出 和"""

    global mysql_binlog_stat  # 使用全局mysql_binlog_stat

    if mysql_binlog_stat != None:  # 不为空才执行

        # 关闭流
        mysql_binlog_stat.stream.close()

        # 打印数据
        mysql_binlog_stat.print_sort_stat()

    sys.exit(0)


# 定义全局变量
mysql_binlog_stat = None


def main():
    global mysql_binlog_stat  # 使用前面的全局变量

    # 注册 捕获型号kill信号
    signal.signal(signal.SIGTERM, kill_sign_op)

    # args = parse_args()  # 解析传入参数

    # mysql_settings = {
    #     'host': args.host,
    #     'port': args.port,
    #     'user': args.username,
    #     'passwd': args.password,
    # }
    # mysql_settings = {
    #     'host': '192.168.134.1',
    #     'port': 3308,
    #     'user': 'admin_user',
    #     'passwd': 'qweQWE123$%^',
    # }
    # skip_to_timestamp = (
    #     time.mktime(time.strptime(args.start_time, '%Y-%m-%d %H:%M:%S'))
    #     if args.start_time else None
    # )
    #
    # stream_conf = {
    #     'connection_settings': mysql_settings,
    #     'server_id': args.server_id,
    #     'slave_uuid': args.slave_uuid,
    #     'blocking': args.blocking,
    #     'log_file': args.log_file,
    #     'log_pos': args.log_pos,
    #     'skip_to_timestamp': skip_to_timestamp,
    #     'only_events': [UpdateRowsEvent, WriteRowsEvent, DeleteRowsEvent],
    # }
    # stream_conf = {
    #     'connection_settings': mysql_settings,
    #     'server_id': 132,
    #     'slave_uuid': '',
    #     'blocking': '',
    #     'log_file': 'mysql-bin.000006',
    #     'log_pos': 4,
    #     'skip_to_timestamp': '',
    #     'only_events': [UpdateRowsEvent, WriteRowsEvent, DeleteRowsEvent],
    # }
    #
    #
    #

host = '192.168.134.1'
port = 3308
user = 'admin_user'
password = 'qweQWE123$%^'
startFile = 'mysql-bin.000008'
endFile = 'mysql-bin.000009'
startPos = 4
connectionSettings = {'host': host, 'port': port, 'user': user, 'passwd': password}
mysql_binlog_stat = MySQLBinlogStat(connectionSettings=connectionSettings, startFile=startFile,
                        startPos=startPos, endFile=endFile, endPos=0,
                        startTime='', stopTime='', only_schemas='',
                        only_tables='', nopk=False, flashback=False, stopnever=False, countnum=1)

try:
    mysql_binlog_stat.run_parse()

except KeyboardInterrupt:  # 捕捉 KeyboardInterrupt 异常
    print 'force to exit...'

except Exception as e:
    print traceback.format_exc()

finally:  # 最终需要关闭流
    pass
    # mysql_binlog_stat.stream.close()

    # 打印数据
mysql_binlog_stat.print_sort_stat(by='insert')
if __name__ == '__main__':
    main()