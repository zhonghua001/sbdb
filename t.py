# -*- coding: utf-8 -*-
import pymysql
def main(sql):
    conf = {
        'user':'root',
        'password':'123456',
        'host':'192.168.0.11',
        'port':3306,
        'db': None,
        'charset':'utf8'
    }

    conn = pymysql.connect(**conf)
    cur = conn.cursor()

    i = range(10000)
    p = 1
    while True:
        try:
            conn = pymysql.connect(**conf)
            cur = conn.cursor()

            cur.execute(sql)
            col = [c[0] for c in cur.description]
            result = [dict(zip(col,row)) for row in cur.fetchall()]


            cur.close()
            conn.commit()
            conn.close()
            print result

            continue
        except IndexError:
            cur.close()
            conn.commit()
            conn.close()
            break

if __name__ == '__main__':
    pymysql.install_as_MySQLdb()
    import MySQLdb
    sql = '''/*--user=all_user;--password=qweQWE123$%^;--host=192.168.0.11;--enable-check;--port=3306;*/            inception_magic_start;            use bbs;CREATE TABLE `index_maxs` (
  `type` int(11) NOT NULL COMMENT 'type id',
  `name` varchar(255) NOT NULL COMMENT 'type name',
  `indexmax` bigint(20) unsigned NOT NULL DEFAULT '1' COMMENT'indexmax',
  PRIMARY KEY (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;inception_magic_commit;'''



    sql1 = '''/*--user=all_user;--password=qweQWE123$%^;--host=192.168.0.11;--enable-check;--port=3306;*/
inception_magic_start;
use zabbix;

commit;
inception_magic_commit;'''

    # sql = '/*--user=all_user;--password=qweQWE123$%^;--host=192.168.134.1;--execute=1;--port=3308;*/\
    # inception_magic_start;\
    # use mysql;\
    # CREATE TABLE adaptive_office(id int);\
    # inception_magic_commit;'
    try:
        conn = MySQLdb.connect(host='192.168.0.11', user='', passwd='', db='', port=6669)
        cur = conn.cursor()
        ret = cur.execute(sql1)
        result = cur.fetchall()
        num_fields = len(cur.description)
        field_names = [i[0] for i in cur.description]
        print field_names
        for row in result:
            print row
        cur.close()
        conn.close()
    except MySQLdb.Error, e:
        print "Mysql Error %d: %s" % (e.args[0], e.args[1])
