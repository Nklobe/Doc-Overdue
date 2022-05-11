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
from pathlib import Path


debugging = False  # show more info
shortrun = False  # only scan 100 files as a small test
deletePackages = True  # Should the script delete the reference packages after
                       # use to save on disk space? NOT WORKING ATM! KEEP TRUE

largeScan = False  # Scans ALL packages on your system finding files. OBS! SLOW [Not implemented]

scannedFilesCount = 0  # Amount of scanned files
configFilesCount = 0  # Amount of config files

nonPackagedFiles = []  # files not found in packages
allUnchangedFiles = []  # All unchanged config files found
allConfigFiles = []  # All config files found
allOrphanFiles = []  # All orphan files found
allPackages = []  # All packages found
allUnknownFiles = []  # All orphan files minus known files in the file standardPackages


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
    cmd = ["rm", "errorLog.txt"]
    run_command(cmd)
    cmd = ["touch", "errorLog.txt"]
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
    errorLogCMD = outCMD
    if captError:  # if the function was called with captError=True
        cmdList = [True, ""]
        if rawCMD.returncode:
            print("Command Failed")
            cmdList[0] = True
            cmdList[1] = outCMD[1].decode('utf-8')
            print(cmdList[1])
            #cmdList[1] = outCMD[1].split("\n")
        else:
            print("Command Successfull")
            cmdList[0] = False
            try:
                cmdList[1] = outCMD[0].decode('utf-8')
                cmdList[1] = str(outCMD[0]).split("\n")
            except Exception as a:
                print("Decode Error!")
                write_errorlog([cmdList])
                pass
            print(cmdList[1])
        outCMD = cmdList
    else:
        outCMD = outCMD[0].decode("utf-8")
        outCMD = outCMD.split("\n")

    if rawCMD.returncode:
        #if the returncode is 1 AKA strERR
        errors = []
        errors.append(cmd)
        print(errorLogCMD)
        errors.append(errorLogCMD[0])
        errors.append(errorLogCMD[1])
        errors.append("\n")
        write_errorlog(errors)

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


def write_errorlog(msg):
    """Write error logs to errorLogFile"""
    print("Error written to errorLog!")
    with open('errorLog.txt', 'a') as file:
        for line in msg:
            file.writelines(str(line))
        pass
    pass


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
    run_command(cmd, cwd=".", outputCap=True, shell=False, captError=False)
    applicationList = run_command(cmd)
    print("Installed packages: ", len(applicationList))
    #return applicationList
    return applicationList[0::10]


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
        # Sort away unwanted files
        # Checks for certificats
        if ".pem" in file or ".0" in file or "crt" in file:
            print("Cert found!")
            continue
        # Check if its a folder
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
                pckg = find_package_name((line), False)
                fileURL = line
                fileURL = fileURL.replace(find_package_name(line), '')
                if pckg not in packages:
                    allPackages.append(pckg.replace("b'", ""))
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
        fileList[p] = run_command(cmd, cwd=".", outputCap=True, shell=False, captError=False)
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
    if pckName is None:
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
    print(fileDict[0])
    #amount = len(fileDict.items())  # Amount of packages
    amount = len(fileDict)  # Amount of packages
    current = 0
    #for f in fileDict.items():  # gets through the items
    for fileURL in fileDict:  # gets through the items
        fileList = []
        #for fileURL in f[1]:  # looping through the file list
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
            package = p[0]
            package = package.replace("b'", "")
            #cmd = ["apt", "download", p[0]]
            cmd = ["apt", "download", package]
            applicationList = run_command(cmd, "PackagesTMP", False)
            extract_files(package)
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
    #fileName = run_command(["ls", wildcardPackage],  cwd="PackagesTMP")  # UGLY solution \
    print("FileNAME: ", fileName)
    # runs ls and uses the first result.
    cmd = ["dpkg", "-x", fileName[0], package]
    run_command(cmd, "PackagesTMP")

    # Moving the files to the reference folder
    etc = package + "/etc/"
    cmd = ["cp", "-rv", etc, "../ReferenceFiles"]
    run_command(cmd, "PackagesTMP")
    # Fetching all files and folders for removal
    fileName = run_command(["ls"], "PackagesTMP")
    for f in fileName:
        if len(f) == 0:
            continue
        else:
            if deletePackages:
                cmd = ["rm", "-rvf",  f]
                run_command(cmd, cwd="PackagesTMP")
            pass


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


def file_in_dpkgInfo(confFile):
    """Is confFile mentioned in /var/lib/dpkg/info/"""
    cmd = ["grep", "-r", confFile, "."]
    rawCMD = run_command(cmd, cwd="/var/lib/dpkg/info/", outputCap=True, shell=True, captError=True)
    if rawCMD[0]:
        print(confFile, " is still unknown!")
        result = False
    else:
        print("Occurence of :", confFile, " Found!")
        result = True
    return result

#def file_in_standardFiles(confFile):
    """Removes known packages from the Orphan files"""

    """result = True
    standardPackages = []
    tempList = []
    with open('standardPackages', 'r') as file:
        for line in file:
            #print(line)
            line = line.rstrip()
            standardPackages.append(line)


    if confFile in standardPackages:
        print(confFile, " Found in standardPackages")
        result = True
    else:
        print(confFile, " Not Found")
        result = False
    return result """

def file_in_standardFiles(confFile):
    """Removes known packages from the Orphan files"""
    result = ""
    standardFiles = []
    tempList = []

    cmd = ["ls"]
    rawCMD = run_command(cmd, cwd="StandardFiles", outputCap=True, shell=True, captError=True)

    print("¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤")
    fileList = rawCMD[1][0]
    fileList = fileList.replace("b'", "")
    fileList = fileList.replace("'", "")
    fileList = fileList.split('\\n')
    print(fileList)

    for f in fileList:
        standardFiles = []
        fileURL = 'StandardFiles/' + f
        if os.path.isfile(fileURL):
            with open(fileURL, 'r') as file:
                for line in file:
                    line = line.rstrip()
                    standardFiles.append(line)
            if confFile in standardFiles:
                print(confFile, " Found in standardFiles")
                result = result + f + " "
        else:
            print("NOT A FILE")
    if result == "":
        result = "False"
    return result


def file_ownedByRoot(confFile):
    """Checks if file is owned by Root or not"""
    try:
        path = Path(confFile)
        owner = path.owner()
        group = path.group()
    except Exception as e:
        print("Path Failed!")
        write_errorlog([str(e)])
        return False
    if owner == "root" and group == "root":
        result = True
        print(confFile, "Is owned by root")
    else:
        result = False
    return result


def file_createdPostInstallation(confFile, systemDate):
    """Checks if the file is created on a date after the inistial
    installation of the system"""
    cmd = ["stat", "--format='%w'", confFile]
    rawCMD = run_command(cmd, cwd="/usr/bin/", outputCap=True, shell=True, captError=True)
    if rawCMD[0]:
        print(confFile, " birth date could NOT be found")
        result = False
    else:
        print("Birth date of :", confFile, " Found!")
        birthDate = rawCMD[1][0]
        print("¤¤¤¤¤¤")
        birthDate = birthDate[3:13]
        print(birthDate, systemDate)
        if str(systemDate) == str(birthDate):
            print("Same")

            result = "True, Created:" + birthDate
        else:
            print("Diff")
            result = "False, Created:" + birthDate

    return result


def file_changedPostInstallation(confFile):
    """Checks if the file is created on a date after the inistial
    installation of the system"""
    birthDate = ""
    changeDate = ""
    cmd = ["stat", "--format='%w'", confFile]
    rawCMD = run_command(cmd, cwd="/usr/bin/", outputCap=True, shell=True, captError=True)
    if rawCMD[0]:
        print(confFile, " birth date could NOT be found")
        return "False, no birth date found"
    else:
        print("Birth date of :", confFile, " Found!")
        birthDate = rawCMD[1][0]
        print("¤¤¤¤¤¤")
        birthDate = birthDate[3:13]

    cmd = ["stat", "--format='%y'", confFile]
    rawCMD = run_command(cmd, cwd="/usr/bin/", outputCap=True, shell=True, captError=True)
    if rawCMD[0]:
        print(confFile, " change date could NOT be found")
        return "False, no change date found"
    else:
        print("Change date of :", confFile, " Found!")
        changeDate = rawCMD[1][0]
        print("¤¤¤¤¤¤")
        changeDate = changeDate[3:13]
    birthDateInt = re.sub('[^0-9]','', birthDate)
    changeDateInt  = re.sub('[^0-9]','', changeDate)
    #birthDateInt = int(birthDate.replace("-", ""))
    #changeDateInt = int(changeDate.replace("-", ""))

    if birthDateInt == changeDateInt:
        return "True"
    else:
        returnMessage = "False Created:" + birthDate + " Changed:" + changeDate
        return returnMessage

    return returnMessage


def create_file_detections():
    """Creates a matrix of different tests in one page"""
    print_sign("Creating File detection")
    global allOrphanFiles
    detectionDict = {}
    resultList = []
    htmlList = []
    cmd = ["stat", "--format='%w'", "/"]
    rawCMD = run_command(cmd, cwd="/usr/bin/", outputCap=True, shell=True, captError=True)
    birthDate = rawCMD[1][0]
    birthDate = birthDate[3:13]

    for o in allOrphanFiles:  # Do all tests and put them in a dict
        resultList = [file_in_dpkgInfo(o), file_in_standardFiles(o), file_ownedByRoot(o), file_createdPostInstallation(o, birthDate), file_changedPostInstallation(o)]
        detectionDict[o] = [resultList]

    #print(detectionDict)
    create_html_list(detectionDict)


def create_html_list(resultDict):
    htmlList = []
    htmlList.append("A matrix of all orphan files, <br>")
    htmlList.append("These test can help in finding outliers, the more a file fails tests the more certain you can be <br>")
    htmlList.append("that the file has been created by an administrator <br>")
    htmlList.append("<br><b>In DPKG info:</b> Searches through all files under /var/lib/dpkg/info/ for mention of the file<br>")
    htmlList.append("<b>In Standard Files:</b> Uses the files under 'StandardFiles' that contains files that exist on newly installed debian/ubuntu systems,<br> if the file exists in a list, the name of that list will be printed<br>")
    htmlList.append("<b>Owned by root:root :</b> Sees if the file is owned by root, this is the standard for most auto created config files<br>")
    htmlList.append("<b>Created post installation date:</b> Check if the file was created on the same day as the system was installed<br><br>")
    htmlList.append("<b>Unmodified since installation: </b> Checks if the file has been modified since its creation")
    htmlList.append("<style>table, th, td {border:1px solid black; }")
    #htmlList.append("th:nth-child(even),td:nth-child(even) {background-color: #D6EEEE;}</style>")
    htmlList.append("</style>")
    htmlList.append("<table style='width:100%' > <tr> ")
    htmlList.append("<th>File</th>")
    htmlList.append("<th>In Dpkg info</th>")
    htmlList.append("<th>In Standardfiles</th>")
    htmlList.append("<th>Owned By root:root</th>")
    htmlList.append("<th>Created on installation date</th>")
    htmlList.append("<th>Unmodified since creation</th>")
    htmlList.append("</tr>")

    for r in resultDict.keys():
        print(resultDict[r][0][0])
        htmlList.append("<tr>")
        resultString = "<td>" + r + "</td>"
        htmlList.append(resultString)
        resultString = cell_color(resultDict[r][0][0]) + str(resultDict[r][0][0]) + "</td>"
        htmlList.append(resultString)
        resultString = cell_color(resultDict[r][0][1]) + str(resultDict[r][0][1]) + "</td>"
        htmlList.append(resultString)
        resultString = cell_color(resultDict[r][0][2]) + str(resultDict[r][0][2]) + "</td>"
        htmlList.append(resultString)
        resultString = cell_color(resultDict[r][0][3]) + str(resultDict[r][0][3]) + "</td>"
        htmlList.append(resultString)
        resultString = cell_color(resultDict[r][0][4]) + str(resultDict[r][0][4]) + "</td>"
        htmlList.append(resultString)
        htmlList.append("<tr>")
    warning = ""
    create_html_page(name="file_tests", content=htmlList, warning="", links=False, title="File Tests", br=False)
    pass


def cell_color(question):
    if "False" in str(question):
        return "<td bgcolor='Red'>"
    else:
        return "<td bgcolor='Green'>"
    pass


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


def create_html_page(name,content,  warning,links=False, title="", br=True):
    """Creates a standard html file with a list of some sort"""
    print_sign("Creating HTML page")
    lines = []
    with open('baseFiles/Base.html.base', 'r') as file:
        for g in file:
            lines.append(g)
        host = socket.gethostname()
        hostname = "<center><b> %s </b> </center><hr>" % (host)
        lines.append(hostname)
        lines.append("<br>")
        lines.append(warning)
        lines.append("<br>")
        if len(content) == 0:
            lines.append("<br>")
            lines.append("<h2>No files found!</h2>")
        title = "<h1>" + title + "</h1>"
        lines.append(title)
        for f in content:
            if br:
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
        lines.append("<br>Config files found with a comparable one in a package, Click the link to show a DIFF comparison")
        lines.append("<br>")
        lines.append("<h1>All found modified files</h1>")
        for f in files:
            linkLine = "<a link href='../ReferenceFiles/" + f + ".diff.html'>" + f + "</a>"
            lines.append(linkLine)
            lines.append("<br>")
        lines.append("<br>")
        with open('html/changedFiles.html', 'w') as file:
            file.writelines(lines)


def create_unknown_files():
    """Removes known packages from the Orphan files"""
    print_sign("Creates Unknown Files")
    global allOrphanFiles
    global allUnknownFiles
    standardPackages = []
    tempList = []
    with open('standardPackages', 'r') as file:
        for line in file:
            #print(line)
            line = line.rstrip()
            standardPackages.append(line)

    print("allOrphanFiles")
    tempList = allOrphanFiles

    for f in standardPackages:
        if f in allOrphanFiles:
            tempList.remove(f)
            print(f, " Removed from list")
            print(len(tempList))
    if allOrphanFiles == tempList:
        allUnknownFiles = tempList
    else:
        allUnknownFiles = tempList

    warning = "All files remaining after known Debian/Ubuntu files are removed from the Orphan Files"
    create_html_page("NewFiles",allUnknownFiles,links=False, warning=warning, title="Unknown/New Files")
    pass


def create_all_pages():
    """Calls the create_html_page() function multiple times"""
    print("Creating files")

    global allUnchangedFiles
    allUnchangedFiles.sort()
    warning = "Files found and compared with no differences found"
    create_html_page(name="unchangedFiles", content=allUnchangedFiles, links=True, title="All unchanged files", warning=warning)

    global allOrphanFiles
    allOrphanFiles.sort()
    warning = "Files found under /etc with no related package"
    create_html_page(name="orphanFiles", content=allOrphanFiles, links=False,title="All orphan files", warning = warning)

    global allPackages
    allPackages.sort()
    #create_html_page("allPackages",allPackages, False)
    warning = "All packages found liked to conf files under /etc"
    create_html_page(name="allPackages", content=allPackages, links=False,title="All found/scanned packages", warning = warning)

    global allConfigFiles
    allConfigFiles.sort()
    #create_html_page("allConfigFiles",allPackages, False)
    warning = "All config files found under /etc"
    create_html_page(name="allConfigFiles", content=allConfigFiles, links=False,title="All found config files", warning = warning)

    #create_unknown_files()

    #test_aptfile()

    summary = create_summary()

    create_html_page(name="index", content=summary, links=False,title="", warning = "")


def test_aptfile():
    global allPackages
    foundFiles = []
    for i in allPackages:
        cmd = ["apt-file", "list", i]
        rawCMD = run_command(cmd, cwd=".", outputCap=True, shell=False, captError=False)
        print("Apt-File: ", rawCMD)
        for line in rawCMD:
            if "/etc/" in line:
                foundFiles.append(line)

    create_html_page(name="apt-file", content=foundFiles, links=False,title="Apt-file files", warning = "")
    pass


def find_mention_in_dpkg():
    """Running a grep command to find occurance of files in /var/lib/dpkg/info/"""
    print_sign("Finding mentions of orphan files in the dpkg files")
    global allOrphanFiles
    global allUnknownFiles
    mentionList = []
    for o in allUnknownFiles:
        #print(o)
        #cmd = ["grep " "-r", o, "."]
        if o == "":
            continue
        cmd = ["grep", "-r", o, "."]
        rawCMD = run_command(cmd, cwd="/var/lib/dpkg/info/", outputCap=True, shell=True, captError=True)
        if rawCMD[0]:
            print(o, " is still unknown!")
        else:
            print("Occurence of :", o, " Found!")
        #print(rawCMD[0])
        #print(type(rawCMD))
        #mentionList.append(o)


def create_summary():
    """Creates the summary for the report"""
    global allOrphanFiles
    global allUnchangedFiles
    global allConfigFiles
    global allUnknownFiles
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
        filedata = filedata.replace('[configFiles]', str(len(allConfigFiles)))
        #filedata = filedata.replace('[unknownFiles]', str(len(allUnknownFiles)))
    listFileData = []
    listFileData.append(filedata)
    return listFileData


def show_info():
    """Show information after the script is done"""
    print("-:Your IP config:-")
    ip = Popen(["ip", "a"])
    ip.communicate()
    print("_-‾-" * 25)
    print("‾-_-" * 25)
    print("Doc-Overdue scan complete!")
    print("Your report is available under html")
    print("The report is also available as a PDF and epub")
    print("If you want to expose the report via a webserver you can do so with the command:")
    print(" python3 -m http.server  ")
    print("This will make your report available at http://[yourIP]:8000/html")
    print("TIP! Your ip config has been printed above!")
    print("_-‾-" * 25)
    print("‾-_-" * 25)
    pass


# Main Runtime
first_run()

installedPackages = []

if largeScan:
    installedPackages = fetch_installed_packages()
    etcFiles = parse_config_files(installedPackages)

else:
    foundEtcFiles = scan_files_etc()
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
create_file_detections()
#find_mention_in_dpkg()
show_info()
