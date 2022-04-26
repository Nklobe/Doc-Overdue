'''
Main script for Doc-Overdue

@package DocOverdue
'''

import os
import subprocess
import sys
import filecmp
import difflib
import re

debugging = False

print("#" * 40)
print("Starting Doc-Overdue")
print("#" * 40)



def bash_command(cmd):
    sp = subprocess.Popen(['/bin/bash', '-c', cmd], stdout=subprocess.PIPE)
    return sp.stdout.readlines()


# runs command and trims the output
def run_command(cmd, cwd=".", outputCap=True):
    if debugging:
        print("Running Command: ", cmd)
    rawCMD = subprocess.run(cmd, capture_output=outputCap, cwd=cwd)

    if outputCap:
        outCMD = rawCMD.stdout.splitlines()
        for c in range(len(outCMD)):
            outCMD[c] = outCMD[c].decode('utf-8')
            outCMD[c] = outCMD[c].replace('\'', '')
            if debugging:
                print(outCMD[c])
        return outCMD
    else:
        return 0


# Converts bytes to UTF strings
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
    amount = len(packageList)
    current = 0
    for p in packageList:
        cmd = ["dpkg", "-S", p]
        fileList[p] = run_command(cmd)
        print(current, "/", amount, "Packages scanned: ", p)
        current += 1

        print(p)

    if debugging:
        for f in fileList.keys():
            print(f)

    return fileList

def find_package_name(txt):
    pckName = re.search("^\S+\s", txt)
    pckName = pckName.group(0)
    print("pckName:", pckName)
    return pckName


def parse_config_files(fileDict):  # checks for files located in /etc
    print_sign("Parsing config files")
    etcFiles = {}
    amount = len(fileDict.items()) # Amount of packages
    current = 0
    for f in fileDict.items():  # gets through the items

        fileList = []
        for fileURL in f[1]:  # looping through the file list
            if "/etc/" in fileURL:
                print(fileURL, " OK")
                pckName = find_package_name(fileURL)
                fileURL = fileURL.replace(pckName, '')  # makes it a pure URL
                if os.path.isfile(fileURL):  # ignores directories
                    fileList.append(fileURL)
                else:
                    print(fileURL, " Is a folder!")
            etcFiles[f[0]] = fileList
    print(etcFiles)

    print("Package ", current, "/", amount)
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
    amount = len(packages.items())
    current = 0
    for p in packages.items():

        print("Downloading package ", current, "/", amount, p[0])
        try:
            cmd = ["apt", "download", p[0]]
            applicationList = run_command(cmd, "PackagesTMP", False)
            extract_files(p[0])
        except Exception:
            print(Exception)
            print("Failed to download package!")

        pass
        current += 1
    pass


# Extracting and moving the files to the correct place
def extract_files(package):  # No list, just one package per time
    print_sign("Extracting files")

    fileName = run_command("ls", "PackagesTMP")  # UGLY solution \
    # runs ls and uses the first result.
    cmd = ["dpkg", "-x", fileName[0], package]
    run_command(cmd, "PackagesTMP")

    # Moving the files to the reference folder
    etc = package + "/etc/"
    cmd = ["cp", "-rv", etc, "../ReferenceFiles"]
    run_command(cmd, "PackagesTMP")
    # Fetching all files and folders for removal
    fileName = run_command("ls", "PackagesTMP")
    for f in fileName:
        cmd = ["rm", "-rv",  f]
        run_command(cmd, "PackagesTMP")


def print_sign(label):  # for making pretty signs
    print("#" * 40)
    print(label)
    print("#" * 40)


def check_for_modified_files(packageList):
    print_sign("Checking for modified files")
    print(packageList)
    filesFound = 0
    for p in packageList.items():  # gets through the items
        for fileURL in p[1]:
            # compare files

            referenceFile = "ReferenceFiles" + fileURL
            # print(referenceFile, " : ", fileURL)
            try:
                comparison = filecmp.cmp(fileURL, referenceFile)
                if comparison is False:  # if difference
                    print(comparison)
                    print(fileURL)
                    filesFound += 1
                    try:
                        create_diff([fileURL, referenceFile])
                    except IsADirectoryError:
                        print(IsADirectoryError)
                    except FileNotFoundError:
                        print(FileNotFoundError)
            except FileNotFoundError:
                print(FileNotFoundError, fileURL)
    found = str(filesFound) + " Modified files found"
    print_sign(found)



def create_diff(files):
    print_sign("Creating Diffs")
    # Files is a list of [ModifiedFile, ReferenceFile]
    fromFile = files[1]
    toFile = files[0]
    fromLines = open(fromFile, 'U').readlines()
    toLines = open(toFile, 'U').readlines()
    fromFileTitle = "<h3>Reference file: " + fromFile + "</h3>"
    toFileTitle = "<h3>Your file: " + toFile + "</h3>"
    diff = difflib.HtmlDiff().make_file(fromLines, toLines, fromFileTitle, toFileTitle)
    # sys.stdout.writelines(diff)
    fileName = files[1] + ".diff.html"
    try:
        with open(fileName, "w") as file:
            print("Found diff in file ", fileName)
            file.write(diff)
    except Exception:
        print("Error in checking diff!: ", Exception)


# Main Runtime
installedPackages = fetch_installed_packages()
shortList = []
for l in range(50):
    shortList.append(installedPackages[l+300])

applicationFiles = fetch_package_files(shortList)

#applicationFiles = fetch_package_files(installedPackages)
#applicationFiles = fetch_package_files(["apt", 'anacron', 'alsa-utils', 'bind9-dnsutils', 'binutils', "ssh", "openssh-client"])
#applicationFiles = fetch_package_files(["ssh", "openssh-client"])
#print(applicationFiles)
etcFiles = parse_config_files(applicationFiles)
print(etcFiles)
create_folders(etcFiles)

#download_package(etcFiles)
check_for_modified_files(etcFiles)


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





