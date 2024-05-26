#!/usr/bin/env python3

import argparse
import contextlib
import getpass
import logging
import os
import platform
import subprocess
import sys
import time


PEER_NAME = 'urfu'


def write_peer_file(login):
    peer_file = f'/etc/ppp/peers/{PEER_NAME}'
    with open(peer_file, 'w') as peer_out:
        print(f"""
pty "pptp ras.urfu.ru --nolaunchpppd"
name "{login}"
maxfail 1
persist
require-mschap-v2
defaultroute
replacedefaultroute
noauth
""", file=peer_out)
    logging.info('Wrote connection info to %s', peer_file)
    return peer_file


@contextlib.contextmanager
def chap_secrets_file():
    path = '/etc/ppp/chap-secrets'
    if os.path.exists(path):
        os.unlink(path)
    os.mkfifo(path, mode=0o400)
    try:
        yield path
    finally:
        os.unlink(path)


def write_chap_secrets(chap_secrets_file, login, passwd):
    for _ in range(2):
        with open(chap_secrets_file, 'wt') as csf_out:
            print(f'"{login}" * "{passwd}"', file=csf_out)
        while subprocess.call(['lsof', chap_secrets_file]) == 0:
            logging.warning('%s still open', chap_secrets_file)
            time.sleep(0.1)


class RedactingFormatter(object):
    def __init__(self, orig_formatter, patterns):
        self.orig_formatter = orig_formatter
        self._patterns = patterns

    def format(self, record):
        msg = self.orig_formatter.format(record)
        for pattern in self._patterns:
            msg = msg.replace(pattern, "***")
        return msg

    def __getattr__(self, attr):
        return getattr(self.orig_formatter, attr)


def connect_time(arg):
    return 0 if arg == 'inf' else int(arg)


def parse_args(raw_args):
    parser = argparse.ArgumentParser(description='Connect UrFU VPN')
    parser.add_argument('LOGIN', help='Your UrFU login')
    parser.add_argument(
        '--connect-time', default=90, type=connect_time,
        help='Connect time, in minutes. '
             'Use "inf" to connect without time limit',
    )
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args(raw_args[1:])
    if not args.LOGIN:
        parser.error('login cannot be empty')

    passwd = getpass.getpass('Your UrFU password: ')

    return args, passwd


def connect_on_linux(login, passwd, connect_time):
    write_peer_file(login)

    with chap_secrets_file() as csf:
        ppp_cmd = ['pppd', 'nodetach', 'call', PEER_NAME]
        logging.info('Connecting: %s', ppp_cmd)
        ppp = subprocess.Popen(ppp_cmd)

        write_chap_secrets(csf, login, passwd)

        try:
            try:
                return ppp.wait(connect_time * 60 if connect_time else None)
            except subprocess.TimeoutExpired:
                logging.warning('Session ended, disconnecting')
                raise KeyboardInterrupt
        except KeyboardInterrupt:
            try:
                ppp.terminate()
                ppp.wait()
            except BaseException:
                logging.exception('Failed to stop pppd')
                return 1


def write_phonebook_file():
    user_pbk_path = os.path.join(os.environ['APPDATA'], f'{PEER_NAME}.pbk')

    os.makedirs(os.path.dirname(user_pbk_path), exist_ok=True)
    with open(user_pbk_path, 'w') as pbk_output:
        print(f"""
[{PEER_NAME}]
Encoding=1
PBVersion=6
Type=2
AutoLogon=0
UseRasCredentials=1
LowDateTime=-937161168
HighDateTime=31063682
DialParamsUID=796328
Guid=3471DF70F3613846A965908540D2B400
VpnStrategy=1
ExcludedProtocols=0
LcpExtensions=1
DataEncryption=8
SwCompression=0
NegotiateMultilinkAlways=0
SkipDoubleDialDialog=0
DialMode=0
OverridePref=15
RedialAttempts=3
RedialSeconds=60
IdleDisconnectSeconds=0
RedialOnLinkFailure=1
CallbackMode=0
CustomDialDll=
CustomDialFunc=
CustomRasDialDll=
ForceSecureCompartment=0
DisableIKENameEkuCheck=0
AuthenticateServer=0
ShareMsFilePrint=1
BindMsNetClient=1
SharedPhoneNumbers=0
GlobalDeviceSettings=0
PrerequisiteEntry=
PrerequisitePbk=
PreferredPort=VPN4-0
PreferredDevice=WAN Miniport (PPTP)
PreferredBps=0
PreferredHwFlow=1
PreferredProtocol=1
PreferredCompression=1
PreferredSpeaker=1
PreferredMdmProtocol=0
PreviewUserPw=1
PreviewDomain=1
PreviewPhoneNumber=0
ShowDialingProgress=1
ShowMonitorIconInTaskBar=1
CustomAuthKey=0
AuthRestrictions=512
IpPrioritizeRemote=1
IpInterfaceMetric=0
IpHeaderCompression=0
IpAddress=0.0.0.0
IpDnsAddress=0.0.0.0
IpDns2Address=0.0.0.0
IpWinsAddress=0.0.0.0
IpWins2Address=0.0.0.0
IpAssign=1
IpNameAssign=1
IpDnsFlags=0
IpNBTFlags=1
TcpWindowSize=0
UseFlags=2
IpSecFlags=0
IpDnsSuffix=
Ipv6Assign=1
Ipv6Address=::
Ipv6PrefixLength=0
Ipv6PrioritizeRemote=0
Ipv6InterfaceMetric=0
Ipv6NameAssign=1
Ipv6DnsAddress=::
Ipv6Dns2Address=::
Ipv6Prefix=0000000000000000
Ipv6InterfaceId=0000000000000000
DisableClassBasedDefaultRoute=0
DisableMobility=0
NetworkOutageTime=0
IDI=
IDR=
ImsConfig=0
IdiType=0
IdrType=0
ProvisionType=0
PreSharedKey=
CacheCredentials=0
NumCustomPolicy=0
NumEku=0
UseMachineRootCert=0
Disable_IKEv2_Fragmentation=0
PlumbIKEv2TSAsRoutes=0
NumServers=0
RouteVersion=1
NumRoutes=0
NumNrptRules=0
AutoTiggerCapable=0
NumAppIds=0
NumClassicAppIds=0
SecurityDescriptor=
ApnInfoProviderId=
ApnInfoUsername=
ApnInfoPassword=
ApnInfoAccessPoint=
ApnInfoAuthentication=1
ApnInfoCompression=0
DeviceComplianceEnabled=0
DeviceComplianceSsoEnabled=0
DeviceComplianceSsoEku=
DeviceComplianceSsoIssuer=
WebAuthEnabled=0
WebAuthClientId=
FlagsSet=0
Options=0
DisableDefaultDnsSuffixes=0
NumTrustedNetworks=0
NumDnsSearchSuffixes=0
PowershellCreatedProfile=1
ProxyFlags=0
ProxySettingsModified=0
ProvisioningAuthority=
AuthTypeOTP=0
GREKeyDefined=0
NumPerAppTrafficFilters=0
AlwaysOnCapable=0
DeviceTunnel=0
PrivateNetwork=0

NETCOMPONENTS=
ms_msclient=1
ms_server=1

MEDIA=rastapi
Port=VPN4-0
Device=WAN Miniport (PPTP)

DEVICE=vpn
PhoneNumber=ras.urfu.ru
AreaCode=
CountryCode=0
CountryID=0
UseDialingRules=0
Comment=
FriendlyName=
LastSelectedPhone=0
PromoteAlternates=0
TryNextAlternateOnFail=1

""", file=pbk_output)
    logging.info('Wrote connection info to %s', user_pbk_path)
    return user_pbk_path


def connect_on_windows(login, passwd, connect_time):
    pbk_path = write_phonebook_file()
    connect_cmd = [
        'rasdial', PEER_NAME, login, passwd, f'/phonebook:{pbk_path}'
    ]
    logging.info('Connecting: %s', connect_cmd)
    connect_result = subprocess.run(connect_cmd, text=True)
    if connect_result.returncode != 0:
        logging.error('Connection failed')
        return 1

    try:
        if connect_time:
            time.sleep(60 * connect_time)
        else:
            while True:
                time.sleep(60)
        logging.warning('Session ended, disconnecting')
        raise KeyboardInterrupt
    except KeyboardInterrupt:
        disconnect_cmd = ['rasdial', PEER_NAME, '/disconnect']
        logging.info('Disonnecting: %s', disconnect_cmd)
        disconnect_result = subprocess.run(disconnect_cmd, text=True)
        if disconnect_result.returncode != 0:
            logging.warning('Disconnect failed')
            return 1


def setup_logging(args, passwd):
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARN)

    for h in logging.root.handlers:
        h.setFormatter(RedactingFormatter(h.formatter, patterns=[passwd]))


def main(raw_args):
    system = platform.system()
    connect_fn = {
        'Linux': connect_on_linux,
        'Windows': connect_on_windows,
    }.get(system)
    assert connect_fn, f'Do not know how to connect on "{system}" platform'

    args, passwd = parse_args(raw_args)
    setup_logging(args, passwd)

    return connect_fn(args.LOGIN, passwd, args.connect_time)


if __name__ == '__main__':
    sys.exit(main(sys.argv))