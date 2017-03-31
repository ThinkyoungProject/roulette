#!/usr/bin/env python 
# encoding: utf-8

__author__ = 'hasee'


from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.internet.defer import Deferred, DeferredList, inlineCallbacks, returnValue
from twisted.protocols.policies import TimeoutMixin
from twisted.internet import reactor
from utility import is_receive_complete
import json,socket

class rpc_socket:
    rpc_request_payload_template = '''{"jsonrpc":"2.0","id":"0","method":"%s","params":%s}'''
    def __init__(self):
        self.dataBuf = ""

    def connection_made(self,ip,port):
        self.dataBuf = ""
        self.conn = socket.socket(socket.AF_INET,socket.SOCK_STREAM)      #定义socket类型，网络通信，TCP
        self.conn.connect((ip, port))       #要连接的IP与端口

    def dataReceived(self):
        self.dataBuf = ''

        while True:
            try:
                self.dataBuf = self.dataBuf + self.conn.recv(1024)
                json_rpc, self.dataBuf = self.parseDataBuf(self.dataBuf)
                if json_rpc != '':
                    return json_rpc
            except Exception, ex:
                break

    def rpc_request(self, rpc_method, rpc_args):
        rpc_args_str = '['
        rpc_args_str = rpc_args_str + ','.join(['"' + rpc_arg + '"' for rpc_arg in rpc_args ])
        rpc_args_str = rpc_args_str + ']'
        self.conn.sendall(rpc_socket.rpc_request_payload_template%(rpc_method,rpc_args_str))
        result = self.dataReceived()
        return result

    def close(self):
        self.conn.close()

    def parseDataBuf(self, databuf):
            try:
                flag = 0
                databuf = databuf.lstrip(' \t\n')
                if databuf == '':
                    return '', ''
                if databuf[0] != '{':
                    raise Exception('Json format error')

                for i in range(len(databuf)):
                    if databuf[i] == '{':
                        flag = flag + 1
                    elif databuf[i] == '}':
                        flag = flag - 1

                    if flag == 0:
                        try:
                            json.loads(databuf[0:i+1])
                        except:
                            raise Exception('Json format error')

                        return databuf[0:i+1], databuf[i+1:]

                return '', databuf
            except Exception, ex:
                raise Exception('Json format error')

