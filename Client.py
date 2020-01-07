#!/usr/bin/python3
import discord
import Config

client = discord.Client()
updatingMembers = []

def IsAdmin(user):
    if user.id in Config.config.additionalAdmins:
        return True
    for guild in client.guilds:
        if guild.owner.id == user.id:
            return True
    return False