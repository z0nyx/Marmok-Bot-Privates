import disnake
from disnake.ext import commands
from disnake import ui

from core.enums import *

class PrivateRoomButtons(ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
    
    @ui.button(style=disnake.ButtonStyle.gray, custom_id="change_name", emoji="<:pen:0>")
    async def change_name(self, button: ui.Button, inter: disnake.MessageInteraction):
        if not await self.cog.is_private_room_owner(inter):
            return
        
        await inter.response.send_modal(
            title="Изменение названия комнаты",
            custom_id="change_name_modal",
            components=[
                ui.TextInput(
                    label="Новое название",
                    placeholder="Введите новое название комнаты",
                    custom_id="new_name",
                    style=disnake.TextInputStyle.short,
                    max_length=100
                )
            ]
        )

    @ui.button(style=disnake.ButtonStyle.gray, custom_id="set_limit", emoji="<:user:0>")
    async def set_limit(self, button: ui.Button, inter: disnake.MessageInteraction):
        if not await self.cog.is_private_room_owner(inter):
            return
        
        await inter.response.send_modal(
            title="Установка лимита пользователей",
            custom_id="set_limit_modal",
            components=[
                ui.TextInput(
                    label="Лимит пользователей (0-99)",
                    placeholder="Введите число от 0 до 99",
                    custom_id="user_limit",
                    style=disnake.TextInputStyle.short,
                    max_length=2
                )
            ]
        )
    @ui.button(style=disnake.ButtonStyle.gray, custom_id="toggle_access", emoji="<:lock:0>")
    async def toggle_access(self, button: ui.Button, inter: disnake.MessageInteraction):
        if not await self.cog.is_private_room_owner(inter):
            return
        
        channel = inter.user.voice.channel
        current_perms = channel.overwrites_for(inter.guild.default_role)
        

        if current_perms.connect is None or current_perms.connect:
            new_perms = disnake.PermissionOverwrite(connect=False)
            message = f'{inter.author.mention}, Вы **закрыли** вашу комнату для всех!'
        else:
            new_perms = disnake.PermissionOverwrite(connect=None)  # None сбрасывает переопределение
            message = f'{inter.author.mention}, Вы **открыли** вашу комнату для всех!'
        
        await channel.set_permissions(inter.guild.default_role, overwrite=new_perms)
        
        emb = disnake.Embed(
            title='Закрыть/Открыть доступ в комнату',
            description=message,
            colour=0x2f3136
        )
        emb.set_thumbnail(url=inter.author.display_avatar.url)
        await inter.response.send_message(embed=emb, ephemeral=True)

    @ui.button(style=disnake.ButtonStyle.gray, custom_id="manage_access", emoji="<:access:1353438463281725553>")
    async def manage_access(self, button: ui.Button, inter: disnake.MessageInteraction):
        if not await self.cog.is_private_room_owner(inter):  # 
            return
        
        emb = disnake.Embed(
            title='Выдать/Забрать доступ в комнате',
            description=f'{inter.author.mention}, **выберите** пользователя, которому хотите **выдать/забрать** право доступ к комнате!',
            colour=0x2f3136
            )
        emb.set_thumbnail(url=inter.author.display_avatar.url)
        components= disnake.ui.UserSelect(
                    placeholder="🔘Выберите пользователя",
                    custom_id="select_user_access"
                )

        await inter.send(embed=emb, components=[components], ephemeral=True)

    @ui.button(style=disnake.ButtonStyle.gray, custom_id="kick_user", emoji="<:kick:0>")
    async def kick_user(self, button: ui.Button, inter: disnake.MessageInteraction):
        if not await self.cog.is_private_room_owner(inter): 
            return
        
        emb = disnake.Embed(
                title='Выгнать пользователя из комнаты',
                description=f'{inter.author.mention}, **выберите** пользователя, которого хотите **выгнать** из комнаты!',
                colour=0x2f3136
        )
        emb.set_thumbnail(url=inter.author.display_avatar.url)
        components= disnake.ui.UserSelect(
                    custom_id="select_user_kick",
                    placeholder="🔘Выберите пользователя",
                    min_values=1,
                    max_values=1
                )
        await inter.send(embed=emb, components=[components], ephemeral=True)

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if not inter.user.voice or not inter.user.voice.channel:
            await inter.response.send_message(
                "Вы должны быть в голосовом канале!", 
                ephemeral=True
            )
            return False
            
        channel = inter.user.voice.channel
        if channel.id not in self.cog.privates_info:
            await inter.response.send_message(
                "Это не приватная комната!", 
                ephemeral=True
            )
            return False
            
        if self.cog.privates_info[channel.id]['owner_id'] != inter.user.id:
            await inter.response.send_message(
                "Вы не владелец этой комнаты!", 
                ephemeral=True
            )
            return False
            
        return True

class PrivateRooms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.privates_info = {} 
        self.persistent_views_added = False
        self.creation_channel_id = 0
        self.category_id = 0
        self.control_message_id = None

    async def is_private_room_owner(self, inter: disnake.Interaction):
        if not inter.user.voice or not inter.user.voice.channel:
            await inter.response.send_message(
                "Вы должны быть в голосовом канале!",
                ephemeral=True
            )
            return False
        
        channel = inter.user.voice.channel
        if channel.id not in self.privates_info:
            await inter.response.send_message(
                "Это не приватная комната!",
                ephemeral=True
            )
            return False
            
        if self.privates_info[channel.id]['owner_id'] != inter.user.id:
            await inter.response.send_message(
                "Вы не владелец этой комнаты!",
                ephemeral=True
            )
            return False
        
        return True

    async def send_control_panel(self, channel):
        """Отправляет панель управления приватными комнатами"""
        embed = disnake.Embed(
            title="Управление приватной комнатой",
            description=(
                "> Жми следующие кнопки, чтобы настроить свою комнату\n"
                " Использовать их можно только когда у тебя есть приватный канал\n\n"
                f"{self.bot.get_emoji(0)} **—** `Изменить название комнаты`\n"
                f"{self.bot.get_emoji(0)} **—** `Установить лимит пользователей`\n"
                f"{self.bot.get_emoji(0)} **—** `Закрыть/Открыть доступ в комнату`\n"
                f"{self.bot.get_emoji(0)} **—** `Забрать/Выдать доступ к комнате пользователю`\n"
                f"{self.bot.get_emoji(0)} **—** `Выгнать пользователя из комнаты`\n"
            ),
            colour=0x2f3136
        )
        message = await channel.send(embed=embed, view=PrivateRoomButtons(self))
        self.control_message_id = message.id
        return message
    @commands.slash_command(name="privates")
    @commands.has_any_role(0)
    async def private_control(self, inter: disnake.ApplicationCommandInteraction):
        """Отправляет панель управления приватными комнатами"""
        if not inter.guild:
            await inter.response.send_message("Эта команда доступна только на сервере!", ephemeral=True)
            return
            
        await inter.response.defer(ephemeral=True)
        try:
            await self.send_control_panel(inter.channel)
            await inter.followup.send("Панель управления приватками отправлена!", ephemeral=True)
        except Exception as e:
            print(f"Ошибка при отправке панели управления: {e}")
            await inter.followup.send("Произошла ошибка при создании панели управления", ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Создание приватки при входе в специальный канал
        if after.channel and after.channel.id == self.creation_channel_id:
            guild = after.channel.guild
            category = guild.get_channel(self.category_id)
            
            if not category:
                return
            
            new_channel = await guild.create_voice_channel(
                name=f"Голосовой канал {member.display_name}",
                category=category,
                reason=f"Голосовой канал {member}"
            )
            
            # Сохраняем информацию о комнате
            self.privates_info[new_channel.id] = {
                'owner_id': member.id,
                'original_name': f"Приватка {member.display_name}"
            }
            
            await new_channel.set_permissions(member, connect=True, manage_channels=True)
            await new_channel.set_permissions(guild.default_role, connect=True)
            await member.move_to(new_channel)

        if before.channel and before.channel.id in self.privates_info:
            if len(before.channel.members) == 0:
                self.privates_info.pop(before.channel.id)
                await before.channel.delete(reason="Приватная комната пуста")

    @commands.Cog.listener()
    async def on_modal_submit(self, inter: disnake.ModalInteraction):
        if inter.custom_id == "change_name_modal":
            new_name = inter.text_values["new_name"]
            channel = inter.user.voice.channel

            await channel.edit(name=new_name)
            if channel.id in self.privates_info:
                self.privates_info[channel.id]['original_name'] = new_name
            
            emb = disnake.Embed(
            title='Установить название приватной комнаты',
            description=f'{inter.author.mention}, Вы **установили** новое имя для своей **приватной комнаты** {channel.mention}',
            colour=0x2f3136
            )
            emb.set_thumbnail(url=inter.author.display_avatar.url)
            await inter.send(embed=emb, ephemeral = True)
            
        elif inter.custom_id == "set_limit_modal":
            try:
                limit = int(inter.text_values["user_limit"])
                if limit < 0 or limit > 99:
                    raise ValueError
                
                channel = inter.user.voice.channel
                await channel.edit(user_limit=limit)
                emb = disnake.Embed(
                title='Установить лимит пользователей',
                description=f'{inter.author.mention}, Лимит пользователей в вашей комнате установлен на **{limit}**',
                colour=0x2f3136
            )
                await inter.send(embed=emb, ephemeral = True)
            except ValueError:
                emb = disnake.Embed(
                    title='Установить лимит пользователей',
                    description=f'{inter.author.mention}, Вы указали **не** корректное значение. Укажите от 0 до 99!',
                    colour=0x2f3136
                )
                await inter.send(embed=emb, ephemeral = True)
                return

    @commands.Cog.listener()
    async def on_dropdown(self, inter: disnake.MessageInteraction):
        try:
            if not inter.guild:
                return

            if inter.data.custom_id == "select_user_access":
                if not await self.is_private_room_owner(inter):
                    return
                
                selected_user_id = int(inter.values[0])
                selected_member = inter.guild.get_member(selected_user_id)
                
                if not selected_member:
                    await inter.response.send_message("❌ Пользователь не найден на сервере", ephemeral=True)
                    return
                
                if selected_member.id == inter.author.id:
                    emb = disnake.Embed(
                        title='Ошибка управления доступом',
                        description=f'{inter.author.mention}, Вы не можете изменять свои собственные права доступа!',
                        colour=0x2f3136
                    )
                    emb.set_thumbnail(url=inter.author.display_avatar.url)
                    return await inter.response.send_message(embed=emb, ephemeral=True)
                
                channel = inter.user.voice.channel
                current_perms = channel.overwrites_for(selected_member)
                
                if current_perms.connect is None or not current_perms.connect:
                    current_perms.connect = True
                    emb = disnake.Embed(
                        title='Управление доступом',
                        description=f'{inter.author.mention}, Вы **дали** доступ в вашу комнату пользователю {selected_member.mention}!',
                        colour=0x2f3136
                    )
                    emb.set_thumbnail(url=inter.author.display_avatar.url)
                else:
                    current_perms.connect = False
                    emb = disnake.Embed(
                        title='Управление доступом',
                        description=f'{inter.author.mention}, Вы **забрали** доступ в вашу комнату у пользователя {selected_member.mention}!',
                        colour=0x2f3136
                    )
                    emb.set_thumbnail(url=inter.author.display_avatar.url)

                await channel.set_permissions(selected_member, overwrite=current_perms)
                await inter.response.send_message(embed=emb, ephemeral=True)
                
            elif inter.data.custom_id == "select_user_kick":
                if not await self.is_private_room_owner(inter):
                    return
                
                selected_user_id = int(inter.values[0])
                selected_member = inter.guild.get_member(selected_user_id)
                
                if not selected_member:
                    await inter.response.send_message("❌ Пользователь не найден на сервере", ephemeral=True)
                    return
                
                # Проверка, что пользователь не пытается кикнуть самого себя
                if selected_member.id == inter.author.id:
                    emb = disnake.Embed(
                        title='Ошибка кика',
                        description=f'{inter.author.mention}, Вы не можете выгнать самого себя из комнаты!',
                        colour=0x2f3136
                    )
                    emb.set_thumbnail(url=inter.author.display_avatar.url)
                    return await inter.response.send_message(embed=emb, ephemeral=True)
                
                channel = inter.user.voice.channel
                
                if selected_member.voice and selected_member.voice.channel and selected_member.voice.channel.id == channel.id:
                    await selected_member.move_to(None)
                    emb = disnake.Embed(
                        title='Выгнать пользователя из комнаты',
                        description=f'{inter.author.mention}, Вы успешно **выгнали** пользователя {selected_member.mention} из вашей комнаты!',
                        colour=0x2f3136
                    )
                    emb.set_thumbnail(url=inter.author.display_avatar.url)
                    await inter.response.send_message(embed=emb, ephemeral=True)
                else:
                    emb = disnake.Embed(
                        title='Выгнать пользователя из комнаты',
                        description=f'{inter.author.mention}, этот пользователь {selected_member.mention} **не находится** в вашем голосовом канале!',
                        colour=0x2f3136
                    )
                    emb.set_thumbnail(url=inter.author.display_avatar.url)
                    await inter.response.send_message(embed=emb, ephemeral=True)
                    
        except Exception as e:
            print(f"Ошибка в on_dropdown: {str(e)}")
            await inter.response.send_message(
                "⚠️ Произошла ошибка при обработке вашего запроса", 
                ephemeral=True
            )

def setup(bot):
    bot.add_cog(PrivateRooms(bot))