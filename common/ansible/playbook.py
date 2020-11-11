import json
import sys
import os
from collections import namedtuple
from optparse import Values

# https://docs.ansible.com/ansible/latest/dev_guide/developing_api.html#python-api
# 核心类
# 用于读取YAML和JSON格式的文件
from pathlib import Path

from ansible.parsing.dataloader import DataLoader
# 用于存储各类变量信息,用来管理变量，包括主机、组、扩展等变量
from ansible.vars.manager import VariableManager
# 用于导入资产文件
from ansible.inventory.manager import InventoryManager
# 操作单个主机信息
from ansible.inventory.host import Host
# 操作单个主机组信息
from ansible.inventory.group import Group
# 存储执行hosts的角色信息
from ansible.playbook.play import Play
# ansible底层用到的任务队列
from ansible.executor.task_queue_manager import TaskQueueManager
# 核心类执行playbook
from ansible.executor.playbook_executor import PlaybookExecutor
# 状态回调，成功失败的状态
from ansible.plugins.callback import CallbackBase

from ansible import context
from ansible.module_utils.common.collections import ImmutableDict


class PlaybookCallbackBase(CallbackBase):
    """
    playbook的callback改写，格式化输出playbook执行结果
    """
    CALLBACK_VERSION = 2.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_ok = {}
        self.task_unreachable = {}
        self.task_failed = {}
        self.task_skipped = {}
        self.task_status = {}

    def v2_runner_on_unreachable(self, result):
        """
        重写 unreachable 状态
        :param result:  这是父类里面一个对象，这个对象可以获取执行任务信息
        """
        self.task_unreachable[result._host.get_name()] = result

    def v2_runner_on_ok(self, result, *args, **kwargs):
        """
        重写 ok 状态
        :param result:
        """
        self.task_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result, *args, **kwargs):
        """
        重写 failed 状态
        :param result:
        """
        self.task_failed[result._host.get_name()] = result

    def v2_runner_on_skipped(self, result):
        self.task_skipped[result._host.get_name()] = result

    # def v2_playbook_on_stats(self, stats):
    #     hosts = sorted(stats.processed.keys())
    #     for h in hosts:
    #         t = stats.summarize(h)
    #         self.task_status[h] = {
    #             "ok": t["ok"],
    #             "changed": t["changed"],
    #             "unreachable": t["unreachable"],
    #             "skipped": t["skipped"],
    #             "failed": t["failed"],
    #         }


class AnsiblePlaybook():
    def __init__(self,
            # 上下文
            connection='smart',  # 连接方式 local 本地方式，smart ssh方式
            remote_user = None,  # 远程用户
            ack_pass = None,  # 提示输入密码
            sudo = None,
            sudo_user = None,
            ask_sudo_pass = None,
            module_path = None,  # 模块路径，可以指定一个自定义模块的路径
            become = None,  # 是否提权
            become_method = None,  # 提权方式 默认 sudo 可以是 su
            become_user = None,  # 提权后，要成为的用户，并非登录用户
            check = False,
            diff = False,
            listhosts = None,
            listtasks = None,
            listtags = None,
            verbosity = 3,
            syntax = None,
            start_at_task = None,
            inventory = None,
        ):
        # 函数文档注释
        """
        初始化函数，定义的默认的选项值，
        在初始化的时候可以传参，以便覆盖默认选项的值
        """
        context.CLIARGS = ImmutableDict(
            connection=connection,
            remote_user=remote_user,
            ack_pass=ack_pass,
            sudo=sudo,
            sudo_user=sudo_user,
            ask_sudo_pass=ask_sudo_pass,
            module_path=module_path,
            become=become,
            become_method=become_method,
            become_user=become_user,
            check=check,
            verbosity=verbosity,
            listhosts=listhosts,
            listtasks=listtasks,
            listtags=listtags,
            syntax=syntax,
            start_at_task=start_at_task,
        )

        self.rogram_pwd = str(Path(__file__).resolve().parent)
        self.sep = os.sep
        self.inventory_file = self.rogram_pwd + self.sep + 'hosts'

    def run_playbook(self,hostip,file,ssh_user,ssh_pwd,extra_vars,ssh_port=22):
        """
            调用 playbooks
            调用playboo大致和调用ad-hoc相同，只是真正调用的是使用PlaybookExecutor
            :return:
        """
        self.hostip = hostip
        self.playbook_file = self.rogram_pwd + self.sep + file
        self.ssh_port = ssh_port
        self.ssh_user = ssh_user
        self.ssh_pwd = ssh_pwd
        self.extra_vars = extra_vars


        # 资产配置信息
        # InventoryManager类的调用方式
        dl = DataLoader()
        # loader= 表示是用什么方式来读取文件  sources=就是资产文件列表，里面可以是相对路径也可以是绝对路径
        # sources 如果为空会抛出一个WARNING 建议使用一个hosts文件 文件可以为空
        im = InventoryManager(loader=dl, sources=[self.inventory_file])
        # VariableManager类的调用方式
        vm = VariableManager(loader=dl, inventory=im)

        # 动态添加主机
        my_host = Host(name=self.hostip)
        im.add_host(host=self.hostip)

        # 动态添加主机变量
        vm.set_host_variable(host=self.hostip, varname="ansible_ssh_host", value=self.hostip)
        vm.set_host_variable(host=self.hostip, varname="ansible_ssh_port", value=self.ssh_port)
        vm.set_host_variable(host=self.hostip, varname="ansible_ssh_user", value=self.ssh_user)
        vm.set_host_variable(host=self.hostip, varname="ansible_ssh_pass", value=self.ssh_pwd)

        # 添加扩展变量
        vm.extra_vars['host'] = self.hostip
        for i in self.extra_vars:
            vm.extra_vars[i] = extra_vars[i]

        passwords = dict()  # 这个可以为空，但必须有此参数

        playbook = PlaybookExecutor(playbooks=[self.playbook_file,], inventory=im, variable_manager=vm, loader=dl,passwords=passwords)
        playbook_callback = PlaybookCallbackBase()
        playbook._tqm._stdout_callback = playbook_callback  # 配置callback
        # result = playbooks.run()
        # print(result)
        playbook.run()
        # print(callback.task_ok.items())  # 它会返回2个东西，一个主机一个是执行结果对象
        result_raw = {"ok": {}, "failed": {}, "unreachable": {}, "skipped": {}, "status": {}}
        for host, result in playbook_callback.task_ok.items():
            result_raw["ok"][host] = result._result

        for host, result in playbook_callback.task_failed.items():
            result_raw["failed"][host] = result._result

        for host, result in playbook_callback.task_unreachable.items():
            result_raw["unreachable"][host] = result._result

        for host, result in playbook_callback.task_skipped.items():
            result_raw["skipped"][host] = result._result

        for host, result in playbook_callback.task_status.items():
            result_raw["status"][host] = result._result

        # 最终打印结果，并且使用 JSON 继续格式化
        # print(json.dumps(result_raw, indent=4))
        return json.dumps(result_raw)


if __name__ == "__main__":
    # playbooks(hostip='182.61.17.159',file='playbooks/os.yml',ssh_port=22,ssh_user='testuser',ssh_pwd='Vinc55#67',extra_vars=dict(version='1.0',os='linux'))

    ansible1 = AnsiblePlaybook()
    result = ansible1.run_playbook(hostip='182.61.17.159', file='playbooks/os.yml', ssh_user='testuser', ssh_pwd='Vinc55#67', extra_vars=dict(version='1.0', os='linux'))
    print(result)

