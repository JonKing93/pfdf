from pfdf._utils import slug


class TestSlugify:
    def test(_):
        a = "A Heading With Caps"
        output = slug.slugify(a)
        assert output == "A-Heading-With-Caps"
