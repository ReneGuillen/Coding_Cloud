import paramiko
import getpass
import time


def main():
    username = getpass.getuser()
    password = '/Users/' + username + '/.ssh/id_rsa.ppk'
    hostname = 'add-host'

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, key_filename=password)

    remote_connection = ssh.invoke_shell()
    remote_connection.send("6")
    remote_connection.send("mbox")
    output = remote_connection.recv(4096)
    buffer = ''
    buffer += output.decode()
    prompt = buffer.splitlines()[-1].strip()
    print(prompt)
    print('Connection Successful')


if __name__ == '__main__':
    main()
