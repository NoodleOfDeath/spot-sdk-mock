"""AuthService implementation - returns a stub JWT token."""
from __future__ import annotations

import base64
import json
import time

from bosdyn.api import auth_pb2, auth_service_pb2_grpc

from ._header import fill_response_header


def _stub_jwt(username: str) -> str:
    """Build an unsigned JWT-shaped string (header.payload.signature)."""
    def b64(d: dict) -> str:
        return base64.urlsafe_b64encode(
            json.dumps(d, separators=(",", ":")).encode()
        ).rstrip(b"=").decode()

    header = b64({"alg": "none", "typ": "JWT"})
    payload = b64({
        "sub": username or "mock-user",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "iss": "mock-spot",
    })
    signature = base64.urlsafe_b64encode(b"mock-signature").rstrip(b"=").decode()
    return f"{header}.{payload}.{signature}"


class AuthServicer(auth_service_pb2_grpc.AuthServiceServicer):
    def GetAuthToken(self, request, context):
        response = auth_pb2.GetAuthTokenResponse()
        fill_response_header(response, request)
        username = request.username or "mock-user"
        # Accept any credentials; if a token is supplied (refresh), still issue a new one.
        response.status = auth_pb2.GetAuthTokenResponse.STATUS_OK
        response.token = _stub_jwt(username)
        return response
