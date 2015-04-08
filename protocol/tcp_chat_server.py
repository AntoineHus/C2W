# -*- coding: utf-8 -*-
from twisted.internet.protocol import Protocol
import logging
import struct
import ctypes
import struct
from c2w.main.movie import *
from c2w.main.user import *
from c2w.main.constants import *
from c2w.main.constants import ROOM_IDS
import core

#version 53
logging.basicConfig()
moduleLogger = logging.getLogger('c2w.protocol.tcp_chat_server_protocol')


class c2wTcpChatServerProtocol(Protocol):

	def __init__(self, serverProxy, clientAddress, clientPort):
		"""
		:param serverProxy: The serverProxy, which the protocol must use
			to interact with the user and movie store (i.e., the list of users
			and movies) in the server.
		:param clientAddress: The IP address (or the name) of the c2w server,
			given by the user.
		:param clientPort: The port number used by the c2w server,
			given by the user.

		Class implementing the TCP version of the client protocol.

		.. note::
			You must write the implementation of this class.

		Each instance must have at least the following attribute:

		.. attribute:: serverProxy

			The serverProxy, which the protocol must use
			to interact with the user and movie store in the server.

		.. attribute:: clientAddress

			The IP address (or the name) of the c2w server.

		.. attribute:: clientPort

			The port number used by the c2w server.

		.. note::
			You must add attributes and methods to this class in order
			to have a working and complete implementation of the c2w
			protocol.

		.. note::
			The IP address and port number of the client are provided
			only for the sake of completeness, you do not need to use
			them, as a TCP connection is already associated with only
			one client.
		"""
		self.clientAddress = clientAddress
		self.clientPort = clientPort
		self.serverProxy = serverProxy
		self.current_client_message = ""
		self.current_message_length = ""
		self.seq_num = 0
		self.length = 0
		self.user = None
		self.ListOfNames_sqNum_hp = []
				

	def dataReceived(self, data):
		"""
		:param data: The message received from the server
		:type data: A string of indeterminate length

		Twisted calls this method whenever new data is received on this
		connection.
		"""
		if(len(data)==1):
			if len(self.current_client_message)<4 :			
				self.current_client_message+=data
			else :
				if len(self.current_message_length)<2 :				
					self.current_message_length+=data
					self.current_client_message+=data
					if (len(self.current_message_length)==2):
						self.length=struct.unpack_from('!H',self.current_message_length)[0]
						if(self.length==6):
							self.dataReceived(self.current_client_message)
							self.current_client_message=""
							self.current_message_length=""								
				else:					 		
					if len(self.current_client_message)<self.length-1:				
						self.current_client_message+=data
					else:
						self.current_client_message+=data
						self.dataReceived(self.current_client_message)
						self.current_client_message=""
						self.current_message_length=""
		else:
			first_message = core.split_flow_message_tcp(data)[0]
			while(len(first_message) > 0):
				message_client = core.parseReceivedData(first_message)
				TYPE=message_client[0]			
				DATA=message_client[6]	
				if (TYPE == 1):				
					username=message_client[6]
					if not(self.serverProxy.userExists(username)):
						User_id=self.serverProxy.addUser(username,ROOM_IDS.MAIN_ROOM,self,None)					
						listOfuser = self.serverProxy.getUserList()
						for user in listOfuser :
							if not(user.userName==username):
								user.userChatInstance.sendUserMessage(user)
						a=(username,0)
						self.ListOfNames_sqNum_hp.append(a)
						self.sendLoginResponse(message_client[4],User_id)
						self.user=self.serverProxy.getUserByName(username)
						self.seq_num+=1											
					else:
						error = 1
						self.sendError(message_client[4],error)

				if (TYPE==6):				
					user_id=struct.unpack_from('!H',DATA[0:])[0]		
					movie_id1=struct.unpack_from('!I',DATA[2:])[0]
					movie_id2=struct.unpack_from('!H',DATA[6:])[0]
					movie_id = (movie_id1 << 2*8) + (movie_id2 << 0)						
					UserName = self.serverProxy.getUserById(user_id).userName			
					MovieName = self.serverProxy.getMovieById(movie_id).movieTitle  
					self.serverProxy.updateUserChatroom(UserName,MovieName)
					list_user=self.serverProxy.getUserList()
					for user in list_user :
						if(user.userChatRoom == ROOM_IDS.MAIN_ROOM):
							user.userChatInstance.sendUserMessage(user)
							user.userChatInstance.seq_num+=1
						elif(user.userChatRoom == MovieName):
							user.userChatInstance.sendUserMessageForMovieRoom(MovieName,user)
							user.userChatInstance.seq_num+=1						
					self.serverProxy.startStreamingMovie(MovieName)	
					self.sendAck(message_client[5])		

				if (TYPE==7):				
					user_id=struct.unpack_from('!H',DATA[0:])[0]
					UserName = self.serverProxy.getUserById(user_id).userName
					self.serverProxy.updateUserChatroom(UserName,ROOM_IDS.MAIN_ROOM)
					list_user=self.serverProxy.getUserList()
					for user in list_user :
						if (user.userChatRoom == ROOM_IDS.MAIN_ROOM):
							user.userChatInstance.sendUserMessage(user)
							user.userChatInstance.seq_num+=1		
						else:
							user.userChatInstance.sendUserMessageForMovieRoom(user.userChatRoom,user)
							user.userChatInstance.seq_num+=1					
					self.sendAck(message_client[5])	

				if (TYPE == 8) :				
					userId = struct.unpack_from('!H',DATA)[0]
					userName = self.serverProxy.getUserById(userId).userName
					self.serverProxy.removeUser(userName)	
					list_user=self.serverProxy.getUserList()
					for user in list_user :
						if not(user.userName==userName):
							user.userChatInstance.sendUserMessage(user)
							user.userChatInstance.seq_num+=1	
					self.sendAck(message_client[5])	

				if(TYPE==15):				
					if(message_client[4]==0):
						self.sendUserMessage(self.user)
						self.seq_num+=1															
					if(message_client[4]==1):
						self.sendMovieMessage(self.user)
						self.seq_num+=1	
					if(message_client[4]==2):
						self.sendMoviesIdlist()				
					else:			
						return	

				if(TYPE == 4):				
					user_id=struct.unpack_from('!H',DATA[0:])[0]
					message = DATA[8:]
					Current_user=self.serverProxy.getUserById(user_id)
					self.sendAck(message_client[5])				
					list_user=self.serverProxy.getUserList()
					for user in list_user :
						if not(user.userName==Current_user.userName) and (user.userChatRoom == Current_user.userChatRoom) :
								seq_num=user.userChatInstance.ListOfNames_sqNum_hp[0][1]
								user.userChatInstance.send_Public_Message(seq_num,user_id,message)	
								user.userChatInstance.seq_num+=1			
		
		  		if(TYPE == 5):
					PrivateMessage_infos = core.extract_private_message(DATA)
					ScrId=PrivateMessage_infos[0]
					CurrentUserName = self.serverProxy.getUserById(ScrId).userName
					DestId=PrivateMessage_infos[1]
					UserNameDest = self.serverProxy.getUserById(DestId).userName
					message= PrivateMessage_infos[2]
					self.sendAck(message_client[5])
					list_user=self.serverProxy.getUserList()
					for user in list_user :
						if user.userChatRoom==ROOM_IDS.MOVIE_ROOM and not(user.userName==CurrentUserName):
							seq_num=user.userChatInstance.ListOfNames_sqNum_hp[0][1]
							user.userChatInstance.send_Private_Message(seq_num,ScrId,DestId,message)
							user.userChatInstance.seq_num+=1
				data = core.split_flow_message_tcp(data)[1]
				first_message = core.split_flow_message_tcp(data)[0]	
											
	def sendError(self,ACK_NUM,error):
		TYPE = '0000'
		A='1'
		R='0'
		buffer_length = 7
		buf = ctypes.create_string_buffer(buffer_length)
		I = (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(bin(ACK_NUM),2) << 13) + (int(bin(0),2) << 0)
		struct.pack_into('>IHB',buf,0,I,buffer_length,error)
		self.transport.write(buf.raw)
	
	def sendLoginResponse(self,ACK_NUM,UserId):
		TYPE = '1110'
		A = '1'
		R = '0'
		buffer_length = 8
		buf = ctypes.create_string_buffer(buffer_length)
		fourbyte = (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(bin(ACK_NUM),2) << 13) + (int(bin(0),2) << 0)
		struct.pack_into('>IHH',buf,0,fourbyte,buffer_length,UserId)
		self.transport.write(buf.raw)

	def sendAck(self,SEQ_NUM):		
		SEQ_NUM = bin(SEQ_NUM)
		TYPE = '1111'
		A = '1'
		R = '0'
		buffer_length = 6
		buf = ctypes.create_string_buffer(buffer_length)
		fourbyte = (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(str(SEQ_NUM),2) << 13) + (int('0',2) << 0)
		struct.pack_into('>IH',buf,0,fourbyte,buffer_length)
		self.transport.write(buf.raw)
    
	def sendUserMessage(self,user):
		TYPE = '0010'
		A = '0'
		R = '0'
		ROO = '0'
		list_users = self.serverProxy.getUserList()
		Number = len(list_users)
		Name_Length = 0		
		for user in list_users:
			Name_Length += len(user.userName)
		buffer_length = 8 + Number*3 + Name_Length
		buf = ctypes.create_string_buffer(buffer_length)
		fourbyte = (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(bin(0),2) << 13) + (int(bin(user.userChatInstance.seq_num),2) << 0)
		ROO_Number = (int(ROO,2) << 14 ) + (int(bin(Number),2) << 0)
		struct.pack_into('>IHH',buf,0,fourbyte,buffer_length,ROO_Number)
		offset = 8
		for user in list_users:			
			current_status='0'			
			if user.userChatRoom==ROOM_IDS.MAIN_ROOM:
				current_status='1'
			lenUsername_status= (int(bin(len(user.userName)),2) <<1) + (int(current_status,2) << 0)			
			struct.pack_into('>BH'+str(len(user.userName))+'s',buf,offset,lenUsername_status,user.userId,user.userName)
			offset+=3+len(user.userName)
		self.transport.write(buf.raw)

	def sendUserMessageForMovieRoom(self,movieName,user):
		TYPE = '0010'
		A='0'
		R='0'
		ROO='0'
		list_users=self.serverProxy.getUserList()
		Number = len(list_users)
		Name_Length = 0		
		for user in list_users:
			Name_Length += len(user.userName)
		buffer_length = 8 + Number*3 + Name_Length
		buf=ctypes.create_string_buffer(buffer_length)		
		fourbyte= (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(bin(0),2) << 13) + (int(bin(user.userChatInstance.seq_num),2) << 0)
		ROO_Number = (int(ROO,2) << 14 ) + (int(bin(Number),2) << 0)
		struct.pack_into('>IHH',buf,0,fourbyte,buffer_length,ROO_Number)
		offset = 8
		for user in list_users:			
			if user.userChatRoom==movieName and not(user.userName==''):
				current_status='0'
				lenUsername_status= (int(bin(len(user.userName)),2) <<1) + (int(current_status,2) << 0 )
				struct.pack_into('>BH'+str(len(user.userName))+'s',buf,offset,lenUsername_status,user.userId,user.userName)
				offset+=3+len(user.userName)
		self.transport.write(buf.raw)



	def sendMovieMessage(self,user):
		TYPE = '0011'
		A='0'
		R='0'
		ACK_NUM='0'
		listOfMovies=self.serverProxy.getMovieList()
		Number = len(listOfMovies)
		fourbyte= (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(ACK_NUM,2) << 13) + (int(bin(user.userChatInstance.seq_num),2) << 0)
		Name_Length = 0		
		for movie in listOfMovies:
			Name_Length += len(movie.movieTitle)
		buffer_length = 8 + Number*7 + Name_Length
		buf=ctypes.create_string_buffer(buffer_length)
		struct.pack_into('>IHH',buf,0,fourbyte,buffer_length,Number)
		offset = 8
		for movie in listOfMovies:
			current_ip_adress = core.tohex(movie.movieIpAddress)
			struct.pack_into('>BBBBHB'+str(len(movie.movieTitle))+'s',buf,offset,current_ip_adress[0],current_ip_adress[1],current_ip_adress[2],current_ip_adress[3],movie.moviePort,len(movie.movieTitle),movie.movieTitle)
			offset+=7+len(movie.movieTitle)
		self.transport.write(buf.raw)    
    
	def sendMoviesIdlist(self):
		l=self.serverProxy.getMovieList()
		s=""
		for movie in l:
			s+=str(movie.movieId)
			s+="."
		buf = ctypes.create_string_buffer(len(s)+4)
		struct.pack_into('!I'+str(len(s))+'s',buf,0,12,s)
		self.transport.write(buf.raw)

	def send_Public_Message(self,SEQ_NUM,UserId,MessageText):
		TYPE='0100'
		A='0'
		R='0'
		ACK_NUM = '0'

		buffer_length = 14 + len(MessageText)
		buf = ctypes.create_string_buffer(buffer_length)
		fourbyte = (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(ACK_NUM,2) << 13) + (int(bin(SEQ_NUM),2) << 0)
		Message = (UserId << 6*8) + (int(str(0),2) << 0)
		struct.pack_into('>IHQ'+str(len(MessageText))+'s',buf,0,fourbyte,buffer_length,Message, MessageText)
		self.type_last_message=int(TYPE,2)
		self.transport.write(buf.raw)

	def send_Private_Message(self,SEQ_NUM,ScrId,DestId,MessageText):
		TYPE='0101'
		A='0'
		R='0'
		ACK_NUM = 0
		buffer_length= 10 + len(MessageText)
		buf= ctypes.create_string_buffer(buffer_length)
		fourbyte= (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(bin(ACK_NUM),2) << 13) + (int(bin(SEQ_NUM),2) << 0)
		Message = (ScrId << 2*8) + (DestId << 0)
		struct.pack_into('>IHI'+str(len(MessageText))+'s',buf,0,fourbyte,buffer_length,Message, MessageText)
		self.type_last_message=int(TYPE,2)
		self.transport.write(buf.raw)	
	
	
