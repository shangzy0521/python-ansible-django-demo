import json
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
# ansible底层用到的任务队列
from ansible.executor.task_queue_manager import TaskQueueManager
# 核心类执行playbook
from ansible.executor.playbook_executor import PlaybookExecutor
# 状态回调，成功失败的状态
from ansible.plugins.callback import CallbackBase

from ansible import context
from ansible.module_utils.common.collections import ImmutableDict

class AdhocCallbackBase(CallbackBase):
    """
    通过api调用ac-hoc的时候输出结果很多时候不是很明确或者说不是我们想要的结果，主要它还是输出到STDOUT，而且通常我们是在工程里面执行
    这时候就需要后台的结果前端可以解析，正常的API调用输出前端很难解析。 对比之前的执行 adhoc()查看区别。
    为了实现这个目的就需要重写CallbackBase类，需要重写下面三个方法
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # python3中重载父类构造方法的方式，在Python2中写法会有区别。
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def v2_runner_on_unreachable(self, result):
        """
        重写 unreachable 状态
        :param result:  这是父类里面一个对象，这个对象可以获取执行任务信息
        """
        self.host_unreachable[result._host.get_name()] = result

    def v2_runner_on_ok(self, result, *args, **kwargs):
        """
        重写 ok 状态
        :param result:
        """
        self.host_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result, *args, **kwargs):
        """
        重写 failed 状态
        :param result:
        """
        self.host_failed[result._host.get_name()] = result

def ad_hoc(host,ssh_port,ssh_user,ssh_pwd,module,args):
    """
    ad-hoc 调用
    资产配置信息  这个是通过 InventoryManager和VariableManager 定义
    执行选项 这个是通过namedtuple来定义(已不适用)
    执行对象和模块 通过dict()来定义
    定义play 通过Play来定义
    最后通过 TaskQueueManager 的实例来执行play
    :return:
    """
    host = host
    ssh_port = ssh_port
    ssh_user = ssh_user
    ssh_pwd = ssh_pwd
    module = module
    args = args

    # 上下文
    connection = 'smart'  # 连接方式 local 本地方式，smart ssh方式
    remote_user = None  # 远程用户
    ack_pass = None  # 提示输入密码
    sudo = None
    sudo_user = None
    ask_sudo_pass = None
    module_path = None  # 模块路径，可以指定一个自定义模块的路径
    become = None  # 是否提权
    become_method = None  # 提权方式 默认 sudo 可以是 su
    become_user = None  # 提权后，要成为的用户，并非登录用户
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
    vm.set_host_variable(host=host, varname="ansible_ssh_host", value=host)
    vm.set_host_variable(host=host, varname="ansible_ssh_port", value=ssh_port)
    vm.set_host_variable(host=host, varname="ansible_ssh_user", value=ssh_user)
    vm.set_host_variable(host=host, varname="ansible_ssh_pass", value=ssh_pwd)

    vm.extra_vars = '{"repo":{"branch":"exec_refactor"}}'

    # play的执行对象和模块，这里设置hosts，其实是因为play把play_source和资产信息关联后，执行的play的时候它会去资产信息中设置的sources的hosts文件中
    # 找你在play_source中设置的hosts是否在资产管理类里面。
    play_source = dict(name="Ansible ad-hoc Play",  # 任务名称
                       hosts=host,  # 目标主机，可以填写具体主机也可以是主机组名称
                       gather_facts="no",  # 是否收集配置信息
                       # tasks是具体执行的任务，列表形式，每个具体任务都是一个字典
                       tasks=[dict(action=dict(module=module, args=args))])

    # 定义play
    play = Play().load(play_source, variable_manager=vm, loader=dl)

    passwords = dict()  # 这个可以为空，因为在hosts文件中
    adhoc_callback = AdhocCallbackBase()  # 实例化自定义callback

    tqm = TaskQueueManager(
        inventory=im,
        variable_manager=vm,
        loader=dl,
        passwords=passwords,
        stdout_callback=adhoc_callback  # 配置使用自定义callback
    )

    # result = tqm.run(play)
    # print(result)
    tqm.run(play)
    # print(mycallback.host_ok.items())  # 它会返回2个东西，一个主机一个是执行结果对象
    # 定义数据结构
    result_raw = {"success": {}, "failed": {}, "unreachable": {}}
    # 如果成功那么  mycallback.host_ok.items() 才可以遍历，上面的任务肯定能成功所以我们就直接遍历这个
    for host, result in adhoc_callback.host_ok.items():
        result_raw["success"][host] = result._result

    for host, result in adhoc_callback.host_failed.items():
        result_raw["failed"][host] = result._result

    for host, result in adhoc_callback.host_unreachable.items():
        result_raw["unreachable"][host] = result._result

    # 最终打印结果，并且使用 JSON 继续格式化
    print(json.dumps(result_raw, indent=4))
    return json.dumps(result_raw)

if __name__ == "__main__":
    # ad_hoc(host='182.61.17.159', ssh_port=22, ssh_user='root', ssh_pwd='Vinc08#22', module='shell', args='whoami')
    ad_hoc(host='182.61.17.159', ssh_port=22, ssh_user='root', ssh_pwd='Vinc08#22', module='shell', args='echo ${aa}')