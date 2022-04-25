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


def run_command(cmd, cwd=".", outputCap=True):  # runs command and trims the output
    print("Running Command: ", cmd)
    rawCMD = subprocess.run(cmd, capture_output=outputCap, cwd=cwd)

    if outputCap:
        outCMD = rawCMD.stdout.splitlines()
        for c in range(len(outCMD)):
            outCMD[c] = outCMD[c].decode('utf-8')
            outCMD[c] = outCMD[c].replace('\'', '')
            print(outCMD[c])

        return outCMD
    else:
        return 0


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

    for f in fileList.keys():
        print(f)

    return fileList


def parse_config_files(fileDict):  # checks for files located in /etc
    print_sign("Parsing config files")
    etcFiles = {}
    for f in fileDict.items():  # gets through the items
        Addcolon = f[0] + ": "

        fileList = []
        for fileURL in f[1]:  # looping through the file list
            if "/etc/" in fileURL and Addcolon in fileURL:
                fileURL = fileURL.replace(Addcolon, '')  # makes it a pure URL
                fileList.append(fileURL)
            etcFiles[f[0]] = fileList
    print(etcFiles)
    return etcFiles


# Gets the package version
def get_package_version(packageList):
    pass


def create_folders(fileDict):  # creates folders for configs
    for f in fileDict.items():
        for url in f[1]:
            urlSplit = os.path.split(url)
            refURL = "ReferenceFiles" + urlSplit[0]
            print(urlSplit[0])
            cmd = ["mkdir", "-p", refURL]
            print(cmd)
            run_command(cmd)


def download_package(packages):
    print_sign("Downloading packages")
    for p in packages.items():

        print("Downloading ", p[0])
        cmd = ["apt", "download", p[0]]
        applicationList = run_command(cmd, "PackagesTMP", False)
        extract_files(p[0])
        pass
    pass


# Extracting and moving the files to the correct place
def extract_files(package):  # No list, just one package per time
    print_sign("Extracting files")

    fileName = run_command("ls", "PackagesTMP" )  # UGLY solution \
    # runs ls and uses the first result.
    cmd = ["dpkg", "-x", fileName[0], package]

    print(run_command(cmd, "PackagesTMP"))

    # Moving the files to the reference folder
    # cp -r apt/etc/* ../ReferenceFiles/etc
    etc = package + "/etc/"
    cmd = ["cp", "-rv", etc, "../ReferenceFiles"]
    # rawCMD = subprocess.run(cmd, capture_output=False, cwd="PackagesTMP")
    print(run_command(cmd, "PackagesTMP"))
    fileName = run_command("ls", "PackagesTMP" )
    for f in fileName:
        cmd = ["rm", "-rv",  f]
        print(run_command(cmd, "PackagesTMP", False))





def print_sign(label):  # for making pretty signs
    print("#" * 40)
    print(label)
    print("#" * 40)


# Main Runtime
installedPackages = fetch_installed_packages()
#applicationFiles = fetch_package_files(installedPackages)
applicationFiles = fetch_package_files(["apt", 'anacron', 'alsa-utils', 'bind9-dnsutils', 'binutils'])
#print(applicationFiles)
etcFiles = parse_config_files(applicationFiles)
create_folders(etcFiles)
download_package(etcFiles)


#for x in etcFiles["apt"]:
#    print(x)



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





