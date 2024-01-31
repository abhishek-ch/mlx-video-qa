import os

import streamlit as st

from create import find_level_above_project_root
from summarizer import process_local
from utils import model_refs, load_model_and_cache, download_youtube_video

base_model_path = f"{find_level_above_project_root()}/mlx-community"

def change_model():
    print("Load Model*******")
    model, tokenizer = load_model_and_cache(
        f"{base_model_path}/{st.session_state.current_model}")
    st.session_state["model"] = model
    st.session_state["tokenizer"] = tokenizer


def sidebar_ui() -> None:
    with st.sidebar:
        model_ref = st.selectbox("model", model_refs,
                                 help="See https://huggingface.co/mlx-community for more models. Add your favorites "
                                      "to models.txt",
                                 key="current_model",
                                 on_change=change_model)

        section = st.expander("Model Context")

        st.session_state["context_length"] = section.number_input('context length', value=400, min_value=100, step=100,
                                                                  max_value=32000,
                                                                  help="how many maximum words to print, roughly")

        st.session_state["temperature"] = section.slider('temperature', min_value=0., max_value=1., step=.10, value=.5,
                                                         help="lower means less creative but more accurate")

        translator_section()


def translator_section():
    video_input = st.expander("Video Translator")
    youtube_url = video_input.text_input("Enter YouTube URL:")
    direct_video_link = video_input.text_input("Or enter direct video link:")

    if youtube_url:
        with st.spinner('Downloading YouTube video...'):
            video_path = download_youtube_video(youtube_url)
            # trim space from video path
            st.session_state.video = video_path.strip()

    elif direct_video_link:
        # Assuming direct_video_link is a path to a local file
        if os.path.exists(direct_video_link):
            st.session_state.video = direct_video_link.strip()
        else:
            video_input.error("File does not exist.")

    # Dropdown for language selection
    languages = ['English', 'Spanish', 'French', 'German', 'Chinese']
    selected_language = st.selectbox("Choose Language", languages)

    # Translate button
    if video_input.button('Summarize'):
        # Add logic for translation
        # video_input.write("Translation feature is not implemented yet.")
        if st.session_state.video:
            process_local(st.session_state.video)
            print(f"Full Summary {st.session_state.summary}")
