import discord
import asyncio
from discord import app_commands
from discord.ext import commands
import Config
import tfWheel
import bullyChecker


def is_guild_admin(interaction: discord.Interaction):
    if interaction.user.id in Config.config.additionalAdmins:
        return True
    return interaction.message.author.guild_permissions.manage_roles

class ErisClient(commands.Bot):
    #events
    async def on_ready(self):
        print(f'Logged on as {self.user} ({self.user.id})!')
        print('------')
        print('Guilds:')
        for guild in self.guilds:
            print(guild.name)
            Config.EnsureGuild(guild.id)
        print('------')
        print('Loading tf wheel')
        self.tfWheel = tfWheel.TfWheel(self)
        print(f'TF wheel loaded with {len(self.tfWheel.characters.characters)} characters and {len(self.tfWheel.allTags)} tags')
        print('------')
        print('Initing bully checker')
        self.bullyChecker = bullyChecker.BullyChecker(self)
        print('------')
        try:
            self.add_listener(self.on_message_edit)
            self.add_listener(self.on_guild_join)
            self.add_listener(self.on_member_update)

            self.tree.add_command(app_commands.Command(name="tf",description="TF into a random character with optional character tags. Exclude tags with '!'",callback=self.tf_command))
            self.tree.add_command(app_commands.Command(name="default_tf_tags",description="See your current default tf tags",callback=self.default_tf_tags))
            self.tree.add_command(app_commands.Command(name="add_default_tf_tag",description="Add a default tf tag",callback=self.add_default_tf_tag))
            self.tree.add_command(app_commands.Command(name="remove_default_tf_tag",description="Remove a default tf tag",callback=self.remove_default_tf_tag))
            self.tree.add_command(app_commands.Command(name="update_bully_settings",description="Updates the bully settings",callback=self.update_bully_settings))
            self.tree.add_command(app_commands.Command(name="set_perma_bully",description="Sets user to be permanently in the bully role",callback=self.set_perma_bully))

            synced = await self.tree.sync()
            print(f"Synced {len(synced)} commands!")
        except Exception as e:
            print(f"Command syncing failed! ({e})")
            pass

    async def on_message(self, message):
        print(f'Message from {message.author}({message.guild.name if message.guild is not None else "dm"}): {message.content}')
        await super(ErisClient, self).on_message(message)
        if message.author == self.user:
            return
        if message.guild is None:
            # private message
            return

        await self.bullyChecker.BullyCheckMessage(message)

    async def on_message_edit(self, messageBefore, messageAfter):
        print(f'Message edit from {messageAfter.author}({messageAfter.guild.name}): {messageAfter.content}')
        if messageAfter.author == self.user:
            return
        if messageAfter.guild is None:
            # private message
            return

        await self.bullyChecker.BullyCheckMessage(messageAfter)

    async def on_member_update(self, memberBefore, memberAfter):
        self.tfWheel.on_member_update(memberBefore, memberAfter)
        self.bullyChecker.on_member_update(memberBefore, memberAfter)

    async def on_guild_join(self, guild):
        Config.EnsureGuild(guild.id)

    #helper functions
    async def tag_autocomplete(self, interaction :discord.Interaction, current :str):
        prefix = ""
        if current.startswith('!'):
            prefix = "!"
            current = current[1:]
        return [app_commands.Choice(name=f"{prefix}{choice}", value=f"{prefix}{choice}") for choice in self.tfWheel.allTags if choice.startswith(current.lower())]

    #commands
    @app_commands.autocomplete(tag1=tag_autocomplete, tag2=tag_autocomplete, tag3=tag_autocomplete)
    async def tf_command(self, interaction :discord.Interaction, tag1 :str = "", tag2 :str = "", tag3 :str = ""):
        print(f"TF command. Tag1\"{tag1}\" Tag2\"{tag2}\" Tag3\"{tag3}\"")

        characterName = self.tfWheel.TriggerTfForUser(interaction.guild, interaction.user, tag1, tag2, tag3)
        if characterName is None:
            await interaction.response.send_message("No characters matching specified tags", ephemeral=True)

        newNickname = self.tfWheel.GetUserCharacterNickname(interaction.user.display_name, characterName)
        try:
            with self.tfWheel.MemberUpdateLock(interaction.user.id):
                await interaction.user.edit(reason="nick", nick=newNickname)

            await interaction.response.send_message("Spinning the tf wheel...")
            await asyncio.sleep(1)
            await interaction.edit_original_response(content=f"Spinning the tf wheel...\nHave fun being {characterName} for a day!")
        except discord.errors.Forbidden:
            print("Can't change user {0} nickname".format(interaction.user.name))
            await interaction.response.send_message(f"No permissions to change your nickname to \"{newNickname}\"", ephemeral=True)
            pass


    async def default_tf_tags(self, interaction :discord.Interaction):
        includeTags, excludeTags = self.tfWheel.GetUserDefaultTags(interaction.user.id)
        if includeTags and excludeTags:
            await interaction.response.send_message(f"Your default tags are ({includeTags}) Excluding({excludeTags})", ephemeral=True)
        elif includeTags:
            await interaction.response.send_message(f"Your default tags are ({includeTags})", ephemeral=True)
        elif excludeTags:
            await interaction.response.send_message(f"Your default tags are excluding({excludeTags})", ephemeral=True)
        else:
            await interaction.response.send_message("Your have no default tags set", ephemeral=True)

    @app_commands.autocomplete(tag=tag_autocomplete)
    async def add_default_tf_tag(self, interaction :discord.Interaction, tag :str):
        self.tfWheel.AddUserDefaultTag(interaction.user.id, tag)
        await self.default_tf_tags(interaction)

    @app_commands.autocomplete(tag=tag_autocomplete)
    async def remove_default_tf_tag(self, interaction :discord.Interaction, tag :str):
        self.tfWheel.RemoveUserDefaultTag(interaction.user.id, tag)
        await self.default_tf_tags(interaction)

    @app_commands.check(is_guild_admin)
    async def update_bully_settings(self, interaction :discord.Interaction, bully_role :discord.Role, bully_duration_days :float):
        print("update_bully_settings")
        self.bullyChecker.UpdateGuildBullySettings(interaction.guild.id, bully_role.id, bully_duration_days)
        await interaction.response.send_message("Settings updated", ephemeral=True)

    @app_commands.check(is_guild_admin)
    async def set_perma_bully(self, interaction :discord.Interaction, user :discord.Member):
        print("set_perma_bully")
        await self.bullyChecker.SetPermanentBully(user)
        await interaction.response.send_message("Perma bully set", ephemeral=True)


Config.LoadConfig()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

client = ErisClient(intents=intents, command_prefix='!')
client.run(Config.config.token)
