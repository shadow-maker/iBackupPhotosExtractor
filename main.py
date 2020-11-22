import os
import sys
import sqlite3
import json
import csv

print("\n\n---------------------------------------")
print("\n\tBackup Photos Extractor")
print("\n---------------------------------------")

print("\nLoading files to memory...")

manifest = {}
config = {}

# Load 'config.json' file to memory
if not os.path.isfile("config.json"):
    sys.exit("ERROR: Could not find configuration 'config.json' file")
with open("config.json", "r") as f:
    config = dict(json.load(f))
print("\tLoaded configuration file")

# Find Manifest database in backup file and load to memory
exists = False
for p, d, f in os.walk("Backup" if config["customBackupDirectory"] == "" else config["customBackupDirectory"]):
    if config["manifestDBName"] in f:
        exists = True
        c = sqlite3.connect(p + "/" + config["manifestDBName"]).cursor()
        c.execute("SELECT fileID, relativePath FROM Files")
        manifest = {i[0]:i[1] for i in c.fetchall()}
        break
if not exists:
    sys.exit("ERROR: Could not find Manifest database with name '" + config["manifestDBName"] + "' in backup file")
print("\tFound and loaded Manifest database\n")

print(len(manifest), "Total files found in Manifest")

# Ask user confirmation to continue
if config["userConfirmationPrompts"]:
    print("\n---\nType [OK] to begin filtering Photo Files from 'manifest.csv', or anything else to exit:\n>", end=" ")
    if input().lower() != "ok":
        sys.exit()

print("\nFiltering 'manifest.csv' file...\n")

# Get all possible file extensions
fileExtensions = []
if config["savePhotos"]:
    fileExtensions += config["photoFileExtensions"]
if config["saveVideos"]:
    fileExtensions += config["videoFileExtensions"]

# Filter all 'manifest.csv' files that follow certain rules
crPhotos = []
crPhotosJPG = []
crPhotosMOV = []
smsPhotos = []
smsPhotosNames = []
progTot = len(manifest)
progCount = 0
for i in manifest.items():
    # relativePath must end with one of the end filters (possible file extensions)
    # Ignores .MOV files, added later on
    if os.path.splitext(i[1])[1].lower() in fileExtensions:
        # Get Camera Roll photos
        if config["getCameraRollPhotos"]:
            # relativePath must begin with one of the start filters
            for f in config["filtersCameraRollPhotos"]:
                if i[1].startswith(f):
                    crPhotos.append({
                        "fileID": i[0],
                        "relativePath": i[1]
                    })
                    if os.path.splitext(i[1])[1].lower() == ".jpg" or os.path.splitext(i[1])[1].lower() == ".jpeg":
                        crPhotosJPG.append(os.path.splitext(i[1])[0])
                    elif os.path.splitext(i[1])[1].lower() == ".mov":
                        crPhotosMOV.append(os.path.splitext(i[1])[0])
        # Get iMessage Attachement Photos
        if config["getSMSPhotos"]:
            # relativePath must begin with one of the start filters
            for f in config["filtersSMSPhotos"]:
                if i[1].startswith(f):
                    smsPhotos.append({
                        "fileID": i[0],
                        "relativePath": i[1]
                    })
                    smsPhotosNames.append(os.path.splitext(i[1])[0])
    # Print progress bar
    progCount += 1
    progInc = int(50.0 / progTot * progCount)
    sys.stdout.write("\r" + "|%s%s| %d%%" % ("\033[7m" + " "*progInc + " \033[27m", " "*(50-progInc), 2*progInc))
    sys.stdout.flush()
# End progress bar
sys.stdout.write("\r" + "|%s| %d%%" % ("\033[7m" + " "*20 + "COMPLETE!" + " "*21 + " \033[27m", 100))
sys.stdout.flush()
sys.stdout.write("\n\n")

# Create 'CSV' directory if it doesn't exist
if not os.path.exists("CSV"):
    os.makedirs("CSV")

# Function to save file to CSV
def saveCSV(file, fileName):
    if len(file) > 0:
        with open(fileName, "w") as newFile:
            csvWrite = csv.DictWriter(newFile, fieldnames=list(file[0].keys()), delimiter=",")
            csvWrite.writeheader()
            for i in file:
                csvWrite.writerow(i)
        print(" -> saved to '" + fileName + "'")

# Save filtered files from 'manifest.csv' to new files
if config["getCameraRollPhotos"]:
    print(len(crPhotos),"\tCamera Roll photo files filtered from 'manifest.csv'", end="")
    saveCSV(crPhotos, "CSV/photosCameraRoll.csv")
if config["getSMSPhotos"]:
    print(len(smsPhotos),"\tiMessage Attachement Photo files filtered from 'manifest.csv'", end="")
    saveCSV(smsPhotos, "CSV/photosSMS.csv")
if config["getCameraRollPhotos"] and config["getSMSPhotos"]:
    print(len(crPhotos) + len(smsPhotos),"\tTotal unique Photo files filtered from 'manifest.csv'", end="")


# Ask user confirmation to continue
if config["userConfirmationPrompts"]:
    print("\n\n---\nType [OK] to continue processing the input Backup Files, or anything else to exit:\n>", end=" ")
    if input().lower() != "ok":
        sys.exit()

# Get all input filenames and filepaths
print("\nGetting all Backup file paths...")
filePaths = {}
for dirpath, dirnames, filenames in os.walk("Backup" if config["customBackupDirectory"] == "" else config["customBackupDirectory"]):
    if len(dirnames) == 0:
        for f in filenames:
            filePaths[f] = dirpath

# Function to get output directory for each file
def getDir(relativePath, typeFolder, filters):
    dir = "Photos/" if config["customPhotosOutputDirectory"] == "" else config["customPhotosOutputDirectory"] + "/"
    if config["outputDirectoriesFormat"].lower() == "type":
        dir += typeFolder + "/" + os.path.dirname(relativePath)
    elif config["outputDirectoriesFormat"].lower() == "ext":
        dir += os.path.splitext(relativePath)[1].upper()[1:] + "/" +  os.path.dirname(relativePath)
    elif config["outputDirectoriesFormat"].lower() == "type_ext":
        dir += typeFolder + "/" + os.path.splitext(relativePath)[1].upper()[1:] + "/" +  os.path.dirname(relativePath)
    elif config["outputDirectoriesFormat"].lower() == "sim":
        for f in filters:
            if relativePath.startswith(f):
                dir += os.path.dirname(relativePath.replace(f, ""))
                break
    elif config["outputDirectoriesFormat"].lower() == "type_sim":
        for f in filters:
            if relativePath.startswith(f):
                dir += typeFolder + "/" + os.path.dirname(relativePath.replace(f, ""))
                break
    elif config["outputDirectoriesFormat"].lower() == "ext_sim":
        for f in filters:
            if relativePath.startswith(f):
                dir += os.path.splitext(relativePath)[1].upper()[1:] + "/" +  os.path.dirname(relativePath.replace(f, ""))
                break
    elif config["outputDirectoriesFormat"].lower() == "type_ext_sim":
        for f in filters:
            if i["relativePath"].startswith(f):
                dir += typeFolder + "/" + os.path.splitext(relativePath)[1].upper()[1:] + "/" +  os.path.dirname(relativePath.replace(f, ""))
                break
    elif config["outputDirectoriesFormat"].lower() == "smart":
        dir += typeFolder + "/"
        if os.path.dirname(relativePath).endswith("IMPRT"):
            dir += "Imports/"
        if os.path.splitext(os.path.dirname(relativePath))[1].lower() == ".pvt":
            dir += os.path.dirname(relativePath).split("/")[-2] + "/" +  os.path.dirname(relativePath).split("/")[-1]
        else:
            dir += os.path.dirname(relativePath).split("/")[-1]
    else:
        dir += os.path.dirname(relativePath)
    return dir


logNotFound = []

# Process Camera Roll Photo files
if config["getCameraRollPhotos"]:
    print("\nProcessing Camera Roll Photo files...\n")
    notExistCount = 0
    progTot = len(crPhotos)
    progCount = 0
    for i in crPhotos:
        # Check if photo file exists in input backup files
        if i["fileID"] in filePaths.keys():
            # Create original directories based on outputDirectoriesMethod
            dir = getDir(i["relativePath"], "CameraRoll", config["filtersCameraRollPhotos"])

            # if is Live Photo (JPG or MOV)
            if (os.path.splitext(i["relativePath"])[1].lower() == ".mov" and os.path.splitext(i["relativePath"])[0] in crPhotosJPG) or ((os.path.splitext(i["relativePath"])[1].lower() == ".jpg" or os.path.splitext(i["relativePath"])[1].lower() == ".jpeg") and os.path.splitext(i["relativePath"])[0] in crPhotosMOV):
                if config["saveLivePhotosPVT"]:
                    newDir = dir + "/" +  os.path.splitext(os.path.basename(i["relativePath"]))[0] + ".pvt"
                    # Create directory if it doesn't exist
                    if not os.path.exists(newDir):
                        os.makedirs(newDir)
                    # Rename (and move) file
                    os.rename(filePaths[i["fileID"]] + "/" + i["fileID"], newDir + "/" + os.path.basename(i["relativePath"]))
                if ((not config["saveLivePhotosJPG"]) and (os.path.splitext(i["relativePath"])[1].lower() == ".jpg" or os.path.splitext(i["relativePath"])[1].lower() == ".jpeg")) or ((not config["saveLivePhotosMOV"]) and os.path.splitext(i["relativePath"])[1].lower() == ".mov"):
                    continue
            else:
                # Create directory if it doesn't exist
                if not os.path.exists(dir):
                    os.makedirs(dir)
                # Rename (and move) file
                os.rename(filePaths[i["fileID"]] + "/" + i["fileID"], dir + "/" + os.path.basename(i["relativePath"]))
        else:
            notExistCount += 1
            logNotFound.append({
                "fileID": i["fileID"],
                "relativePath": i["relativePath"],
                "type": "CameraRoll"
            })
        # Print progress bar
        progCount += 1
        progInc = int(50.0 / progTot * progCount)
        sys.stdout.write("\r" + "|%s%s| %d%%" % ("\033[7m" + " "*progInc + " \033[27m", " "*(50-progInc), 2*progInc))
        sys.stdout.flush()
    # End progress bar
    sys.stdout.write("\r" + "|%s| %d%%" % ("\033[7m" + " "*20 + "COMPLETE!" + " "*21 + " \033[27m", 100))
    sys.stdout.flush()
    sys.stdout.write("\n\n")
    if notExistCount > 0:
        print(notExistCount, " Photo files from Main Photos were not found in the input backup files")

# Process iMessage Attachement Photo files
if config["getSMSPhotos"]:
    print("\nProcessing iMessage Attachement Photo files...\n")
    notExistCount = 0
    progTot = len(smsPhotos)
    progCount = 0
    for i in smsPhotos:
        # Check if photo file exists in input backup files
        if i["fileID"] in filePaths.keys():
            # Create original directories based on outputDirectoriesMethod
            dir = getDir(i["relativePath"], "iMessage", config["filtersSMSPhotos"])
            if not os.path.exists(dir):
                os.makedirs(dir)
            # Rename (and move) file
            os.rename(filePaths[i["fileID"]] + "/" + i["fileID"], dir + "/" + os.path.basename(i["relativePath"]))
        else:
            notExistCount += 1
            logNotFound.append({
                "fileID": i["fileID"],
                "relativePath": i["relativePath"],
                "type": "SMS"
            })
        # Print progress bar
        progCount += 1
        progInc = int(50.0 / progTot * progCount)
        sys.stdout.write("\r" + "|%s%s| %d%%" % ("\033[7m" + " "*progInc + " \033[27m", " "*(50-progInc), 2*progInc))
        sys.stdout.flush()
    # End progress bar
    sys.stdout.write("\r" + "|%s| %d%%" % ("\033[7m" + " "*20 + "COMPLETE!" + " "*21 + " \033[27m", 100))
    sys.stdout.flush()
    sys.stdout.write("\n\n")
    if notExistCount > 0:
        print(notExistCount, " Photo files from iMessage Attachement Photos were not found in the input backup files")

# Save Log of files not found in backup files to new file
if len(logNotFound) > 0:
    with open("CSV/logNotFound.csv", "w") as newFile:
        csvWrite = csv.DictWriter(newFile, fieldnames=list(logNotFound[0].keys()), delimiter=",")
        csvWrite.writeheader()
        for i in logNotFound:
            csvWrite.writerow(i)
    print("\n")
    print(len(logNotFound), "Files in total were not found in backup files -> Log saved to 'CSV/logNotFound.csv'")

# Remove unwanted iMessage Photo files from output directory
print("\nRemoving unwanted iMessage Attachement Photo files...\n")
for path, dirs, files in os.walk("Photos/iMessage" if config["customPhotosOutputDirectory"] == "" else config["customPhotosOutputDirectory"] + "/iMessage"):
    if os.path.splitext(path)[1].lower() == ".pvt":
        for file in files:
            if ((not config["saveLivePhotosJPG"] and (os.path.splitext(file)[1].lower() == ".jpg" or os.path.splitext(file)[1].lower() == ".jpeg")) or (not config["saveLivePhotosMOV"] and os.path.splitext(file)[1].lower() == ".mov")) and os.path.isfile(os.path.dirname(path) + "/" + file):
                os.remove(os.path.dirname(path) + "/" + file)
    if (not config["saveLivePhotosPVT"]) and config["getSMSPhotos"]:
        if os.path.splitext(path)[1].lower() == ".pvt":
            for file in files:
                if os.path.isfile("/".join(path.split("/")[:-1]) + "/" + file):
                    os.remove("/".join(path.split("/")[:-1]) + "/" + file)
        # Remove directory if empty
        if len([f for f in os.listdir("/".join(path.split("/")[:-1])) if f != ".DS_Store"]) == 0:
            if os.path.exists("/".join(path.split("/")[:-1]) + "/.DS_Store"):
                os.remove("/".join(path.split("/")[:-1]) + "/.DS_Store")
            os.rmdir("/".join(path.split("/")[:-1]))

print("\n\nDONE!")
