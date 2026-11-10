"""Unchanged native96 proxy; loopback synthetic only."""
import socket,select,threading,struct
class CutProxy:
 def __init__(self,mode):
  self.mode=mode;self.arm=False;self.cut=False;self.error=None
  self.listener=socket.socket();self.listener.bind(('127.0.0.1',0));self.listener.listen(1);self.port=self.listener.getsockname()[1]
  self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()
 def run(self):
  front=back=None
  try:
   front,_=self.listener.accept();back=socket.create_connection(('127.0.0.1',5432),timeout=10);front.settimeout(10)
   buffers={front:b'',back:b''}
   while True:
    ready,_,_=select.select([front,back],[],[],10)
    if not ready:raise TimeoutError('bounded proxy wait')
    for s in ready:
     data=s.recv(65536)
     if not data:return
     other=back if s is front else front
     if not self.arm:other.sendall(data);continue
     buffers[s]+=data
     while len(buffers[s])>=5:
      n=1+struct.unpack('!I',buffers[s][1:5])[0]
      if len(buffers[s])<n:break
      frame=buffers[s][:n];buffers[s]=buffers[s][n:]
      before=s is front and frame[:1]==b'Q' and frame[5:].rstrip(b'\0').strip().upper()==b'COMMIT'
      after=s is back and frame[:1]==b'C' and frame[5:]==b'COMMIT\0'
      if (self.mode=='before' and before) or (self.mode=='after' and after):
       self.cut=True
       for c in [front,back]:
        try:c.shutdown(socket.SHUT_RDWR)
        except OSError:pass
       return
      other.sendall(frame)
  except Exception as e:self.error=type(e).__name__
  finally:
   for c in [front,back,self.listener]:
    if c:c.close()
 def join(self):self.thread.join(12);assert not self.thread.is_alive();assert self.error is None,self.error
