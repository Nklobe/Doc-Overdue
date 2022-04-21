'''
Main script for Doc-Overdue

@package DocOverdue
'''
import os
import subprocess
import sys

print("#" * 40)
print("Starting Doc-Overdue")
print("#" * 40)


def bash_command(cmd):
    sp = subprocess.Popen(['/bin/bash', '-c', cmd], stdout=subprocess.PIPE)
    return sp.stdout.readlines()


def run_command(cmd):  # runs command and trims the output
    rawCMD = subprocess.run(cmd, capture_output=True)
    outCMD = rawCMD.stdout.splitlines()
    for c in range(len(outCMD)):
        outCMD[c] = outCMD[c].decode('utf-8')
        outCMD[c] = outCMD[c].replace('\'', '')
        #print(outCMD[c])
    return outCMD


def fetch_installed_packages():
    # gets all the install packages
    print_sign("Fetching installed packages")
    cmd = ["dpkg-query", "-f", "'${Package}\n'", "-W"]
    applicationList = run_command(cmd)
    print("Installed packages: ", len(applicationList))
    print("")
    return applicationList


def fetch_package_files(packageList):
    print_sign("Fetching package files")
    fileList = {}
    for p in packageList:
        cmd = ["dpkg", "-S", p]
        fileList[p] = run_command(cmd)
        sys.stdout.write("Package scanned: ")
        print(p)


def print_sign(label):  # for making pretty signs
    print("#" * 40)
    print(label)
    print("#" * 40)


installedPackages = fetch_installed_packages()
applicationFiles = fetch_package_files(installedPackages)


# for x in applicationList:
#   print(x)
#   a = 1


# testar = os.system("dpkg-query -f '${Package}\n' -W")

#rawPacketlist = subprocess.run(["dpkg-query", "-f", "'${Package}\n'", "-W"], capture_output=True, encoding='ASCII')

# rawPacketlist = subprocess.check_output(["dpkg-query", "-f", "'${Package}\n'", "-W"], shell=True, )


#print(rawPacketlist)
#testar = str(rawPacketlist)

#linjer = rawPacketlist.stdout.splitlines()
#testarList = testar.split('\\n')

#print(bash_command("ls"))

#for x in range(len(linjer)):  # Convrt subprocess.object 2 strings trims list
    #linjer[x] = str(linjer[x]).lstrip('b\"\'\'')
    #linjer[x] = linjer[x].rstrip('\"')
    #print(linjer[x].decode('ascii'))
    #a = 0

#print(type(rawPacketlist))
# print(testarList)
#print("#" * 40)




# detta funkar!
#packetTest = subprocess.run(["dpkg", "-S", "htop"], capture_output=True)
#packetlinjer = packetTest.stdout.splitlines()
#for y in range(len(packetlinjer)):
#    packetlinjer[y] = packetlinjer[y].decode('utf-8')
    #print(packetlinjer[y])





