import json
import sys
from collections import namedtuple
from optparse import Values

# https://docs.ansible.com/ansible/latest/dev_guide/developing_api.html#python-api
# 核心类
# 用于读取YAML和JSON格式的文件
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

def playbook(host):
    connection = 'smart'  # 连接方式 local 本地方式，smart ssh方式
    remote_user = None  # 远程用户
    ack_pass = None  # 提示输入密码
    sudo = None
    sudo_user = None
    ask_sudo_pass = None
    module_path = None  # 模块路径，可以指定一个自定义模块的路径
    become = None  # 是否提权
    become_method = None # 提权方式 默认 sudo 可以是 su
    become_user = None # 提权后，要成为的用户，并非登录用户
    check = False
    diff = False
    listhosts = None
    listtasks = None
    listtags = None
    verbosity = 3
    syntax = None
    start_at_task = None
    inventory = None

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
    """
    调用 playbook
    调用playboo大致和调用ad-hoc相同，只是真正调用的是使用PlaybookExecutor
    :return:
    """
    host = host

    # 资产配置信息
    # InventoryManager类的调用方式
    dl = DataLoader()
    # loader= 表示是用什么方式来读取文件  sources=就是资产文件列表，里面可以是相对路径也可以是绝对路径
    # sources 如果为空会抛出一个WARNING 建议使用一个hosts文件 文件可以为空
    im = InventoryManager(loader=dl, sources=["hosts"])
    # VariableManager类的调用方式
    vm = VariableManager(loader=dl, inventory=im)

    # 动态添加主机
    im.add_host(host=host)

    # 动态添加主机变量
    vm.set_host_variable(host=host, varname="ansible_ssh_host", value='182.61.17.159')
    vm.set_host_variable(host=host, varname="ansible_ssh_port", value=22)
    vm.set_host_variable(host=host, varname="ansible_ssh_user", value='root')
    vm.set_host_variable(host=host, varname="ansible_ssh_pass", value='Vinc08#22')


    passwords = dict()  # 这个可以为空，因为在hosts文件中


    playbook = PlaybookExecutor(playbooks=["./os.yml"], inventory=im, variable_manager=vm, loader=dl,passwords=passwords)
    playbook_callback = PlaybookCallbackBase()
    playbook._tqm._stdout_callback = playbook_callback  # 配置callback
    # result = playbook.run()
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
    print(json.dumps(result_raw, indent=4))
    return json.dumps(result_raw)


if __name__ == "__main__":
    playbook(host='182.61.17.159')
