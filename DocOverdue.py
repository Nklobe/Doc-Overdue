'''
Main script for Doc-Overdue

@package DocOverdue
'''

import os
import subprocess
from subprocess import Popen, PIPE
import sys
import filecmp
import difflib
import re
import socket


debugging = True  # show more info
shortrun = True  # only scan 100 files as a small test


largeScan = False  # Scans ALL packages on your system finding files. OBS! SLOW [Not implemented]

scannedFilesCount = 0  # Amount of scanned files
configFilesCount = 0  # Amount of config files

nonPackagedFiles = []  # files not found in packages
allUnchangedFiles = []  # All unchanged config files found
allConfigFiles = []  # All config files found
allOrphanFiles = []  # All orphan files found
allPackages = []

print("#" * 40)
print("Starting Doc-Overdue")
print("#" * 40)

summary = {"scannedPackages": "NA", "scannedFiles": 0, "configFiles": 0, "modifiedFiles": "NA", "newFiles": "NA", "orphanFiles": "NA"}


def bash_command(cmd):
    sp = subprocess.Popen(['/bin/bash', '-c', cmd], stdout=subprocess.PIPE)
    return sp.stdout.readlines()


def first_run():
    """Creates folders misc items needed to run the script"""
    print_sign("Creating folders")
    cmd = ["mkdir", "-p", "PackagesTMP"]
    run_command(cmd)
    cmd = ["mkdir", "-p", "ReferenceFiles/etc"]
    run_command(cmd)


def run_command(cmd, cwd=".", outputCap=True, shell=False, captError=False):
    """Runs command and trims the output"""
    # OBS! captError=True returns a LIST of [Errorcode, stdout/errout]
    if debugging:
        print("Running Command: ", cmd)
    rawCMD = Popen(cmd, stdout=PIPE, stderr=PIPE, cwd=cwd)
    print("Waiting for command ", str(cmd), " to complete")
    #outCMD = rawCMD.stdout.splitlines()
    outCMD = rawCMD.communicate()

    if captError:  # if the function was called with captError=True
        cmdList = [True,""]
        if rawCMD.returncode:
            print("Command Failed")
            cmdList[0] = True
            cmdList[1] = outCMD[1].decode('utf-8')
            print(cmdList[1])
            #cmdList[1] = outCMD[1].split("\n")
        else:
            print("Command Successfull")
            cmdList[0] = False
            cmdList[1] = outCMD[0].decode('utf-8')
            cmdList[1] = str(outCMD[0]).split("\n")
            print(cmdList[1])
        outCMD = cmdList
    else:
        outCMD = outCMD[0].decode("utf-8")
        outCMD = outCMD.split("\n")


    #conversionList = str(outCMD[0]).split('\\n')
    #print(outCMD)

    if debugging:
        print(outCMD)
    return outCMD


    # old version
    """if debugging:
        print("Running Command: ", cmd)
    rawCMD = subprocess.run(cmd, capture_output=outputCap, cwd=cwd, shell=shell)

    if outputCap:
        outCMD = rawCMD.stdout.splitlines()
        for c in range(len(outCMD)):
            outCMD[c] = outCMD[c].decode('utf-8')
            outCMD[c] = outCMD[c].replace('\'', '')
            if debugging:
                print(outCMD[c])

        return outCMD
    else:
        return 0"""


def parse_output(byteList):
    """Converts bytes to UTF strings"""
    byteList = byteList.stdout.splitlines()
    for c in range(len(byteList)):
        byteList[c] = byteList[c].decode('utf-8')
        byteList[c] = byteList[c].replace('\'', '')
    return byteList


def scan_files_etc():
    """Find all files under /etc and find related packages"""
    print("Scanning /etc")
    #cmd = ["find", "-L", "/etc/", "-type", "f", "-name", "'*'"]
    cmd = ["sh", "findEtcFiles.sh"]
    allFiles = run_command(cmd, shell=False, outputCap=True)
    #allFiles = subprocess.run(cmd, capture_output=True, shell=True)
    print("Allfiles: ", allFiles)
    return allFiles


def fetch_installed_packages():
    """Gets all installed packages via dpkg"""
    print_sign("Fetching installed packages")
    cmd = ["dpkg-query", "-f", "'${Package}\n'", "-W"]
    applicationList = run_command(cmd)
    print("Installed packages: ", len(applicationList))
    print("")
    return applicationList


def find_origin_package(allFiles):
    """Finds all packages related to files
    The inverse of fetch_package_files"""
    global allOrphanFiles
    global allConfigFiles
    global allPackages

    print("All Files: ", allFiles)

    allConfigFiles = allFiles
    packages = {}
    amount = len(allFiles)
    current = 0
    for file in allFiles:
        print("File: " + file)
        #Sort away unwanted files
        #Checks for certificats
        if ".pem" in file or ".0" in file or "crt" in file:
            print("Cert found!")
            continue
        #Check if its a folder
        if os.path.isdir(file):
            print(file + " Is directory!")
            continue
        cmd = ["dpkg", "-S", file]
        rawCMD = run_command(cmd, shell=False, outputCap=True, captError=True)
        if rawCMD[0] is True:
            print("Orphan File found! ", file)
            allOrphanFiles.append(file)
        else:
            for line in rawCMD[1]:
                if len(line) == 0 or line == "b''":
                    print("No Files found!")
                    break
                print("Packages Found")
                print(line)
                pckg = find_package_name((line), False)
                fileURL = line
                fileURL = fileURL.replace(find_package_name(line), '')
                if pckg not in packages:
                    allPackages.append(pckg.replace("b'",""))
                    packages[pckg] = []
                    packages[pckg].append(fileURL)
                else:
                    packages[pckg].append(fileURL)
            pass
        current += 1
        print(str(current) + "/", str(amount))
    return packages


def fetch_package_files(packageList):
    """Checks files related to package"""
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


def find_package_name(txt, colon=True):
    """Extracts the package name from found strings ex: package: /etc/conf.conf"""
    if len(txt) == 0:
        txt = " "

    pckName = re.search("^\S+\s", txt)
    if pckName == None:
        pckName = ""
    else:
        pckName = pckName.group(0)

    if colon is False:
        pckName = pckName.replace(": ", "")
    pckName = pckName.replace("\n", "")
    print("pckName:", pckName)
    return pckName


def parse_config_files(fileDict):
    """Checks for files located in /etc from packages"""
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


def get_package_version(packageList):
    """Gets the package version"""
    pass


def create_folders(fileDict):
    """Creates folders for configs"""
    for f in fileDict.items():
        for url in f[1]:
            urlSplit = os.path.split(url)
            refURL = "ReferenceFiles" + urlSplit[0]
            print(urlSplit[0])
            cmd = ["mkdir", "-p", refURL]
            print(cmd)
            run_command(cmd)


def download_package(packages):
    """Downloads and extracts all /etc/ files
       One package at a time to save on disk space"""
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


def extract_files(package):  # No list, just one package per time
    """Extracting and moving the files to the correct place"""
    print_sign("Extracting files")

    fileName = run_command("ls", cwd="PackagesTMP")  # UGLY solution \
    print("FileNAME: ", fileName)
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
        run_command(cmd, cwd="PackagesTMP")


def print_sign(label):
    """For making pretty signs"""
    print("#" * 40)
    print(label)
    print("#" * 40)


def check_for_modified_files(packageList):
    """Compares system files to reference files"""
    print_sign("Checking for modified files")
    global nonPackagedFiles
    global allUnchangedFiles
    filesFound = 0
    diffFiles = []
    for p in packageList.items():  # gets through the items
        for fileURL in p[1]:
            # compare files
            fileURL = fileURL.replace('\\n', "")
            fileURL = fileURL.replace('\'', "")
            referenceFile = "ReferenceFiles" + fileURL
            print(referenceFile, " : ", fileURL)

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
                else:
                    print("Unchanged file: ", fileURL)
                    allUnchangedFiles.append(fileURL)
            except FileNotFoundError:
                print(FileNotFoundError, fileURL)
                nonPackagedFiles.append(fileURL)
            except Exception:
                print("Other error")

    found = str(filesFound) + " Modified files found"
    if filesFound > 0:
        add_diffs_2_html(diffFiles)
    else:
        add_diffs_2_html([])
    print_sign(found)

    # Adding amount of files to summary
    summary["modifiedFiles"] = filesFound


def create_diff(files):
    """Creates the Diff summaries"""
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


def create_html_page(name,content,links=False, warning = "", title=""):
    """Creates a standard html file with a list of some sort"""
    print_sign("Creating HTML page")
    lines = []
    with open('baseFiles/Base.html.base', 'r') as file:
        for g in file:
            lines.append(g)
        host = socket.gethostname()
        hostname = "<center><b> %s <b> </center><hr>" % (host)
        lines.append(hostname)

        lines.append("<br>")
        if len(content) == 0:
            lines.append("<br>")
            lines.append("<h2>No files found!</h2>")
        title = "<h1>" + title + "</h1>"
        lines.append(title)
        for f in content:
            lines.append("<br>")
            if links:
                lines.append("    <a link href='../ReferenceFiles" + f + "'>" + f + "<a/><br>")
            else:
                lines.append(f)

        htmlFilename = "html/" + name + ".html"
        with open(htmlFilename, 'w') as file:
            file.writelines(lines)


def add_diffs_2_html(files):
    """Adds the changed file to the report"""
    print("adding diff links to the HTML")
    with open('baseFiles/Base.html.base', 'r') as file:
        lines = []
        for g in file:
            lines.append(g)
        host = socket.gethostname()
        hostname = "<center><b> %s <b> </center><hr>" % (host)
        lines.append(hostname)
        lines.append("<br>")
        lines.append("<h1>All found modified files</h1>")
        for f in files:

            lines.append("<br>")
            linkLine = "<a link href='../ReferenceFiles/" + f + ".diff.html'>" + f + "</a>"
            lines.append(linkLine)
            pass
        lines.append("<br>")
        with open('html/changedFiles.html', 'w') as file:
            file.writelines(lines)

def create_all_pages():
    """Calls the create_html_page() function multiple times"""
    print("Creating files")

    global allUnchangedFiles
    allUnchangedFiles.sort()
    create_html_page(name="unchangedFiles", content=allUnchangedFiles, links=True,title="All unchanged files")

    global allOrphanFiles
    allOrphanFiles.sort()
    create_html_page(name="orphanFiles", content=allOrphanFiles, links=False,title="All orphan files")

    global allPackages
    allPackages.sort()
    create_html_page("allPackages",allPackages, False)
    create_html_page(name="allPackages", content=allPackages, links=False,title="All found/scanned packages")

    global allConfigFiles
    allConfigFiles.sort()
    create_html_page("allConfigFiles",allPackages, False)
    create_html_page(name="allConfigFiles", content=allConfigFiles, links=False,title="All found config files")

    summary = create_summary()
    print(type(summary))
    create_html_page("index", summary, False)


def create_summary():
    """Creates the summary for the report"""
    global allOrphanFiles
    global allUnchangedFiles
    global allConfigFiles
    print_sign("Creating summary")
    filedata = []
    with open('baseFiles/Summary.html.base', 'r') as file:
        filedata = file.read()
        filedata = filedata.replace('[scannedPackages]', str(summary["scannedPackages"]))
        #filedata = filedata.replace('[scannedFiles]', str(len(allConfigFiles)))
        filedata = filedata.replace('[modifiedFiles]', str(summary["modifiedFiles"]))
        filedata = filedata.replace('[unmodifiedFiles]', str(len(allUnchangedFiles)))
        filedata = filedata.replace('[newFiles]', str(summary["newFiles"]))
        filedata = filedata.replace('[orphanFiles]', str(len(allOrphanFiles)))
        filedata = filedata.replace('[configFiles] ', str(len(allConfigFiles)))
    listFileData = []
    listFileData.append(filedata)
    return listFileData


def show_info():
    """Show information after the script is done"""
    print("-:Your IP config:-")
    ip = Popen(["ip","a"])
    ip.communicate()
    print("_-‾-" * 25)
    print("‾-_-" * 25)
    print("Doc-Overdue scan complete!")
    print("Your report is available under html")
    print("The report is also available as a PDF and epub")
    print("If you want to expose the report via a webserver you can do so with the command:")
    print(" python3 -m http.server  ")
    print("This will make your report available at http://[yourIP]:8000/html")
    print("TIP! Your ip config has been printed above ^")
    print("_-‾-" * 25)
    print("‾-_-" * 25)
    pass


# Main Runtime
first_run()

foundEtcFiles = scan_files_etc()

#installedPackages = fetch_installed_packages()
installedPackages = []

#for l in range(10):
#    shortList.append(installedPackages[l+200])

if shortrun:
    shortList = []
    for L in range(50):
        shortList.append(foundEtcFiles[L])

    etcFiles = find_origin_package(shortList)
else:
    etcFiles = find_origin_package(foundEtcFiles)

download_package(etcFiles)

applicationFiles = fetch_package_files(installedPackages)

#etcFiles = parse_config_files(applicationFiles)

#create_folders(etcFiles)
check_for_modified_files(etcFiles)

create_all_pages()
show_info()
