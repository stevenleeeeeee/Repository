#!/usr/bin/env python

import argparse
parser = argparse.ArgumentParser(prog='usage_name', description='开头打印', epilog="结束打印")  #创建解析对象
# prog:  程序名
# description: help时显示的开始文字
# epilog: help时显示的结尾文字
# add_help: 是否增加-h/--help选项，默认True

parser.add_argument('-f', '--foo', help='foo help', action='append',required=True,type=str, choices=['a', 'b'])      
# 可选参数需设置 action='store_true' 不加参数为True  
# action='append' 多个参数可叠加为列表
# action形参的值说明: 'count' 将参数出现次数作为参数值、'append' 将每次出现的该参数后的值都存入同一个数组再赋值
# required=True 必须参数
# type 指定参数类型
# choices 指定仅能使用的选项的参数范围

parser.add_argument('-file', choices=['test1','test2'], dest='world')
# dest 设置当对-file选项赋值后，传递到代码内的parser属性的名字

parser.add_argument('file', type=argparse.FileType('r'))    
# 读取文件，打印文件内容
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


