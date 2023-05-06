import json
import os
import re

import application
import connection

DISCUSSIONS_CATEGORY = os.environ["DISCUSSIONS_CATEGORY"]


def parse_checkboxes(text):
    """Parses the checkboxes in the text

    Parameters
    ----------
    text : str
        The text to be parsed

    Returns
    -------
    list
        List of checked checkboxes
    """

    checkbox_re = r"- \[([X])\] (.*)"

    checked = []
    for line in text.splitlines():
        matched = re.match(checkbox_re, line)
        if matched:
            checked.append(matched.group(2))

    return checked


def get_category_id():
    """Gets the id of the category with name discussions_category

    Returns
    -------
    str
        id of the category
    """

    response = connection.send_request(connection.CATEGORIES_QUERY)
    categories = json.loads(response.text)["data"]["repository"][
        "discussionCategories"
    ]["nodes"]

    for category in categories:
        if category["name"] == DISCUSSIONS_CATEGORY:
            return category["id"]
    return None


def parse_discussions():
    """Gets discussions from server's response and prints them

    Returns
    -------
    list
        List of App objects
    """

    categoryId = get_category_id()

    variables = {
        "categoryId": categoryId,
    }

    response = connection.send_request(connection.DISCUSSIONS_QUERY, variables)

    # Regexes for parsing the entries in discussion body
    # multiline_re is needed to match even if there are new lines
    multiline_re = r"[\s\S]*"
    description_re = r"### Description\s*" + r"(" + multiline_re + r")"
    url_re = r"### URLs\s*" + r"(" + multiline_re + r")"
    types_re = r"### Types*" + r"(" + multiline_re + r")"
    platforms_re = r"### Platforms" + r"(" + multiline_re + r")"
    categories_re = r"### Categories\s*" + r"(" + multiline_re + r")"
    comments_re = r"###\s*\s*---\s*" + r"(" + multiline_re + r")"

    body_regex = re.compile(
        description_re
        + url_re
        + types_re
        + platforms_re
        + categories_re
        + comments_re
        + r"$"
    )

    apps = []
    for discussion in json.loads(response.text)["data"]["repository"]["discussions"][
        "nodes"
    ]:
        app_name = discussion["title"]
        matched = body_regex.match(discussion["body"])
        try:
            description = matched.group(1).rstrip()
            urls = matched.group(2)
            types = parse_checkboxes(matched.group(3))
            platforms = parse_checkboxes(matched.group(4))
            categories = matched.group(5).rstrip()
            comments = matched.group(6).rstrip()
        except AttributeError:
            print(f"Error during body parsing for {app_name}")
            continue

        app = application.App(
            app_name, description, urls, types, platforms, categories, comments
        )
        apps.append(app)
        print(f"Parsed discussion for {app_name} successfully")

    return apps
