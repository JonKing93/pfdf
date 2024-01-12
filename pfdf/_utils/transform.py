from math import nan

from affine import Affine
from rasterio.coords import BoundingBox

from pfdf._utils import validate
from pfdf.typing import shape2d


class Transform:
    "Utility class for working with raster transforms"

    @staticmethod
    def build(dx, dy, left, top) -> Affine:
        return Affine(dx, 0, left, 0, dy, top)

    def __init__(self, affine: Affine):
        if affine is not None:
            affine = validate.transform(affine)
        self.affine = affine

    def coefficient(self, k: int) -> float:
        if self.affine is None:
            return nan
        else:
            return self.affine[k]

    @property
    def dx(self) -> float:
        return self.coefficient(0)

    @property
    def dy(self) -> float:
        return self.coefficient(4)

    @property
    def left(self) -> float:
        return self.coefficient(2)

    @property
    def top(self) -> float:
        return self.coefficient(5)

    def right(self, width: int) -> float:
        return self.left + self.dx * width

    def bottom(self, height: int) -> float:
        return self.top + self.dy * height

    def bounds(self, shape: shape2d) -> BoundingBox:
        left = self.left
        top = self.top
        bottom = self.bottom(shape[0])
        right = self.right(shape[1])
        return BoundingBox(left, bottom, right, top)

    def oriented_bounds(
        self, shape: shape2d, left_min: bool = True, top_max: bool = True
    ) -> BoundingBox:
        """
        Returns an oriented bounding box derived from the transform
        ----------
        self.oriented_bounds(shape)
        Returns a bounding box for the transform, such that (left <= right) and
        (bottom <= top).

        self.oriented_bounds(shape, left_min, top_max)
        Specifies the orientation of the returned bounding box. If left_min=False,
        then reverses the left and right bounds, such that (left >= right).
        If top_max=False, reverses the top and bottom bounds, such that
        (bottom >= top).
        ----------
        Inputs:
            shape: The shape used to compute bounds
            left_min: True for (left <= right). False for (left >= right)
            top_max: True for (bottom <= top). False for (bottom >= top)

        Outputs:
            BoundingBox: The oriented bounds derived from the transform
        """

        left, bottom, right, top = self.bounds(shape)
        flip_x = left_min != (left <= right)
        flip_y = top_max != (top >= bottom)
        if flip_x:
            left, right = right, left
        if flip_y:
            top, bottom = bottom, top
        return BoundingBox(left, bottom, right, top)

    @property
    def xres(self):
        return abs(self.dx)

    @property
    def yres(self):
        return abs(self.dy)

    @property
    def resolution(self):
        return self.xres, self.yres
