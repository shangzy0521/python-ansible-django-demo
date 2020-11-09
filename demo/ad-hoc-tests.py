import sys
from collections import namedtuple
from optparse import Values

# 核心类
# 用于读取YAML和JSON格式的文件
from ansible.parsing.dataloader import DataLoader
# 用于存储各类变量信息
from ansible.vars.manager import VariableManager
# 用于导入资产文件
from ansible.inventory.manager import InventoryManager
# 操作单个主机信息
from ansible.inventory.host import Host
# 操作单个主机组信息
from ansible.inventory.group import Group
# 存储执行hosts的角色信息
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.playbook_executor import PlaybookExecutor

from ansible import context
from ansible.module_utils.common.collections import ImmutableDict

def ad_hoc(host,module,args):
    host = host
    module = module
    args = args
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

    # 此方式已不适用
    # Options = namedtuple("Options", ["connection", "remote_user", "ask_sudo_pass", "verbosity", "ack_pass",
    #                                  "module_path", "forks", "become", "become_method", "become_user", "check",
    #                                  "listhosts", "listtasks", "listtags", "syntax", "sudo_user", "sudo", "diff"
    # ])
    # options = Options(connection='smart', remote_user=None, ack_pass=None, sudo_user=None, forks=5, sudo=None,
    #                   ask_sudo_pass=False,verbosity=5, module_path=None, become=None, become_method=None,
    #                   become_user=None, check=False, diff=False,listhosts=None, listtasks=None, listtags=None,
    #                   syntax=None)
    options = {'verbosity': 0, 'connection': 'smart', 'timeout': 60,}
    ops = Values(options)
    context._init_global_context(ops)

    play_source = dict(name="Ansible Play",hosts='myhost', gather_facts="no",
                       tasks=[dict(action=dict(module=module, args=args))])

    play = Play().load(play_source, variable_manager=vm, loader=dl)
    passwords = dict()

    tqm = TaskQueueManager(inventory=im,variable_manager=vm,loader=dl, passwords=passwords,)

    result = tqm.run(play)
    print(result)

if __name__ == "__main__":
    ad_hoc(host='182.61.17.159', module='shell', args='whoami')