"""ImageService implementation - serves a precomputed 640x480 grayscale JPEG."""
from __future__ import annotations

import base64

from bosdyn.api import image_pb2, image_service_pb2_grpc
from google.protobuf.timestamp_pb2 import Timestamp

from ._header import fill_response_header


SOURCES = [
    "frontleft_fisheye",
    "frontright_fisheye",
    "left_fisheye",
    "right_fisheye",
    "back_fisheye",
]

IMG_COLS = 640
IMG_ROWS = 480


_JPEG_B64 = (
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAoHBwgHBgoICAgLCgoLDhgQDg0NDh0VFhEYIx8lJCIf"
    "IiEmKzcvJik0KSEiMEExNDk7Pj4+JS5ESUM8SDc9Pjv/wAALCAHgAoABAREA/8QAHwAAAQUBAQEB"
    "AQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1Fh"
    "ByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZ"
    "WmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXG"
    "x8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/9oACAEBAAA/APHkSp0SpkSpkSp0SpkS"
    "p0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSv"
    "LPij8Uf7N87w94en/wBN5S7vIz/x7+qIf7/qf4eg+b7viSJU6JUyJUyJU6JUyJU6JUyJUyJU6JUy"
    "JU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJXlnxR+KP9m+d4e8"
    "PT/6byl3eRn/AI9/VEP9/wBT/D0Hzfd8SRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnR"
    "KmRK8mRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnR"
    "KmRKnRKmRKmRKnRKmRK8s+KPxR/s3zvD3h6f/TeUu7yM/wDHv6oh/v8Aqf4eg+b7viSJU6JUyJUy"
    "JU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJ"
    "U6JUyJXlnxR+KP8AZvneHvD0/wDpvKXd5Gf+Pf1RD/f9T/D0Hzfd8SRKnRKmRKmRKnRKmRKnRKmR"
    "KmRKnRKmRKnRKmRKmRKnRKmRKnRK8lRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmR"
    "KmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRK8s+KPxR/s3zvD3h6f/TeUu7yM/8AHv6oh/v+"
    "p/h6D5vu+JIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolT"
    "IlTIlTolTIlTolTIlTIlTolTIleWfFH4o/2b53h7w9P/AKbyl3eRn/j39UQ/3/U/w9B833fEkSp0"
    "SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSvJUSp0SpkSp0SpkSpkSp0SpkSp0"
    "SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSvLPij8Uf7N87w94en/"
    "ANN5S7vIz/x7+qIf7/qf4eg+b7viSJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU"
    "6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJXlnxR+KP9m+d4e8PT/6byl3eRn/j39UQ"
    "/wB/1P8AD0Hzfd8SRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRK8mRK"
    "mRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKm"
    "RK8s+KPxR/s3zvD3h6f/AE3lLu8jP/Hv6oh/v+p/h6D5vu+JIlTolTIlTIlTolTIlTolTIlTIlTo"
    "lTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIleWfFH4o/2b53"
    "h7w9P/pvKXd5Gf8Aj39UQ/3/AFP8PQfN93xJEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZE"
    "qdEqZEqdEqZEqZEqdEryVEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZE"
    "qdEqZEqdEqZEqZEqdEqZEryz4o/FH+zfO8PeHp/9N5S7vIz/AMe/qiH+/wCp/h6D5vu+JIlTolTI"
    "lTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIl"
    "TIlTolTIleWfFH4o/wBm+d4e8PT/AOm8pd3kZ/49/VEP9/1P8PQfN93xJEqdEqZEqZEqdEqZEqdE"
    "qZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEryZEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdE"
    "qZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEryz4o/FH+zfO8PeHp/9N5S7vIz/wAe/qiH"
    "+/6n+HoPm+74kiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVO"
    "iVMiVMiVOiVMiVOiVMiVMiVOiVMiV5Z8Ufij/ZvneHvD0/8ApvKXd5Gf+Pf1RD/f9T/D0Hzfd8SR"
    "KnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRK8lRKmRKnRKmR"
    "KnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRK8s+KPxR/s3zvD3h"
    "6f8A03lLu8jP/Hv6oh/v+p/h6D5vu+JIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolT"
    "IlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIleWfFH4o/2b53h7w9P/pvKXd5Gf+Pf"
    "1RD/AH/U/wAPQfN93xJEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqd"
    "EqZEqdEqZEryVEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqd"
    "EqZEryz4o/FH+zfO8PeHp/8ATeUu7yM/8e/qiH+/6n+HoPm+74kiVOiVMiVMiVOiVMiVOiVMiVMi"
    "VOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiV5Z8Ufij/Z"
    "vneHvD0/+m8pd3kZ/wCPf1RD/f8AU/w9B833fEkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkS"
    "pkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSvJkSpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkS"
    "pkSp0SpkSp0SpkSpkSp0SpkSvLPij8Uf7N87w94en/03lLu8jP8Ax7+qIf7/AKn+HoPm+74kiVOi"
    "VMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiV"
    "MiVMiVOiVMiV5Z8Ufij/AGb53h7w9P8A6byl3eRn/j39UQ/3/U/w9B833fEkSp0SpkSpkSp0SpkS"
    "p0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SvJUSp0SpkSpkSp0SpkS"
    "p0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSvLPij8Uf7N87w94en/03lLu8jP/AB7+"
    "qIf7/qf4eg+b7viSJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUy"
    "JU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJXlnxR+KP9m+d4e8PT/wCm8pd3kZ/49/VEP9/1P8PQfN93"
    "xJEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEq"
    "ZEryZEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEryz4o/FH+zfO8"
    "PeHp/wDTeUu7yM/8e/qiH+/6n+HoPm+74kiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVO"
    "iVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiV5Z8Ufij/ZvneHvD0/+m8pd3kZ/"
    "49/VEP8Af9T/AA9B833fEkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpk"
    "Sp0SpkSp0SpkSpkSp0SpkSp0SvJUSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpk"
    "Sp0SpkSvLPij8Uf7N87w94en/wBN5S7vIz/x7+qIf7/qf4eg+b7viSJU6JUyJUyJU6JUyJU6JUyJ"
    "UyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJXlnxR+K"
    "P9m+d4e8PT/6byl3eRn/AI9/VEP9/wBT/D0Hzfd8SRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRK"
    "mRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRK8lRKnRKmRKnRKmRKmRKnRKmRKnRK"
    "mRKmRKnRKmRKnRKmRKmRKnRKmRK8s+KPxR/s3zvD3h6f/TeUu7yM/wDHv6oh/v8Aqf4eg+b7viSJ"
    "U6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU"
    "6JUyJUyJU6JUyJXlnxR+KP8AZvneHvD0/wDpvKXd5Gf+Pf1RD/f9T/D0Hzfd8SRKnRKmRKmRKnRK"
    "mRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRK8mRK"
    "mRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRK8s+KPxR/s3zvD3h6f/TeUu7yM/8A"
    "Hv6oh/v+p/h6D5vu+JIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTo"
    "lTIlTolTIlTIlTolTIlTolTIlTIlTolTIleWfFH4o/2b53h7w9P/AKbyl3eRn/j39UQ/3/U/w9B8"
    "33fEkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp"
    "0SpkSp0SpkSpkSp0SvJUSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSvLPij8Uf7N"
    "87w94en/ANN5S7vIz/x7+qIf7/qf4eg+b7viSJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUy"
    "JU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJXlnxR+KP9m+d4e8PT/6byl3e"
    "Rn/j39UQ/wB/1P8AD0Hzfd8SRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmR"
    "KmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRK8mRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmR"
    "KmRKnRKmRK8s+KPxR/s3zvD3h6f/AE3lLu8jP/Hv6oh/v+p/h6D5vu+JIlTolTIlTIlTolTIlTol"
    "TIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIleWfF"
    "H4o/2b53h7w9P/pvKXd5Gf8Aj39UQ/3/AFP8PQfN93xJEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEq"
    "dEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEryz4o/FH+zfO8PeHp"
    "/wDTeUu7yM/8e/qiH+/6n+HoPm+6IlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIleWfFH4o"
    "/wBm+d4e8PT/AOm8pd3kZ/49/VEP9/1P8PQfN93xJEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEq"
    "ZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEryz4o/FH+zfO8PeHp/8A"
    "TeUu7yM/8e/qiH+/6n+HoPm+74kiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOi"
    "VMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiV5Z8Ufij/ZvneHvD0/+m8pd3kZ/wCPf1RD"
    "/f8AU/w9B833fEkSvc0Sp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSvLPij8Uf7N87w94en/03"
    "lLu8jP8Ax7+qIf7/AKn+HoPm+74kiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVO"
    "iVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiV5Z8Ufij/AGb53h7w9P8A6byl3eRn/j39"
    "UQ/3/U/w9B833fEkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0Spk"
    "Sp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSvLPij8Uf7N87w94en/wBN5S7vIz/x7+qIf7/qf4eg+b7v"
    "iSJU6JXuaJUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJXlnxR+KP9m+d4e8PT/wCm8pd3kZ/49/VE"
    "P9/1P8PQfN93xJEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEq"
    "dEqZEqZEqdEqZEqdEqZEqZEqdEqZEryz4o/FH+zfO8PeHp/9N5S7vIz/AMe/qiH+/wCp/h6D5vu+"
    "JIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolT"
    "IlTolTIlTIlTolTIleWfFH4o/wBm+d4e8PT/AOm8pd3kZ/49/VEP9/1P8PQfN93xJEqdEqZEr3NE"
    "qdEqZEqZEqdEqZEqdEqZEqZEqdEqZEryz4o/FH+zfO8PeHp/9N5S7vIz/wAe/qiH+/6n+HoPm+74"
    "kiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVM"
    "iVOiVMiVMiVOiVMiV5Z8Ufij/ZvneHvD0/8ApvKXd5Gf+Pf1RD/f9T/D0Hzfd8SRKnRKmRKmRKnR"
    "KmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRK"
    "mRK8s+KPxR/s3zvD3h6f/TeUu7yM/wDHv6oh/v8Aqf4eg+b7viSJU6JUyJUyJXuiJUyJUyJU6JUy"
    "JU6JUyJUyJU6JUyJXlnxR+KP9m+d4e8PT/6byl3eRn/j39UQ/wB/1P8AD0Hzfd8SRKnRKmRKmRKn"
    "RKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnR"
    "KmRK8s+KPxR/s3zvD3h6f/TeUu7yM/8AHv6oh/v+p/h6D5vu+JIlTolTIlTIlTolTIlTolTIlTIl"
    "TolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIleWfFH4o/2b"
    "53h7w9P/AKbyl3eRn/j39UQ/3/U/w9B833fEkSp0SpkSpkSp0Svc0SpkSp0SpkSp0SpkSpkSp0Sp"
    "kSvLPij8Uf7N87w94en/ANN5S7vIz/x7+qIf7/qf4eg+b7viSJU6JUyJUyJU6JUyJU6JUyJUyJU6"
    "JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJXlnxR+KP9m+d"
    "4e8PT/6byl3eRn/j39UQ/wB/1P8AD0Hzfd8SRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmR"
    "KnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRK8s+KPxR/s3zvD3h6f/TeUu7y"
    "M/8AHv6oh/v+p/h6D5vu+JIlTolTIlTIlTolTIle5olTolTIlTolTIlTIlTolTIleWfFH4o/2b53"
    "h7w9P/pvKXd5Gf8Aj39UQ/3/AFP8PQfN93xJEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZE"
    "qdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEryz4o/FH+zfO8PeHp/wDTeUu7"
    "yM/8e/qiH+/6n+HoPm+74kiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVM"
    "iVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiV5Z8Ufij/ZvneHvD0/+m8pd3kZ/49/VEP8Af9T/"
    "AA9B833fEkSp0SpkSpkSp0SpkSp0Svc0SpkSp0SpkSpkSp0SpkSvLPij8Uf7N87w94en/wBN5S7v"
    "Iz/x7+qIf7/qf4eg+b7viSJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUy"
    "JU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJXlnxR+KP9m+d4e8PT/6byl3eRn/AI9/VEP9/wBT"
    "/D0Hzfd8SRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmR"
    "KmRKnRKmRKnRKmRKmRKnRKmRK8s+KPxR/s3zvD3h6f8A03lLu8jP/Hv6oh/v+p/h6D5vu+JIlTol"
    "TIlTIlTolTIlTolTIle5olTolTIlTIlTolTIleWfFH4o/wBm+d4e8PT/AOm8pd3kZ/49/VEP9/1P"
    "8PQfN93xJEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZE"
    "qZEqdEqZEqdEqZEqZEqdEqZEryz4o/FH+zfO8PeHp/8ATeUu7yM/8e/qiH+/6n+HoPm+74kiVOiV"
    "MiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVM"
    "iVMiVOiVMiV5Z8Ufij/ZvneHvD0/+m8pd3kZ/wCPf1RD/f8AU/w9B833fEkSp0SpkSpkSp0SpkSp"
    "0SpkSpkSvdESpkSpkSp0SpkSvLPij8Uf7N87w94en/03lLu8jP8Ax7+qIf7/AKn+HoPm+74kiVOi"
    "VMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiV"
    "MiVMiVOiVMiV5Z8Ufij/AGb53h7w9P8A6byl3eRn/j39UQ/3/U/w9B833fEkSp0SpkSpkSp0SpkS"
    "p0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSv"
    "LPij8Uf7N87w94en/wBN5S7vIz/x7+qIf7/qf4eg+b7viSJU6JUyJUyJU6JUyJU6JUyJUyJU6JXu"
    "aJUyJU6JUyJXlnxR+KP9m+d4e8PT/wCm8pd3kZ/49/VEP9/1P8PQfN93xJEqdEqZEqZEqdEqZEqd"
    "EqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEryz"
    "4o/FH+zfO8PeHp/9N5S7vIz/AMe/qiH+/wCp/h6D5vu+JIlTolTIlTIlTolTIlTolTIlTIlTolTI"
    "lTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIleWfFH4o/wBm+d4e"
    "8PT/AOm8pd3kZ/49/VEP9/1P8PQfN93xJEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEr3NEqdEqZEry"
    "z4o/FH+zfO8PeHp/9N5S7vIz/wAe/qiH+/6n+HoPm+74kiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMi"
    "VOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiV5Z8Ufij/ZvneHvD"
    "0/8ApvKXd5Gf+Pf1RD/f9T/D0Hzfd8SRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKm"
    "RKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRK8s+KPxR/s3zvD3h6f/TeUu7yM/wDH"
    "v6oh/v8Aqf4eg+b7viSJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JXuaJUyJXlnxR+KP9m+d4e8P"
    "T/6byl3eRn/j39UQ/wB/1P8AD0Hzfd8SRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRK"
    "mRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRK8s+KPxR/s3zvD3h6f/TeUu7yM/8A"
    "Hv6oh/v+p/h6D5vu+JIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTo"
    "lTIlTolTIlTIlTolTIlTolTIlTIlTolTIleWfFH4o/2b53h7w9P/AKbyl3eRn/j39UQ/3/U/w9B8"
    "33fEkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSvc0SvLPij8Uf7N87w94en/ANN5S7vIz/x7"
    "+qIf7/qf4eg+b7viSJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JU"
    "yJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJXlnxR+KP9m+d4e8PT/6byl3eRn/j39UQ/wB/1P8AD0Hz"
    "fd8SRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKn"
    "RKmRKnRKmRKmRKnRKmRK8s+KPxR/s3zvD3h6f/TeUu7yM/8AHv6oh/v+p/h6D5vu+JIlTolTIlTI"
    "lTolTIlTolTIlTIlTolTIlTolTIlTIlbXxR+KP8AZvneHvD0/wDpvKXd5Gf+Pf1RD/f9T/D0Hzfd"
    "8SRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRK"
    "mRKnRKmRKmRKnRKmRK8s+KPxR/s3zvD3h6f/AE3lLu8jP/Hv6oh/v+p/h6D5vu+JIlTolTIlTIlT"
    "olTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTo"
    "lTIleWfFH4o/2b53h7w9P/pvKXd5Gf8Aj39UQ/3/AFP8PQfN93xJEqdEqZEqZEqdEqZEqdEqZEqZ"
    "EqdEqZEqdEqZEqZEqdEryVEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZ"
    "EqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEryz4o/FH+zfO8PeHp/9N5S7vIz/AMe/qiH+/wCp"
    "/h6D5vu+JIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTI"
    "lTIlTolTIlTolTIlTIlTolTIleWfFH4o/wBm+d4e8PT/AOm8pd3kZ/49/VEP9/1P8PQfN93xJEqd"
    "EqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEryZEqZEqZEqdEqZEqdEqZEqZEqdEqZEqd"
    "EqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEryz4o/FH+zfO8PeHp/"
    "9N5S7vIz/wAe/qiH+/6n+HoPm+74kiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiV"
    "OiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiV5Z8Ufij/ZvneHvD0/8ApvKXd5Gf+Pf1"
    "RD/f9T/D0Hzfd8SRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRK8lRKmRKnRKm"
    "RKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmR"
    "K8s+KPxR/s3zvD3h6f8A03lLu8jP/Hv6oh/v+p/h6D5vu+JIlTolTIlTIlTolTIlTolTIlTIlTol"
    "TIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIleWfFH4o/2b53h"
    "7w9P/pvKXd5Gf+Pf1RD/AH/U/wAPQfN93xJEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEq"
    "dEqZEqdEqZEryVEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEq"
    "dEqZEqdEqZEqZEqdEqZEryz4o/FH+zfO8PeHp/8ATeUu7yM/8e/qiH+/6n+HoPm+74kiVOiVMiVM"
    "iVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMi"
    "VOiVMiV5Z8Ufij/ZvneHvD0/+m8pd3kZ/wCPf1RD/f8AU/w9B833fEkSp0SpkSpkSp0SpkSp0Spk"
    "SpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSvJkSpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0Spk"
    "SpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSvLPij8Uf7N87w94en/03lLu8jP8Ax7+qIf7/"
    "AKn+HoPm+74kiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOi"
    "VMiVMiVOiVMiVOiVMiVMiVOiVMiV5Z8Ufij/AGb53h7w9P8A6byl3eRn/j39UQ/3/U/w9B833fEk"
    "Sp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SvJUSp0SpkSpkSp0Spk"
    "Sp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSvLPij8Uf7N87w94"
    "en/03lLu8jP/AB7+qIf7/qf4eg+b7viSJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JU"
    "yJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJXlnxR+KP9m+d4e8PT/wCm8pd3kZ/4"
    "9/VEP9/1P8PQfN93xJEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdE"
    "qZEryZEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdE"
    "qZEryz4o/FH+zfO8PeHp/wDTeUu7yM/8e/qiH+/6n+HoPm+74kiVOiVMiVMiVOiVMiVOiVMiVMiV"
    "OiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiV5Z8Ufij/Zv"
    "neHvD0/+m8pd3kZ/49/VEP8Af9T/AA9B833fEkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSp"
    "kSp0SpkSp0SpkSpkSp0SpkSp0SvJUSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSp"
    "kSp0SpkSp0SpkSpkSp0SpkSvLPij8Uf7N87w94en/wBN5S7vIz/x7+qIf7/qf4eg+b7viSJU6JUy"
    "JUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJ"
    "UyJU6JUyJXlnxR+KP9m+d4e8PT/6byl3eRn/AI9/VEP9/wBT/D0Hzfd8SRKnRKmRKmRKnRKmRKnR"
    "KmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRK8lRKnRKmRKnRKmRKmRKnRKmRKnR"
    "KmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRK8s+KPxR/s3zvD3h6f/TeUu7yM/wDHv6oh"
    "/v8Aqf4eg+b7viSJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJ"
    "U6JUyJUyJU6JUyJU6JUyJUyJU6JUyJXlnxR+KP8AZvneHvD0/wDpvKXd5Gf+Pf1RD/f9T/D0Hzfd"
    "8SRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRK8mR"
    "KmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRK8s+KPxR/s3zv"
    "D3h6f/TeUu7yM/8AHv6oh/v+p/h6D5vu+JIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlT"
    "olTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIleWfFH4o/2b53h7w9P/AKbyl3eR"
    "n/j39UQ/3/U/w9B833fEkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkS"
    "p0SpkSp0SpkSpkSp0SvJUSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkS"
    "p0SpkSvLPij8Uf7N87w94en/ANN5S7vIz/x7+qIf7/qf4eg+b7viSJU6JUyJUyJU6JUyJU6JUyJU"
    "yJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJXlnxR+KP"
    "9m+d4e8PT/6byl3eRn/j39UQ/wB/1P8AD0Hzfd8SRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKm"
    "RKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRK8mRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKm"
    "RKmRKnRKmRKnRKmRKmRKnRKmRK8s+KPxR/s3zvD3h6f/AE3lLu8jP/Hv6oh/v+p/h6D5vu+JIlTo"
    "lTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTol"
    "TIlTIlTolTIleWfFH4o/2b53h7w9P/pvKXd5Gf8Aj39UQ/3/AFP8PQfN93xJEqdEqZEqZEqdEqZE"
    "qdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEryVEqZEqdEqZE"
    "qdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEryz4o/FH+zfO8PeHp/9N5S7vIz/AMe/"
    "qiH+/wCp/h6D5vu+JIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTol"
    "TIlTolTIlTIlTolTIlTolTIlTIlTolTIleWfFH4o/wBm+d4e8PT/AOm8pd3kZ/49/VEP9/1P8PQf"
    "N93xJEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEq"
    "dEqZEqdEqZEryVEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEryz4o/FH+z"
    "fO8PeHp/9N5S7vIz/wAe/qiH+/6n+HoPm+74kiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVM"
    "iVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiV5Z8Ufij/ZvneHvD0/8ApvKX"
    "d5Gf+Pf1RD/f9T/D0Hzfd8SRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRK"
    "mRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRK8mRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRK"
    "mRKnRKmRK8s+KPxR/s3zvD3h6f8A03lLu8jP/Hv6oh/v+p/h6D5vu+JIlTolTIlTIlTolTIlTolT"
    "IlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIleWfFH"
    "4o/2b53h7w9P/pvKXd5Gf+Pf1RD/AH/U/wAPQfN93xJEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqd"
    "EqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEryVEqdEqZEqZEqdEqZEqd"
    "EqZEqZEqdEqZEqdEqZEqZEqdEqZEryz4o/FH+zfO8PeHp/8ATeUu7yM/8e/qiH+/6n+HoPm+74ki"
    "VOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiV"
    "OiVMiVMiVOiVMiV5Z8Ufij/ZvneHvD0/+m8pd3kZ/wCPf1RD/f8AU/w9B833fEkSp0SpkSpkSp0S"
    "pkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0Sp"
    "kSvJkSpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSvLPij8Uf7N87w94en/03lLu8jP8A"
    "x7+qIf7/AKn+HoPm+74kiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiV"
    "OiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiV5Z8Ufij/AGb53h7w9P8A6byl3eRn/j39UQ/3/U/w"
    "9B833fEkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSp"
    "kSp0SpkSp0SpkSpkSp0SpkSvLPij8Uf7N87w94en/wBN5S7vIz/x7+qIf7/qf4eg+b7oiVMiVOiV"
    "MiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiV5Z8Ufij/ZvneHvD0/8ApvKXd5Gf+Pf1RD/f9T/D0Hzf"
    "d8SRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnR"
    "KmRKnRKmRKmRKnRKmRK8s+KPxR/s3zvD3h6f/TeUu7yM/wDHv6oh/v8Aqf4eg+b7viSJU6JUyJUy"
    "JU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJ"
    "U6JUyJXlnxR+KP8AZvneHvD0/wDpvKXd5Gf+Pf1RD/f9T/D0Hzfd8SRK9zRKnRKmRKnRKmRKmRKn"
    "RKmRKnRKmRKmRKnRKmRK8s+KPxR/s3zvD3h6f/TeUu7yM/8AHv6oh/v+p/h6D5vu+JIlTolTIlTI"
    "lTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIl"
    "TolTIleWfFH4o/2b53h7w9P/AKbyl3eRn/j39UQ/3/U/w9B833fEkSp0SpkSpkSp0SpkSp0SpkSp"
    "kSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSvLPij8Uf"
    "7N87w94en/03lLu8jP8Ax7+qIf7/AKn+HoPm+74kiVOiV7miVMiVOiVMiVMiVOiVMiVOiVMiVMiV"
    "OiVMiV5Z8Ufij/ZvneHvD0/+m8pd3kZ/49/VEP8Af9T/AA9B833fEkSp0SpkSpkSp0SpkSp0SpkS"
    "pkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSvLPij8U"
    "f7N87w94en/03lLu8jP/AB7+qIf7/qf4eg+b7viSJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUy"
    "JUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJXlnxR+KP9m+d4e8PT/wCm"
    "8pd3kZ/49/VEP9/1P8PQfN93xJEqdEqZEr3NEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEryz4o/FH+"
    "zfO8PeHp/wDTeUu7yM/8e/qiH+/6n+HoPm+74kiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiV"
    "MiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiV5Z8Ufij/ZvneHvD0/+m8pd"
    "3kZ/49/VEP8Af9T/AA9B833fEkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0Sp"
    "kSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSvLPij8Uf7N87w94en/03lLu8jP/AB7+qIf7"
    "/qf4eg+b7viSJU6JUyJUyJXuiJUyJUyJU6JUyJU6JUyJUyJU6JUyJXlnxR+KP9m+d4e8PT/6byl3"
    "eRn/AI9/VEP9/wBT/D0Hzfd8SRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKm"
    "RKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRK8s+KPxR/s3zvD3h6f8A03lLu8jP/Hv6oh/v"
    "+p/h6D5vu+JIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTol"
    "TIlTIlTolTIlTolTIlTIlTolTIleWfFH4o/2b53h7w9P/pvKXd5Gf+Pf1RD/AH/U/wAPQfN93xJE"
    "qdEqZEqZEqdEr3NEqZEqdEqZEqdEqZEqZEqdEqZEryz4o/FH+zfO8PeHp/8ATeUu7yM/8e/qiH+/"
    "6n+HoPm+74kiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiVMiVMiVOiVMiVOiV"
    "MiVMiVOiVMiVOiVMiVMiVOiVMiV5Z8Ufij/ZvneHvD0/+m8pd3kZ/wCPf1RD/f8AU/w9B833fEkS"
    "p0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp"
    "0SpkSpkSp0SpkSvLPij8Uf7N87w94en/ANN5S7vIz/x7+qIf7/qf4eg+b7viSJU6JUyJUyJU6JUy"
    "JXuaJU6JUyJU6JUyJUyJU6JUyJXlnxR+KP8AZvneHvD0/wDpvKXd5Gf+Pf1RD/f9T/D0Hzfd8SRK"
    "nRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKn"
    "RKmRKmRKnRKmRK8s+KPxR/s3zvD3h6f/AE3lLu8jP/Hv6oh/v+p/h6D5vu+JIlTolTIlTIlTolTI"
    "lTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIl"
    "eWfFH4o/2b53h7w9P/pvKXd5Gf8Aj39UQ/3/AFP8PQfN93xJEqdEqZEqZEqdEqZEqdEr3NEqZEqd"
    "EqZEqZEqdEqZEryz4o/FH+zfO8PeHp/9N5S7vIz/AMe/qiH+/wCp/h6D5vu+JIlTolTIlTIlTolT"
    "IlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTI"
    "leWfFH4o/wBm+d4e8PT/AOm8pd3kZ/49/VEP9/1P8PQfN93xJEqdEqZEqZEqdEqZEqdEqZEqZEqd"
    "EqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEqdEqZEqZEqdEqZEryz4o/FH+zfO"
    "8PeHp/8ATeUu7yM/8e/qiH+/6n+HoPm+74kiVOiVMiVMiVOiVMiVOiVMiV7miVOiVMiVMiVOiVMi"
    "V5Z8Ufij/ZvneHvD0/8ApvKXd5Gf+Pf1RD/f9T/D0Hzfd8SRKnRKmRKmRKnRKmRKnRKmRKmRKnRK"
    "mRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRKnRKmRKmRKnRKmRK8s+KPxR/s3zvD"
    "3h6f/TeUu7yM/wDHv6oh/v8Aqf4eg+b7viSJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU"
    "6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJXlnxR+KP8AZvneHvD0/wDpvKXd"
    "5Gf+Pf1RD/f9T/D0Hzfd8SRKnRKmRKmRKnRKmRKnRKmRKmRK90RKmRKmRKnRKmRK8s+KPxR/s3zv"
    "D3h6f/TeUu7yM/8AHv6oh/v+p/h6D5vu+JIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlT"
    "olTIlTolTIlTIlTolTIlTolTIlTIlTolTIlTolTIlTIlTolTIleWfFH4o/2b53h7w9P/AKbyl3eR"
    "n/j39UQ/3/U/w9B833fEkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkS"
    "p0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSvLPij8Uf7N87w94en/03lLu8jP8Ax7+qIf7/AKn+"
    "HoPm+74kiVOiVMiVMiVOiVMiVOiVMiVMiVOiV7miVMiVOiVMiV5Z8Ufij/ZvneHvD0/+m8pd3kZ/"
    "49/VEP8Af9T/AA9B833fEkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSp0SpkSpk"
    "Sp0SpkSp0SpkSpkSp0SpkSp0SpkSpkSp0SpkSvLPij8Uf7N87w94en/03lLu8jP/AB7+qIf7/qf4"
    "eg+b7viSJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJUyJU6JUyJU6JUyJU"
    "yJU6JUyJU6JUyJUyJU6JUyJXlnxR+KP9m+d4e8PT/wCm8pd3kZ/49/VEP9/1P8PQfN93xJEqdEqZ"
    "EqZEqdEqZEqdEqZEqZEqdEqZEr//2Q=="
)


_CACHED_JPEG = base64.b64decode(_JPEG_B64)


def _now_ts() -> Timestamp:
    ts = Timestamp()
    ts.GetCurrentTime()
    return ts


def _make_source(name: str) -> image_pb2.ImageSource:
    src = image_pb2.ImageSource()
    src.name = name
    src.cols = IMG_COLS
    src.rows = IMG_ROWS
    src.depth_scale = 1.0
    src.image_type = image_pb2.ImageSource.IMAGE_TYPE_VISUAL
    src.pixel_formats.append(image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8)
    src.image_formats.append(image_pb2.Image.FORMAT_JPEG)
    return src


class ImageServicer(image_service_pb2_grpc.ImageServiceServicer):
    def ListImageSources(self, request, context):
        response = image_pb2.ListImageSourcesResponse()
        fill_response_header(response, request)
        for name in SOURCES:
            response.image_sources.add().CopyFrom(_make_source(name))
        return response

    def GetImage(self, request, context):
        response = image_pb2.GetImageResponse()
        fill_response_header(response, request)
        for ireq in request.image_requests:
            iresp = response.image_responses.add()
            if ireq.image_source_name not in SOURCES:
                iresp.status = image_pb2.ImageResponse.STATUS_UNKNOWN_CAMERA
                continue
            iresp.source.CopyFrom(_make_source(ireq.image_source_name))
            shot = iresp.shot
            shot.acquisition_time.CopyFrom(_now_ts())
            shot.frame_name_image_sensor = ireq.image_source_name
            shot.image.cols = IMG_COLS
            shot.image.rows = IMG_ROWS
            shot.image.format = image_pb2.Image.FORMAT_JPEG
            shot.image.pixel_format = image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8
            shot.image.data = _CACHED_JPEG
            snap = shot.transforms_snapshot
            edge = snap.child_to_parent_edge_map[ireq.image_source_name]
            edge.parent_frame_name = "body"
            edge.parent_tform_child.position.x = 0.3
            edge.parent_tform_child.position.y = 0.0
            edge.parent_tform_child.position.z = 0.05
            edge.parent_tform_child.rotation.w = 1.0
            iresp.status = image_pb2.ImageResponse.STATUS_OK
        return response
