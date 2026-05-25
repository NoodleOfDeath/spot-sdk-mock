"""Mission control helpers — small CLI wrapper around bosdyn-mission gRPC."""
from __future__ import annotations

import json
import os
import sys

import grpc
from bosdyn.api.mission import (
    mission_pb2,
    mission_service_pb2_grpc,
)


def _channel():
    host = os.environ.get("ROBOT_MOCK_HOST", "robot_mock")
    port = int(os.environ.get("ROBOT_MOCK_PORT", "44444"))
    return grpc.insecure_channel(f"{host}:{port}")


def play() -> dict:
    stub = mission_service_pb2_grpc.MissionServiceStub(_channel())
    resp = stub.PlayMission(mission_pb2.PlayMissionRequest(), timeout=4.0)
    return {"status": mission_pb2.PlayMissionResponse.Status.Name(resp.status)}


def pause() -> dict:
    stub = mission_service_pb2_grpc.MissionServiceStub(_channel())
    resp = stub.PauseMission(mission_pb2.PauseMissionRequest(), timeout=4.0)
    return {"status": mission_pb2.PauseMissionResponse.Status.Name(resp.status)}


def restart() -> dict:
    stub = mission_service_pb2_grpc.MissionServiceStub(_channel())
    resp = stub.RestartMission(
        mission_pb2.RestartMissionRequest(), timeout=4.0
    )
    return {"status": mission_pb2.RestartMissionResponse.Status.Name(resp.status)}


def answer(question_id: int, code: int) -> dict:
    stub = mission_service_pb2_grpc.MissionServiceStub(_channel())
    req = mission_pb2.AnswerQuestionRequest(question_id=question_id, code=code)
    resp = stub.AnswerQuestion(req, timeout=4.0)
    return {
        "status": mission_pb2.AnswerQuestionResponse.Status.Name(resp.status)
    }


def question() -> dict:
    stub = mission_service_pb2_grpc.MissionServiceStub(_channel())
    resp = stub.GetState(mission_pb2.GetStateRequest(), timeout=4.0)
    state = resp.state
    qs = []
    for q in state.questions:
        qs.append(
            {
                "id": q.id,
                "source": q.source,
                "text": q.text,
                "options": [
                    {"answer_code": o.answer_code, "text": o.text}
                    for o in q.options
                ],
            }
        )
    return {
        "mission_state": (
            "PLAYING"
            if state.status == mission_pb2.State.STATUS_RUNNING
            else "PAUSED"
            if state.status == mission_pb2.State.STATUS_PAUSED
            else "IDLE"
        ),
        "questions": qs,
    }


COMMANDS = {
    "play": play,
    "pause": pause,
    "restart": restart,
    "question": question,
}


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: mission.py <command> [args]", file=sys.stderr)
        return 1
    cmd = sys.argv[1]
    if cmd == "answer":
        if len(sys.argv) != 4:
            print("usage: mission.py answer <question_id> <code>", file=sys.stderr)
            return 1
        out = answer(int(sys.argv[2]), int(sys.argv[3]))
    elif cmd in COMMANDS:
        out = COMMANDS[cmd]()
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        return 1
    json.dump(out, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
