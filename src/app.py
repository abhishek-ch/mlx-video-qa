import re
import time

import mlx.core as mx
import streamlit as st
from mlx_lm.utils import generate_step

from create import find_level_above_project_root
from sidebarmgr import sidebar_ui
from utils import default_model_load

title = "QA with a Video"
ver = "0.7.19"
debug = False

base_model_path = f"{find_level_above_project_root()}/mlx-community"

assistant_greeting = "Start chatting with the Video"

# model_refs = {k.strip(): v.strip() for k, v in [line.split("|") for line in model_refs]}
st.set_page_config(
    page_title=title,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title(title)

if 'video' not in st.session_state:
    st.session_state.video = None


st.markdown(r"<style>.stDeployButton{display:none}</style>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": assistant_greeting}]

if "model" not in st.session_state:
    st.session_state["model"] = f"{base_model_path}/NeuralBeagle14-7B-mlx"
    default_model_load()

if "tokenizer" not in st.session_state:
    st.session_state["tokenizer"] = None

if "temperature" not in st.session_state:
    st.session_state["temperature"] = 0.5

if "context_length" not in st.session_state:
    st.session_state["context_length"] = 400

if "video" not in st.session_state:
    st.session_state["video"] = ""

if "summary" not in st.session_state:
    st.session_state["summary"] = ""

if "coremessage" not in st.session_state:
    st.session_state["coremessage"] = ""

if "status" not in st.session_state:
    st.session_state["status"] = ""

if "progress" not in st.session_state:
    st.session_state["progress"] = 1


# Function to download YouTube video

# Function to load video (placeholder for now)
def load_video(video_path):
    st.video(video_path)


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


# give a bit of time for sidebar widgets to render
time.sleep(0.05)
sidebar_ui()

system_prompt = ("You are a Software Engineering Video QA Assistant. "
                 "You can find all insights from the Video and share with the user")

st.sidebar.markdown("---")
actions = st.sidebar.columns(2)

st.sidebar.markdown("---")
st.sidebar.markdown(f"@abc / llm-locally")

if st.session_state.tokenizer and st.session_state.tokenizer.chat_template:
    chatml_template = st.session_state.tokenizer.chat_template
else:
    chatml_template = (
        "{% for message in messages %}"
        "{{'<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>' + '\n'}}"
        "{% endfor %}"
        "{% if add_generation_prompt %}"
        "{{ '<|im_start|>assistant\n' }}"
        "{% endif %}"
    )

stop_words = ["<|im_start|>", "<|im_end|>", "<s>", "</s>"]


def generate(the_prompt, the_model):
    tokens = []
    skip = 0

    for (token, prob), n in zip(generate_step(mx.array(st.session_state.tokenizer.encode(the_prompt)),
                                              the_model, st.session_state.temperature),
                                range(st.session_state.context_length)):

        if token == st.session_state.tokenizer.eos_token_id:
            break

        tokens.append(token.item())
        text = st.session_state.tokenizer.decode(tokens)

        trim = None

        for sw in stop_words:
            if text[-len(sw):].lower() == sw:
                # definitely ends with a stop word. stop generating
                return
            else:
                # if text ends with start of an end word, accumulate tokens and wait for the full word
                for i, _ in enumerate(sw, start=1):
                    if text[-i:].lower() == sw[:i]:
                        trim = -i

        # flush text up till trim point (beginning of stop word)
        yield text[skip:trim]
        skip = len(text)


def show_chat(the_prompt, previous=""):
    if debug:
        print(the_prompt)
        print("-" * 80)

    with ((st.chat_message("assistant"))):
        message_placeholder = st.empty()
        response = previous

        for chunk in generate(the_prompt, st.session_state.model):
            response = response + chunk

            if not previous:
                # begin neural-beagle-14 fixes
                response = re.sub(r"^/\*+/", "", response)
                response = re.sub(r"^:+", "", response)
                # end neural-beagle-14 fixes

            response = response.replace('�', '')
            message_placeholder.markdown(response + "▌")

        message_placeholder.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})


def remove_last_occurrence(array, criteria_fn):
    for i in reversed(range(len(array))):
        if criteria_fn(array[i]):
            del array[i]
            break


def build_memory():
    if len(st.session_state.messages) > 2:
        return st.session_state.messages[1:-1]
    return []


def queue_chat(the_prompt, continuation=""):
    # workaround because the chat boxes are not really replaced until a rerun
    st.session_state["prompt"] = the_prompt
    st.session_state["continuation"] = continuation
    st.rerun()


if actions[0].button("😶‍🌫️ Forget", use_container_width=True,
                     help="Forget the previous conversations."):
    st.session_state.messages = [{"role": "assistant", "content": assistant_greeting}]
    if "prompt" in st.session_state and st.session_state["prompt"]:
        st.session_state["prompt"] = None
        st.session_state["continuation"] = None
    st.rerun()

if actions[1].button("🔂 Continue", use_container_width=True,
                     help="Continue the generation."):

    user_prompts = [msg["content"] for msg in st.session_state.messages if msg["role"] == "user"]

    if user_prompts:

        last_user_prompt = user_prompts[-1]

        assistant_responses = [msg["content"] for msg in st.session_state.messages
                               if msg["role"] == "assistant" and msg["content"] != assistant_greeting]
        last_assistant_response = assistant_responses[-1] if assistant_responses else ""

        # remove last line completely, so it is regenerated correctly (in case it stopped mid-word or mid-number)
        last_assistant_response_lines = last_assistant_response.split('\n')
        if len(last_assistant_response_lines) > 1:
            last_assistant_response_lines.pop()
            last_assistant_response = "\n".join(last_assistant_response_lines)
        print(f"st.session_state.tokenizerst.session_state.tokenizer {st.session_state.tokenizer}")
        full_prompt = st.session_state.tokenizer.apply_chat_template([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": last_user_prompt},
            {"role": "assistant", "content": last_assistant_response},
        ], tokenize=False, add_generation_prompt=False, chat_template=chatml_template)
        full_prompt = full_prompt.rstrip("\n")

        # remove last assistant response from state, as it will be replaced with a continued one
        remove_last_occurrence(st.session_state.messages,
                               lambda msg: msg["role"] == "assistant" and msg["content"] != assistant_greeting)

        queue_chat(full_prompt, last_assistant_response)

# Dashboard Main Panel
col = st.columns((3.0, 5.0), gap='medium')

# Column 2: Translated Video
with col[0]:
    st.markdown("#### Loaded Video")
    with st.container():
        # Placeholder for translated video
        # You need to replace 'path_to_translated_video' with the actual path of the translated video
        # path_to_translated_video = 'path_to_translated_video.mp4'
        if st.session_state.video and len(st.session_state.video) > 2:
            load_video(st.session_state.video)
        else:
            st.write("No Video...")

with col[1]:
    st.markdown('#### Summary')
    if st.session_state.coremessage:
        with st.expander("Main Message", expanded=True):
            st.write(st.session_state.coremessage)
    with st.expander('AI Summary', expanded=True):
        st.write(st.session_state.summary)

st.markdown("---")

# Section 2: Chat
st.header("Chat Section")
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})

    messages = [{"role": "system", "content": system_prompt}]
    messages += build_memory()
    messages += [{"role": "user", "content": prompt}]

    print(f"st.session_state.==========state.tokenizer {st.session_state.tokenizer}")

    full_prompt = st.session_state.tokenizer.apply_chat_template(messages, tokenize=False,
                                                                 add_generation_prompt=True,
                                                                 chat_template=chatml_template)
    full_prompt = full_prompt.rstrip("\n")

    queue_chat(full_prompt)

# Scrollable container for chat messages
with st.container():
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

# give a bit of time for messages to render
time.sleep(0.05)
chat_expander = st.expander("Chat Messages", expanded=True)
if "prompt" in st.session_state and st.session_state["prompt"]:
    with chat_expander:
        show_chat(st.session_state["prompt"], st.session_state["continuation"])
        st.session_state["prompt"] = None
        st.session_state["continuation"] = None
