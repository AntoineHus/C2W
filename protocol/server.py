# -*- coding: utf-8 -*- #
from twisted.internet.protocol import Protocol
import logging
import struct
import ctypes
from c2w.main.movie import *
from c2w.main.user import *
from c2w.main.constants import *

class c2wServer(Protocol):

    def __init__(self, serverProxy):
        self.serverProxy = serverProxy

    def handle_login():
        pass

    def Userlist():
        USERS = self.userList
        NUMBER = len(USERS)
        variable_length=[]
        S=[]
        length_sum = 0 
        i = 0
        while i<NUMBER:
            variable_length.append(sys.getsizeof((USERS[i]).userName))
            if (USERS[i]).userChatRoom==ROOM_IDS.MAIN_ROOM :
                S.append(1)
            else :
                S.append(0)
            length_sum = length_sum+variable_length[i]
            i=i+1
        length_buffer = 2+3*NUMBER+length_sum
        buffer_USERS = ctypes.create_string_buffer(length_buffer)
        header = (int(str(00),2)<<14)+(int(str(bin(NUMBER)),2))
        buffer_USERS=struct.pack('H',header)
        i=0
        while i<NUMBER:
            length_status=(int(str(bin(variable_length[i])),2)<<1)+
            (int(str(bin(S[i])),2))       
            buffer_USERS += struct.pack('BH' + str(variable_length[i]) +
            's',length_status,USERS[i].userId,USERS[i].userName)
            i=i+1
        return [buffer_USERS, length_buffer]

    def Movielist():
        MOVIES=self.serverProxy.getMovieList()
        NUMBER=len(MOVIES)
        variable_length=[]
        length_sum=0
        i = 0
        while i<NUMBER:
            variable_length.append(len(MOVIES[i].movieTitle))
            length_sum=length_sum+variable_length[i]
            i=i+1
        length_buffer=2+7*NUMBER+length_sum
        buffer_MOVIES=ctypes.create_string_buffer(length_buffer)
        buffer_MOVIES=struct.pack('H',NUMBER)
        i=0
        while i<NUMBER:
            buffer_MOVIES += struct.pack('IHB' + str(variable_length[i]) + 
            's',MOVIES[i].movieIpAddress,MOVIES[i].moviePort,variable_length[i],MOVIES[i].movieTitle)
            i=i+1
        return [buffer_MOVIES, length_buffer]

    def Private_message(source_ID, dest_ID, message_text):
        buffer_private = ctypes.create_string_buffer(4+len(message_text))
        buffer_private = struct.pack('HH'+str(len(message_text))+'s',source_ID, dest_ID, message_text)
        return buffer_private

    def Public_message(user_ID, room, message_text):
        buffer_public=ctypes.create_string_buffer(8+len(message_text))
        if room==ROOM_IDS.MAIN_ROOM:
            user_ID1=0
            user_ID2=0
        else:
            room.MOVIE_ROOM
        buffer_public=struct.pack('HHI'+str(len(message_text))+'s',user_ID, room_ID1, room_ID2, message_text)
        return buffer_public

    def send_userID():    
        userID=len(self.serverProxy.getUserList())+1
        while self.serverProxy.getUserById(userID)!=None:
            userID=userID+1
        #buffer_ID=ctypes.create_string_buffer(2)
        #buffer_ID=struct.pack('H',userID)
        return user_ID
    
#    #lors de la connexion    
#    if self.serverProxy.getUserByName(userName)!=None:
#        error_code=1
#    if 'connection_denied':
#        error_code=1
#    #lors d'une requête de chat message
#    if :
#        error_code=2
#    #lors d'une requête de join movie room
#    if :
#        error_code=3
#    #malformed message
#    if :
#        error_code=4
    def send_errorMessage(error_code):    
        buffer_error=ctypes.create_string_buffer(1)
        buffer_error=struct.pack('B',error_code)
        return buffer_error

    list UserMovie

    # attente active pour la notification de la mise à jour de la liste
    while(1)

    lenght
