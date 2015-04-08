# -*- coding: utf-8 -*-
from twisted.internet.protocol import DatagramProtocol
from c2w.main.lossy_transport import LossyTransport
from c2w.main.constants import ROOM_IDS
import logging
import ctypes
import struct
import random
from twisted.internet import reactor
from c2w.main.movie import *
from c2w.main.user import *
from c2w.main.constants import *
import core
#version 53

logging.basicConfig()
moduleLogger = logging.getLogger('c2w.protocol.udp_chat_server_protocol')
class c2wUdpChatServerProtocol(DatagramProtocol):        
	def __init__(self, serverProxy, lossPr):
		"""
		:param serverProxy: The serverProxy, which the protocol must use
			to interact with the user and movie store (i.e., the list of users
			and movies) in the server.
		:param lossPr: The packet loss probability for outgoing packets.  Do
			not modify this value!

		Class implementing the UDP version of the client protocol.

		.. note::
			You must write the implementation of this class.

		Each instance must have at least the following attribute:

		.. attribute:: serverProxy

			The serverProxy, which the protocol must use
			to interact with the user and movie store in the server.

		.. attribute:: lossPr

			The packet loss probability for outgoing packets.  Do
			not modify this value!  (It is used by startProtocol.)

		.. note::
			You must add attributes and methods to this class in order
			to have a working and complete implementation of the c2w
			protocol.
		"""
		self.serverProxy = serverProxy
		self.lossPr = lossPr
		self.ListOfNames_sqNum_hp = []
		self.ack = 0
		self.seq_num = 0
		self.listOfloginResponseReceived=[]
		self.idcall = None


	def startProtocol(self):
		"""
		DO NOT MODIFY THE FIRST TWO LINES OF THIS METHOD!!

		If in doubt, do not add anything to this method.  Just ignore it.
		It is used to randomly drop outgoing packets if the -l
		command line option is used.
		"""
		self.transport = LossyTransport(self.transport, self.lossPr)
		DatagramProtocol.transport = self.transport
	
	def datagramReceived(self, datagram, (host, port)):
		"""
		:param string datagram: the payload of the UDP packet.
		:param host: the IP address of the source.
		:param port: the source port.

		Called **by Twisted** when the server has received a UDP
		packet.
		"""
		#extraction du type du message avec l'entête dans une liste
		message_client = core.parseReceivedData(datagram)	
		TYPE=message_client[0]
		data=message_client[6]
		
		if (TYPE == 1):
			username=message_client[6]
			if not(self.serverProxy.userExists(username)):

				User_id=self.serverProxy.addUser(username,ROOM_IDS.MAIN_ROOM,None,None)
				for a in self.ListOfNames_sqNum_hp :
					self.sendUserMessage(a[2])
				a=(username,0,(host,port))
				self.ListOfNames_sqNum_hp.append(a)
				self.listOfloginResponseReceived.append(((host,port),False,User_id,False,False))
				self.sendLoginResponse(message_client[4],User_id,(host,port))																
			else:
				v=0
				while(not(self.listOfloginResponseReceived[v][0]==(host,port))):
					v+=1
				if(self.listOfloginResponseReceived[v][1]==False):
					self.sendLoginResponse(message_client[4],self.listOfloginResponseReceived[v][2],(host,port))
				else:

					self.sendAck(message_client[5],(host, port))
					error = 1
					self.sendError(message_client[4],error,(host,port))

		if (TYPE==6):
				user_id = struct.unpack_from('!H',data[0:])[0]
				movie_id1 = struct.unpack_from('!I',data[2:])[0]
				movie_id2 = struct.unpack_from('!H',data[6:])[0]
				movie_id = (movie_id1 << 2*8) + (movie_id2 << 0)						
				UserName = self.serverProxy.getUserById(user_id).userName			
				MovieName = self.serverProxy.getMovieById(movie_id).movieTitle  
				self.serverProxy.updateUserChatroom(UserName,MovieName)
				for a in self.ListOfNames_sqNum_hp :
					user = self.serverProxy.getUserByName(a[0])
					if (user.userChatRoom == ROOM_IDS.MAIN_ROOM):
						self.sendUserMessage(a[2])
					elif(user.userChatRoom == MovieName):
						self.sendUserMessageForMovieRoom(MovieName,a[2])
				self.serverProxy.startStreamingMovie(MovieName)	
				self.sendAck(message_client[5],(host, port))	
				
		if (TYPE==7):
			user_id=struct.unpack_from('!H',data[0:])[0]
			UserName = self.serverProxy.getUserById(user_id).userName
			self.serverProxy.updateUserChatroom(UserName,ROOM_IDS.MAIN_ROOM)
			for a in self.ListOfNames_sqNum_hp :
				user = self.serverProxy.getUserByName(a[0])
				if (user.userChatRoom == ROOM_IDS.MAIN_ROOM):
					self.sendUserMessage(a[2])
				else:
					self.sendUserMessageForMovieRoom(user.userChatRoom,a[2])
			self.sendAck(message_client[5],(host, port))
		
		if (TYPE == 8) :
			userId = struct.unpack_from('!H',data)[0]					
			userName = self.serverProxy.getUserById(userId).userName
			self.serverProxy.removeUser(userName)
			for p in self.ListOfNames_sqNum_hp:
				if (p[0] == userName):
					self.ListOfNames_sqNum_hp.remove(p)	
			for a in self.ListOfNames_sqNum_hp :
				if not(userName==a[0]):
					self.sendUserMessage(a[2])
			self.sendAck(message_client[5],(host, port))
			
		if(TYPE==15):
			if(message_client[4]==0):
				v = 0
				while(not(self.listOfloginResponseReceived[v][0]==(host,port))):
					v+=1
				if(self.listOfloginResponseReceived[v][1]==False):
					a=((host,port),True,self.listOfloginResponseReceived[v][2],False,False)
					self.listOfloginResponseReceived.remove(((host,port),False,self.listOfloginResponseReceived[v][2],False,False))
					self.listOfloginResponseReceived.append(a)
					self.sendMovieMessage((host, port))
				else:
					self.sendUserMessage((host, port))												
			if(message_client[4]==1):				
				self.idcall.cancel()
				v = 0
				while(not(self.listOfloginResponseReceived[v][0]==(host,port))):
					v+=1
				a=((host,port),True,self.listOfloginResponseReceived[v][2],True,False)
				self.listOfloginResponseReceived.remove(((host,port),True,self.listOfloginResponseReceived[v][2],False,False))
				self.listOfloginResponseReceived.append(a)
				self.sendUserMessage((host, port))
			if (message_client[4]==2):
				v=0
				while(not(self.listOfloginResponseReceived[v][0]==(host,port))):
					v+=1				
				a=((host,port),True,self.listOfloginResponseReceived[v][2],True,True)
				self.listOfloginResponseReceived.remove(((host,port),True,self.listOfloginResponseReceived[v][2],True,False))
				self.listOfloginResponseReceived.append(a)
				self.sendMoviesIdlist((host, port))
				self.idcall.cancel()
				return	

		if(TYPE == 4):
			user_id=struct.unpack_from('!H',data[0:])[0]
			message = data[8:]
			user=self.serverProxy.getUserById(user_id)
			CurrentUserName = user.userName
			self.sendAck(message_client[5],(host, port))
			for userName_seq in self.ListOfNames_sqNum_hp:
				if not( CurrentUserName == userName_seq[0]):
					dest_user=self.serverProxy.getUserByName(userName_seq[0])
					if (user.userChatRoom == dest_user.userChatRoom):
						(h,p) = self.getHost_Port(userName_seq[0])
						self.send_Public_Message(userName_seq[1],user_id,message,(h,p))
  		if(TYPE == 5):
			ScrId=struct.unpack_from('!H',data[0:])[0]
			DestId=struct.unpack_from('!H',data[2:])[0]
			UserNameDest = self.serverProxy.getUserById(DestId).userName
			(h,p) = self.getHost_Port(UserNameDest)
			message= data[4:]
			self.sendAck(message_client[5],(host, port))
			self.send_Private_Message(self.seq_num,ScrId,DestId,message,(h,p))

	def sendError(self,ACK_NUM,error,(host,port)):

		TYPE = '0000'
		A='1'
		R='0'
		buffer_length= 7
		buf= ctypes.create_string_buffer(buffer_length)
		I= (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(bin(ACK_NUM),2) << 13) + (int(bin(0),2) << 0)
		struct.pack_into('>IHB',buf,0,I,buffer_length,error)
		self.transport.write(buf.raw,(host,port))
    
	def sendLoginResponse(self,ACK_NUM,UserId,(host,port)):
		TYPE = '1110'
		A='1'
		R='0'
		buffer_length= 8
		buf= ctypes.create_string_buffer(buffer_length)
		fourbyte= (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(bin(ACK_NUM),2) << 13) + (int(bin(0),2) << 0)
		struct.pack_into('>IHH',buf,0,fourbyte,buffer_length,UserId)
		self.transport.write(buf.raw,(host,port))

    def sendAck(self,SEQ_NUM,(host,port)):
		
		SEQ_NUM=bin(SEQ_NUM)
		TYPE='1111'
		A='1'
		R='0'
		buffer_length= 6 
		buf= ctypes.create_string_buffer(buffer_length)
		fourbyte= (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(str(SEQ_NUM),2) << 13) + (int('0',2) << 0)    
		struct.pack_into('>IH',buf,0,fourbyte,buffer_length)
		self.transport.write(buf.raw,(host,port))
    
	def sendUserMessage(self,(host,port)):
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
		fourbyte= (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(bin(0),2) << 13) + (int(bin(2),2) << 0)
		ROO_Number = (int(ROO,2) << 14 ) + (int(bin(Number),2) << 0)
		struct.pack_into('>IHH',buf,0,fourbyte,buffer_length,ROO_Number)
		offset = 8
		for user in list_users:			
			current_status='0'	
			if user.userChatRoom==ROOM_IDS.MAIN_ROOM:
				current_status='1'
			lenUsername_status= (int(bin(len(user.userName)),2) <<1) + (int(current_status,2) << 0 )
			
			struct.pack_into('>BH'+str(len(user.userName))+'s',buf,offset,lenUsername_status,user.userId,user.userName)
			offset+=3+len(user.userName)
		self.transport.write(buf.raw,(host, port))
		v=0
		while(not(self.listOfloginResponseReceived[v][0]==(host,port))):
					v+=1
		if(self.listOfloginResponseReceived[v][4]==False):
			self.idcall = reactor.callLater(0.5,self.sendUserMessage,(host,port))

	def sendUserMessageForMovieRoom(self,movieName,(host,port)):
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
		fourbyte= (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(bin(0),2) << 13) + (int(bin(2),2) << 0)
		ROO_Number = (int(ROO,2) << 14 ) + (int(bin(Number),2) << 0)
		struct.pack_into('>IHH',buf,0,fourbyte,buffer_length,ROO_Number)
		offset = 8
		for user in list_users:			
			if user.userChatRoom==movieName and not(user.userName==''):
				current_status='0'
				lenUsername_status= (int(bin(len(user.userName)),2) <<1) + (int(current_status,2) << 0 )
				struct.pack_into('>BH'+str(len(user.userName))+'s',buf,offset,lenUsername_status,user.userId,user.userName)
				offset+=3+len(user.userName)
		self.transport.write(buf.raw,(host, port))


	def sendMovieMessage(self,(host, port)):
		TYPE = '0011'
		A='0'
		R='0'
		ACK_NUM='0'
		listOfMovies=self.serverProxy.getMovieList()
		Number = len(listOfMovies)
		fourbyte= (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(ACK_NUM,2) << 13) + (int(bin(1),2) << 0)
		Name_Length = 0		
		for movie in listOfMovies:
			Name_Length += len(movie.movieTitle)
		buffer_length = 8 + Number*7 + Name_Length
		buf=ctypes.create_string_buffer(buffer_length)
		struct.pack_into('>IHH',buf,0,fourbyte,buffer_length,Number)
		offset = 8
		for movie in listOfMovies:
			current_ip_adress=core.tohex(movie.movieIpAddress)
			struct.pack_into('>BBBBHB'+str(len(movie.movieTitle))+'s',buf,offset,current_ip_adress[0],current_ip_adress[1],current_ip_adress[2],current_ip_adress[3],movie.moviePort,len(movie.movieTitle),movie.movieTitle)
			offset+=7+len(movie.movieTitle)
		self.transport.write(buf.raw,(host, port))		
			
		v=0
		while(not(self.listOfloginResponseReceived[v][0]==(host,port))):
					v+=1
		
		if(self.listOfloginResponseReceived[v][3]==False):
			self.idcall = reactor.callLater(0.5,self.sendMovieMessage,(host,port))	

        
	def sendMoviesIdlist(self,(host, port)):
		l=self.serverProxy.getMovieList()
		s=""
		for movie in l:
			s+=str(movie.movieId)
			s+="."
		buf = ctypes.create_string_buffer(len(s)+4)
		struct.pack_into('!I'+str(len(s))+'s',buf,0,12,s)
		self.transport.write(buf.raw,(host, port))

	def getHost_Port(self,userName):
		for element in self.ListOfNames_sqNum_hp:
			if(element[0]==userName):
				return element[2]

	def send_Public_Message(self,SEQ_NUM,UserId,MessageText,(host,port)):
		TYPE='0100'
		A='0'
		R='0'
		ACK_NUM = 0
		buffer_length= 14 + len(MessageText)
		buf= ctypes.create_string_buffer(buffer_length)
		fourbyte= (int(TYPE,2) << 28) + (int(A,2) << 27) + (int(R,2) << 26) + (int(bin(ACK_NUM),2) << 13) + (int(bin(SEQ_NUM),2) << 0)
		Message = (UserId << 6*8) + (int(str(0),2) << 0)
		struct.pack_into('>IHQ'+str(len(MessageText))+'s',buf,0,fourbyte,buffer_length,Message, MessageText)
		self.type_last_message=int(TYPE,2)
		self.transport.write(buf.raw,(host, port))

	def send_Private_Message(self,SEQ_NUM,ScrId,DestId,MessageText,(host,port)):
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
		self.transport.write(buf.raw,(host, port))
	
	def sendUpdate(self,(host,port)):
		TYPE = '1010'
		A = '0000'
		buffer_length = 1
		buf = ctypes.create_string_buffer(buffer_length)
		byte = (int(TYPE,2) << 4) + (int(A,2) << 0)
		struct.pack_into('>B',buf,0,byte)
		self.transport.write(buf.raw,(host,port))
