import argparse
parser = argparse.ArgumentParser(prog='usage_name', description='开头打印', epilog="结束打印")  #创建解析对象
# prog:  程序名
# description: help时显示的开始文字
# epilog: help时显示的结尾文字
# add_help: 是否增加-h/--help选项，默认True

# parser.add_argument('-f', '--foo', help='foo help', action='append',required=True,type=str, choices=['a', 'b'])      

# 读取文件，打印文件内容
# parser.add_argument('file', type=argparse.FileType('r'))    
# for line in args.file:
#     print(line.strip())

parser.add_argument('--aa', type=int, default=42, help='aa!')             # type规定参数类型,default设置默认值
parser.add_argument('bar', nargs='*', default=[1, 2, 3], help='BAR!')     # 位置参数必须传递  nargs=2 需传2个参数
parser.add_argument('args', nargs=argparse.REMAINDER)                     # 剩余参数收集到列表
args = parser.parse_args()                                                # 全部的值
args.bar                                                                  # 获取选项开关的值
print(vars(args))                                                         # 将参数和值转化为字典的形式 

parser.get_default('foo')                                                 # 获取
parser.print_help()                                                       # 打印使用帮助

python a.py --foo ww  --aa 40 xuesong 27                                  # 执行此脚本


#-------------------------------------------------------- Example
# https://www.cnblogs.com/piperck/p/8446580.html

parser.add_argument('--ver','-v',action='store_true',help="帮助信息",required=True,type="str",nargs=1)

dest        #设置选项value解析出后放到哪个属性 ( 当对选项赋值后传递到代码内的parser属性的名字 )
action	    #表示值赋予键的方式，，action意思是当读取的参数中出现指定参数的时候的行为
            #'count' 将参数出现次数作为参数值
            #'append' 将每次出现的该参数后的值都存入同一个数组再赋值（多个参数叠加为列表）
            # 可选参数需设置 action='store_true' 不加参数为True 
required    #必需参数，通常-f这样的选项是可选的，但是如果required=True那么就是必须的了
type        #指定参数类型
help		#可以写帮助信息 
choices     #设置参数的范围，如果choice中的类型不是字符串，要指定type表示该参数能接受的值只能来自某几个值候选值中，除此之外会报错，用choice参数即可
nargs       #指定这个参数后面的value有多少个，默认为1 ( nargs还可以'*'用来表示如果有该位置参数输入的话，之后所有的输入都将作为该位置参数的值；‘+’表示读取至少1个该位置参数。'?'表示该位置参数要么没有，要么就只要一个 )