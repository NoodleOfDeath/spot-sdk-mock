"""MissionService implementation — synthetic mission + question/answer flow."""
from __future__ import annotations

from bosdyn.api.mission import mission_pb2, mission_service_pb2_grpc

from ..state import ROBOT_STATE
from ._header import fill_response_header


def _ensure_default_question() -> None:
    """Seed an active question if none exists. Caller must hold the state lock."""
    if ROBOT_STATE.active_question is not None:
        return
    qid = ROBOT_STATE.next_question_id
    ROBOT_STATE.next_question_id += 1
    ROBOT_STATE.active_question = {
        "id": qid,
        "source": "mock-mission",
        "text": "Continue mission to the next waypoint?",
        "options": [
            {"answer_code": 1, "text": "Yes — proceed"},
            {"answer_code": 2, "text": "No — pause"},
            {"answer_code": 3, "text": "Abort mission"},
        ],
    }


class MissionServicer(mission_service_pb2_grpc.MissionServiceServicer):
    def GetState(self, request, context):
        response = mission_pb2.GetStateResponse()
        fill_response_header(response, request)
        with ROBOT_STATE.lock:
            _ensure_default_question()
            ROBOT_STATE.mission_tick += 1
            state = response.state
            state.tick_counter = ROBOT_STATE.mission_tick
            state.mission_id = ROBOT_STATE.mission_id
            if ROBOT_STATE.mission_state == "PLAYING":
                state.status = mission_pb2.State.STATUS_RUNNING
            elif ROBOT_STATE.mission_state == "PAUSED":
                state.status = mission_pb2.State.STATUS_PAUSED
            else:
                state.status = mission_pb2.State.STATUS_NONE
            aq = ROBOT_STATE.active_question
            if aq is not None:
                q = state.questions.add()
                q.id = aq["id"]
                q.source = aq["source"]
                q.text = aq["text"]
                for opt in aq["options"]:
                    o = q.options.add()
                    o.answer_code = opt["answer_code"]
                    o.text = opt["text"]
            for ans in ROBOT_STATE.answered_questions:
                a = state.answered_questions.add()
                a.question.id = ans["id"]
                a.question.text = ans["text"]
                a.code = ans["code"]
        return response

    def AnswerQuestion(self, request, context):
        response = mission_pb2.AnswerQuestionResponse()
        fill_response_header(response, request)
        with ROBOT_STATE.lock:
            aq = ROBOT_STATE.active_question
            # Already answered: check history
            for ans in ROBOT_STATE.answered_questions:
                if ans["id"] == request.question_id:
                    response.status = mission_pb2.AnswerQuestionResponse.STATUS_ALREADY_ANSWERED
                    return response
            if aq is None or aq["id"] != request.question_id:
                response.status = mission_pb2.AnswerQuestionResponse.STATUS_INVALID_QUESTION_ID
                return response
            valid_codes = {opt["answer_code"] for opt in aq["options"]}
            if request.code not in valid_codes:
                response.status = mission_pb2.AnswerQuestionResponse.STATUS_INVALID_CODE
                return response
            ROBOT_STATE.answered_questions.append(
                {"id": aq["id"], "text": aq["text"], "code": request.code}
            )
            ROBOT_STATE.active_question = None
            response.status = mission_pb2.AnswerQuestionResponse.STATUS_OK
        return response

    def PlayMission(self, request, context):
        response = mission_pb2.PlayMissionResponse()
        fill_response_header(response, request)
        with ROBOT_STATE.lock:
            ROBOT_STATE.mission_state = "PLAYING"
            ROBOT_STATE.mission_id += 1
            response.status = mission_pb2.PlayMissionResponse.STATUS_OK
        return response

    def PauseMission(self, request, context):
        response = mission_pb2.PauseMissionResponse()
        fill_response_header(response, request)
        with ROBOT_STATE.lock:
            ROBOT_STATE.mission_state = "PAUSED"
            response.status = mission_pb2.PauseMissionResponse.STATUS_OK
        return response

    def RestartMission(self, request, context):
        response = mission_pb2.RestartMissionResponse()
        fill_response_header(response, request)
        with ROBOT_STATE.lock:
            ROBOT_STATE.mission_state = "PLAYING"
            ROBOT_STATE.mission_id += 1
            ROBOT_STATE.mission_tick = 0
            ROBOT_STATE.answered_questions.clear()
            ROBOT_STATE.active_question = None
            response.status = mission_pb2.RestartMissionResponse.STATUS_OK
        return response

    def LoadMission(self, request, context):
        response = mission_pb2.LoadMissionResponse()
        fill_response_header(response, request)
        with ROBOT_STATE.lock:
            ROBOT_STATE.mission_state = "IDLE"
            response.status = mission_pb2.LoadMissionResponse.STATUS_OK
        return response

    def StopMission(self, request, context):
        response = mission_pb2.StopMissionResponse()
        fill_response_header(response, request)
        with ROBOT_STATE.lock:
            ROBOT_STATE.mission_state = "IDLE"
            response.status = mission_pb2.StopMissionResponse.STATUS_OK
        return response

    def GetInfo(self, request, context):
        response = mission_pb2.GetInfoResponse()
        fill_response_header(response, request)
        return response

    def GetMission(self, request, context):
        response = mission_pb2.GetMissionResponse()
        fill_response_header(response, request)
        return response
