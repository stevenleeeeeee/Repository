from ansible import constants
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback import CallbackBase
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
import json
import IPy

'''
实现任意IP执行模块或playbook
支持2.4以上版本
'''

class ModelResultsCollector(CallbackBase):
    '''
    对Ansible Model执行后的返回信息进行收集
    '''
    def __init__(self, *args, **kwargs):
        super(ModelResultsCollector, self).__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    # 记录不可达
    def v2_runner_on_unreachable(self, result):
        self.host_unreachable[result._host.get_name()] = result

    # 记录成功
    def v2_runner_on_ok(self, result, *args, **kwargs):
        self.host_ok[result._host.get_name()] = result

    # 记录失效
    def v2_runner_on_failed(self, result, *args, **kwargs):
        self.host_failed[result._host.get_name()] = result


class PlayBookResultsCollector(CallbackBase):
    '''
    对Ansible PlayBook执行后的返回信息进行收集
    '''
    CALLBACK_VERSION = 2.0

    def __init__(self, *args, **kwargs):
        super(PlayBookResultsCollector, self).__init__(*args, **kwargs)
        self.task_ok = {}
        self.task_skipped = {}
        self.task_failed = {}
        self.task_status = {}
        self.task_unreachable = {}

    # 
    def v2_runner_on_ok(self, result, *args, **kwargs):
        self.task_ok[result._host.get_name()] = result

    # 
    def v2_runner_on_failed(self, result, *args, **kwargs):
        self.task_failed[result._host.get_name()] = result

    # 
    def v2_runner_on_unreachable(self, result):
        self.task_unreachable[result._host.get_name()] = result

    # 
    def v2_runner_on_skipped(self, result):
        self.task_ok[result._host.get_name()] = result

    # 
    def v2_playbook_on_stats(self, stats):
        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)
            self.task_status[h] = {
                "ok": t['ok'],
                "changed": t['changed'],
                "unreachable": t['unreachable'],
                "skipped": t['skipped'],
                "failed": t['failures']
            }


class ANSRunner(object):
    """
    This is a General object for parallel execute modules.
    """

    def __init__(self, ips=None, *args, **kwargs):
        self.ips = ips
        self.inventory = None
        self.variable_manager = None
        self.loader = None
        self.options = None
        self.passwords = None
        self.callback = None
        self.__initializeData()
        self.results_raw = {}

    # 判断是否为IP地址
    def is_ip(self,address):
        try:
            IPy.IP(address)
            return True
        except Exception as e:
            return False

    # 用逗号分割的IP组成的字符串
    def list_to_str(self,ips):
        ipsstr = ','.join(ips)
        if len(ips) == 1:
            ipsstr += ','
        return ipsstr

    # 对IP列表组成的字符串进行检查
    def list_ip_check(self,ips):
        ipslist = ips
        ipslist_len = len(ips)
        if ipslist_len > 1:
            for ip in ipslist:
                if not self.is_ip(ip):
                    ipslist.remove(ip)
        return ipslist

    # 
    def ips_cov_str(self):
        if not self.ips:
            self.ips = "127.0.0.1"

        if isinstance(self.ips,list):
            self.ips = self.list_ip_check(self.ips)
            self.ips = self.list_to_str(self.ips)

        elif isinstance(self.ips,str):
            ipslist = self.ips.split(',')
            ipslist = self.list_ip_check(ipslist)
            self.ips = self.list_to_str(ipslist)



    def __initializeData(self):
        """
        初始化ansible
        """

        # 命名元祖
        Options = namedtuple('Options', ['connection', 'module_path', 'forks', 'timeout', 'remote_user',
                                         'ask_pass', 'private_key_file', 'ssh_common_args', 'ssh_extra_args',
                                         'sftp_extra_args',
                                         'scp_extra_args', 'become', 'become_method', 'become_user', 'ask_value_pass',
                                         'verbosity',
                                         'check', 'listhosts', 'listtasks', 'listtags', 'syntax', 'diff'])


        self.options = Options(connection='smart', module_path=None, forks=100, timeout=10,
                               remote_user='root', ask_pass=False, private_key_file=None, ssh_common_args=None,
                               ssh_extra_args=None,
                               sftp_extra_args=None, scp_extra_args=None, become=None, become_method=None,
                               become_user='root', ask_value_pass=False, verbosity=None, check=False, listhosts=False,
                               listtasks=False, listtags=False, syntax=False, diff=True)

        self.loader = DataLoader()
        self.ips_cov_str()
        self.inventory = InventoryManager(loader=self.loader, sources='%s'%(self.ips))
        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)

    def run_model(self, module_name, module_args):
        """
        run module from andible ad-hoc.
        module_name: ansible module_name
        module_args: ansible module args
        """

        self.ips_cov_str()

        play_source = dict(
            name="Ansible Play",
            hosts=self.ips,
            gather_facts='no',
            tasks=[dict(action=dict(module=module_name, args=module_args))]
        )

        play = Play().load(play_source, variable_manager=self.variable_manager, loader=self.loader)
        tqm = None
        self.callback = ModelResultsCollector()
        import traceback
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=self.passwords,
                stdout_callback="minimal",
            )
            tqm._stdout_callback = self.callback
            constants.HOST_KEY_CHECKING = False  # 关闭第一次使用ansible连接客户端时输入命令
            tqm.run(play)
        except Exception as err:
            print(traceback.print_exc())
        finally:
            if tqm is not None:
                tqm.cleanup()

    def run_playbook(self, playbook_path, extra_vars=None):
        """
        运行playbook
        """
        try:
            self.callback = PlayBookResultsCollector()
            if extra_vars:
                self.variable_manager.extra_vars = extra_vars
            executor = PlaybookExecutor(
                playbooks=[playbook_path], inventory=self.inventory, variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options, passwords=self.passwords,
            )
            executor._tqm._stdout_callback = self.callback
            constants.HOST_KEY_CHECKING = False  # 关闭第一次使用ansible连接客户端时输入命令
            executor.run()
        except Exception as err:
            return False

    def get_model_result(self):
        self.results_raw = {'success': {}, 'failed': {}, 'unreachable': {}}
        for host, result in self.callback.host_ok.items():
            hostvisiable = host.replace('.', '_')
            self.results_raw['success'][hostvisiable] = result._result

        for host, result in self.callback.host_failed.items():
            hostvisiable = host.replace('.', '_')
            self.results_raw['failed'][hostvisiable] = result._result

        for host, result in self.callback.host_unreachable.items():
            hostvisiable = host.replace('.', '_')
            self.results_raw['unreachable'][hostvisiable] = result._result

        return self.results_raw

    def get_playbook_result(self):
        self.results_raw = {'skipped': {}, 'failed': {}, 'ok': {}, "status": {}, 'unreachable': {}, "changed": {}}
        for host, result in self.callback.task_ok.items():
            self.results_raw['ok'][host] = result._result

        for host, result in self.callback.task_failed.items():
            self.results_raw['failed'][host] = result._result

        for host, result in self.callback.task_status.items():
            self.results_raw['status'][host] = result

        for host, result in self.callback.task_skipped.items():
            self.results_raw['skipped'][host] = result._result

        for host, result in self.callback.task_unreachable.items():
            self.results_raw['unreachable'][host] = result._result
        return self.results_raw


if __name__ == '__main__':
    a="192.168.111.137,127.0.0.1"
    rbt = ANSRunner(a)
    # rbt.run_playbook(playbook_path='test.yml')
    # result = json.dumps(rbt.get_playbook_result(),indent=4)
    rbt.run_model('shell','uptime')
    result = json.dumps(rbt.get_model_result(),indent=4)
    print(result)