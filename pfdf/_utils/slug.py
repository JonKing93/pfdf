from string import ascii_letters, digits


def slugify(title):
    "Converts heading titles to anchor link slugs for the docs"

    allowed = "-" + ascii_letters + digits
    slug = ""
    for char in title:
        value = char
        if value not in allowed:
            value = "-"
        slug += value
    return slug
