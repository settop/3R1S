#!/usr/bin/python3
import discord
import re
import os
import datetime
import asyncio
import Client
import Config
import uwuDetection
import tfWheel

async def SetBully(guild, member):
    print("Setting bully role on server member \"{0}\" in server \"{1}\"".format(member.name, guild.name))
    guildConfig = Config.GetGuildConfig(guild.id)
    bullyRoleID = guildConfig.bullyRoleID
    if bullyRoleID is None:
        return

    guildConfig.EnsureMemberBully(member.id)
    guildConfig.bullies[member.id].timeBullySet = datetime.datetime.now()
    Config.SaveConfig()

    currentRoles = member.roles
    for role in currentRoles:
        if role.id == bullyRoleID:
            #already has the bully role
            return

    bullyRole = guild.get_role(bullyRoleID)
    currentRoles.append(bullyRole)
    Client.updatingMembers.append(member.id)
    await member.edit(reason="roles", roles=currentRoles)
    Client.updatingMembers.remove(member.id)

async def BullyDetection(message):
    bullyRoleID = Config.GetGuildConfig(message.guild.id).bullyRoleID
    if bullyRoleID is None:
        return
    bullyRole = message.guild.get_role(bullyRoleID)
    if await uwuDetection.DoesMessageContainUWU(message):
        #await message.channel.send('uwu detected!')
        await SetBully(message.guild, message.author)

helpCommandRegex = re.compile("!Help", re.IGNORECASE)
getUserIDCommandRegex = re.compile("!GetMyUserID", re.IGNORECASE)
setBullyCommandRegex = re.compile("!SetBullyRole \"(.*?)\" \"(.*?)\"", re.IGNORECASE)

async def HandleCommands(message):
    matchResult = helpCommandRegex.match(message.content)
    isAdmin = Client.IsAdmin(message.author)
    if matchResult is not None:
        helpString = "!Help - Prints this message you're currently reading\n"
        helpString += "!GetMyUserID - Returns your discord user id\n"
        if isAdmin:
            helpString += """!SetBullyRole "ServerName" "RoleName" - Sets the bully role for a server\n"""
        helpString += tfWheel.GetHelp(False, isAdmin)
        await message.channel.send(helpString)
        return
    if isAdmin:
        matchResult = setBullyCommandRegex.match(message.content)
        if matchResult is not None:
            serverName = matchResult.group(1)
            bullyRole = matchResult.group(2)

            foundGuild = discord.utils.find(lambda g: g.name == serverName, Client.client.guilds)
            if foundGuild is None:
                await message.channel.send('Unrecognised server name \"{0}\"'.format(serverName))
                return

            foundRole = discord.utils.find(lambda r: r.name == bullyRole, foundGuild.roles)
            if foundRole is None:
                await message.channel.send('Unrecognised role name \"{0}\"'.format(bullyRole))
                return

            Config.config.guildConfigs[foundGuild.id].bullyRoleID = foundRole.id
            Config.SaveConfig()
            await message.channel.send('Set the bully role to \"{0}\" for server \"{1}\"'.format(bullyRole, serverName))
            return
    matchResult = getUserIDCommandRegex.match(message.content)
    if matchResult:
        await message.channel.send('Your user id is {0}'.format(message.author.id))

    await tfWheel.HandleCommands(message, isAdmin)


async def HandleGuildCommands(message):
    isAdmin = Client.IsAdmin(message.author)
    matchResult = helpCommandRegex.match(message.content)
    if matchResult is not None:
        helpString = """!Help - Prints this message you're currently reading\n"""
        helpString = helpString + tfWheel.GetHelp(True, isAdmin)
        await message.channel.send(helpString)
        return
    await tfWheel.HandleGuildCommands(message, isAdmin)


@Client.client.event
async def on_message(message):
    #p = message.channel.permissions_for(message.channel.guild.get_member(Client.client.user.id))
    # we do not want the bot to reply to itself
    if message.author == Client.client.user:
        return
    if message.guild is None:
        # private message
        await HandleCommands(message)
    else:
        if message.author == Client.client.user:
            return
        await HandleGuildCommands(message)
        await BullyDetection(message)


@Client.client.event
async def on_message_edit(before, after):
    # we do not want the bot to reply to itself
    if after.author == Client.client.user:
        return
    if after.guild is not None:
        await BullyDetection(after)


@Client.client.event
async def on_guild_join(guild):
    Config.EnsureGuild(guild.id)

def CheckBullyUpdate(before, after):
    guildConfig = Config.GetGuildConfig(before.guild.id)
    bullyRoleID = guildConfig.bullyRoleID
    if bullyRoleID is None:
        return
    bullyRole = discord.utils.find(lambda r: r.id == bullyRoleID, before.guild.roles)
    if bullyRole is None:
        return

    bullyBefore = bullyRole in before.roles
    bullyAfter  = bullyRole in after.roles

    if bullyBefore == bullyAfter:
        #bully role didn't change, so don't care
        return

    if bullyBefore:
        #bully role was removed by an admin
        print("Bully role on \"{0}\" in server \"{1}\" removed by admin".format(before.name, before.guild.name))
        if before.id in guildConfig.bullies:
            del guildConfig.bullies[before.id]
    else:
        #bully role was added by an admin
        print("Bully role on \"{0}\" in server \"{1}\" added by admin".format(before.name, before.guild.name))
        if before.id not in guildConfig.bullies:
            guildConfig.bullies[before.id] = Bully()
        guildConfig.bullies[before.id].timeBullySet = datetime.datetime.now()
    Config.SaveConfig()

@Client.client.event
async def on_member_update(before, after):
    if before.id in Client.updatingMembers:
        #we are updating this role
        return
    CheckBullyUpdate(before, after)
    tfWheel.on_member_update(before,after)


@Client.client.event
async def on_ready():
    print('Logged in as')
    print(Client.client.user.name)
    print(Client.client.user.id)
    print('------')
    print('Guilds:')
    for guild in Client.client.guilds:
        print(guild.name)
        Config.EnsureGuild(guild.id)
    print('------')

async def tick():
    while True:
        await asyncio.sleep(5)
        try:
            currentTime = datetime.datetime.now()
            for (guildID, guildConfig) in Config.config.guildConfigs.items():
                for (user, bully) in list(guildConfig.bullies.items()):
                    if not bully.permaBully and bully.timeBullySet is not None:
                        bullyEndTime = bully.timeBullySet + guildConfig.bullyTime
                        if currentTime > bullyEndTime:
                            #remove the bully
                            foundGuild = discord.utils.find(lambda g: g.id == guildID, Client.client.guilds)
                            member = foundGuild.get_member(user)
                            if member is None:
                                del guildConfig.bullies[user]
                                continue
                            currentRoles = member.roles

                            print("Bully role on {0} in server \"{1}\" expired".format(member.name, foundGuild.name))

                            bullyRole = foundGuild.get_role(guildConfig.bullyRoleID)
                            if bullyRole in currentRoles:
                                currentRoles.remove(bullyRole)

                                Client.updatingMembers.append(member.id)
                                await member.edit(reason="roles", roles=currentRoles)
                                Client.updatingMembers.remove(member.id)
                            del guildConfig.bullies[user]
                            Config.SaveConfig()
            await tfWheel.tick()
        except Exception as ex:
            print("Tick exception: {0}".format(ex))
            pass



future = asyncio.ensure_future(tick(), loop=Client.client.loop)

Config.LoadConfig()
try:
    Client.client.run(Config.config.token)
except discord.DiscordException as ex:
    print(ex)
    pass