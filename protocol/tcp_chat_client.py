# -*- coding: utf-8 -*-
from c2w.main.lossy_transport import LossyTransport
from c2w.main.client_proxy import c2wClientProxy
from c2w.main.client_model import c2wClientModel
from c2w.main.controller import c2wController
from twisted.internet import reactor
import core
import logging
import c2w.main.constants
import struct
import ctypes
from c2w.main.constants import ROOM_IDS
from threading import Timer
import time
from twisted.internet.protocol import Protocol

#version 53

logging.basicConfig()
moduleLogger = logging.getLogger('c2w.protocol.tcp_chat_client_protocol')


class c2wTcpChatClientProtocol(Protocol):

	def __init__(self, clientProxy, serverAddress, serverPort):
		"""
		:param clientProxy: The clientProxy, which the protocol must use
			to interact with the Graphical User Interface.
		:param serverAddress: The IP address (or the name) of the c2w server,
			given by the user.
		:param serverPort: The port number used by the c2w server,
			given by the user.

		Class implementing the UDP version of the client protocol.

		.. note::
			You must write the implementation of this class.

		Each instance must have at least the following attribute:

		.. attribute:: clientProxy

			The clientProxy, which the protocol must use
			to interact with the Graphical User Interface.

		.. attribute:: serverAddress

			The IP address (or the name) of the c2w server.

		.. attribute:: serverPort

			The port number used by the c2w server.

		.. note::
			You must add attributes and methods to this class in order
			to have a working and complete implementation of the c2w
			protocol.
		"""
		self.serverAddress = serverAddress
		self.serverPort = serverPort
		self.clientProxy = clientProxy
		self.idcall = None
		self.status = None
		self.userID = None
		self.seq_num =0
		self.expected_seq_num=0
		self.listOfUserName =[]
		self.listOfUserId = ()
		self.userNames=[]
		self.listOfTitles=[]
		self.listOfMovieId=[]
		self.usernamesUpdated=0
		self.listOfMovies=[]
		self.NbrMovie = None
		self.NbrUser = None
		self.current_movie_room_id=None
		self.requested_movie_room_id=None
		self.type_last_message=None
		self.state= False
       
	def sendLoginRequestOIE(self, userName):
		"""
		:param string userName: The user name that the user has typed.

		The client proxy calls this function when the user clicks on
		the login button.
		"""
		if type(userName)==str :		
			moduleLogger.debug('loginRequest called with username=%s', userName)
			TYPE = '0001'
			self.type_last_message=int(TYPE,2)
			A = '0'
			R = '0'
			ACK_NUM = 0
			DATA=userName
			buffer_length= 6 + len(DATA)
			buf= ctypes.create_string_buffer(buffer_length)
			fourbyte= (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(str(ACK_NUM),2) << 13) + (int(str(self.seq_num),2) << 0)
			struct.pack_into('>IH'+str(len(DATA))+'s',buf,0,fourbyte, buffer_length,DATA)
			self.transport.write(buf.raw)
			self.idcall = reactor.callLater(3.0,self.sendLoginRequestOIE,[userName])   

		else :
			if type(userName)==list :
				if not(userName==[]):
					first_username=userName[0]
					self.sendLoginRequestOIE(first_username)
					userName.pop(0)
					self.sendLoginRequestOIE(userName)
				else:
					return
	def sendChatMessageOIE(self, message):
		"""
		:param message: The text of the chat message.
		:type message: string

		Called by the client proxy when the user has decided to send
		a chat message

		.. note::
		   This is the only function handling chat messages, irrespective
		   of the room where the user is.  Therefore it is up to the
		   c2wChatClientProctocol or to the server to make sure that this
		   message is handled properly, i.e., it is shown only by the
		   client(s) who are in the same room.
		"""

		ACK_NUM = 0;
		self.send_Public_Message(ACK_NUM,self.seq_num,self.userID,message)
		self.idcall = reactor.callLater(3.0,self.sendChatMessageOIE,[message])
                    
	def sendJoinRoomRequestOIE(self, roomName):
		"""
		:param roomName: The room name (or movie title.)

		Called by the client proxy  when the user
		has clicked on the watch button or the leave button,
		indicating that she/he wants to change room.

		.. warning:
			The controller sets roomName to
			c2w.main.constants.ROOM_IDS.MAIN_ROOM when the user
			wants to go back to the main room.
		"""
		ACK_NUM = 0;
		if(roomName == ROOM_IDS.MAIN_ROOM):
			self.requested_movie_room_id= 0
			self.status = 1
			self.send_MainRoom_Request(ACK_NUM,self.seq_num,self.userID)
		else:			
			indexOfRoom = self.listOfTitles.index(roomName)
			self.status = 0
			self.MovieName = roomName			
			movieId = self.listOfMovieId[indexOfRoom]
			self.send_MovieRoom_Request(ACK_NUM,self.seq_num,self.userID,movieId)
		self.idcall = reactor.callLater(3.0,self.sendJoinRoomRequestOIE,[roomName])	
        

	def sendLeaveSystemRequestOIE(self):
		"""
		Called by the client proxy  when the user
		has clicked on the leave button in the main room.
		"""
		ACK_NUM = 0
		self.disconnect(ACK_NUM,self.seq_num,self.userID)
		self.idcall = reactor.callLater(3.0,self.sendLeaveSystemRequestOIE)
				        
	def dataReceived(self, data):
		"""
		:param data: The message received from the server
		:type data: A string of indeterminate length

		Twisted calls this method whenever new data is received on this
		connection.
		"""
		first_message = core.split_flow_message_tcp(data)[0]
		while(len(first_message) > 0):
			j=struct.unpack_from('!I',first_message[0:])[0]
			if(j==12):
				l=data[4:].split('.')			
				for item in l:
					if not(item==''):
						self.listOfMovieId.append(int(item))
			
			else:
				dataParsed = core.parseReceivedData(first_message)
				TYPE = dataParsed[0]
				data_extracted = dataParsed[6]					
				if (TYPE == 2  ):
					if(self.state == False):
						self.AnalyseUserMessage(data_extracted)						
						self.sendAck(1)
						self.seq_num +=1
						self.state = True
					else:
							if (self.status == 1):
								self.AnalyseUserMessage(data_extracted)
								self.clientProxy.setUserListONE(self.listOfUserName) 
							else:
								self.AnalyseUserMessageForMovieRoom(self.MovieName,data_extracted)
								self.clientProxy.setUserListONE(self.listOfUserName) 
				if (TYPE == 3):

					self.AnalyseMovieMessage(data_extracted)
					self.clientProxy.initCompleteONE(self.listOfUserName,self.listOfMovies)				
					self.sendAck(dataParsed[5])
				if (TYPE == 4):
					PublicMessage_infos= core.extract_public_message(data_extracted)
					userId = PublicMessage_infos[0]
					indiceUser = self.listOfUserId.index(userId)
					username=self.listOfUserName[indiceUser][0]
					self.clientProxy.chatMessageReceivedONE(username,PublicMessage_infos[2])						
					self.sendAck(dataParsed[5])
				if (TYPE == 5):
					PrivateMessage_infos = core.extract_private_message(data_extracted)
					userId = PrivateMessage_infos[0]
					indiceUser = self.listOfUserId.index(userId)
					username=self.listOfUserName[indiceUser][0]
					self.clientProxy.chatMessageReceivedONE(username,PrivateMessage_infos[2])
					self.sendAck(dataParsed[5])
				if (TYPE == 14):
					self.idcall.cancel()
					self.ReceiveLoginResponse(data_extracted)				
					self.sendAck(dataParsed[5])
				if (TYPE == 15):					
					self.idcall.cancel()
					self.seq_num +=1
					if self.type_last_message == 8:
						self.clientProxy.leaveSystemOKONE()						
					elif (self.type_last_message == 6 or self.type_last_message == 7):
						self.current_movie_room_id=self.requested_movie_room_id				
						self.clientProxy.joinRoomOKONE()				
				elif (TYPE == 0):
					self.extract_error(data_extracted)
			data = core.split_flow_message_tcp(data)[1]
			first_message = core.split_flow_message_tcp(data)[0]

        
	def extract_error(self,data):
		Error_num=struct.unpack_from('!B',data)[0]
		if (Error_num==1):
			self.clientProxy.connectionRejectedONE("invalid username") 
		if (Error_num==2):
			self.clientProxy.connectionRejectedONE("Unknown User")
		if (Error_num==3):
			self.clientProxy.connectionRejectedONE("Unknown Movie")
		if (Error_num==4):
			self.clientProxy.connectionRejectedONE("Malformed Message")
    
	def sendAck(self,SEQ_NUM):
		SEQ_NUM=bin(SEQ_NUM)
		TYPE='1111'
		A='1'
		R='0'
		buffer_length= 6 
		buf= ctypes.create_string_buffer(buffer_length)
		fourbyte= (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(str(SEQ_NUM),2) << 13) + (int(str(0),2) << 0)    
		struct.pack_into('>IH',buf,0,fourbyte,buffer_length)
		self.transport.write(buf.raw)    

	def disconnect(self,ACK_NUM,SEQ_NUM,UserId):				
		TYPE='1000'
		A='0'
		R='0'
		buffer_length= 8
		buf= ctypes.create_string_buffer(buffer_length)
		fourbyte= (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(bin(ACK_NUM),2) << 13) + (int(bin(SEQ_NUM),2) << 0)
		Message = (int(bin(UserId),2) << 0) 
		struct.pack_into('>IHH',buf,0,fourbyte,buffer_length,Message)
		self.type_last_message=int(TYPE,2)
		self.transport.write(buf.raw)		
       
	def send_Public_Message(self,ACK_NUM,SEQ_NUM,UserId,MessageText):
		TYPE='0100'
		A='0'
		R='0'
		buffer_length= 14 + len(MessageText)
		buf= ctypes.create_string_buffer(buffer_length)
		fourbyte= (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(bin(ACK_NUM),2) << 13) + (int(bin(SEQ_NUM),2) << 0)
		Message = (UserId << 6*8) + (int(str(0),2) << 0)
		struct.pack_into('>IHQ'+str(len(MessageText))+'s',buf,0,fourbyte,buffer_length,Message, MessageText)
		self.type_last_message=int(TYPE,2)
		self.transport.write(buf.raw)

	def send_Private_Message(self,ACK_NUM,SEQ_NUM,ScrId,DestId,MessageText):
		TYPE='0101'
		A='0'
		R='0'
		buffer_length= 10 + len(MessageText)
		buf= ctypes.create_string_buffer(buffer_length)
		fourbyte= (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(bin(ACK_NUM),2) << 13) + (int(bin(SEQ_NUM),2) << 0)
		Message = (ScrId<< 2*8) + (DestId << 0)
		struct.pack_into('>IHI'+str(len(MessageText))+'s',buf,0,fourbyte,buffer_length,Message, MessageText)
		self.type_last_message=int(TYPE,2)
		self.transport.write(buf.raw)

	def send_MovieRoom_Request(self,ACK_NUM,SEQ_NUM,UserId,MovieId):
		TYPE='0110'
		A='0'
		R='0'     
		buffer_length= 14
		buf= ctypes.create_string_buffer(buffer_length)
		fourbyte= (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(bin(ACK_NUM),2) << 13) + (int(bin(SEQ_NUM),2) << 0)
		eightbyte = (UserId << 48 ) + MovieId
		struct.pack_into('>IHQ',buf,0,fourbyte,buffer_length,eightbyte)
		self.type_last_message=int(TYPE,2)
		self.transport.write(buf.raw)

	def send_MainRoom_Request(self,ACK_NUM,SEQ_NUM,UserId):
		TYPE='0111'
		A='0'
		R='0'
		buffer_length= 8
		buf= ctypes.create_string_buffer(buffer_length)
		fourbyte= (int(TYPE,2) << 28) + (int(A,2) << 27) +(int(R,2) << 26) + (int(bin(ACK_NUM),2) << 13) +(int(bin(SEQ_NUM),2) << 0)		  
		Message = (int(bin(UserId),2) << 0) 
		struct.pack_into('>IHH',buf,0,fourbyte,buffer_length,Message)
		self.type_last_message=int(TYPE,2)
		self.transport.write(buf.raw)

	def ReceiveLoginResponse(self, message):
		self.userID = struct.unpack_from('!H',message)[0]
		self.status = 1				   
 
	def AnalyseMovieMessage(self,data):
		dataParsed = core.extract_movie(data)
		three_tuple=(dataParsed[5],dataParsed[2],dataParsed[3])
		self.listOfTitles.append(dataParsed[5])
		self.listOfMovies.append(three_tuple)
		self.NbrMovie = dataParsed[1]
		dataParsed = dataParsed[0]
		while ( len(dataParsed) > 0):
			dataParsed = core.extract_movie_2(dataParsed)
			three_tuple=(dataParsed[4],dataParsed[1],dataParsed[2])
			self.listOfTitles.append(dataParsed[4])
			self.listOfMovies.append(three_tuple)
			dataParsed = dataParsed[0]	
					        
	def AnalyseUserMessage(self, data):
		self.listOfUserName =[]
		self.listOfUserId = ()
		self.userNames=[]
		dataParsed = core.extract_user(data)
		self.NbrUser = dataParsed[2]
		self.listOfUserId += (dataParsed[5],)		
		self.userNames.append(dataParsed[6])
		if dataParsed[4]==1:
			a=(dataParsed[6],ROOM_IDS.MAIN_ROOM)
		elif dataParsed[4]==0:
			a=(dataParsed[6],ROOM_IDS.MOVIE_ROOM)
		self.listOfUserName.append(a)
		dataParsed = dataParsed[0]
		while ( len(dataParsed) > 3):
			dataParsed = core.extract_user2(dataParsed)
			self.listOfUserId += (dataParsed[3],)		
			if not(dataParsed[4] in self.userNames) : 			
				self.userNames.append(dataParsed[4])
				if dataParsed[2]==1:
					a=(dataParsed[4],ROOM_IDS.MAIN_ROOM)
				elif dataParsed[2]==0:
					a=(dataParsed[4],ROOM_IDS.MOVIE_ROOM)
				self.listOfUserName.append(a)
			dataParsed = dataParsed[0]  
   
	def AnalyseUserMessageForMovieRoom(self,movieName,data):
		self.listOfUserName =[]
		self.listOfUserId = ()
		self.userNames=[]
		dataParsed = core.extract_user(data)
		self.NbrUser = dataParsed[2]
		self.listOfUserId += (dataParsed[5],)		
		self.userNames.append(dataParsed[6])
		a=(dataParsed[6],movieName)
		self.listOfUserName.append(a)
		dataParsed = dataParsed[0]
		while ( len(dataParsed) > 3):
			dataParsed = core.extract_user2(dataParsed)
			self.listOfUserId += (dataParsed[3],)
			if not(dataParsed[4] in self.userNames) : 			
				self.userNames.append(dataParsed[4])
				a=(dataParsed[4],movieName)
				self.listOfUserName.append(a)
			dataParsed = dataParsed[0]
		
