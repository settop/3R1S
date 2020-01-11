#!/usr/bin/python3
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from tfWheelUtils import TfCharacters
from tfWheelUtils import TfCharacter

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('google_secret.json', scope)
client = gspread.authorize(creds)

def LoadTFWheelChoices():
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
        name = row["Character"]
        weight = row["Weight"]
        specificUser = row["UserID"]

        if (len(name) == 0 or
                type(weight) is not int or weight <= 0):
            print("Row {0} is invalid".format(row))
            continue

        newCharacter = TfCharacter()
        newCharacter.name = name
        newCharacter.weight = weight
        newCharacter.specificUser = specificUser if type(specificUser) is int else None
        for columnName, tag in row.items():
            if columnName.startswith("Tag") and len(tag) > 0:
                newCharacter.tags.append(tag.lower())

        characters.characters.append(newCharacter)
    return True, characters