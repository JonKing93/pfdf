from pfdf._utils.buffers import buffers_to_base
from pfdf.projection import BoundingBox


class TestBuffersToBase:
    def test(_):
        obj = BoundingBox(0, 0, 0, 0, 4326)
        edges = ["left", "bottom", "right", "top"]
        b = 111194.92664455874
        buffers = {name: b for name in edges}
        output = buffers_to_base(obj, buffers, "meters")
        assert output == {name: 1 for name in edges}
