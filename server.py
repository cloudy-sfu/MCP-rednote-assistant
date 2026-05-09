import json
import logging
import os
import sys

from mcp.server.fastmcp import FastMCP
from requests import Session

from cookies import load_cookies
from get_data import feed_first_page, feed_subsequent_page, search_page, get_details_

# %% Logging system.
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    stream=sys.stdout,
)
error_handler = logging.Logger(name="Error", level=logging.ERROR)
error_handler.addHandler(logging.StreamHandler(sys.stderr))


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    error_handler.error(f"{exc_type.__name__}: {exc_value}")


sys.excepthook = handle_exception

# %% Initial definitions.
os.makedirs("raw", exist_ok=True)
mcp = FastMCP("rednote-assistant")
with open("role_introduction") as f:
    role = f.read()
cookies = load_cookies()

# %% API.
@mcp.prompt()
def rednote_assistant_general_workflow():
    """
    This prompt returns the general workflow of using this MCP server.
    """
    return role


@mcp.tool()
def get_feed(pages: int):
    """
    Retrieves recommended posts for the home page, personalized according to user
    preferences. Each calling may fetch different results, because the server may
    recommend different posts when human user refreshes the page. Use this function
    to display or explore recommended content without specific search terms.
    Args:
        pages: integer, number of pages. The first page has 39 posts, and each subsequent
        pages has 15 records.
    Returns:
        JSON format of table of recommended posts with the following columns.
            id: Post unique identifier
            xsec_token: Token for accessing detailed content
            title: Post title
            cover_median_url: Medium-sized cover image URL
            user_id: Author's unique identifier (not useful)
            user_name: Author's nickname (not useful)
            user_xsec_token: Token for author's homepage (not useful)
    """
    assert pages >= 1, "Number of pages must be a positive integer."

    session = Session()
    posts = feed_first_page(session, cookies)
    if pages == 1:
        return json.dumps(posts)
    cursor_score = ""
    for page in range(1, pages):
        new_posts, cursor_score = feed_subsequent_page(
            session=session,
            cookies=cookies,
            note_index=len(posts) - 1,
            page=page,
            cursor_score=cursor_score
        )
        posts += new_posts
    return json.dumps(posts)


@mcp.tool()
def search(query: str, pages: int):
    """
    Search posts by keyword or query terms. Use this function when you want to find posts
    on specific topics or keywords.
    Args:
        query: string, the input to the searching box.
        pages: integer, number of pages. Each page returns 20 posts. The number of pages
        returned may be less than this value, which usually mean there are not enough
        searching results.
    Returns:
        JSON format of table of searching results (posts) with the following columns.
            id: Post unique identifier
            xsec_token: Token for accessing detailed content
            title: Post title
            cover_median_url: Medium-sized cover image URL
            user_id: Author's unique identifier (not useful)
            user_name: Author's nickname (not useful)
            user_xsec_token: Token for author's homepage (not useful)
    """
    session = Session()
    posts = []
    for page in range(pages):
        new_posts, has_more = search_page(session, cookies, query, page)
        posts += new_posts
        if not has_more:
            break
    return json.dumps(posts)


@mcp.tool()
def get_details(id_list: list[str], xsec_token_list: list[str]):
    """
    Retrieves detailed content of a list of posts, identified by the list of "id" and
    the corresponding list of "xsec_token". Use this function to access complete post
    details necessary for answering detailed questions or further content analysis.
    Args:
        id_list: list of string, the list of post IDs.
        xsec_token_list: list of string, the list of access tokens corresponding to the
        post IDs.
    Returns:
        JSON format of detailed content of the requested posts with the following columns.
            url: URL link of the post
            title: Title of the post
            description: Textual content of the post
            images: URLs of images attached to the post
            labels: Topic labels categorizing the post
            published_time: The time when the post is published
            location: The location of the author when publishing the post
    """
    session = Session()
    posts = get_details_(session, cookies, id_list, xsec_token_list)
    return json.dumps(posts)


if __name__ == '__main__':
    mcp.run()
