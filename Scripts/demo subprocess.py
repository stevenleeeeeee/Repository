"""
subprocess从2.4版本引入。主要用来取代一些旧模块如 os.system、os.spawn*、os.popen*、commands.* ...
其不但可调用外部命令作为子进程，而且可以连接到子进程的 input/output/error 管道以获取相关返回信息
通过标准库中的subprocess包来fork子进程并运行一个外部程序（其定义了数个创建子进程的函数，它们分别以不同方式创建子进程）
"""

#参数说明：
args:         #可以是一个字符串，可以是一个包含程序参数的列表。要执行的程序一般就是这个列表的第一项，或者是字符串本
executable:   #一般不用，args字符串或列表第一项表示程序名
stdin/stdout/stderr:
              #None 表示没有任何重定向，继承父进程
              #PIPE 创建管道
              #文件对象
              #文件描述符(整数)
preexec_fn    #钩子函数，在fork和exec之间执行(Unix)
close_fds     #在Unix下表示在执行新进程之前是否关闭0/1/2之外的文件，在windows下为是否继承父进程的文件描述符
shell         #为真时在Unix下相当于args前面添加了：/bin/sh -c，Windows下相当于添加了：cmd.exe /c
cwd           #设置工作目录 ( 如果cwd不是None，则会把cwd做为子程序的当前目录 )
env           #设置环境变量 ( 如果env不是None，则子程序的环境变量由env的值来设置 )


# demo1
import subprocess
"""
在复杂场景中需将一个进程的执行输出作为另一个进程的输入。
在另一些场景中我们需要先进入到某个输入环境然后再执行一系列的指令等。这时要用 Popen()
参数：
args：                 shell命令，可以是字串或序列类型如 list,tuple。
bufsize：              缓冲区大小，可不关心
stdin,stdout,stderr：  分别表示程序的标准输入，标准输出，标准错误
shell：                与下面方法中用法相同
cwd：                  设置子进程的当前目录
env：                  指定子进程的环境变量。若 env=None 则默认从父进程继承环境变量
universal_newlines：   不同OS的换行符不同，当该参数为true时表示使用\n作换行符
"""
s=subprocess.Popen('ls', shell=True, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
s.stdin.write('test 1 \n')
s.stdin.write('test 2 \n')
print s.stdout.read()
print s.stderr.read()
print s.wait()         # 等待子进程结束。并返回执行状态 shell 0 为正确
s.stdout.close()
s.stderr.close()
# stdout, stderr 说明：
# run()函数默认不捕获命令执行结果的正常输出和错误输出，若要获取这些内容需要传递subprocess.PIPE
# 然后可通过返回的CompletedProcess类实例的stdout和stderr属性或捕获相应的内容


# demo2
import subprocess
"""
subprocess.call()：执行命令并返回状态，其中shell参数为False时，命令需要通过列表方式传入，当shell为True时可直接传入命令
"""
>>> a = subprocess.call(['df','-hT'],shell=False)
Filesystem    Type    Size  Used Avail Use% Mounted on
/dev/sda2     ext4     94G   64G   26G  72% /
tmpfs        tmpfs    2.8G     0  2.8G   0% /dev/shm
/dev/sda1     ext4    976M   56M  853M   7% /boot

>>> a = subprocess.call('df -hT',shell=True)
Filesystem    Type    Size  Used Avail Use% Mounted on
/dev/sda2     ext4     94G   64G   26G  72% /
tmpfs        tmpfs    2.8G     0  2.8G   0% /dev/shm
/dev/sda1     ext4    976M   56M  853M   7% /boot

>>> print a
0


# demo3
import subprocess
"""
subprocess.check_call()：与subprocess.call()类似，区别是当返回值不为0时直接抛出异常
"""
>>> a = subprocess.check_call('dfdsf',shell=True)
/bin/sh: dfdsf: command not found
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/usr/lib64/python2.6/subprocess.py", line 502, in check_call
    raise CalledProcessError(retcode, cmd)
subprocess.CalledProcessError: Command 'dfdsf' returned non-zero exit status 127


#注：
# subprocess.check_output() 与上面两个方法类似，区别是如果当返回值为0时直接返回输出结果，不为0则抛出异常
# 该方法在python3.x中才有


# demo4
#将一个子进程的输出，作为另一个子进程的输入
import subprocess
child1 = subprocess.Popen(["cat","/etc/passwd"], stdout=subprocess.PIPE)
child2 = subprocess.Popen(["grep","0:0"],stdin=child1.stdout, stdout=subprocess.PIPE)
out = child2.communicate()


# Other
import subprocess
child = subprocess.Popen('sleep 60',shell=True,stdout=subprocess.PIPE)
child.poll()          #检查子进程状态
child.kill()          #终止子进程
child.send_signal()   #向子进程发送信号
child.terminate()     #终止子进程


# 通过对subprocess.Popen的封装来实现的高级函数:
# subprocess.run()、subprocess.call()、subprocess.check_call()和subprocess.check_output()