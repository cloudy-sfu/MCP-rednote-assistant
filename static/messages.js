/*
This section should correspond to chat application page.
Map HTML elements to widgets.
 */
const msg_list = document.getElementById('messages-list');
const conv_form = document.getElementById('main-right-input');
// usage: switch to read-only and clear values
const conv_form_msg = conv_form.querySelector('textarea');
// usage: disable the button to prevent duplicate submission
const conv_form_submit = conv_form.querySelector('button[type="submit"]');

function render_msg_error(text) {
    /*
    This function is used when messages are not standard LLM messages' format, and
    doesn't have a message ID in LLM chat history. So, error messages have to
    pre-rendered and match HTML style of those having a message ID.
     */
    return `<div class="d-flex text-body-secondary pt-3" style="color: red !important;">
<i class="bi bi-exclamation-circle me-2" style="font-size: 2rem;"></i>
<div class="mb-0 border-bottom w-100 lh-sm">
    <span class="text-gray-dark small"><b>Error</b></span>
    <div style="word-break: break-all">
        ${text}
    </div>
</div>
</div>`
}

function get_conv_title(conv_id) {
    return document.querySelector(`a[href="/conv/${conv_id}"] div`);
}

/*
Messages function.
submit_message
 ├─ add_conversation
 └─ update_message
     ├─ append_message
     └─ get_message_start_id
 */
function get_message_start_id() {
    const messages = msg_list.querySelectorAll(`div[message_id]`);
    let start_id = 0;
    messages.forEach(div => {
        const message_id = parseInt(div.getAttribute('message_id'));
        if (!isNaN(message_id)) {
            const start_id_0 = message_id + 1;
            if (start_id_0 > start_id) start_id = start_id_0;
        }
    });
    return start_id;
}

function append_message(rendered_msg) {
    msg_list.innerHTML += rendered_msg;
    msg_list.scrollIntoView({behavior: 'smooth', block: 'end'});
}

function update_message(conv_id) {
    $.ajax({
        type: 'POST',
        url: "/conv/update",
        data: {conv_id: conv_id, start_id: get_message_start_id()},
        success: function(response) {
            if (response['messages']) {
                append_message(response['messages']);
                const title_node = get_conv_title(conv_id);
                if (title_node && response['title']) {
                    title_node.textContent = response['title'];
                }
            }
            if (response['busy']) {
                setTimeout(update_message, 1000, conv_id);
            }
        },
        error: function(response) {
            append_message(render_msg_error(
                `Cannot update messages. HTTP status ${response.status}`)
            );
        }
    });
}

async function add_conversation() {
    const response = await fetch("/conv/add");
    if (!response.ok) {
        const error_msg = `Cannot create new conversation. HTTP status: ${response.status}.`;
        append_message(render_msg_error(error_msg));
        throw Error(error_msg)
    } else if (response.redirected) {
        location.href = response.url;  // Redirected to cookies page.
    } else if (response['error']) {
        const error_msg = response['error'];
        append_message(render_msg_error(error_msg));
        throw Error(error_msg)
    }
    const response_json = await response.json();
    const conv_id = parseInt(response_json['conv_id']);
    if (isNaN(conv_id)) {
        const error_msg = `Cannot to create new conversation. Conversation ID: ${conv_id}.`;
        append_message(render_msg_error(error_msg));
        throw Error(error_msg)
    }
    return conv_id
}

async function submit_message(event) {
    event.preventDefault();
    conv_form.removeEventListener('submit', submit_message);
    conv_form.addEventListener('submit', Event.prototype.preventDefault);
    conv_form_msg.readOnly = true;
    if (conv_form_submit) conv_form_submit.disabled = true;
    console.log(conv_form_submit);
    const form = $(this);
    const action_target = form.attr('action'); // Get the form's action URL
    if (!form[0].conv_id.value) {
        form[0].conv_id.value = await add_conversation();
    }
    $.ajax({
        type: 'POST',
        url: action_target,
        data: form.serialize(), // Serialize the form data
        success: function(response) {
            conv_form.removeEventListener('submit', Event.prototype.preventDefault);
            conv_form.addEventListener('submit', submit_message);
            conv_form_msg.readOnly = false;
            if (conv_form_submit) conv_form_submit.disabled = false;
            conv_form_msg.value = '';
            if (response['error']) {
                for (let error_message of response['error']) {
                    append_message(render_msg_error(error_message))
                }
            }
        },
        error: function() {
            conv_form.removeEventListener('submit', Event.prototype.preventDefault);
            conv_form.addEventListener('submit', submit_message);
            conv_form_msg.readOnly = false;
            if (conv_form_submit) conv_form_submit.disabled = false;
            append_message(render_msg_error(
                "Fail to get response from the AI agent, please try again.")
            );
        }
    });
    update_message(form[0].conv_id.value);
}
conv_form.addEventListener('submit', submit_message);

// Independent functions.
function print_message_list() {
    const cloned_messages_list = msg_list.cloneNode(true);
    const print_preview = window.open('about:blank', '_blank');
    const stylesheets = Array.from(document.styleSheets);
    stylesheets.forEach(stylesheet => {
        if (stylesheet.href) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = stylesheet.href;
            print_preview.document.head.appendChild(link);
        } else if (stylesheet.cssRules) {
            const style = document.createElement('style');
            style.textContent = Array.from(stylesheet.cssRules)
                .map(rule => rule.cssText)
                .join('\n');
            print_preview.document.head.appendChild(style);
        }
    });
    const title = print_preview.document.createElement('title');
    title.textContent = "Messages history print preview";
    print_preview.document.head.appendChild(title);
    print_preview.document.body.appendChild(cloned_messages_list);
    print_preview.document.close();
}

// Shortcut: Ctrl+Enter to submit user message.
conv_form_msg.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        // conv_form.
        conv_form.dispatchEvent(new SubmitEvent('submit'));
    }
});
