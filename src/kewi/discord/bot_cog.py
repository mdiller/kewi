import disnake
from disnake.ext import commands
import kewi
from disnake.ext import commands
import typing
from .custom_cog import get_custom_cogs

class KewiCog(commands.Cog):
	pass


def get_cogs(bot: commands.InteractionBot) -> typing.List[commands.Cog]:
	cogs = get_custom_cogs(bot)
	cogs.append(KewiCog(bot))
	return cogs