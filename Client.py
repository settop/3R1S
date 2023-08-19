#!/usr/bin/python3
import discord
import Config

clientIntents = discord.Intents(messages=True, message_content=True, guilds=True)
client = discord.Client(intents=clientIntents)
updatingMembers = []

def IsAdmin(user):
    if user.id in Config.config.additionalAdmins:
        return True
    for guild in client.guilds:
        if guild.owner_id == user.id:
            return True
    return False