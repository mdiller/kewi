from __future__ import annotations
import asyncio
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
import typing
from collections import OrderedDict
import tiktoken
from ..globals._generated_globals import Globals

from openai import OpenAI
from openai.types.chat import ChatCompletion


# better async task runner
async def run_async(func: callable) -> asyncio.Task:
	loop = asyncio.get_event_loop()
	return await loop.run_in_executor(ThreadPoolExecutor(), func)

class ConversatorRole(Enum):
	SYSTEM = ("system")
	USER = ("user")
	ASSISTANT = ("assistant")
	def __init__(self, data_name: str):
		self.data_name = data_name

class ConversatorMessage:
	def __init__(self, text: str, role: ConversatorRole, options: typing.List[str] = None):
		self.text = text
		self.role = role
		if options is None:
			options = [ self.text ]
		self.options = options
	
	def toJson(self):
		return {
			"role": self.role.data_name,
			"content": self.text
		}
	
	def toMarkdown(self):
		if len(self.options) > 1:
			text = ""
			for i, opt in enumerate(self.options):
				text += f"#### OPTION {i}:\n{opt}\n\n"
		else:
			text = self.text

		return f"> {self.role.data_name.upper()}\n\n{text}\n"

# TODO: add good support for serializing this and for having model as an arg for this
# arguments for the generation of new content
class ConvGenArgs():
	def __init__(self, step_name: str = None, response_count: int = 1, output_limit: int = None):
		self.step_name = step_name
		self.response_count = response_count
		self.output_limit = output_limit

class Conversator:
	def __init__(self):
		self.messages: typing.List[ConversatorMessage] = []
		self.token_counts = []
		self.tokens_total = 0
		self.openai_client = OpenAI(api_key=Globals.OpenAI.KEY)

	def _input_message(self, role: ConversatorRole, message: str):
		self.messages.append(ConversatorMessage(message, role))

	def input_system(self, message):
		self._input_message(ConversatorRole.SYSTEM, message)

	def input_user(self, message):
		self._input_message(ConversatorRole.USER, message)

	def input_self(self, message):
		self._input_message(ConversatorRole.ASSISTANT, message)
	
	def _get_response(self, args: ConvGenArgs):
			return self.openai_client.chat.completions.create(
				model="gpt-4o-mini",
				messages=list(map(lambda m: m.toJson(), self.messages)),
				n=args.response_count,
				max_tokens=args.output_limit,
				timeout=30)
	
	async def get_response(self, args: ConvGenArgs = None) -> str:
		messages = await self.get_responses(args)
		return messages[0]

	async def get_responses(self, args: ConvGenArgs = None) -> typing.List[str]:
		if args is None:
			args = ConvGenArgs()
		response: ChatCompletion

		response = await run_async(lambda: self._get_response(args))
		messages = list(map(lambda c: c.message.content, response.choices))
		
		self_message = ConversatorMessage(messages[0], ConversatorRole.ASSISTANT, messages)
		self.messages.append(self_message)

		return messages
	
	def to_markdown(self):
		return "\n".join(map(lambda m: m.toMarkdown(), self.messages))


# 1 micro cent is 0.000001 cents. 
# chatgpt 3.5 input is $0.001 per 1k tokens, or 1 microcent per token
# output is 2 microcents per token
