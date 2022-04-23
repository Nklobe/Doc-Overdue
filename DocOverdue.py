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
    return outCMD


def parse_output(byteList):
    byteList = byteList.stdout.splitlines()
    for c in range(len(byteList)):
        byteList[c] = byteList[c].decode('utf-8')
        byteList[c] = byteList[c].replace('\'', '')
    return byteList


def fetch_installed_packages():  # gets all installed packages via dpkg
    print_sign("Fetching installed packages")
    cmd = ["dpkg-query", "-f", "'${Package}\n'", "-W"]
    applicationList = run_command(cmd)
    print("Installed packages: ", len(applicationList))
    print("")
    return applicationList


def fetch_package_files(packageList):  # checks files related to package
    print_sign("Fetching package files")
    fileList = {}
    for p in packageList:
        cmd = ["dpkg", "-S", p]
        fileList[p] = run_command(cmd)
        sys.stdout.write("Package scanned: ")
        print(p)
    return fileList


def parse_config_files(fileDict):  # checks for files located in /etc

    print_sign("Parsing config files")

    for f in fileDict.items():  # gets through the items
        Addcolon = f[0] + ":"
        etcFiles = {}
        fileList = []
        for fileURL in f[1]:  # looping through the file lis
            if "/etc/" in fileURL and Addcolon in fileURL:
                print(fileURL)
                fileList.append(fileURL)
            etcFiles[f[0]] = fileList
        return etcFiles

    # Lägga in någon form av regex som plockar ut alla delar av det


def find_references():
    # jag ska hitta en bra referens av filerna.

    pass


def download_package(packageList):
    # download package
    pass


def extract_files():
    # extract config files
    pass


def print_sign(label):  # for making pretty signs
    print("#" * 40)
    print(label)
    print("#" * 40)




installedPackages = fetch_installed_packages()
#applicationFiles = fetch_package_files(installedPackages)
applicationFiles = fetch_package_files(["apt"])
#print(applicationFiles)
etcFiles = parse_config_files(applicationFiles)
for x in etcFiles["apt"]:
    print(x)
#print(etcFiles)

#print(applicationFiles)


















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





