import asyncio

from utils.logger import log


class Session:
	session_count = 0

	def __init__(self, ip, port, reader, writer):
		Session.session_count += 1
		self.session_id = Session.session_count
		self.ip = ip
		self.port = port
		self.reader = reader
		self.writer = writer
		self.lock = asyncio.Lock()
		self.buffer = ""

	async def send(self, content) -> None:
		content += "EOM"
		self.writer.write(content.encode())
		await self.writer.drain()
		log(f"Message envoyé à {self.session_id}", 0)


	async def recv(self) -> str:
		message = b""
		while b"EOM" not in message:
			chunk = await self.reader.read(4096)
			if not chunk:
				break
			message += chunk

		message = message.replace(b"EOM", b"").strip()
		result = message.decode()
		log(f"Message reçu de {self.session_id}: {result}", 0)
		self.buffer += result
		return result

	def clear_buffer(self):
		pass

	def close(self) -> None:
		log(f"Session {self.session_id} fermée", 3)
		self.reader.close()
		self.writer.close()

	def __eq__(self, other) -> bool:
		return self.session_id == other.session_id



