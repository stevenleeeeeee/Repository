#-*- coding:utf-8 -*-

from concurrent import futures
 
def test(num):
    import time
    return time.ctime(),num

def muti_exec(m,n):
    # m 并发次数
    # n 运行次数
 
    with futures.ProcessPoolExecutor(max_workers=m) as executor: #多进程
    #with futures.ThreadPoolExecutor(max_workers=m) as executor: #多线程
        executor_dict=dict((executor.submit(test,times), times) for times in range(m*n))

    # print('--------------- debug ---------------')
    # for k,v in executor_dict.items():
    #     print(,"     ",v)
    # print('--------------- debug ---------------')

    for future in futures.as_completed(executor_dict):
        times = executor_dict[future]
        if future.exception() is not None:
            print('%r generated an exception: %s' % (times,future.exception()))
        else:
            print('RunTimes:%d,Res:%s'% (times, future.result()))
 
if __name__ == '__main__':
    muti_exec(5,1)
 
# >>>
# RunTimes:0,Res:('Tue Jan 17 15:56:53 2017', 0)
# RunTimes:4,Res:('Tue Jan 17 15:56:53 2017', 4)
# RunTimes:3,Res:('Tue Jan 17 15:56:53 2017', 3)
# RunTimes:1,Res:('Tue Jan 17 15:56:53 2017', 1)
# RunTimes:2,Res:('Tue Jan 17 15:56:53 2017', 2)