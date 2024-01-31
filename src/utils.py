from pytube import YouTube
import streamlit as st
from mlx_lm.utils import load
from create import find_project_root
from pathlib import Path

with open('models.txt', 'r') as file:
    model_refs = [line.strip() for line in file.readlines() if not line.startswith('#')]

model_refs = [line.strip() for line in model_refs]


@st.cache_resource(show_spinner=True)
def load_model_and_cache(ref):
    return load(ref, {"trust_remote_code": True})

def default_model_load():
    print("Load Model*******")
    model, tokenizer = load_model_and_cache(st.session_state.model)
    st.session_state["model"] = model
    st.session_state["tokenizer"] = tokenizer



# model, tokenizer = load_model_and_cache(f"{base_model_path}/{model_ref}")
def download_youtube_video(url, output_path="files/video"):
    video_file = Path(f"{find_project_root()}/{output_path}/downloaded.mp4")

    if not video_file.exists():
        yt = YouTube(url)
        stream = (
            yt.streams.filter(progressive=True, file_extension="mp4")
            .order_by("resolution")
            .desc()
            .first()
        )
        stream.download(output_path=output_path, filename="downloaded.mp4")
    return f"{output_path}/downloaded.mp4"

# def download_youtube_video(url):
#     yt = YouTube(url)
#     video = yt.streams.filter(file_extension='mp4').first()
#     return video.download()
