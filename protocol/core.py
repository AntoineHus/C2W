# -*- coding: utf-8 -*- #
from twisted.internet.protocol import Protocol
import logging
import struct
import ctypes
#version 53
def construct_header(TYPE,a,r,ACK_NUM,SEQ_NUM):
    """Permet de construire le Header à partir des valeurs
        des champs qu'on lui transmet
        """
            
            TYPE_hdr = TYPE
                a_hdr = a
                    r_hdr = r
                        ack_num_hdr = ACK_NUM
                            seq_num_hdr = SEQ_NUM
                                
                                header = (int(str(TYPE),2) << 28) + (int(str(A),2) << 27) + (int(str(R),2) << 26) + (int(str(ACK_NUM),2) << 13) + (int(str(SEQ_NUM),2) << 0)
                                    
                                    return header


def split_message(datagram):
    """Méthode qui sépare le header du message d'un paquet
        """
            
            header = struct.unpack_from('!B',datagram)[0]
                message = datagram[6:]
                    
                    return (header, message)


def deconstruct_header(hdr):
    """Méthode qui parse le header et qui retourne une list
        """
    header = []
    header.append(hdr >> 4)
    hdr -= TYPE*16
                        
                        header.append(hdr >> 3)
                            
                            hdr -= A*8
                                
                                header.append(hdr >> 2)
                                    
                                    two_first_bits_Ack -= R*4
                                        
                                        Ack_cont = struct.unpack_from('!B',hdr[1:])[0]
                                            
                                            two_last_bytes = struct.unpack_from('!H',hdr[2:])[0]
                                                
                                                a = two_last_bytes >> 13
                                                    
                                                    ACK_NUM = two_first_bits_Ack*2048 + Ack_cont*8 + a
                                                        
                                                        header.append(ACK_NUM)
                                                            
                                                            SEQ_NUM = two_last_bytes - a*8192
                                                                
                                                                header.append(SEQ_NUM)
                                                                    
                                                                    MSG_Length = struct.unpack_from('!H',hdr[4:])[0]
                                                                        
                                                                        header.append(MSG_LENGTH)
                                                                            
                                                                            return header


def message_length():
    """
        """
pass

def handle_errors(number_error):
    """
        """
pass

def acknowledge(SEQ_NUM):
    TYPE=1111
        A=1
        R=0
        buffer_length= 6
        buf= ctypes.create_string_buffer(buffer_length)
        fourbyte= (int(str(TYPE),2) << 28) + (int(str(A),2) << 27) + (int(str(R),2) << 26) + (int(str(SEQ_NUM),2) << 13) + (int(str(0),2) << 0)
        struct.pack_into('>IH'+'s',buf,0,fourbyte,buffer_length)
        return buf

def parseReceivedData(datagram):
    first_byte=struct.unpack_from('!B',datagram)[0]
        Type=first_byte>>4
        first_byte=first_byte-Type*16
        A=first_byte>>3
        first_byte=first_byte-A*8
        R=first_byte>>2
        two_first_bits_Ack=first_byte-R*4
        Ack_cont=struct.unpack_from('!B',datagram[1:])[0]
        two_last_bytes=struct.unpack_from('!H',datagram[2:])[0]
        a=two_last_bytes>>13
        ACK_NUM=two_first_bits_Ack*2048 + Ack_cont*8 +a
        SEQ_NUM=two_last_bytes-a*8192
        MSG_Length=struct.unpack_from('!H',datagram[4:])[0]
        datagram=datagram[6:]
        return (Type, A, R, MSG_Length, ACK_NUM, SEQ_NUM,datagram)

def extract_user(data):
    two_first_bytes=struct.unpack_from('!H',data)[0]
        ROO=two_first_bytes>>14
        Number=two_first_bytes-ROO*16384
        third_byte=struct.unpack_from('!B',data[2:])[0]
        length=third_byte>>1
        status=third_byte-length*2
        User_id=struct.unpack_from('!H',data[3:])[0]
        User_name=data[5:5+length]
        data=data[5+length:]
        return (data,ROO,Number,length,status,User_id,User_name)

def extract_user2(data):
    first_byte=struct.unpack_from('!B',data[0:])[0]
        length=first_byte>>1
        status=first_byte-length*2
        User_id=struct.unpack_from('!H',data[1:])[0]
        User_name=data[3:3+length]
        data=data[3+length:]
        return (data,length,status,User_id,User_name)

def extract_movie(data):
    Number=struct.unpack_from('!H',data)[0]
        Ip_str=""
        Ip_str=Ip_str+str(struct.unpack_from('!B',data[2:])[0])
        for i in xrange(3):
            IP=str(struct.unpack_from('!B',data[3+i:])[0])
                Ip_str=Ip_str+'.'+IP
        port_num=struct.unpack_from('!H',data[6:])[0]
        Length=struct.unpack_from('!B',data[8:])[0]
        Movie_name=data[9:9+Length]
        data=data[9+Length:]
    return (data,Number,Ip_str,port_num,Length,Movie_name)

def extract_movie_2(data):
    Ip_str=""
        Ip_str=Ip_str+str(struct.unpack_from('!B',data[0:])[0])
        for i in xrange(3):
            IP=str(struct.unpack_from('!B',data[1+i:])[0])
                Ip_str=Ip_str+'.'+IP
        port_num=struct.unpack_from('!H',data[4:])[0]
        Length=struct.unpack_from('!B',data[6:])[0]
        Movie_name=data[7:7+Length]
        data=data[7+Length:]	
    return (data,Ip_str,port_num,Length,Movie_name)

def extract_private_message(data):
    Source_Id=struct.unpack_from('!H',data[0:])[0]
        Dest_Id=struct.unpack_from('!H',data[2:])[0]
        Message_Text=data[4:]
        return (Source_Id,Dest_Id,Message_Text)

def extract_public_message(data):
    User_Id=struct.unpack_from('!H',data[0:])[0]
        Movie_Id=struct.unpack_from('!IH',data[2:])[0]
        Message_Text=data[8:]
        return (User_Id,Movie_Id,Message_Text)

def split_flow_message_tcp(data):
    if (len(data) >0):
        MSG_Length=struct.unpack_from('!H',data[4:])[0]
            message1=data[0:MSG_Length]
                data=data[MSG_Length:]
                if (len(data) >0):
                    return (message1,data)
                else:
                    a =""
                        return (message1 ,a)
    else:
        a = ""
            return (a,a)


def tohex(ip_adress):
    listIp=ip_adress.split('.')
        s=[]
        for i in listIp :
            s.append(int(i))
        
        return s	

