#!/usr/bin/python3
import discord
import re
import random
import asyncio
import math
import datetime
import os
import Client
import Config

tfListFile = "tfList.txt"
tfList = []
cumulativeWeights = []
totalWeight = 0
userUniqueTFs = {}
userUniqueTFCumulativeWeights = {}
userUniqueTFTotalWeights = {}

tfRegex = re.compile('(([0-9]+):)?(.*?)(:([0-9]+))?\n?', re.IGNORECASE)

with open(tfListFile, 'r') as file:
    for line in file:
        match = tfRegex.fullmatch(line)
        if match:
            if match.group(1):
                userID = int(match.group(2))
                tfTarget = match.group(3)
                weight = int(match.group(5)) if match.group(5) else 1
                if userID not in userUniqueTFs:
                    userUniqueTFs[userID] = []
                    userUniqueTFCumulativeWeights[userID] = []
                    userUniqueTFTotalWeights[userID] = 0
                userList = userUniqueTFs[userID]
                userCumulativeWeightList = userUniqueTFCumulativeWeights[userID]
                newUserTotalWeight = userUniqueTFTotalWeights[userID] + weight

                userList.append(tfTarget)
                userCumulativeWeightList.append(newUserTotalWeight)
                userUniqueTFTotalWeights[userID] = newUserTotalWeight
            else:
                tfTarget = match.group(3)
                weight = int(match.group(5)) if match.group(5) else 1
                totalWeight = totalWeight + weight
                tfList.append(tfTarget)
                cumulativeWeights.append(totalWeight)

def PickFromList(list, cumulativeWeights):
    count = len(cumulativeWeights)
    weight = random.randint(0, cumulativeWeights[count - 1])

    lower = 0
    while count > 0:
        step = int(count / 2)
        i = lower + step
        if cumulativeWeights[i] < weight:
            lower = i + 1
            count = count - (step + 1)
        else:
            count = step;

    return list[lower]


def SaveTfList():
    global userUniqueTFs
    global userUniqueTFCumulativeWeights
    global tfList
    global cumulativeWeights

    tempTfListFile = tfListFile +  ".tmp"
    try:
        with open(tempTfListFile, 'w') as file:
            totalWeight = 0
            for (character, cumulativeWeight) in zip(tfList, cumulativeWeights):
                weight = cumulativeWeight - totalWeight
                totalWeight = cumulativeWeight
                file.write("{0}:{1}\n".format(character,weight))
            for (userId, characters) in userUniqueTFs.items():
                characterCumulativeWeights = userUniqueTFCumulativeWeights[userId]
                totalWeight = 0
                for (character, cumulativeWeight) in zip(characters, characterCumulativeWeights):
                    weight = cumulativeWeight - totalWeight
                    totalWeight = cumulativeWeight
                    file.write("{0}:{1}:{2}\n".format(userId, character, weight))
        try:
            os.remove(tfListFile)
        except:
            #don't care
            pass
        os.rename(tempTfListFile, tfListFile)
    except Exception as ex:
        print("Failed to save tf list file")




def GetHelp(isGuildHelp, isAdmin):
    if isGuildHelp:
        return "!TF - get tfed into somepony else for a day"
    elif isAdmin:
        return "!AddTfCharacter \"UserName\" \"CharacterName\" - Adds a character for tfing into, you can omitt the user name to add to the global tf list"
    else:
        return "!AddUserTfCharacter \"CharacterName\" - Adds a character that you can tf into"

addTfCharacterRegex = re.compile('!AddTfCharacter ("(.*?)" )?"(.*?)"', re.IGNORECASE)
addUserTfCharacterRegex = re.compile('!AddUserTfCharacter "(.*?)"', re.IGNORECASE)

async def HandleCommands(message, isAdmin):
    global userUniqueTFs
    global userUniqueTFCumulativeWeights
    global userUniqueTFTotalWeights
    global tfList
    global cumulativeWeights
    global totalWeight
    if isAdmin:
        match = addTfCharacterRegex.match(message.content)
        if match:
            if match.group(2):
                #user specific tf
                userName = match.group(2)
                #find the user
                foundUser = None
                for guild in Client.client.guilds:
                    foundUser = discord.utils.find(lambda m: m.name.lower() == userName.lower(), guild.members)
                    if foundUser is not None:
                        break
                if foundUser is None:
                    await message.channel.send("Unable to find user {0}".format(userName))
                    return

                character = match.group(3)
                if foundUser.id not in userUniqueTFs:
                    userUniqueTFs[foundUser.id] = []
                    userUniqueTFCumulativeWeights[foundUser.id] = []
                    userUniqueTFTotalWeights[foundUser.id] = 0

                userList = userUniqueTFs[foundUser.id]
                userCumulativeWeightList = userUniqueTFCumulativeWeights[foundUser.id]
                newUserTotalWeight = userUniqueTFTotalWeights[foundUser.id] + 10

                userList.append(character)
                userCumulativeWeightList.append(newUserTotalWeight)
                userUniqueTFTotalWeights[foundUser.id] = newUserTotalWeight

                await message.channel.send("Added character {0} to users {1} list".format(character, userName))
            else:
                #global tf
                character = match.group(3)

                tfList.append(character)
                totalWeight = totalWeight + 1
                cumulativeWeights.append(totalWeight)
                await message.channel.send("Added character {0} to global list".format(character))
            SaveTfList()
    else:
        match = addUserTfCharacterRegex.match(message.content)
        if match:

            character = match.group(1)
            if message.author.id not in userUniqueTFs:
                userUniqueTFs[message.author.id] = []
                userUniqueTFCumulativeWeights[message.author.id] = []
                userUniqueTFTotalWeights[message.author.id] = 0

            userList = userUniqueTFs[message.author.id]
            userCumulativeWeightList = userUniqueTFCumulativeWeights[message.author.id]
            newUserTotalWeight = userUniqueTFTotalWeights[message.author.id] + 10

            userList.append(character)
            userCumulativeWeightList.append(newUserTotalWeight)
            userUniqueTFTotalWeights[message.author.id] = newUserTotalWeight

            await message.channel.send("Added character {0} to your list".format(character))

tfMeRegex = re.compile("!TF", re.IGNORECASE)

async def HandleGuildCommands(message, isAdmin):
    matchResult = tfMeRegex.match(message.content)
    if matchResult:
        await TriggerTF(message)

def on_member_update(before, after):
    if before.display_name == after.display_name:
        return

async def TriggerTF(message):
    async with message.channel.typing():

        selectedTf = ""
        if message.author.id in userUniqueTFs:
            userWeight = userUniqueTFTotalWeights[message.author.id]
            listSelectWeight = random.randint(0, userWeight + totalWeight - 1)
            if listSelectWeight < totalWeight:
                selectedTf = PickFromList(tfList, cumulativeWeights)
            else:
                selectedTf = PickFromList(userUniqueTFs[message.author.id], userUniqueTFCumulativeWeights[message.author.id])
        else:
            selectedTf = PickFromList(tfList, cumulativeWeights)

        sentMessage = await message.channel.send("Spinning the tf wheel...")
        rollTime = random.uniform(1.0, 1.5)

        await asyncio.sleep(rollTime)
        await sentMessage.edit(content="Spinning the tf wheel...\nHave fun being {0} for a day!".format(selectedTf))

        try:
            await message.author.edit(reason="nick", nick=selectedTf)
        except discord.errors.Forbidden:
            print("Can't change user {0} nickname".format(message.author.name))
            pass
        # else:
        guildConfig = Config.GetGuildConfig(message.guild.id)
        if message.author.id in guildConfig.tfs:
            #already tfed, so just update the time
            guildConfig.tfs[message.author.id].timeTfSet = datetime.datetime.now()
        else:
            newTF = Config.TF()
            newTF.timeTfSet = datetime.datetime.now()
            newTF.originalName = message.author.display_name
            guildConfig.tfs[message.author.id] = newTF
        Config.SaveConfig()


async def tick():
    currentTime = datetime.datetime.now()
    for (guildID, guildConfig) in Config.config.guildConfigs.items():
        for (user, tf) in list(guildConfig.tfs.items()):
            if tf.timeTfSet is not None:
                tfTimeEnd = tf.timeTfSet + guildConfig.tfTime
                if currentTime > tfTimeEnd:
                    # remove the tf
                    foundGuild = discord.utils.find(lambda g: g.id == guildID, Client.client.guilds)
                    member = foundGuild.get_member(user)

                    if member is None:
                        print("TF on {0} in server \"{1}\" expired. Member not found".format(user, foundGuild.name))
                    else:
                        print("TF on {0} in server \"{1}\" expired".format(member.name, foundGuild.name))

                        try:
                            Client.updatingMembers.append(member.id)
                            await member.edit(reason="nick", nick=tf.originalName)
                            Client.updatingMembers.remove(member.id)
                        except discord.errors.Forbidden:
                            print("Can't change user {0} nickname".format(member.name))
                            pass

                    del guildConfig.tfs[user]
                    Config.SaveConfig()