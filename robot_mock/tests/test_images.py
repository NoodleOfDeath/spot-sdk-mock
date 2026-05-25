"""Image service tests."""
from __future__ import annotations

from bosdyn.api import image_pb2
from bosdyn.client.image import ImageClient


def test_list_sources(make_client, vlog):
    vlog("TEST: ImageService — ListImageSources advertises all 5 fisheye cameras at 640x480")
    client = make_client(ImageClient)
    vlog("ACTION: calling ImageClient.list_image_sources()")
    sources = client.list_image_sources()
    names = {s.name for s in sources}
    expected = {
        "frontleft_fisheye",
        "frontright_fisheye",
        "left_fisheye",
        "right_fisheye",
        "back_fisheye",
    }
    vlog(f"ASSERT: source names include all 5 expected fisheyes ({sorted(expected)})")
    assert expected.issubset(names)
    for src in sources:
        if src.name in expected:
            vlog(f"ASSERT: source {src.name!r} has cols == 640")
            assert src.cols == 640
            vlog(f"ASSERT: source {src.name!r} has rows == 480")
            assert src.rows == 480
    vlog("PASS: ListImageSources advertised all 5 fisheye cameras at 640x480")


def test_get_image_returns_jpeg(make_client, vlog):
    vlog("TEST: ImageService — GetImage returns a valid JPEG for frontleft_fisheye")
    client = make_client(ImageClient)
    vlog("ACTION: calling get_image_from_sources(['frontleft_fisheye'])")
    responses = client.get_image_from_sources(["frontleft_fisheye"])
    vlog("ASSERT: len(responses) == 1 (one response per requested source)")
    assert len(responses) == 1
    resp = responses[0]
    vlog("ASSERT: resp.status == ImageResponse.STATUS_OK")
    assert resp.status == image_pb2.ImageResponse.STATUS_OK
    img = resp.shot.image
    vlog("ASSERT: img.format == Image.FORMAT_JPEG")
    assert img.format == image_pb2.Image.FORMAT_JPEG
    vlog("ASSERT: img.data starts with the JPEG SOI marker (FF D8)")
    assert img.data[:2] == b"\xff\xd8"
    vlog("ASSERT: img.data ends with the JPEG EOI marker (FF D9)")
    assert img.data[-2:] == b"\xff\xd9"
    vlog("PASS: GetImage returned a well-formed JPEG payload")


def test_get_image_all_sources(make_client, vlog):
    vlog("TEST: ImageService — GetImage succeeds for every advertised camera")
    client = make_client(ImageClient)
    sources = [
        "frontleft_fisheye",
        "frontright_fisheye",
        "left_fisheye",
        "right_fisheye",
        "back_fisheye",
    ]
    vlog(f"ACTION: calling get_image_from_sources({sources!r})")
    responses = client.get_image_from_sources(sources)
    vlog("ASSERT: len(responses) == 5 (one per requested source)")
    assert len(responses) == 5
    for r in responses:
        vlog(
            f"ASSERT: response for {r.shot.frame_name_image_sensor!r} has "
            "status == STATUS_OK"
        )
        assert r.status == image_pb2.ImageResponse.STATUS_OK
    vlog("PASS: GetImage returned STATUS_OK for all 5 fisheye cameras")
