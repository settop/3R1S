#!/usr/bin/python3
import discord
from discord.ext import tasks, commands
import re
import random
import asyncio
import math
import datetime
import os
import Config
import tfGoogleSpreadsheet

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

class TfWheel(commands.Cog):

    def __init__(self, client : discord.Client):
        self.client = client

        self.originalNameRegex = re.compile(".+\((.+)\)", re.IGNORECASE)
        self.updatingMembers = []
        self.UpdateCharactersImpl()
        self.UpdateTf.start()
        self.UpdateCharacters.start()

    def cog_unload(self):
        self.UpdateTf.cancel()
        self.UpdateCharacters.cancel()

    def UpdateCharactersImpl(self):
        loadSuccess, self.characters = tfGoogleSpreadsheet.LoadTFWheelChoices()
        if not loadSuccess:
            raise Exception("Failed to load tf list spreadsheet")

        self.lastTfCharacterUpdate = datetime.datetime.now()

        self.allTags = set()
        for character in self.characters.characters:
            for tag in character.tags:
                self.allTags.add(tag)

    def ParseTags(self, *tags):
        includeTags = []
        excludeTags = []
        for tag in tags:
            if tag is None or tag == "" or tag == "!":
                continue
            if tag.startswith('!'):
                excludeTags.append(tag[1:])
            else:
                includeTags.append(tag)
        return includeTags, excludeTags

    def GetOriginalName(self, name :str):
        match = self.originalNameRegex.match(name)
        if match is None:
            return
        return match.group(1)

    def GetUserCharacterNickname(self, currentName :str, characterName :str):
        originalName = self.GetOriginalName(currentName)
        if originalName is not None:
            currentName = originalName
        return f"{characterName}({currentName})"

    def GetUserDefaultTags(self, userID :int):
        config = Config.config.GetUserConfig(userID)
        includeTags = config.tfIncludeTags
        excludeTags = config.tfExcludeTags
        return includeTags, excludeTags

    def AddUserDefaultTag(self, userID :int, tag :str):
        config = Config.config.GetUserConfig(userID)
        if tag.startswith('!'):
            tag = tag[1:]
            if tag:
                config.tfExcludeTags.append(tag)
        elif tag:
            config.tfIncludeTags.append(tag)
        Config.SaveConfig()

    def RemoveUserDefaultTag(self, userID: int, tag: str):
        config = Config.config.GetUserConfig(userID)
        if tag.startswith('!'):
            tag = tag[1:]
            if tag:
                config.tfExcludeTags.remove(tag)
        elif tag:
            config.tfIncludeTags.remove(tag)
        Config.SaveConfig()

    def TriggerTfForUser(self, guild :discord.Guild, user :discord.User, *tags):
        includeTags = []
        excludeTags = []

        includeTags, excludeTags = self.ParseTags(*tags)
        if not includeTags and not excludeTags:
            includeTags, excludeTags = self.GetUserDefaultTags(user.id)

        selectedCharacters, weights = self.characters.GetCharactersAndWeights(userID=user.id, includeTags=includeTags,excludeTags=excludeTags)

        if len(selectedCharacters) == 0:
            return

        selectedCharacterTf = PickFromList(selectedCharacters, weights)

        guildConfig = Config.GetGuildConfig(guild.id)
        if user.id in guildConfig.tfs:
            # already tfed, so just update the time
            guildConfig.tfs[user.id].timeTfSet = datetime.datetime.now()
        else:
            newTF = Config.TF()
            newTF.timeTfSet = datetime.datetime.now()
            guildConfig.tfs[user.id] = newTF
        Config.SaveConfig()
        return selectedCharacterTf

    def MemberUpdateLock(self, memberID :int):
        class UpdateLock:
            def __init__(self, updatingMembers, memberID):
                self.updatingMembers = updatingMembers
                self.memberID = memberID
            def __enter__(self):
                self.updatingMembers.append(self.memberID)
            def __exit__(self, exc_type, exc_value, traceback):
                self.updatingMembers.remove(self.memberID)
        return UpdateLock(self.updatingMembers, memberID)


    def on_member_update(self, memberBefore :discord.Member, memberAfter :discord.Member):
        if memberBefore.id in self.updatingMembers:
            return
        if memberBefore.guild.id not in Config.config.guildConfigs:
            return
        if memberBefore.display_name == memberAfter.display_name:
            return
        #name has changed
        #clear them from the updating config
        guildConfig = Config.config.guildConfigs[memberBefore.guild.id]
        if memberBefore.id in guildConfig.tfs:
            print("Nickname on {0} in server \"{1}\" changed. Removing tf timer".format(memberAfter.name, memberAfter.guild.name))
            del guildConfig.tfs[memberBefore.id]
            Config.SaveConfig()

    @tasks.loop(seconds=5.0)
    async def UpdateTf(self):
        currentTime = datetime.datetime.now()
        for (guildID, guildConfig) in  Config.config.guildConfigs.items():
            for (userID, tf) in list(guildConfig.tfs.items()):
                if tf.timeTfSet is not None:
                    tfTimeEnd = tf.timeTfSet + guildConfig.tfTime
                    if currentTime > tfTimeEnd:
                        # remove the tf
                        foundGuild = discord.utils.find(lambda g: g.id == guildID, self.client.guilds)
                        member = foundGuild.get_member(userID)

                        if member is None:
                            print("TF on {0} in server \"{1}\" expired. Member not found".format(userID, foundGuild.name))
                        else:
                            print("TF on {0} in server \"{1}\" expired".format(member.name, foundGuild.name))

                            try:
                                originalName = self.GetOriginalName(member.display_name)
                                if originalName is not None:
                                    with self.MemberUpdateLock(member.id):
                                        await member.edit(reason="nick", nick=originalName)
                                else:
                                    print(f"Unable to find original name from current display name '{member.display_name}'")
                            except discord.errors.Forbidden:
                                print("Can't change user {0} nickname".format(member.name))
                                pass

                        del guildConfig.tfs[userID]
                        Config.SaveConfig()

    @tasks.loop(hours=6.0)
    async def UpdateCharacters(self):
        self.UpdateCharactersImpl()