# -*- coding: utf-8 -*- #
from twisted.internet.protocol import Protocol
from c2w.main.client_proxy import c2wClientProxy
from c2w.main.client_model import c2wClientModel
from c2w.main.controller import c2wController
from twisted.internet import reactor
from threading import Event
import core
import logging
import c2w.main.constants
import struct
import ctypes

from c2w.main.constants import ROOM_IDS
from threading import Timer
import time

logging.basicConfig()
moduleLogger = logging.getLogger('c2w.protocol.udp_chat_client_protocol')

class Client_common(Protocol):

    def __init__(self, client, clientProxy):
        self.clientProxy = clientProxy
        self.client = client
        
    def sendLoginRequestOIE(self, userName):
		"""
		:param string userName: The user name that the user has typed.

		The client proxy calls this function when the user clicks on
		the login button.
		"""
		if type(userName) == str :		
			moduleLogger.debug('loginRequest called with username=%s', userName)
			
			
			TYPE = 0001
			self.type_last_message = int(str(TYPE),2)
			A = 0
			R = 0
			ACK_NUM = 0
			
			message = construct_message(construct_header(TYPE,A,R,ACK_NUM,self.seq_num, len_data),userName)
			
			self.transport.write(message.raw,(self.serverAddress,self.serverPort))
			  
			self.idcall = reactor.callLater(3.0,self.sendLoginRequestOIE,[userName])
		else :
			if type(userName) == list :
				if not(userName == []):
					first_username = userName[0]
					self.sendLoginRequestOIE(first_username)
					userName.pop(0)
					self.sendLoginRequestOIE(userName)
				else:
					return

    def sendLeaveSystemRequestOIE(self):
        pass

    def sendJoinRoomRequestOIE(self, roomName):
        pass

    def sendChatMessageOIE(self, message):
        pass
