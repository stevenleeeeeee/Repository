
import time  
def tail(f):  
  f.seek(0,2)               #移动到文件EOF 
  while True:  
    line = f.readline()     #读取文件中新的文本行 
    if not line:  
      time.sleep(0.1)  
      continue 
    yield line  
