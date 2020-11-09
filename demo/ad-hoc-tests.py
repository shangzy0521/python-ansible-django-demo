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

# InventoryManager类的调用方式
dl = DataLoader()
# loader= 表示是用什么方式来读取文件  sources=就是资产文件列表，里面可以是相对路径也可以是绝对路径
# sources 如果为空会抛出一个WARNING 建议使用一个hosts文件 文件可以为空
im = InventoryManager(loader=dl, sources=["hosts"])
variable_manager = VariableManager(loader=dl, inventory=my_inventory)
# my_inventory.add_group('mygroup')
# my_group = Group(name='mygroup')

# my_host = Host(name='182.61.17.1599')
# my_inventory.add_host(host='myhost', group='mygroup')
my_inventory.add_host(host='myhost')

variable_manager.set_host_variable(host='myhost', varname="ansible_ssh_host", value='182.61.17.159')
variable_manager.set_host_variable(host='myhost', varname="ansible_ssh_port", value=22)
variable_manager.set_host_variable(host='myhost', varname="ansible_ssh_user", value='root')
variable_manager.set_host_variable(host='myhost', varname="ansible_ssh_pass", value='Vinc08#22')

# print(my_inventory.list_hosts())
# print(variable_manager.get_vars())
# Options = namedtuple("Options", ["connection", "remote_user", "ask_sudo_pass", "verbosity", "ack_pass",
#                                  "module_path", "forks", "become", "become_method", "become_user", "check",
#                                  "listhosts", "listtasks", "listtags", "syntax", "sudo_user", "sudo", "diff"
# ])
# options = Options(connection='smart', remote_user=None, ack_pass=None, sudo_user=None, forks=5, sudo=None,
#                   ask_sudo_pass=False,verbosity=5, module_path=None, become=None, become_method=None,
#                   become_user=None, check=False, diff=False,listhosts=None, listtasks=None, listtags=None,
#                   syntax=None)
options = {'verbosity': 0, 'connection': 'smart', 'timeout': 30,}
ops = Values(options)
context._init_global_context(ops)

play_source = dict(name="Ansible Play",hosts='myhost', gather_facts="no",
                   tasks=[dict(action=dict(module="shell", args="whoami"))])

play = Play().load(play_source, variable_manager=variable_manager, loader=dl)
passwords = dict()

tqm = TaskQueueManager(inventory=my_inventory,variable_manager=variable_manager,loader=dl, passwords=passwords,)


result = tqm.run(play)
print(result)