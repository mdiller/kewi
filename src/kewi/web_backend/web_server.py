from aiohttp import web
from aiohttp.web_request import Request
from kewi.context import KewiContextWebJson

from kewi.core.runner import Runner

# root path: localhost:8080/kewi/

class KewiWebBackend():
	def __init__(self):
		self.runner = Runner()
	
	async def handle_request(self, request: Request):
		endpoint = request.match_info.get("endpoint")
		target = request.match_info.get("target")
		if endpoint == "list":
			return await self.handle_list(request)
		elif endpoint == "info":
			return await self.handle_info(request, target)
		elif endpoint == "run":
			return await self.handle_run(request, target)
		else:
			return web.Response(text=f"'{endpoint}' is not a valid endpoint!", status=400)
	
	async def handle_list(self, request: Request):
		scripts = self.runner.list_scripts()
		results = []
		for scriptinfo in scripts:
			results.append(scriptinfo.name)
		return web.json_response(results)
	
	async def handle_info(self, request: Request, scriptname: str):
		script_info = self.runner.get_script(scriptname)
		if script_info is None:
			return web.Response(text=f"'{scriptname}' is not a script name!", status=400)
		args = self.runner.query_script_args(script_info)
		result = {
			"name": script_info.name,
			"args": []
		}
		if args:
			for arg in args:
				result["args"].append(arg.to_json())
		return web.json_response(result)
	
	async def handle_run(self, request: Request, scriptname: str):
		script_info = self.runner.get_script(scriptname)
		if script_info is None:
			return web.Response(text=f"'{scriptname}' is not a script name!", status=400)

		ctx = KewiContextWebJson(request)
		# TODO: wrap this with proper error handling to be handled correctly
		try:
			self.runner.run_script(script_info, ctx)
		except Exception as e:
			ctx.handle_error(e)
		
		return ctx.to_web_response()
