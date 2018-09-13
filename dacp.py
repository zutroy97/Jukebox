#import select
#import random
#import socket
#import urlparse
import urllib
#import string
import struct
import re
import http.client
#import hashlib
import urllib


DNS_TOUCHABLE_PORT = 3689
class Parser:
	def __init__(self, raw):
		self._raw = raw
	
	def __call__(self, raw):
		self._raw = raw
	
	
	def nested(self, tag):
		s = re.search(tag.encode('ascii'), self._raw)
		
		if not s: return None
		
		p = s.start()
		l = struct.unpack('>I', self._raw[p + 4:p + 8])[0]
		
		return Parser(self._raw[p + 8:p + 8 + l])
	
	def array(self, tag):
		q = []
		for m in re.finditer(tag.encode('ascii'), self._raw):
			p = m.start()
			l = struct.unpack('>I', self._raw[p + 4:p + 8])[0]
			q += [Parser(self._raw[p + 8:p + 8 + l])]
		
		return q
	
	
	def string(self, tag=None):
		if not tag:
			return self._raw
		
		s = re.search(tag.encode('ascii'), self._raw)
		if not s:
			return None
		
		p = s.start()
		l = struct.unpack('>I', self._raw[p + 4:p + 8])[0]
		
		return self._raw[p + 8:p + 8 + l]
	
	def bool(self, tag=None):
		if not tag:
			return bool(struct.unpack('>B', self._raw)[0])
		
		s = re.search(tag.encode('ascii'), self._raw)
		if not s:
			return None
		
		p = s.start()
		l = struct.unpack('>I', self._raw[p + 4:p + 8])[0]
		
		return bool(struct.unpack('>B', self._raw[p + 8:p + 8 + l])[0])
	
	def int(self, tag=None):
		if not tag:
			return struct.unpack('>I', self._raw)[0]
		
		s = re.search(tag.encode('ascii'), self._raw)
		if not s:
			return None
		
		p = s.start()
		l = struct.unpack('>I', self._raw[p + 4:p + 8])[0]
		
		return struct.unpack('>I', self._raw[p + 8:p + 8 + l])[0]
	

class DACPTouchableConnection(object):
    def __init__(self, **kwargs):
        self.__host = kwargs.get('host', 'localhost')
        self.__port = kwargs.get('port', DNS_TOUCHABLE_PORT)
        self.__guid = kwargs.get('guid', '')
        
        self.__conn = None
        self.__mlid = None
    
    
    def connect(self):
        self.close()
        self.__conn = http.client.HTTPConnection(self.__host, self.__port, )
    
    def close(self):
        if self.__conn:
            self.__conn.close()
            self.__conn = None
    
    
    def is_alive(self):
        return bool(self.__conn)
    
    
    def login(self, **kwargs):
        guid = kwargs.get('guid', self.__guid)
        
        self.__conn.request("GET", "/login?pairing-guid=0x{0}".format(guid), None, {'Viewer-Only-Client': '1'})
        
        respond = self.__conn.getresponse()
        if respond and respond.status == 200:
            self.__mlid = Parser(respond.read()).int('mlid')
            return True
        
        else:
            self.close()
            return False
    
    
    def send_raw(self, raw):
        self.connect()
        self.__conn.request('GET', str(raw)+'&session-id='+str(self.__mlid), None, {'Viewer-Only-Client': '1'})
        
        respond = self.__conn.getresponse()
        if respond:
            if respond.status == 200:
                return respond.read()
            
            return respond.status
            
    
    def send_cmd(self, cmd, args={}):
        return self.send_raw('{0}?{1}'.format(cmd, urllib.parse.urlencode(args)))
    
    
    @property
    def host(self):
        return self.__host
    
    @property
    def port(self):
        return self.__port
    
    @property
    def guid(self):
        return self.__guid
    
    @property
    def session_id(self):
        return self.__mlid

class ITunesController(DACPTouchableConnection):
    def __init__(self, **kwargs):
        DACPTouchableConnection.__init__(self, **kwargs)
        
        self._cmsr = 1
    
    
    def play_pause(self):
        self.send_cmd('/ctrl-int/1/playpause')
    
    
    def next_item(self):
        self.send_cmd('/ctrl-int/1/nextitem')
    
    def prev_item(self):
        self.send_cmd('/ctrl-int/1/previtem')
    
    
    def shuffle(self, value=None):
        if not value:
            d = dacp.Parser(list(self.send_cmd('/ctrl-int/1/getproperty', {'properties': 'dacp.shufflestate'})))
            return d.int('cash')
        
        if 0 <= value <= 1:
            self.send_cmd('/ctrl-int/1/setproperty', {'dacp.shufflestate': value})
    
    def repeat(self, value=None):
        if not value:
            d = dacp.Parser(list(self.send_cmd('/ctrl-int/1/getproperty', {'properties': 'dacp.repeatstate'})))
            return d.int('carp')
        
        if 0 <= value <= 2:
            self.send_cmd('/ctrl-int/1/setproperty', {'dacp.repeatstate': value})
    
    def volume(self, value=None):
        if not value:
            d = dacp.Parser(list(self.send_cmd('/ctrl-int/1/getproperty', {'properties': 'dmcp.volume'})))
            return d.int('cmvo')
        
        if 0.0 <= value <= 100.0:
            self.send_cmd('/ctrl-int/1/setproperty?dmcp.volume', {'dmcp.volume': value})
    
    
    def artwork(self, min_w, min_h):
        return self.send_cmd('/ctrl-int/1/nowplayingartwork', {'mw': min_w, 'mh': min_h})
    
    
    def status(self, **kwargs):
        if kwargs.get('wait', False):
            rev = self._cmsr
        
        else:
            rev = 1
        
        d = dacp.Parser(self.send_cmd('/ctrl-int/1/playstatusupdate', {'revision-number': rev}))
        self._cmsr = d.int('cmsr')
		
        return d
    
    
    @property
    def revision_number(self):
        return self._cmsr        

if __name__ == "__main__":
    q = ITunesController(host='localhost')
    q.connect()
    if q.login(guid='0000000000000002'):
        #q.next_item()
        q.play_pause()
    else:
        print('failed to connect to server....')
    q.close()
