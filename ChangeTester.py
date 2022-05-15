import random
from subprocess import Popen, PIPE

"""
DO NOT RUN THIS FILE! IT DOES POTENTIALLY SYSTEM BREAKING CHANGES!!
"""


ChangeFiles = []
NewFiles = []

amountChangedFiles = random.randrange(1,10)

outputSummary = ['-=:Summary:=- \n', '## Files changed by script ## \n']

#"echo "NewFile" > bajs.conf"
#Finding files
cmd = ["sh", "findEtcFiles.sh"]
rawCMD = Popen(cmd, stdout=PIPE)
outCMD = rawCMD.communicate()
etcFiles = str(outCMD[0]).split("\\n")

#removing certificates
certAmounts = 0
for r in etcFiles:
    if ".crt" in r or ".certs" in r or ".o" in r or "ca-certificates" in r:
        etcFiles.remove(r)
        certAmounts += 1
print(str(certAmounts) + " certificates removed")

print("#"*20)
# Adds a comment to a random amount of files in random locations


for i in range(amountChangedFiles):
    chosenFile = random.randrange(1,(len(etcFiles)-1))
    outputSummary.append(etcFiles[chosenFile]+'\n')
    with open(etcFiles[chosenFile], 'a') as file:
        file.writelines("# Added change by Doc-Overdue/ChangeTester")

#Print the changed files to a file that can be mached later.
for line in outputSummary:
    with open('ChangeFiles.log', 'w') as file:
        for lineSum in outputSummary:
            file.writelines(str(lineSum))
        pass
    print(outCMD)
