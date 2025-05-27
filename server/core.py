import asyncio

from server.manager import Manager
from server.session import Session
from utils.logger import log


class Core:
	def __init__(self):
		self.server = None
		self.addr = None
		self.session_manager = Manager()
		self.recv_available = asyncio.Event()

	async def start_server(self) -> None:
		self.server = await asyncio.start_server(self.handle_client, '0.0.0.0', 12008)
		self.addr = self.server.sockets[0].getsockname()
		print(f"[✓] Serveur lancé sur {self.addr}")
		log("Serveur lancé", 1)

		self.recv_available.set()

		async with self.server:
			await self.server.serve_forever()


	async def handle_client(self, reader, writer) -> None:
		ip = writer.get_extra_info("peername")[0]
		port = writer.get_extra_info('peername')[1]
		log(f"Nouveau client {ip}:{port}", 1)

		session = Session(ip, port, reader, writer)
		log(f"Nouvelle session id:{session.session_id}", 0)
		await self.session_manager.add(session)
		await asyncio.create_task(self.session_manager.listen_sessions(session, self.recv_available))

