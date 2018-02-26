#!/usr/bin/python
import os
import time
import struct
import sys

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
    BINLOG_HEADER = '\\xfe\\x62\\x69\\x6e'
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
        if reader.char() ==  '\\x00' :
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

def get_info(mysql_binlog) :

    reader = BinFileReader(mysql_binlog)
    binlog_header = reader.chars(Constant.BINLOG_HEADER_LEN)
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
                retval['start_time'] = event_header.timestamp
            elif event_header.type_code == EventType.ROTATE_EVENT :
                event_body = RotateEvent(reader , event_header)
                retval['end_time'] = event_header.timestamp
                retval['next_binlog'] = event_body.next_binlog
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

    if not getattr(retval , 'end_time'    , None) :
        retval['end_time'] = event_header.timestamp
    if not getattr(retval , 'next_binlog' , None) :
        idx =  mysql_binlog.rindex('.')
        _id =  int(mysql_binlog[idx+1:] ) + 1
        retval['next_binlog'] =  mysql_binlog[:idx] + ('.%06d' % _id )
    return retval

if __name__ == '__main__' :
    if len(sys.argv) == 2 :
        mysql_binlog = sys.argv[1]
    else :
        print 'Usage : \\n./readbinlog.py <mysql-bin-log>'
        exit()

    info = get_info(mysql_binlog)
    for (k ,v) in info.items() :
        print '%s = %s' % (k , v)
