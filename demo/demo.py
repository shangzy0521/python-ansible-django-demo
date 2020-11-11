from common.ansible.playbook import AnsiblePlaybook
from common.ansible.adhoc import AnsibleAdhoc

def test():
    ansible1 = AnsibleAdhoc()
    result = ansible1.run_adhoc(hostip='182.61.17.159', ssh_user='testuser', ssh_pwd='Vinc55#67',
                                extra_vars=dict(version='1.0', os='linux'), module='shell',
                                args='echo {{version}} {{os}}')
    print('----------')
    print(result)
    print('----------')

    ansible2 = AnsiblePlaybook()
    result = ansible2.run_playbook(hostip='182.61.17.159', file='common/ansible/playbook/os.yml', ssh_user='testuser',
                                   ssh_pwd='Vinc55#67', extra_vars=dict(version='1.0', os='linux'))
    print('~~~~~~~~~~')
    print(result)
    print('~~~~~~~~~~')

if __name__ == "__main__":

    ansible1 = AnsibleAdhoc()
    result = ansible1.run_adhoc(hostip='182.61.17.159', ssh_user='testuser', ssh_pwd='Vinc55#67',extra_vars=dict(version='1.0',os='linux'), module='shell', args='echo {{version}} {{os}}')
    print('----------')
    print(result)
    print('----------')

    ansible2 = AnsiblePlaybook()
    result = ansible2.run_playbook(hostip='182.61.17.159', file='playbook/os.yml', ssh_user='testuser',
                                   ssh_pwd='Vinc55#67', extra_vars=dict(version='1.0', os='linux'))
    print('~~~~~~~~~~')
    print(result)
    print('~~~~~~~~~~')
