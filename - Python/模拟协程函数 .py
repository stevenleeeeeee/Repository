class Future:

    def __iter__(self):
        print('enter Future ...')
        print('foo 挂起在yield处 ')
        yield self
        print('foo 恢复执行')
        print('exit Future ...')
        return 'future'

    __await__ = __iter__

class Task:

    def __init__(self, cor, *, loop=None):
        self.cor = cor
        self._loop = loop

    def _step(self):
        cor = self.cor
        try:
            result = cor.send(None)
        except StopIteration as e:
            self._loop.close()
        except Exception as e:
            pass

class Loop:

    def __init__(self):
        self._stop = False

    def create_task(self, cor):
        task = Task(cor, loop = self)
        return task

    def run_until_complete(self, task):
        while not self._stop:
            task._step()

    def close(self):
        self._stop = True

async def foo():
    print('enter foo ...')
    await bar()
    print('exit foo ...')

async def bar():
    future = Future()
    print('enter bar ...')
    await future
    print('exit bar ...')

if __name__ == '__main__':
    
    f = foo()
    loop = Loop()
    task = loop.create_task(f)
    loop.run_until_complete(task)

# 执行结果：

# enter foo ...
# enter bar ...
# enter Future ...
# foo 挂起在yield处 
# foo 恢复执行
# exit Future ...
# exit bar ...
# exit foo ...