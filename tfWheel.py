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
import tfGoogleSpreadsheet

loadSuccess, characters = tfGoogleSpreadsheet.LoadTFWheelChoices()
if not loadSuccess:
    raise Exception("Failed to load tf list spreadsheet")

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


def GetHelp(isGuildHelp, isAdmin):
    if isGuildHelp:
        return "!TF \"Tag\"* - get tfed into somepony else for a day, optionally specify tags to use for the selection, use - before a tag to exclude a tag"
    else:
        return ("!SetDefaultTFTags \"Tag\"* - Sets the default set of tags that will be used for the !TF command use - before a tag to exclude a tag\n"
                "!GetDefaultTags - Returns the current ")

setDefaultTFTagsRegex = re.compile('!SetDefaultTFTags (".*?")*', re.IGNORECASE)
getDefaultTFTagsRegex = re.compile('!GetDefaultTFTags', re.IGNORECASE)

async def HandleCommands(message, isAdmin):
    global characters
    match = setDefaultTFTagsRegex.fullmatch(message.content)
    match = getDefaultTFTagsRegex.fullmatch(message.content)


tfMeRegex = re.compile("!TF", re.IGNORECASE)

async def HandleGuildCommands(message, isAdmin):
    matchResult = tfMeRegex.match(message.content)
    if matchResult:
        await TriggerTF(message)

def on_member_update(before, after):
    if before.display_name == after.display_name:
        return

async def TriggerTF(message):
    global characters
    async with message.channel.typing():

        selectedCharacters, weights = characters.GetCharactersAndWeights(userID=message.author.id, includeTags=[],excludeTags=[])
        selectedTf = PickFromList(selectedCharacters, weights)

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