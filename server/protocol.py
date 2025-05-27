import json
from enum import Enum

from server.session import Session


class RequestBuilder:
    def __init__(self, *args):
        """
        Format :
            [<type>, <key>, <value>, <key>, <value>, ...]
        """
        data = {}
        self.request = {"type": args[0][0], "data": data}
        former = ""
        for arg in args[0][1:]:
            if former == "":
                former = arg
            else:
                data[former] = arg
                former = ""


    def build(self) -> str:
        return json.dumps(self.request)


class Request:
    def __init__(self, *args):
        self.request_builder = RequestBuilder(args)
        self.request = self.request_builder.build()

    @staticmethod
    async def recv(session):
        answer = await session.recv()
        session.clear_buffer()
        answer_json, type_ = AnswerParser.parse(answer)
        if type_ == AnswerType.ERROR:
            print(answer_json["data"]["content"], end="")
            session.clear_buffer()

        elif type_ == AnswerType.RESULT:
            print(answer_json["data"]["output"], end="")
            session.clear_buffer()

        elif type_ == AnswerType.FILE:
            print(f"File {answer_json['data']['file_name']} received")
            with open(answer_json["data"]["file_name"], "wb") as f:
                f.write(answer_json["data"]["content"])
            session.clear_buffer()
        return answer_json, type_

    async def send(self, session: Session) -> tuple:
        await session.send(self.request)
        return await self.recv(session)


class Exec(Request):
    def __init__(self, command: str):
        super().__init__("exec", "command",command)


class Upload(Request):
    def __init__(self, file: str, content: str):
        super().__init__("upload", "file", file, "content", content)


class Download(Request):
    def __init__(self, url: str):
        super().__init__("download", "url", url)


class RunModule(Request):
    def __init__(self, module: str):
        super().__init__("run_module", "module", module)


class Kill(Request):
    def __init__(self):
        super().__init__("kill")


class Info(Request):
    def __init__(self):
        super().__init__("info")

class AnswerType(Enum):
    RESULT = 1
    FILE = 2
    ERROR = 3
    KILL = 4


class AnswerParser:
    @staticmethod
    def parse(request: str) -> tuple[dict, AnswerType]:
        answer = json.loads(request)
        type_str = answer["type"]
        type_int = None
        if type_str == "result":
            type_int = AnswerType.RESULT

        elif type_str == "file":
            type_int = AnswerType.FILE

        elif type_str == "error":
            type_int = AnswerType.ERROR

        elif type_str == "kill":
            type_int = AnswerType.KILL

        return answer, type_int





