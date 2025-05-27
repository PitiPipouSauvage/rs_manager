import asyncio

from server.core import Core

async def main():
    server_core = Core()
    await asyncio.gather(server_core.start_server(), server_core.session_manager.start())

if __name__ == '__main__':
    asyncio.run(main())
