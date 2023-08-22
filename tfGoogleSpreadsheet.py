#!/usr/bin/python3
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from tfWheelUtils import TfCharacters
from tfWheelUtils import TfCharacter

def LoadTFWheelChoices():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('google_secret.json', scope)
        client = gspread.authorize(creds)
    except Exception as ex:
        print("Failed to log in to google spreadsheet")
        return False

    try:
        spreadsheet = client.open("Tf Wheel Choices")
        sheet = spreadsheet.worksheet("Characters")
        if sheet is None:
            print("Failed to find worksheet 'Characters'")
            return False
        sheetData = sheet.get_all_records()
    except gspread.SpreadsheetNotFound as ex:
        print("Failed to load spreadsheet")
        return False

    characters = TfCharacters()
    for row in sheetData:
        name = row["Character"].strip('\n')
        weight = row["Weight"]
        specificUser = row["UserID"]

        if (len(name) == 0 or
                type(weight) is not int or weight <= 0):
            if any(len(v) > 0 for k, v in row.items()):
                print("Row {0} is invalid".format(row))
            #else a completely empty row so just ignore
            continue

        newCharacter = TfCharacter()
        newCharacter.name = name
        newCharacter.weight = weight
        newCharacter.specificUser = specificUser if type(specificUser) is int else None
        for columnName, tag in row.items():
            if columnName.startswith("Tag") and type(tag) is str:
                tag = tag.strip()
                if len(tag) > 0:
                    newCharacter.tags.append(tag.lower())

        characters.characters.append(newCharacter)
    return True, characters
