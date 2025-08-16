const msg_list = document.getElementById('messages-list');

function append_message_list(messages_html) {
    msg_list.innerHTML += messages_html;
    msg_list.scrollIntoView({behavior: 'smooth', block: 'end'});
}

function get_start_id() {
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

function envelop_error(text) {
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

async function add_conversation() {
    try {
        const response = await fetch("/conv/add");
        if (!response.ok) {
            append_message_list(envelop_error(
                `Cannot create new conversation. HTTP status ${response.status}`));
            return
        } else if (response.redirected) {
            location.href = response.url;  // Redirected to cookies page.
            return
        }
        return await response.json();
    } catch (error) {
        append_message_list(envelop_error(
            `Cannot create new conversation. ${error}`));
    }
}

async function add_conversation_ui() {
    const response_json = await add_conversation();
    const conv_id = parseInt(response_json['conv_id']);
    if (isNaN(conv_id)) {
        append_message_list(envelop_error(
            `Cannot to create new conversation. <code>conv_id=${conv_id}</code>`));
        return
    }
    location.href = `/conv/${conv_id}`;
}

function update_messages(conv_id) {
    $.ajax({
        type: 'POST',
        url: "/conv/update",
        data: {conv_id: conv_id, start_id: get_start_id()},
        success: function(response) {
            if (response['messages']) {
                append_message_list(response['messages']);
                const title_node = document.querySelector(`a[href="/conv/${conv_id}"] div`);
                if (title_node && response['title']) {
                    title_node.textContent = response['title'];
                }
            }
            if (response['busy']) {
                setTimeout(update_messages, 1000, conv_id);
            }
        },
        error: function(response) {
            append_message_list(envelop_error(`Cannot update messages. HTTP status ${response.status}`));
        }
    });
}

$('#conv-send').submit(async function(event) {
    event.preventDefault();
    user_message.readOnly = true;
    const form = $(this);
    const action_target = form.attr('action'); // Get the form's action URL
    if (!form[0].conv_id.value) {
        const response_json = await add_conversation();
        const conv_id = parseInt(response_json['conv_id']);
        if (isNaN(conv_id)) {
            return
        }
        form[0].conv_id.value = conv_id;
    }
    $.ajax({
        type: 'POST',
        url: action_target,
        data: form.serialize(), // Serialize the form data
        success: function(response) {
            user_message.readOnly = false;
            user_message.value = '';
            if (response['error']) {
                for (let error_message of response['error']) {
                    append_message_list(envelop_error(error_message))
                }
            }
        },
        error: function() {
            user_message.readOnly = false;
            append_message_list(envelop_error("Fail to get response from the AI agent, please try again."));
        }
    });
    update_messages(form[0].conv_id.value);
});