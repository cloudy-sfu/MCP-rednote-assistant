import json
import logging
import os
import socket
import sys
import threading
import webbrowser
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler

import pandas as pd
from bs4 import BeautifulSoup
from flask import Flask, render_template, redirect, request, jsonify
from markdown import markdown

import auth
from azure_openai_agent import Conversation

logging.basicConfig(
    format="%(levelname)s | %(asctime)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S %z",
    handlers=[
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler('log/log.txt', maxBytes=1_048_576)
    ]
)
app = Flask(__name__)
# Basic config doesn't affect Flask logging.
app.logger.propagate = False
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.propagate = False
os.makedirs("raw", exist_ok=True)
cookies_path = "raw/cookies.csv"
cookies = {}
cookies_lock = threading.Lock()


@dataclass
class ArchivedConversation:
    title: str
    messages: list[dict]


def load_archived_conversations():
    if os.path.isfile("raw/conversations"):
        archived_convs = pd.read_pickle("raw/conversations")
        return {
            i+1: conv
            for i, conv in enumerate(archived_convs)
        }
    else:
        return {}


conversations = load_archived_conversations()  # id: instance
conversations_lock = threading.Lock()


@app.route('/')
def main():  # put application's code here
    conv_display_list = [
        {"title": conv.title or "New chat", "id": id_}
        for id_, conv in conversations.items()
    ]
    return render_template(
        'main.html',
        conversations=conv_display_list,
        home_page=True,
    )


@app.route('/cookies')
def view_cookies(failed_reason=None):
    return render_template(
        'update_cookies.html',
        failed_reason=failed_reason,
    )


@app.route('/cookies/update', methods=['POST'])
def update_cookies():
    j2teams_cookies = request.files.get('cookies')
    if not (j2teams_cookies and j2teams_cookies.filename):
        return view_cookies(failed_reason="No file selected.")
    try:
        cookies_dict = json.load(j2teams_cookies.stream)
    except json.JSONDecodeError:
        return view_cookies(failed_reason="Invalid cookies file.")
    auth.dump_cookies(cookies_dict, cookies_path)
    return redirect("/")


@app.route('/conv/add', methods=['POST'])
def add_conversation():
    global cookies
    if auth.check_cookies(cookies_path):
        with cookies_lock:
            cookies = auth.load_cookies(cookies_path)
    else:
        return redirect('/cookies')
    max_func_call_rounds = request.form.get('max_func_call_rounds', type=int)
    if not max_func_call_rounds:
        return render_template(
            'new_chat_error.html',
            failed_reason="Maximum function call rounds is required."
        )
    conv = Conversation(cookies, max_func_call_rounds)
    with conversations_lock:
        if conversations:
            conv_id = max(conversations.keys()) + 1
        else:
            conv_id = 1
        conversations[conv_id] = conv
    return redirect(f'/conv/{conv_id}')


def render_message_list(messages, start_id: int = 0):
    messages_html = ""
    for i, message in enumerate(messages):
        messages_html += render_template(
            'message.html', message=message,
            message_id=start_id + i,
        )
    return messages_html


@app.route('/conv/<int:conv_id>')
def view_conversation(conv_id: int):
    conv_display_list = [
        {"title": conv.title or "New chat", "id": id_}
        for id_, conv in conversations.items()
    ]
    conv = conversations.get(conv_id)
    if conv is None:
        return redirect('/')
    messages_html = render_message_list(conv.messages)
    return render_template(
        'main.html',
        conversations=conv_display_list,
        home_page=False,
        messages=messages_html,
        conv_id=conv_id,
        active=isinstance(conv, Conversation)
    )


@app.route('/conv/delete/<int:conv_id>')
def delete_conversation(conv_id: int):
    conv = conversations.get(conv_id)
    if conv is not None:
        del conversations[conv_id]
    return redirect('/')


def parse_content_filter_error(prefix: str, error: dict):
    errors = []
    if 'innererror' in error.keys():
        error = error.get('innererror', {})
    error_type = error.get('code')
    match error_type:
        case 'ResponsibleAIPolicyViolation':
            for filter_name, filter_result in (error.get('content_filter_result', {}).items()):
                if not filter_result.get('filtered'):
                    continue
                severity = filter_result.get('severity')
                if severity:
                    errors.append(f"{prefix}, the user's message is ignored because of "
                                  f"{severity} severity of {filter_name} content.")
                else:
                    errors.append(f"{prefix}, the user's message is ignored because of "
                                  f"{filter_name} content.")
        case _:
            errors.append(f"{prefix}, error type \"{error_type}\" happens. "
                          f"{error.get('message')} Read the terminal log for details.")
    return errors


@app.route('/conv/send', methods=["POST"])  # AJAX, No-response
def process_user_message():
    conv_id = request.form.get('conv_id', type=int)
    user_message = request.form.get('user_message', type=str)
    if conv_id is None:
        return jsonify()
    conv = conversations.get(conv_id)
    if not isinstance(conv, Conversation):
        return jsonify()
    conv.busy = True
    error_message = []
    if not conv.title:
        error_1 = conv.generate_title(user_message)
        if error_1:
            error_message.append(parse_content_filter_error(
                "When generating the conversation title", error_1
            ))
    error_2 = conv.answer_query(user_message)
    if error_2:
        error_message.append(parse_content_filter_error(
            "When answering the user's query", error_2
        ))
    conv.busy = False
    return jsonify({"error": error_message})


@app.route('/conv/update', methods=["POST"])  # AJAX, JSON-response
def update_message():
    conv_id = request.form.get('conv_id', type=int)
    start_id = request.form.get('start_id', type=int)
    if conv_id is None:
        return jsonify({"error": "Conversation doesn't exist.", "busy": False})
    conv = conversations.get(conv_id)
    if not isinstance(conv, Conversation):
        return jsonify({"error": "Conversation doesn't exist.", "busy": False})
    messages_html = render_message_list(conv.messages[start_id:], start_id=start_id)
    response = {"messages": messages_html, "busy": conv.busy}
    return jsonify(response)


@app.template_filter('render_markdown')
def render_markdown(text):
    extensions = ['markdown_link_attr_modifier', ]
    extension_configs = {
        'markdown_link_attr_modifier': {
            'new_tab': 'external_only',
            'no_referrer': 'external_only',
            'auto_title': 'on',
        },
    }
    tree_text = markdown(text, extensions=extensions, extension_configs=extension_configs)
    tree = BeautifulSoup(tree_text, 'html.parser')
    for img_tag in tree.find_all('img'):
        src = img_tag.get('src')
        alt = img_tag.get('alt', '')
        a_tag = tree.new_tag('a', href=src, target="_blank",
                             referrerpolicy="no-referrer", rel="noopener noreferrer")
        a_tag.string = alt
        img_tag.replace_with(a_tag)
    return str(tree)


@app.template_filter('render_tool_call_token')
def render_tool_call_token(tool_call):
    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments)
    call_id = tool_call.id.removeprefix('call')
    func_arg_str = ", ".join(f"{k}=\"{v}\"" for k, v in function_args.items())
    return f"{function_name}{call_id}({func_arg_str})"


@app.template_filter('render_tool_response_token')
def render_tool_response_token(message):
    call_id = message.get('tool_call_id', '').removeprefix('call')
    function_name = message.get('name', '')
    return f"{function_name}{call_id}"


def find_available_port(start_port: int, tries: int = 100):
    """
    Find the first available port from {start_port} to {start_port + tries}
    :param start_port: The port that the program starts to scan, if it's occupied, the
    program will scan {start_port + 1}. If it's occupied again, try the next one...
    :param tries: Default 100, the maximum trying times from the start port.
    :return:
    """
    for i in range(tries):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("127.0.0.1", start_port + i))
            s.close()
            return start_port + i
        except OSError:
            pass
    raise Exception(f"Tried {tries} times, no available port from {start_port} to "
                    f"{start_port + tries}.")


@app.route('/archive')
def archive_all():
    archived_convs = []
    with conversations_lock:
        for conv in conversations.values():
            archived_conv = ArchivedConversation(title=conv.title, messages=conv.messages)
            archived_convs.append(archived_conv)
    pd.to_pickle(archived_convs, "raw/conversations")
    return redirect("/")


if __name__ == '__main__':
    port = find_available_port(5000)
    webbrowser.open_new_tab(f'http://localhost:{port}')
    app.run(port=port)
