
import time

file = xxxxxxxx

def tail(f):  
  f.seek(0,2)               # 移动到文件EOF 
  while True:  
    line = f.readline()     # 读取文件中新的文本行 
    if not line:  
      time.sleep(0.1)       # 间隔
      continue 
    yield line  

if __name__ == '__main__':
    tail(file)