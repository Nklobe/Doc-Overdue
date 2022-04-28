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

scannedFilesCount = 0  # Amount of scanned files
configFilesCount = 0  # Amount of config files

nonPackagedFiles = []  # files not found in packages
allConfigFiles = []  # All config files found

print("#" * 40)
print("Starting Doc-Overdue")
print("#" * 40)

summary = {"scannedPackages": "NA", "scannedFiles": 0, "configFiles": 0, "modifiedFiles": "NA", "newFiles": "NA", "orphanFiles": "NA"}


def bash_command(cmd):
    sp = subprocess.Popen(['/bin/bash', '-c', cmd], stdout=subprocess.PIPE)
    return sp.stdout.readlines()


# Creates folders misc items needed to run the script
def first_run():
    print_sign("Creating folders")
    cmd = ["mkdir", "-p", "PackagesTMP"]
    run_command(cmd)
    cmd = ["mkdir", "-p", "ReferenceFiles/etc"]
    run_command(cmd)
    # Öppna Loggfiler?


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
    global scannedFilesCount
    global configFilesCount
    global allConfigFiles

    print_sign("Parsing config files")
    etcFiles = {}
    amount = len(fileDict.items())  # Amount of packages
    current = 0
    for f in fileDict.items():  # gets through the items
        fileList = []
        for fileURL in f[1]:  # looping through the file list
            scannedFilesCount += 1
            if "/etc/" in fileURL:
                configFilesCount += 1
                allConfigFiles.append(fileURL)
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

    summary["configFiles"] = configFilesCount
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
        current += 1

    summary["scannedPackages"] = current
    summary["scannedFiles"] = scannedFilesCount


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
    global nonPackagedFiles

    print(packageList)
    filesFound = 0
    diffFiles = []
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
                    diffFiles.append(fileURL)
                    try:
                        create_diff([fileURL, referenceFile])
                    except IsADirectoryError:
                        print(IsADirectoryError)
                    except FileNotFoundError:
                        print(FileNotFoundError)
            except FileNotFoundError:
                print(FileNotFoundError, fileURL)
                nonPackagedFiles.append(fileURL)
            except Exception:
                print("Other error")

    found = str(filesFound) + " Modified files found"
    if filesFound > 0:
        add_diffs_2_sphinx(diffFiles)
    else:
        add_diffs_2_sphinx([])
    print_sign(found)

    # Adding amount of files to summary
    summary["modifiedFiles"] = filesFound


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


# Adds the changed file to the
def add_diffs_2_sphinx(files):
    print("adding files 2 sphinx")
    lines = []
    with open('baseFiles/changedFiles.rst.base', 'r') as file:
        for g in file:
            lines.append(g)
        lines.append("\n")
        for f in files:
            lines.append("\n")
            linkName = "`" + f + "`_."
            lines.append(linkName)
            lines.append("\n\n")
            linkLine = ".. _" + f + ": ../../ReferenceFiles/" + f + ".diff.html"
            lines.append(linkLine)
            pass
        lines.append("======================================")
        with open('source/changedFiles.rst', 'w') as file:
            file.writelines(lines)
        pass

    pass


# List all files without a reference
def create_non_package_files():
    print_sign("Creating_non_package_files")
    global nonPackagedFiles
    print(nonPackagedFiles)
    lines = []
    with open('baseFiles/nonPackageFiles.rst.base', 'r') as file:
        for g in file:
            lines.append(g)
        lines.append("\n")
        for f in nonPackagedFiles:
            lines.append("\n")
            lines.append("    <a link href='" + f + "'>" + f + "<a/><br>")
            pass
        print(lines)
        lines.append("======================================")
        with open('source/nonPackageFiles.rst', 'w') as file:
            file.writelines(lines)
        pass

    pass


# Create a list of all files
def create_all_files():
    print_sign("Creating_all_files")
    global allConfigFiles
    lines = []
    with open('baseFiles/allConfigFiles.rst.base', 'r') as file:
        for g in file:
            lines.append(g)
        lines.append("\n")
        for f in allConfigFiles:
            lines.append("\n")
            lines.append("    <a link href='" + f + "'>" + f + "<a/><br>")
            pass
        print(lines)
        with open('source/allConfigFiles.rst', 'w') as file:
            file.writelines(lines)
        pass

    pass


# Creates the summary for sphinx
def create_summary():
    print_sign("Creating summary")
    with open('baseFiles/Summary.html.base', 'r') as file:
        filedata = file.read()
        filedata = filedata.replace('[scannedPackages]', str(summary["scannedPackages"]))
        filedata = filedata.replace('[scannedFiles]', str(summary["scannedFiles"]))
        filedata = filedata.replace('[modifiedFiles]', str(summary["modifiedFiles"]))
        filedata = filedata.replace('[newFiles]', str(summary["newFiles"]))
        filedata = filedata.replace('[orphanFiles]', str(summary["orphanFiles"]))
        filedata = filedata.replace('[configFiles] ', str(summary["configFiles"]))

    with open('source/Summary.html', 'w') as file:
        file.write(filedata)
    pass


# Building sphinx
def build_sphinx():
    print_sign("Building sphinx")
    cmd = ["make", "clean"]
    run_command(cmd)
    cmd = ["make", "html"]
    run_command(cmd)

    cmd = ["make", "latex"]
    run_command(cmd)
    cmd = ["make", "latexpdf"]
    run_command(cmd)
    cmd = ["cp", "build/latex/doc-overdue.pdf", "build/html"]
    run_command(cmd)
    pass


# Show information after the script is done
def show_info():
    pass

# Main Runtime
first_run()

installedPackages = fetch_installed_packages()
shortList = []
#for l in range(10):
#    shortList.append(installedPackages[l+200])


#applicationFiles = fetch_package_files(shortList)

applicationFiles = fetch_package_files(installedPackages)
#applicationFiles = fetch_package_files(["apt", 'anacron', 'alsa-utils', 'bind9-dnsutils', 'binutils', "ssh", "openssh-client"])
#applicationFiles = fetch_package_files(["ssh", "openssh-client", "snmp", "dpkg"])
#print(applicationFiles)
etcFiles = parse_config_files(applicationFiles)
create_folders(etcFiles)

download_package(etcFiles)
check_for_modified_files(etcFiles)
create_summary()
create_non_package_files()
create_all_files()
build_sphinx()
