#!/usr/bin/env python3
"""
# Purpose: For a Google Drive User(s), show all drive file ACLs for Team Drive files shared with selected groups.
# Note: This script requires Advanced GAM:
#	https://github.com/taers232c/GAMADV-XTD3
# Customize: Set GROUP_LIST.
# Usage:
# For all Team Drives, start at step 1; For Team Drives selected by user/group/OU, start at step 6
# All Team Drives
# 1: Get all Team Drives.
#  $ gam redirect csv ./TeamDrives.csv print teamdrives fields id,name
# 2: Get ACLs for all Team Drives
#  $ gam redirect csv ./TeamDriveACLs.csv multiprocess csv TeamDrives.csv gam print drivefileacls ~id
# 3: Customize GetTeamDriveOrganizers.py for this task:
#    Set DOMAIN_LIST as required
#    Set ONE_ORGANIZER = True
#    Set SHOW_GROUP_ORGANIZERS = False
#    Set SHOW_USER_ORGANIZERS = True
# 4: From that list of ACLs, output a CSV file with headers "id,name,organizers"
#    that shows the organizers for each Team Drive
#  $ python GetTeamDriveOrganizers.py TeamDriveACLs.csv TeamDrives.csv TeamDriveOrganizers.csv
# 4: Get ACLs for all team drive files
#  $ gam redirect csv ./filelistperms.csv multiprocess csv TeamDriveOrganizers.csv gam user ~organizers print filelist select teamdriveid ~id fields teamdriveid,id,title,permissions pm type group em
# 5: Go to step 10
# Selected Team Drives
# 6: If want Team Drives for a specific set of organizers, replace <UserTypeEntity> with your user selection in the command below
#  $ gam redirect csv ./AllTeamDrives.csv <UserTypeEntity> print teamdrives role organizer fields id,name
# 7: Customize DeleteDuplicateRows.py for this task:
#    Set ID_FIELD = 'id'
# 8: Delete duplicate Team Drives (some may have multiple organizers).
#  $ python DeleteDuplicateRows.py ./AllTeamDrives.csv ./TeamDrives.csv
# 9: Get ACLs for all team drive files
#  $ gam redirect csv ./filelistperms.csv multiprocess csv TeamDrives.csv gam user ~User print filelist select teamdriveid ~id fields teamdriveid,id,title,permissions pm type group em
# Common code
# 10: From that list of ACLs, output a CSV file with headers "Owner,driveFileId,driveFileTitle,permissionId,role,emailAddress"
#    that lists the driveFileIds and permissionIds for all ACLs with the desired groups
#    (n.b., driveFileTitle, role, and emailAddress are not used in the next step, they are included for documentation purposes)
#  $ python GetSharedWithGroupTeamDriveACLs.py filelistperms.csv deleteperms.csv
# 11: Inspect deleteperms.csv, verify that it makes sense and then proceed
# 12: Delete the ACLs
#  $ gam csv deleteperms.csv gam user "~Owner" delete drivefileacl "~driveFileId" "~permissionId"
"""

import csv
import re
import sys

FILE_NAME = 'name'
ALT_FILE_NAME = 'title'

# Substitute your group(s) in the list below, e.g., GROUP_LIST = ['group1@domain.com',] GROUP_LIST = ['group1@domain.com', 'group2@domain.com',]
GROUP_LIST = ['group@domain.com',]

QUOTE_CHAR = '"' # Adjust as needed
LINE_TERMINATOR = '\n' # On Windows, you probably want '\r\n'

PERMISSIONS_N_TYPE = re.compile(r"permissions.(\d+).type")

if (len(sys.argv) > 2) and (sys.argv[2] != '-'):
  outputFile = open(sys.argv[2], 'w', encoding='utf-8', newline='')
else:
  outputFile = sys.stdout
outputCSV = csv.DictWriter(outputFile, ['Owner', 'driveFileId', 'driveFileTitle', 'permissionId', 'role', 'emailAddress'], lineterminator=LINE_TERMINATOR, quotechar=QUOTE_CHAR)
outputCSV.writeheader()

if (len(sys.argv) > 1) and (sys.argv[1] != '-'):
  inputFile = open(sys.argv[1], 'r', encoding='utf-8')
else:
  inputFile = sys.stdin

for row in csv.DictReader(inputFile, quotechar=QUOTE_CHAR):
  for k, v in iter(row.items()):
    mg = PERMISSIONS_N_TYPE.match(k)
    if mg and v == 'group':
      permissions_N = mg.group(1)
      emailAddress = row.get('permissions.{0}.emailAddress'.format(permissions_N), '')
      if emailAddress in GROUP_LIST:
        outputCSV.writerow({'Owner': row['Owner'],
                            'driveFileId': row['id'],
                            'driveFileTitle': row.get(FILE_NAME, row.get(ALT_FILE_NAME, 'Unknown')),
                            'permissionId': 'id:{0}'.format(row['permissions.{0}.id'.format(permissions_N)]),
                            'role': row['permissions.{0}.role'.format(permissions_N)],
                            'emailAddress': emailAddress})

if inputFile != sys.stdin:
  inputFile.close()
if outputFile != sys.stdout:
  outputFile.close()
