# 简单将日志打印到屏幕
# import logging
# logging.debug('debug message')
# logging.info('info message')
# logging.warning('warning message')
# logging.error('error message')
# logging.critical('critical message')

# 灵活配置日志级别，日志格式，输出位置
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='/tmp/test.log',
                    filemode='w')
 
logging.debug('debug message')
logging.info('info message')
logging.warning('warning message')
logging.error('error message')
logging.critical('critical message')

# 查看输出：cat /tmp/test.log 
# Mon, 05 May 2014 16:29:53 test_logging.py[line:9] DEBUG debug message
# Mon, 05 May 2014 16:29:53 test_logging.py[line:10] INFO info message
# Mon, 05 May 2014 16:29:53 test_logging.py[line:11] WARNING warning message
# Mon, 05 May 2014 16:29:53 test_logging.py[line:12] ERROR error message
# Mon, 05 May 2014 16:29:53 test_logging.py[line:13] CRITICAL critical message

# logging.basicConfig() 函数中可通过具体参数来更改logging模块默认行为，可用参数如下：
# filename：            用指定的文件名创建FiledHandler，这样日志会被存储在指定的文件中。
# filemode：            文件打开方式，在指定了filename时使用这个参数，默认为"a",还可指定为"w"
# format：              指定handler使用的日志显示格式。
# datefmt：             指定日期时间格式
# level：               设置rootlogger（后边会讲解具体概念）的日志级别 
# stream：              用指定的stream创建StreamHandler。可指定输出到sys.stderr,sys.stdout或者文件，默认为sys.stderr
#                       若同时列出了filename和stream两个参数，则stream参数会被忽略。

# format参数中可能用到的格式化串：
# %(name)s              Logger的名字
# %(levelno)s           数字形式的日志级别
# %(levelname)s         文本形式的日志级别
# %(pathname)s          调用日志输出函数的模块的完整路径名，可能没有
# %(filename)s          调用日志输出函数的模块的文件名
# %(module)s            调用日志输出函数的模块名
# %(funcName)s          调用日志输出函数的函数名
# %(lineno)d            调用日志输出函数的语句所在的代码行
# %(created)f           当前时间，用UNIX标准的表示时间的浮 点数表示
# %(relativeCreated)d   输出日志信息时的，自Logger创建以 来的毫秒数
# %(asctime)s           字符串形式的当前时间。默认格式是 “2003-07-08 16:49:45,896”。逗号后面的是毫秒
# %(thread)d            线程ID。可能没有
# %(threadName)s        线程名。可能没有
# %(process)d           进程ID。可能没有
# %(message)s           用户输出的消息

# ------------------------------------------------- 日志回滚

import logging
from logging.handlers import RotatingFileHandler

# 定义一个RotatingFileHandler，最多备份5个日志文件，每个日志文件最大10M
Rthandler = RotatingFileHandler('myapp.log', maxBytes=1024*1024*10,backupCount=5)
Rthandler.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
Rthandler.setFormatter(formatter)
logging.getLogger('').addHandler(Rthandler)

# -------------------------------------------------

import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='myapp.log',
                    filemode='w')

# 定义一个StreamHandler，将INFO级别或更高的日志信息打印到标准错误，并将其添加到当前的日志处理对象
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
logging.getLogger('').addHandler(console)

logging.debug('This is debug message')
logging.info('This is info message')
logging.warning('This is warning message')

# 屏幕上打印:
# root        : INFO     This is info message
# root        : WARNING  This is warning message

# ./myapp.log文件中内容为:
# Sun, 24 May 2009 21:48:54 demo2.py[line:11] DEBUG This is debug message
# Sun, 24 May 2009 21:48:54 demo2.py[line:12] INFO This is info message
# Sun, 24 May 2009 21:48:54 demo2.py[line:13] WARNING This is warning message