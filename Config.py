#!/usr/bin/env python
import json
import datetime
import os

configFile = "config.ini"

class Bully:
    def __init__(self):
        self.timeBullySet = None
        self.permaBully = False

class TF:
    def __init__(self):
        self.timeTfSet = None
        self.originalName = None

class GuildConfig:
    def __init__(self):
        self.bullyRoleID = None
        self.bullyTime = datetime.timedelta(days=1)
        self.tfTime = datetime.timedelta(days=1)
        self.bullies = {}
        self.tfs = {}

    def EnsureMemberBully(self, memberID):
        if memberID not in self.bullies:
            self.bullies[memberID] = Bully()

class UserConfig:
    def __init__(self):
        self.tfIncludeTags = []
        self.tfExcludeTags = []

class Config:
    def __init__(self):
        self.guildConfigs = {}
        self.token = ""
        self.additionalAdmins = []
        self.userConfigs = {}

    def GetUserConfig(self, userID):
        if userID not in self.userConfigs:
            self.userConfigs[userID] = UserConfig()
        return self.userConfigs[userID]

def encode_guildConfig(o):
    if isinstance(o, Config):
        return {"__Config__":True, "GuildConfigs":o.guildConfigs, "Token":o.token, "AdditionalAdmins":o.additionalAdmins, "UserConfigs":o.userConfigs}
    elif isinstance(o, GuildConfig):
        return {"__GuildConfig__":True, "BullyRole":o.bullyRoleID, "BullyTime":o.bullyTime, "TFTime":o.tfTime, "Bullies":o.bullies, "TFs":o.tfs}
    elif isinstance(o, datetime.timedelta):
        return {"__timedelta__": True, "Days": o.days, "Seconds": o.seconds}
    elif isinstance(o, datetime.datetime):
        return {"__datetime__": True, "Year": o.year, "Month": o.month, "Day": o.day, "Hour": o.hour, "Minute": o.minute, "Second": o.second}
    elif isinstance(o, Bully):
        return {"__Bully__": True, "TimeBullySet": o.timeBullySet, "PermaBully": o.permaBully}
    elif isinstance(o, TF):
        return {"__TF__": True, "TimeTfSet": o.timeTfSet, "OriginalName": o.originalName}
    elif isinstance(o, UserConfig):
        return {"__UserConfig__": True, "TFIncludeTags": o.tfIncludeTags, "TFExcludeTags": o.tfExcludeTags}
    else:
       type_name = o.__class__.__name__
       raise TypeError("Object of type '{0}' is not JSON serializable".format(type_name))

def decode_guildConfig(dct):
    if "__Config__" in dct:
        config = Config()

        guildConfigsTemp = dct["GuildConfigs"]
        for (key, value) in guildConfigsTemp.items():
            #convert the key into an int from a string
            config.guildConfigs[int(key)] = value

        config.token = dct["Token"]
        config.additionalAdmins = dct["AdditionalAdmins"]

        try:
            userConfigsTemp = dct["UserConfigs"]
            for (key, value) in userConfigsTemp.items():
                #convert the key into an int from a string
                config.userConfigs[int(key)] = value
        except KeyError:
            pass


        return config
    if "__GuildConfig__" in dct:
        guildConfig = GuildConfig()
        guildConfig.bullyRoleID = dct["BullyRole"]
        guildConfig.bullyTime = dct["BullyTime"] if 'BullyTime' in dct else guildConfig.bullyTime
        guildConfig.tfTime = dct["TFTime"] if 'TFTime' in dct else guildConfig.tfTime
        bullies = dct["Bullies"] if 'Bullies' in dct else guildConfig.bullies
        tfs = dct["TFs"] if 'TFs' in dct else guildConfig.tfs

        for (key, value) in bullies.items():
            guildConfig.bullies[int(key)] = value

        for (key, value) in tfs.items():
            guildConfig.tfs[int(key)] = value

        return guildConfig
    elif "__timedelta__" in dct:
        return datetime.timedelta(days=dct["Days"], seconds=dct["Seconds"])
    elif "__datetime__" in dct:
        return datetime.datetime(year=dct["Year"], month=dct["Month"], day=dct["Day"], hour=dct["Hour"], minute=dct["Minute"], second=dct["Second"])
    elif "__Bully__" in dct:
        bully = Bully()
        bully.timeBullySet = dct["TimeBullySet"]
        bully.permaBully = dct["PermaBully"]
        return bully
    elif "__TF__" in dct:
        tf = TF()
        tf.timeTfSet = dct["TimeTfSet"]
        tf.originalName = dct["OriginalName"]
        return tf
    elif "__UserConfig__" in dct:
        userConfig = UserConfig()
        userConfig.tfIncludeTags = dct["TFIncludeTags"]
        userConfig.tfExcludeTags = dct["TFExcludeTags"]
        return userConfig
    return dct

config = None

def LoadConfig():
    global config
    try:
        with open(configFile, 'r') as file:
            config = json.load(file, object_hook=decode_guildConfig)
    except FileNotFoundError:
        print("No config file found")
        config = Config()
    except Exception as ex:
        print("Failed to load config file")
        raise

def SaveConfig():
    tempConfigFile = configFile +  ".tmp"
    try:
        with open(tempConfigFile, 'w') as file:
            json.dump(config, file, default=encode_guildConfig)

        try:
            os.remove(configFile)
        except:
            #don't care
            pass
        os.rename(tempConfigFile, configFile)
    except Exception as ex:
        print("Failed to save config file")

def EnsureGuild(guildID):
    global config
    if guildID not in config.guildConfigs:
        config.guildConfigs[guild.id] = GuildConfig()

def GetGuildConfig(guildID):
    if guildID in config.guildConfigs:
        return config.guildConfigs[guildID]
    else:
        return None