#!/usr/bin/python3
import getopt, ConfigParser,hashlib
import logging
import logging.config
import glob
import subprocess
from subprocess import Popen, PIPE
import shlex
import commands
import json
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex
from datetime import datetime
import os
import time
import struct
import sys


instance_id = 7
server_ip = '192.168.134.135:9999'
token = 'HPcWR7l4NJNJ'

result = {}
result['instance_id'] = instance_id
result['token'] = token


def main():
    """main method for parsing the command line options and what happens after that"""
    # options, args and config all need to be global so they can be used in other methods
    parameter = ['backup','--incremental','--all-databases','--manual']

    global options, args, config, logger, quiet, manual


    # quiet tells the application to not print it's current status to stdout. It just
    # logs instead.
    quiet = False
    manual = False

    # open the config file and parse it
    config = ConfigParser.RawConfigParser()
    config_file = '%s/config.cfg' % (os.path.abspath(os.path.dirname(__file__)))
    config.read(config_file)

    # configure the logger
    logger = logging.getLogger("PMB LOG")
    logger.setLevel(logging.DEBUG)
    fileHandler = logging.FileHandler(config.get('Logging', 'log_path'))
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)

    # list of available options
    available = ['backup', 'restore', 'fetch']

    # attemped to parse the command line arguments. getopt will detect and throw an exception if an argument
    # exists that wasn't meant to be there.

    try:
        options, args = getopt.gnu_getopt(
            parameter,
                'fi',
                ['full',
                 'incremental',
                 'all-databases',
                 'database=',
                 'time=',
                 'date=',
                 'quiet',
                 'manual',]
        )
    except getopt.GetoptError, err:
        logAndPrint(err, 'error', True, True)

    # check for the quiet option
    for o, a in options:
        if '--quiet' == o:
            logger.info('Entering quiet mode...')
            quiet = True
            break

    for o, a in options:
        if '--manual' == o:
            logger.info('Entering manual mode...')

            manual = True
            break

    message = '### Starting Pamiris MySQL Backup Application ###'
    logAndPrint(message, 'info')

    # log what was passed in via command line
    logAndPrint('Running with: %s' % (' '.join(parameter)), 'info', False)

    # we do this because we only want either backup, restore, or fetch to be passed in. aka one at a time
    if len(args) > 1:
        message = 'FATAL: Cannot pass in more than one action (argument)'

        logAndPrint(message, 'error', True, True)

    # detect which action is needed and call it's method
    if 'backup' == args[0]:
        logger.info('Database backup wanted...')
        backup()
    elif 'restore' == args[0]:
        logger.info('Database restore wanted...')
        restore()
    elif 'fetch' == args[0]:
        logger.info('Database fetch wanted...')
        fetch()
    else:
        message = "FATAL: Argument '%s' not recognized" % (args[0])
        logAndPrint(message, 'error', True, True)




try:
    import requests
except ImportError as msg:
    print msg
    print("------------------------------------------------")
    print("begining install schedule module, please waiting")
    p = Popen('pip install requests==2.17.3', stdout=PIPE, shell=True)
    stdout, stderr = p.communicate()
    print stdout
    import requests

def post_data(url, data):
    try:
        r = requests.post(url, data)
        if r.text:
            logAndPrint(r.text,'info',True,False)
            return True
            # print r.text
        else:
            logAndPrint("Server return http status code: {0}".format(r.status_code), 'error',True, False)
            return False
    except StandardError as msg:
        if r.status_code <> 200:
            with open(os.path.dirname(__file__)+'/PostError.cache','a+') as f:
                f.write(data)
        logAndPrint(msg,'error',True,False)



def _post_failed():
    os.chdir(os.path.dirname(__file__))
    if os.path.isfile('PostError.cache' ):
        os.system('cp PostError.cache PostError.cache.1')
        with open('PostError.cache.1','r') as f:
            for r in f.readlines():
                try:
                    push_data(json.loads(r))
                    continue
                except Exception,e:
                    print e
                    print r
                    with open('PostError.cache.tmp', 'a+') as f_t:
                        f_t.write(r)
        if os.path.isfile('PostError.cache.tmp'):
            os.system('rm -f PostError.cache')
            os.system('rm -f PostError.cache.1')
            os.system('mv PostError.cache.tmp PostError.cache')
        else:
            os.system('rm -f PostError.cache')
            os.system('rm -f PostError.cache.1')



def push_data(backup_info):
    print backup_info

    json_data = json.dumps(backup_info)

    post_data("http://{0}/dbmanage/backup_manage/received/backup_info/".format(server_ip), json_data)
    print '----------------------------------------------------------'
    return True



def get_backup_conn_info():


    t = repr(time.time())

    r = requests.get('http://{0}/dbmanage/backup_manage/received/backup_info/'.format(server_ip),params={'instance_id':instance_id,'token':token,'t':t})
    print r
    if r.status_code != 200:
        result['error'] = r.content
        result['instance_id'] = instance_id
        push_data(result)

    mode = AES.MODE_CBC
    cryptor = AES.new(t[-16:], mode, t[-16:])
    response_data = json.loads(r.content)
    ip = response_data['ip']
    port = response_data['port']
    user = response_data['user']
    password = cryptor.decrypt(a2b_hex(response_data['password'])).rstrip('\0')
    data = {
        'ip':ip,
        'port':port,
        'user':user,
        'password':password
    }

    return data



def to_uint8(byts) :
    retval,= struct.unpack('B' , byts)
    return retval

def to_uint16(byts) :
    retval,= struct.unpack('H' , byts)
    return retval

def to_uint32(byts) :
    retval,= struct.unpack('I' , byts)
    return retval

def to_uint64(byts) :
    retval,= struct.unpack('Q' , byts)
    return retval

def to_char(byts) :
    retval,= struct.unpack('c' , byts)
    return retval

class BinFileReader(object) :

    def __init__(self , bin_filename) :
        self.stream = open(bin_filename , 'rb')

    def uint8(self)  :
        buf = self.stream.read(1)
        if buf is None or buf=='' :
            raise Exception('End of file.')
        return to_uint8(buf)

    def uint16(self) :
        buf = self.stream.read(2)
        if buf is None or buf=='' :
            raise Exception('End of file.')
        return to_uint16(buf)

    def uint32(self) :
        buf = self.stream.read(4)
        if buf is None or buf=='' :
            raise Exception('End of file.')
        return to_uint32(buf)

    def uint64(self) :
        buf = self.stream.read(8)
        if buf is None or buf=='' :
            raise Exception('End of file.')
        return to_uint64(buf)

    def char(self) :
        buf = self.stream.read(1)
        if buf is None or buf=='' :
            raise Exception('End of file.')
        return to_char(buf)

    def chars(self , byte_size=1) :
        buf = self.stream.read(byte_size)
        if buf is None or buf=='' :
            raise Exception('End of file.')
        return buf

    def close(self) :
        self.stream.close()

    def seek(self , p , seek_type=0) :
        self.stream.seek(p , seek_type)

class Constant :
    BINLOG_HEADER = '\xfe\x62\x69\x6e'
    BINLOG_HEADER_LEN = 4
    EVENT_HEADER_LEN = 19

class EventType :
    UNKNOWN_EVENT= 0
    START_EVENT_V3= 1
    QUERY_EVENT= 2
    STOP_EVENT= 3
    ROTATE_EVENT= 4
    INTVAR_EVENT= 5
    LOAD_EVENT= 6
    SLAVE_EVENT= 7
    CREATE_FILE_EVENT= 8
    APPEND_BLOCK_EVENT= 9
    EXEC_LOAD_EVENT= 10
    DELETE_FILE_EVENT= 11
    NEW_LOAD_EVENT= 12
    RAND_EVENT= 13
    USER_VAR_EVENT= 14
    FORMAT_DESCRIPTION_EVENT= 15
    XID_EVENT= 16
    BEGIN_LOAD_QUERY_EVENT= 17
    EXECUTE_LOAD_QUERY_EVENT= 18
    TABLE_MAP_EVENT = 19
    PRE_GA_WRITE_ROWS_EVENT = 20
    PRE_GA_UPDATE_ROWS_EVENT = 21
    PRE_GA_DELETE_ROWS_EVENT = 22
    WRITE_ROWS_EVENT = 23
    UPDATE_ROWS_EVENT = 24
    DELETE_ROWS_EVENT = 25
    INCIDENT_EVENT= 26
    HEARTBEAT_LOG_EVENT= 27

class ErrCode :
    ERR_BAD_ARGS = 1
    ERR_OPEN_FAILED = 2
    ERR_NOT_BINLOG = 3
    ERR_READ_FDE_FAILED = 4
    ERR_READ_RE_FAILED = 5

class EventHeader :
    EVENT_HEADER_LEN = 19
    def __init__(self , reader) :
        self.timestamp = reader.uint32()
        self.type_code = reader.uint8()
        self.server_id = reader.uint32()
        self.event_length = reader.uint32()
        self.next_position = reader.uint32()
        self.flags = reader.uint16()

    def __repr__(self) :
        msg = 'EventHeader: Timestamp=%s type_code=%s server_id=%s event_length=%s next_position=%s flags=%s' % \
              (self.timestamp  , self.type_code , self.server_id , self.event_length , self.next_position ,
               self.flags)
        return msg





class FormatDescEventData :
    def __init__(self , reader , event_header) :
        self.binlog_version = reader.uint16()
        self.server_version = reader.chars(50)
        self.create_timestamp = reader.uint32()
        self.header_length = reader.uint8()
        # post_header_len is not decoded
        self.post_header_len = reader.chars(event_header.event_length - 2 - 50 - 4 - 1 -19 -1 )
        if reader.char() ==  '\x00' :
            pass

    def __repr__(self) :
        msg ='FormatDescEventData: binlog_version=%s    server_version=%s    create_timestamp=%s    header_length=%s' % \
                (self.binlog_version , self.server_version , self.create_timestamp , self.header_length)
        return msg

class RotateEvent :
    def __init__(self , reader , event_header) :
        self.position = reader.uint64()
        self.next_binlog = reader.chars(event_header.event_length - 8 - 19 )

    def __repr__(self) :
        msg = 'Rotate Event : position=%s next_binlog=%s' % (self.position , self.next_binlog )
        return msg




def getBigFileMD5(filepath):
    if os.path.isfile(filepath):
        md5obj = hashlib.md5()
        maxbuf = 8192
        f = open(filepath,'rb')
        while True:
            buf = f.read(maxbuf)
            if not buf:
                break
            md5obj.update(buf)
        f.close()
        hash = md5obj.hexdigest()
        return str(hash).upper()
    return None

def get_info(mysql_binlog) :

    reader = BinFileReader(mysql_binlog)
    binlog_header = reader.chars(Constant.BINLOG_HEADER_LEN)

    # print binlog_header
    if binlog_header != Constant.BINLOG_HEADER :
        raise Exception('It\'s not a mysql binlog file')
    last_event_header = None
    retval = {}

    try :
        while True:
            event_header = EventHeader(reader)
            last_event_header = event_header
            if event_header.type_code == EventType.FORMAT_DESCRIPTION_EVENT :
                event_body = FormatDescEventData(reader , event_header)
                retval['start_pos'] = event_header.next_position
                retval['start_time'] = event_header.timestamp
                retval['cur_binlog'] = mysql_binlog
            elif event_header.type_code == EventType.ROTATE_EVENT :
                event_body = RotateEvent(reader , event_header)
                retval['end_time'] = event_header.timestamp
                retval['next_binlog'] = event_body.next_binlog
                retval['end_pos'] = event_header.next_position
                break
            elif event_header.type_code == EventType.STOP_EVENT :
                # event_body = StopEvent(reader , event_header)
                break
            else :
                reader.seek(event_header.event_length - 19 , 1 )
    except Exception :
        if reader.stream.read() == '' :
            pass
        else :
            raise Exception('Error when read mysql binlog,filename is %s '\
                %(mysql_binlog , ) )
    finally :
        reader.close()

    if not getattr(retval, 'end_pos', None):
        retval['end_pos'] = event_header.next_position
    if not getattr(retval , 'end_time'    , None) :
        retval['end_time'] = event_header.timestamp
    if not getattr(retval , 'next_binlog' , None) :
        idx =  mysql_binlog.rindex('.')
        _id =  int(mysql_binlog[idx+1:] ) + 1
        retval['next_binlog'] =  mysql_binlog[:idx] + ('.%06d' % _id )
    return retval


def _mkdir(path):
    if not os.path.exists(path):
        try:
            os.system('mkdir -p %s' %path)
            return 1
        except Exception,e:
            print e
            return -2
    return 1
def backup():
    """backup method for running full and incremental mysql backups"""
    backup_option_found = False
    for o, a in options:
        if o in ('-f', '--full'):
            backup_option_found = True
            message = 'Running full backup...'
            logAndPrint(message, 'info')

            # run the full backup method
            _backup_full()
            break
        elif o in('-i', '--incremental'):
            backup_option_found = True
            message = 'Running incremental backup...'
            logAndPrint(message, 'info')

            # run the incremental backup method
            _backup_incremental()
            break

    if not backup_option_found:
        message = 'FATAL: No backup option was passed in. Full or incremental flag is required. Backup terminating...'

        logAndPrint(message, 'error', True, True)

def _exec_command(command):
    s,r = commands.getstatusoutput(command)
    if s == 0:
        return s,r
    else:
        logAndPrint(r,'error',True,True)

def _backup_full():
    conf = get_backup_conn_info()
    result['backup_type'] = 'mysqldump'
    result['begin_backup_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    result['token'] = token
    message = 'Full backup in progress...'
    logAndPrint(message, 'info')

    # check if the full directory is set in config file and attempt to enter it
    backup_base_path = config.get('Backup', 'backup_base_path')
    if not backup_base_path:
        message = '`backup_base_path` is required to be set in config.cfg. Backup terminiating...'
        result['error'] = message
        push_data(result)
        logAndPrint(message, 'error', True, True)
    """full backup"""


    db_host = conf['ip']
    db_port = int(conf['port'])

    now = datetime.today()
    date = now.strftime('%Y%m%d')
    dic_date = now.strftime('%Y-%m-%d')
    dateandtime = now.strftime('%Y%m%d_%H%M')
    file_prefix = ''.join([i.zfill(3) for i in db_host.split('.')])+'_'+str(db_port)

    database = config.get('Backup', 'database')
    ip_port = ''.join([i.zfill(3) for i in db_host.split('.')])+'_'+str(db_port)
    result['ip'] = db_host
    result['port'] = db_port
    for o, a in options:
        if '--all-databases' == o:
            database = o
            full_path = '{backup_base_path}{ip_port}/mysqldump/all/{dic_date}'.format(backup_base_path=backup_base_path,
                                                                             ip_port=ip_port,
                                                                             dic_date = dic_date)
            test_file = '%s_all_dump_%s*' % (file_prefix, date)
            break
        elif '--database' == o:
            database = '--databases ' + a
            full_path = '{backup_base_path}{ip_port}/mysqldump/{dbs}/{dic_date}'.format(ip_port=ip_port,
                                                                               backup_base_path=backup_base_path,
                                                                               dbs='_'.join(filter(lambda x:len(x)>0,a.split(' '))),
                                                                               dic_date = dic_date
                                                                               )
            test_file = '%s_%s_dump_%s*' % (file_prefix, '_'.join(filter(lambda x:len(x)>0,a.split(' '))),date)
            break
    if database == '':
        database = '-A'
        full_path = '{backup_base_path}{ip_port}/mysqldump/all/{dic_date}'.format(ip_port=ip_port,
                                                                         backup_base_path=backup_base_path,
                                                                         dic_date=dic_date
                                                                         )
        test_file = '%s_all_dump_%s*' % (file_prefix, date)
    result['database'] = database
    try:
        _mkdir(full_path)
        os.chdir(full_path)
        logger.info('Changing directories... (%s)' % (full_path))
    except Exception, e:
        message = 'Directory does not exist. Backup terminating...'
        result['error'] = message
        push_data(result)
        logAndPrint(message, 'error', True, True)

    # setup the date and time and prepare to check for the existence of an already-run full backup

    
    # check if a full backup has been run for today
    if manual is False:
        if glob.glob(test_file):
            message = 'Full backup for today already exists. Backup terminating...'
            result['error'] = message
            push_data(result)
            logAndPrint(message, 'error', True, True)

    
    # prepare to run the full back up
    file_name = '%s%s' % (test_file[:-9], dateandtime)

    # logAndPrint('Preparing binary logs...', 'info')

    # this checks the bin-log directory and puts the output into a file.
    # we do this because we need to keep track of the last bin-log
    # available before we flush them with --flush-logs.
    # this will let us easily grab the bin-logs created after a full backup
    # to be used with incremental backups.
    ls_command = "ls -l --time-style=long-iso %s |grep %s. |  grep -v 'index' |awk '{print $8}' > bin_logs" \
            % (config.get('Backup', 'bin_log_path'),
               config.get('Backup', 'bin_log_name'))
    _exec_command(ls_command)
    last_line = file('bin_logs', "r").readlines()[-1]
    _exec_command('rm -f bin_log_info')
    _exec_command('touch bin_log_info')


    file('bin_log_info', 'w').write('before:' + last_line)

    message = 'Running mysqldump and creating File: %s' % (file_name)
    logAndPrint(message, 'info')



    backup_command = 'mysqldump %s -B -R --single-transaction --master-data=2 ' \
                     '--flush-logs -h%s -P%s -u%s --password=%s --result-file=%s.sql' % (
                        database, #config.get('Backup', 'database'),
                        db_host,
                        db_port,
                        conf['user'],
                        conf['password'],
                        file_name
                 )
    #os.system(backup_command)
    result['command'] = backup_command.replace(conf['password'],'######')
    result['backup_path'] = full_path+'/'
    backup_command = shlex.split(backup_command)
    process = subprocess.Popen(backup_command, stderr=subprocess.PIPE)
    
    # Set the stderr (if any) in p_out
    p_out = process.communicate()

    # Check for erorrs in the output. Error will not be None and 
    # will be longer than ''
    # 
    # we completely ignore stdout since it's being piped into
    # a file using the mysqldump --result-file flag.
    for v in p_out:
        if v is not None and v != 'mysqldump: [Warning] Using a password on the command line interface can be insecure.\n':
            result['backup_status'] = -1
            os.system('rm -f %s.sql' % (file_name))
            message = 'Backup encountered a fatal error from MySQL. Exiting...'
            logAndPrint(message, 'error')
            logAndPrint(v, 'error', exit=True)

    message = 'Full backup created successfully!'
    logAndPrint(message, 'info')
    result['backup_status'] = 1

    if config.get('Encryption', 'enabled')is not None and \
    config.get('Encryption', 'enabled') == 'true':

        logAndPrint('Encryption enabled...', 'info')
        logAndPrint('Encrypting and compressing backup...', 'info')

        encryption_command = 'gpg --always-trust -r %s --output %s.gpg --encrypt %s.sql' \
                % (config.get('Encryption', 'key_name'), file_name, file_name)
        logAndPrint('running: %s' % encryption_command, 'info')

        encryption_command = shlex.split(encryption_command)
        process = subprocess.Popen(encryption_command, stderr=subprocess.PIPE)
        p_out = process.communicate()

        # Check for erorrs in the output. Error will not be None and 
        # will be longer than ''
        # 
        # we completely ignore stdout since it's being piped into
        # a file using the mysqldump --result-file flag.
        for v in p_out:
            if v is not None and v != '':
                os.system('rm -f %s.sql' % (file_name))
                message = 'Backup encountered a fatal error when encrypting with GPG. Exiting...'
                logAndPrint(message, 'error')
                logAndPrint(v, 'error', exit=True)

        #os.system(encryption_command)
        logAndPrint('removing unencrypted sql file...(%s.sql)' \
                % (file_name), 'info')
        os.system('rm -rf %s.sql' % file_name)

    else:
        logAndPrint('Compressing backup...', 'info')
        change_master = 'grep -e  "-- CHANGE MASTER TO MASTER_LOG_FILE" {logfile}.sql'.format(logfile=file_name)
        status, data = commands.getstatusoutput(change_master)
        if status == 0:
            result['change_master_to'] = data

        compress_command = 'gzip %s.sql' % (file_name)
        os.system(compress_command)
        md5= getBigFileMD5('%s.sql.gz' % file_name)
        result['md5'] = md5
        result['backup_file'] = '%s.sql.gz' % file_name
        result['backup_status'] = 2
        result['end_backup_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result['size'] = os.path.getsize('%s.sql.gz' % file_name)
        logAndPrint('File compression completed...', 'info')
        push_data(result)

    
def _backup_incremental():

    result = {}
    result['backup_type'] = 'binlog'
    result['instance_id'] = instance_id
    result['token'] = token
    try:
        conf = get_backup_conn_info()
        result['ip'] = conf['ip']
        result['port'] = conf['port']
        """incremental backup"""
        logAndPrint('Incremental backup in progress...', 'info')
        backup_base_path = config.get('Backup', 'backup_base_path')
        if not backup_base_path:
            message = '`backup_base_path` is required to be set in config.cfg. Backup terminiating...'
            logAndPrint(message, 'error', True, True)
        """full backup"""
        now = datetime.today()
        date = now.strftime('%Y%m%d')
        dateandtime = now.strftime('%Y%m%d_%H%M')
        file_prefix = ''.join([i.zfill(3) for i in conf['ip'].split('.')]) + '_' + conf['port']

        database = config.get('Backup', 'database')
        ip_port = ''.join([i.zfill(3) for i in conf['ip'].split('.')]) + '_' + conf['port']
        # for o, a in options:
        #
        binlog_path = '{backup_base_path}{ip_port}/binlog/'.format(ip_port=ip_port, backup_base_path=backup_base_path)
        test_file = '%s_%s*' % (file_prefix, date)



        try:
            _mkdir(binlog_path)
            os.chdir(binlog_path)
            logger.info('Changing directories... (%s)' % (binlog_path))
        except Exception, e:
            message = 'Directory does not exist. Backup terminating...'
            logAndPrint(message, 'error', True, True)

        # check for the existence of a full backup for today
        # full_backup_test = test_file
        # if not glob.glob(full_backup_test):
        #     message = 'There was no full backup run for today. Run the application with --full, then run incrementals after that'
        #     logAndPrint(message, 'error', True, True)

        # relist binary logs
        # os.system('rm -rf bin_logs')
        ls_command = "ls -l --time-style=long-iso %s |grep %s.0 | awk '{print $8}' > tmp_binlogs" % (
            config.get('Backup', 'bin_log_path'),
            config.get('Backup', 'bin_log_name')
        )
        _exec_command(ls_command)
        if not os.path.isfile('binlog_backuped_info'):
            _exec_command('>binlog_backuped_info')

        binlog_backuped = file('binlog_backuped_info', "r").readlines()

        # add end to bin_log_info
        # file('binlog_backuped_info', 'a').write('last:' + last_line)

        bin_log_info = file('tmp_binlogs', 'r').readlines()

        binlog_not_backup = []
        for line in bin_log_info:
            t_line = line.replace('\n','')
            if t_line not in [x.split(' ')[0] for x in binlog_backuped]:
                binlog_not_backup.append(t_line)




        #flush the logs, update bin_log_info and copy the binary log files over
        logAndPrint('Flushing binary logs...', 'info')
        _exec_command('mysql -h%s -P%s -u%s --password=%s -e "flush logs;"' %
            (conf['ip'],conf['port']
                ,conf['user'],conf['password']))
        # change directories
        inc_path = os.path.dirname(binlog_path)


        try:
            _mkdir(inc_path)
            os.chdir(inc_path)
            logger.info('Changing directories... (%s)' % (inc_path))
        except Exception, e:
            logAndPrint('Directory does not exist. Backup terminating...', 'error', True, True)



        # start copying
        logger.info('Copying binary logs...')
        if not quiet:
            print 'Copying binary logs...'

        for i in binlog_not_backup:
            begin_backup_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_file = '%s%s' % (config.get('Backup', 'bin_log_path'), i)
            os.system('cp %s .' %(log_file))
            info = get_info('{inc_path}/{i}'.format(inc_path=inc_path,i=i))
            # print info
            logAndPrint('cp {log_file} {inc_path}'.format(log_file=log_file, inc_path=inc_path), 'info')
            # start compressing...
            logAndPrint('Compressing incremental backup...', 'info')
            compress_command = 'gzip %s' % (i)
            status2, output2 = commands.getstatusoutput(compress_command)
            if status2 == 0:
                end_backup_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                logAndPrint('Compressing backup completed successfully!', 'info')
                file('binlog_backuped_info', 'a').write('{binlog_file} 1 0\n'.format(binlog_file=i))
                result['binlog_file'] = info['cur_binlog']
                result['start_pos'] =info['start_pos']
                result['end_pos'] = info['end_pos']
                result['start_time'] = info['start_time']
                result['end_time'] = info['end_time']
                result['begin_backup_time'] = begin_backup_date
                result['end_backup_time'] = end_backup_date
                result['backup_status'] = 2
                result['backup_path'] = inc_path+'/'
                result['backup_file'] = i + '.gz'
                md5 = getBigFileMD5('%s.gz' % i)
                result['md5'] = md5
                result['size'] = os.path.getsize('%s.gz' % i)
                push_data(result)

    except Exception,e:
        result['error'] = e
        push_data(result)


    
def restore():
    """restore method"""
    logAndPrint('Restore needs confirmation...', 'info')
    print "WARNING: You have chosen to restore the database. This will destroy your current instance and replace it with the given back up."
    answer = raw_input('Are you sure? yes/no ')
    logAndPrint('"%s" given as the answer' % (answer), 'info', False)
    if answer != 'yes':
        logAndPrint('User wanted to abort database restore. Program exiting...', 'info', True, True)

    """for o,a in options:

    if not '--time' in options or not '--date' in options:
        logger.error('The restore option needs --time= and --date flags. Restore terminating...')
        if not quiet:
            print 'The restore option needs --time= and --date flags. Restore terminating...'

        sys.exit(2)
    logger.info('Restoring database...')"""

    extension = '.sql.gz'
    if config.get('Encryption', 'enabled') == 'true':
        extension = '.gpg'

    for o,a in options:
        if '--time' in o:
            _time = a

    for o,a in options:
        if '--date' in o:
            _date = a

    #_time = options['time']
    #_date = options['date']

    # change directories

    try:
        os.chdir(config.get('Backup', 'full_path'))
        logAndPrint('Changing directories... (%s)' % (config.get('Backup', 'full_path')), 'info')
    except Exception, e:
        logAndPrint('FATAL: Directory does not exist. Backup terminating...', 'error', True, True)

    for o, a in options:
        if '--all-databases' == o:
            database = o
            full_path = '{backup_base_path}/{ip_port}/mysqldump/all/{dic_date}'.format(
                backup_base_path=backup_base_path,
                ip_port=ip_port,
                dic_date=dic_date)
            test_file = '%s_all_dump_%s*' % (file_prefix, date)
            break
        elif '--database' == o:
            database = '--databases ' + a
            full_path = '{backup_base_path}/{ip_port}/mysqldump/{dbs}/{dic_date}'.format(ip_port=ip_port,
                                                                                         backup_base_path=backup_base_path,
                                                                                         dbs='_'.join(filter(
                                                                                             lambda x: len(x) > 0,
                                                                                             a.split(' '))),
                                                                                         dic_date=dic_date
                                                                                         )
            test_file = '%s_%s_dump_%s*' % (file_prefix, '_'.join(filter(lambda x: len(x) > 0, a.split(' '))), date)
            break
    if database == '':
        database = '-A'
        full_path = '{backup_base_path}/{ip_port}/mysqldump/all/{dic_date}'.format(ip_port=ip_port,
                                                                                   backup_base_path=backup_base_path,
                                                                                   dic_date=dic_date
                                                                                   )
        test_file = '%s_all_dump_%s*' % (file_prefix, date)

    full_backup = glob.glob('%sfull_%s*' % (config.get('Backup', 'file_prefix'), str(_date)))

    if len(full_backup) < 1:
        message = 'FATAL: Looks like there was no full backup run for this date. Restore terminating...'
        logAndPrint(message, 'error', True, True)

    if len(full_backup) > 1:
        message = 'FATAL: Looks like there is more than one full backup for this date in %s.' % \
            (config.get('Backup', 'full_path'))
        logAndPrint(message, 'error', True, True)

    full_output = full_backup[0].split('.')[0] + '.sql'

    decrypt = 'gpg --quiet --passphrase-file %s --output %s%s --decrypt %s' % \
        (config.get('Encryption', 'passphrase_file'),
         config.get('Main', 'tmp'),
         full_output,
         full_backup[0])

    decrypt = shlex.split(decrypt)
    
    logAndPrint('Decrypting full and incremental backup files...','info')
    #os.system(decrypt)
    process = subprocess.Popen(decrypt, stderr=subprocess.PIPE)
    p_out = process.communicate()

    for v in p_out:
        if v is not None and v != '':
            logAndPrint('Backup encountered a fatal error when dencrypting with GPG. Exiting...', 'error')
            logAndPrint(v, 'error', exit=True)

    if config.get('Backup', 'inc_path'):
        try:
            os.chdir(config.get('Backup', 'inc_path'))
            logAndPrint('Changing directories... (%s)' % (config.get('Backup', 'inc_path')), 'info')
        except Exception, e:
            logAndPrint('FATAL: Directory does not exist. Backup terminating...', 'error', True, True)

    inc_back_name = '%sinc_%s_' % (config.get('Backup', 'file_prefix'), str(_date))

    # glob for inc files
    inc_backs = glob.glob(inc_back_name + '*')

    decrypt_incs = []

    # loop for a crap ton and check if the file exists in the list
    # there is most likely a more efficient way of doing this...
    for inc in inc_backs:
        inc_time = inc.split('.')[0].split('_')[3]
        if inc_time <= _time:
            decrypt_incs.append(inc)

    decrypt_incs.sort()
    
    inc_outputs = []
    for inc in decrypt_incs:
        out = config.get('Main', 'tmp') + inc.split('.')[0] + '.sql'
        decrypt = 'gpg --passphrase-file %s --output %s --decrypt %s' % \
            (config.get('Encryption', 'passphrase_file'),
             out,
             inc)
        os.system(decrypt)
        inc_outputs.append(out)

    build_me = 'cat %s%s %s > %stemp_restore.sql' % ( \
            config.get('Main', 'tmp'),
            full_output,
            ' '.join(inc_outputs),
            config.get('Main', 'tmp'))
    os.system(build_me)

    database = config.get('Backup', 'database')
    for o,a in options:
        if '--all-databases' == o:
            database = ''
            break
        elif '--database' == o:
            database = '--database=%s' % (a)
            break

    start_flush = 'mysql --password=%s -e "FLUSH LOGS;"' % \
            (config.get('Backup', 'password'))
    start_flush = shlex.split(start_flush)

    process = subprocess.Popen(start_flush, stdout=subprocess.PIPE)
    p_out = process.communicate()

    for v in p_out:
        if v is not None and v !='':
            message = 'Backup encountered an error when accessing MySQL. Backup Exiting...'
            logAndPrint(message, 'error')
            logAndPrint(v, 'error', exit=True)

    #os.system(start_flush)

    ls_command = "ls -l --time-style=long-iso %s |grep %s.0 | awk '{print $8}' > ignore_bin_log" % \
        (config.get('Backup', 'bin_log_path'),
        config.get('Backup', 'bin_log_name'))
    os.system(ls_command)
    first_log = file('ignore_bin_log', "r").readlines()[-1]
    
    """
    logAndPrint('Dropping database...', 'info')
    drop_db_command = 'mysql --password=%s -e "drop database %s"' % \
            (config.get('Backup', 'password'),
             config.get('Backup', 'database'))
    drop_db_command = shlex.split(drop_db_command)
    
    process = subprocess.Popen(drop_db_command, stderr=subprocess.PIPE)
    p_out = process.communicate()
    
    for v in p_out:
        if v is not None and v != '':
            message = 'Backup encountered an error when accessing MySQL. Backup Exiting...'
            logAndPrint(message, 'error')
            logAndPrint(v, 'error', exit=True)
    #os.system(drop_db_command)
    """

    """
    logAndPrint('Restoring database from backup...', 'info')
    create_db_command = 'mysql --password=%s -e "create database %s"' % \
            (config.get('Backup', 'password'),
             config.get('Backup', 'database'))
    create_db_command = shlex.split(create_db_command)

    process = subprocess.Popen(create_db_command, stderr=subprocess.PIPE)
    p_out = process.communicate()

    for v in p_out:
        message = 'Backup encountered an error when accessing MySQL. Backup Exiting...'
        logAndPrint(message, 'error')
        logAndPrint(v, 'error', exit=True)
    #os.system(create_db_command)
    """

    logAndPrint('Restoring database from backup...', 'info')

    cat_full_command = 'cat %stemp_restore.sql' % (config.get('Main', 'tmp'))
    cat_full_command = shlex.split(cat_full_command)
    
    # The output of this process will be piped into the restore process below.
    # This is done because subprocess separates the processes and how
    # piping actually works.
    cat_process = subprocess.Popen(cat_full_command, stdout=subprocess.PIPE)

    restore_command = 'mysql %s --password=%s' % \
            (database, #config.get('Backup', 'database'),
             config.get('Backup', 'password'))
    restore_command = shlex.split(restore_command)

    process = subprocess.Popen(restore_command, stdin=cat_process.stdout, stderr=subprocess.PIPE)
    p_out = process.communicate()

    for v in p_out:
        if v is not None and v != '':
            message = 'Backup encountered an error when accessing MySQL. Backup Exiting...'
            logAndPrint(message, 'error')
            logAndPrint(v, 'error', exit=True)

    #os.system(restore_command)

    ls_command = "ls -l --time-style=long-iso %s |grep %s.0 | awk '{print $8}' > ignore_bin_log" % \
        (config.get('Backup', 'bin_log_path'),
        config.get('Backup', 'bin_log_name'))
    os.system(ls_command)
    last_log = file('ignore_bin_log', "r").readlines()[-1]

    end_flush = 'mysql --password=%s -e "FLUSH LOGS;"' % \
            (config.get('Backup', 'password'))
    end_flush = shlex.split(end_flush)

    process = subprocess.Popen(end_flush, stderr=subprocess.PIPE)
    p_out = process.communicate()

    for v in p_out:
        if v is not None and v != '':
            message = 'Backup encountered an error when accessing MySQL. Backup Exiting...'
            logAndPrint(message, 'error')
            logAndPrint(v, 'error', exit=True)

    #os.system(end_flush)

    first_log = first_log.split('.')[1]
    last_log = last_log.split('.')[1]

    logs = []
    for i in range(int(first_log), int(last_log) + 1):
        logs.append('%s%s.%06d' % \
                (config.get('Backup', 'bin_log_path'),
                config.get('Backup', 'bin_log_name'),
                i))

    try:
        os.chdir(config.get('Backup', 'full_path'))
    except:
        logAndPrint('Director does not exist', 'error', True, True)
    
    import pickle

    try:
        f = file('ignore_logs', 'rb')
        f_logs = pickle.load(f)
        os.remove('ignore_logs')
        for log in f_logs:
            logs.append(log)
        f = file('ignore_logs', 'wb')
        pickle.dump(logs, f)
        f.close()
    except IOError:
        f = file('ignore_logs', 'wb')
        pickle.dump(logs, f)
        f.close()

    try:
        os.chdir(config.get('Backup', 'inc_path'))
    except:
        logAndPrint('Directory does not exist', 'error', True, True)

    logAndPrint('Cleaning up temp files...', 'info')

    cleanup_command = 'rm -f %s%s %s' % \
            (config.get('Main', 'tmp'),
             full_output,
             ' '.join(inc_outputs))

    os.system(cleanup_command)

    logAndPrint('Restore completed!', 'info')

def fetch():
    """fetch method"""
    logAndPrint('Fetching database backup from remote server...')
    for o,a in options:
        if o in ('--time'):
            _time = a
            time_found = True
            break

    for o,a in options:
        if o in ('--date'):
            _date = a
            date_found = True
            break

    if not time_found or not date_found:
        message = '--date and --time flags are required when trying to fetch a database backup'
        logAndPrint(message, 'error', True, True)

    full_file = '%sfull_%s_*' % (config.get('Backup', 'file_prefix'), _date)
    inc_file = '%sinc_%s_*' % (config.get('Backup', 'file_prefix'), _date)

    full_list_command = 'ssh %s "ls -l --time-style=long-iso %s | grep %s | awk \'{print $8}\'"' % \
            (config.get('Fetch', 'connection_string'),
             config.get('Fetch', 'remote_full_path'),
             full_file)
    f = os.popen(full_list_command)
    full_backup = [l.strip('\n').split(' ')[7] for l in f]
    print full_backup

    if len(full_backup) < 1:
        message = 'It doesn\'t look like the remote system has a full backup for the given date (%s)' % \
                (_date)
        logAndPrint(message, 'error', True, True)

    if len(full_backup) > 1:
        message = 'It looks like there is more than one backup for the given date (%s)' % (_date)
        logAndPrint(message, 'error', True, True)
 
    full_backup = full_backup[0]

    inc_list_command = 'ssh %s "ls -l --time-style=long-iso %s | grep %s | awk \'{print $8}\'"' % \
            (config.get('Fetch', 'connection_string'),
             config.get('Fetch', 'remote_inc_path'),
             inc_file)
    f = os.popen(inc_list_command)

    inc_backups = []
    later_backups = []
    for l in f.readlines():
        l = l.strip('\n').replace('  ', ' ').replace('  ', ' ')
        l = l.split(' ')[7]
        if int(l.split('.')[0].split('_')[3]) < int(_time):
            inc_backups.append(config.get('Fetch', 'remote_inc_path') + l)
            later_backups.append(l)

    scp_command = 'scp %s:"%s%s %s" %s' % (\
            config.get('Fetch', 'connection_string'),
            config.get('Fetch', 'remote_full_path'),
            full_backup,
            ' '.join(inc_backups),
            config.get('Main', 'tmp'))
    os.system(scp_command)

    # decompression or decryption
    if config.get('Encryption', 'enabled') == 'true':
        #decrypt
        tmp = config.get('Main', 'tmp')
        full_decrypt_command = 'gpg --passphrase-file %s --output %s --decrypt %s' % \
            (config.get('Encryption', 'passphrase_file'),
             tmp + full_backup.split('.')[0] + '.sql',
             tmp + full_backup)
        os.system(full_decrypt_command)

        later_backups.sort()
        for inc in later_backups:
            inc_decrypt_command = 'gpg --passphrase-file %s --output %s --decrypt %s' % \
                (config.get('Encryption', 'passphrase_file'),
                 tmp + inc.split('.')[0] + '.sql',
                 tmp + inc)
            os.system(inc_decrypt_command)

        cat_command = 'cat %s%s %s > %s%s_backup.sql' % \
            (config.get('Main', 'tmp'),
             full_backup.split('.')[0] + '.sql',
             [tmp + inc.split('.')[0] + '.sql' for inc in inc_backups],
             config.get('Fetch', 'local_save_path'),
             config.get('Backup', 'file_prefix'))

        os.system(cat_command)
    else:
        tmp = config.get('Main', 'tmp')
        full_decompress = 'gzip -d %s%s' % (tmp, full_backup)
        os.system(full_decompress)
        incs = []
        for inc in later_backups:
            inc_decompress = 'gzip -d %s%s' & (tmp, inc)
            incs = '%s%s' % (tmp, inc)
            os.system(inc_decompress)

        cat_command = 'cat %s%s %s > %s%s_backup.sql' % \
                (tmp,
                 full_backup.split('.'),
                 ' '.join([inc.strip('.gz') for inc in incs]),
                 config.get('Fetch', 'local_save_path'),
                 config.get('Backup', 'file_prefix'))

        os.system(cat_command)

def logAndPrint(message, type='info', print_message=True, exit=False):
    if type == 'info':
        logger.info(message)
    elif type == 'warn':
        logger.warn(message)
    elif type == 'error':
        logger.error(message)
    else:
        logger.info(message)

    if not quiet and print_message:
        print message

    if exit:
        sys.exit()

if __name__=='__main__':

    main()
    _post_failed()
