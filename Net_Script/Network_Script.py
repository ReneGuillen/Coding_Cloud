from netmiko import ConnectHandler
from netmiko import NetMikoAuthenticationException, NetMikoTimeoutException
import getpass
import sys


def run_initial_checks(output, net_connect):
    """
    run_initial_checks() sends a list of initial commands and parses to the output.
    param output: String use to parse and return all the outputs(logs).
    param net_connect: SSH Connection object needed to send commands to the network device.
    return:
        String with output of all the commands sent.
    """

    # List of initial commands to be send.
    commands = ['show clock', 'sh ver | section uptime', 'show bgp sum', 'show int des']

    # Loop to run every command and added to the output string to be later returned.
    for command in commands:
        output += net_connect.send_command(command) + '\n'
    output = run_ping_and_traceroute(output, net_connect)
    return output


def get_tunnel_interface(net_connect):
    """
    get_tunnel_interface() identifies Prod tunnel and its interface IP.
    param net_connect: SSH Connection object needed to send commands to the network device.
    return:
        output of Prod tunnel interface and the source and destination IPs.
    """

    # Send commands to identify Prod tunnel interface.
    search_tunnel = net_connect.send_command('sh int desc | I Prod')
    interface = search_tunnel.split()

    # Splits the string to get its interface and returns source + destination IPs.
    prod_interface = net_connect.send_command(f"show int {interface[0]} | i des")
    return prod_interface


def get_source_and_destination_ips(net_connect, output):
    """
    get_source_and_destination_IPs() calls get_tunnel_interface()
    to retrieve a list and split it + adding the output.
    param net_connect: SSH Connection object needed to send commands to the network device.
    param output: String use to parse and return all the outputs(logs).
    return:
        list of IPs where the destination and source can be retrieved.
        + output after parsing the command output.
    """
    # Splitting the IP list and parsing the command output.
    destination = get_tunnel_interface(net_connect)
    output += destination
    return destination.split(), output


def run_ping_and_traceroute(output, net_connect):
    """
    run_ping_and_traceRoute() uses source and destination IPs to run pings, traces
    and returns output.
    param output: String use to parse and return all the outputs(logs).
    param net_connect: SSH Connection object needed to send commands to the network device.
    return:
        ping and trace output after running commands on the network device.
    """

    # Gets a list of strings and retrieve source and destination IP + output.
    get_ips = get_source_and_destination_ips(net_connect, output)
    source_ip = get_ips[0][2]
    destination_ip = get_ips[0][5]
    output = get_ips[1]

    # Send Ping and TraceRoute Commands to the network device and returns the output.
    ping_command = f"ping {destination_ip} so {source_ip} re 500 si 1400"
    trace_command = f"traceroute {destination_ip} time 1"
    output += net_connect.send_command(ping_command, delay_factor=7)
    output += net_connect.send_command(trace_command)
    return output


def main():
    """
    main() gathers all information to connect to the network device, run checks
    and returns the output.
    returns:
        WAN logs from network device to verify if circuit is up and stable.
    """

    # Gathering credentials and information needed to ssh to network device.
    username = getpass.getuser()
    password = getpass.getpass('Please Enter Your Password: ')
    try:
        site_id = sys.argv[1]
        router_number = sys.argv[2]
        hostname = 'Collect your hostname device'
    except IndexError as error:
        print(error)
        print("Missing/Incorrect whid or v-router number. "
              "\nMake sure you correctly add: FC_Check.py whid #")
        return

    ssh_info = {
        'device_type': 'cisco_ios',
        'host': hostname,
        'username': username,
        'password': password,
        'secret': password
    }
    print("Thank you, trying to ssh and running checks now.. \nPlease wait for output.")

    # try to ssh and connect to device, if not returns possible authentication error.
    try:
        net_connect = ConnectHandler(**ssh_info)
        net_connect.enable()
    except (NetMikoAuthenticationException, NetMikoTimeoutException) as error:
        print(error)
        return

    # start running checks and if not, return timeout error. Circuit possible down.
    try:
        output = ''
        output = run_initial_checks(output, net_connect)
        print("\n" + output + "\nDone! Closing Connection")
    except IOError as error:
        print(error)
        print("Possible Hard Down issue, or Circuit having huge % of packet loss")
        return


if __name__ == '__main__':
    main()