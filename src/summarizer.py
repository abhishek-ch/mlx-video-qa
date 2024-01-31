import os
import re
import streamlit as st
from transcribe.get_video import process_local_video  # Adjusted import
from transcribe.summarize_model import split_text, summarize_in_parallel, merge_summaries
from transcribe.transcribe import transcribe
from transcribe.utils import get_filename


def create_logseq_note(
        summary_path=None,
        source=None,
        title=None
):
    """
    Takes the bullet point summary and formats it so that it becomes a logseq
    note.
    """
    if not summary_path or not title:
        raise ValueError("Please provide summary_path and title.")

    with open(summary_path, "r") as f:
        lines = f.readlines()

    formatted_lines = ["    " + line for line in lines]

    logseq_note_path = summary_path.replace("files/summaries", "files/logseq")
    os.makedirs(os.path.dirname(logseq_note_path), exist_ok=True)

    with open(logseq_note_path, "w") as f:
        f.write(f"- summarized [[{title}]]")
        f.write("\n- [[summary]]\n")
        f.writelines(formatted_lines)

    print(f"Logseq note saved at {logseq_note_path}")


def call_mlx_model(text_path=None, source=None, title=None):
    filename_only = get_filename(text_path)

    chunks = split_text(text_path=text_path, title=title)
    print(f"Found {len(chunks)} chunks. Summarizing using MLX model...")

    summaries = summarize_in_parallel(chunks)
    # summary_path = save_summaries(summaries, filename_only)
    # print(f"Summary saved at {summary_path}.")

    return merge_summaries(summaries)


def extract_summary(full_summary: str) -> (str, str):
    # Splitting the message into main_message and full_message
    split_text = re.split(r'Main message:', full_summary, maxsplit=1)
    full_message = split_text[0].strip() if len(split_text) > 0 else ""
    main_message = split_text[1].strip() if len(split_text) > 1 else ""

    return main_message, full_message

def process_local(input_path):
    """
    Processes a local video file, transcribes it, splits it into chunks,
    summarizes each chunk, and saves the summaries to a file.

    :input_path: The path of the local video file to be processed.
    :title: The title of the video.
    """
    if not input_path:
        raise ValueError("Please provide input_path and title.")

    my_bar = st.progress(0, text="Operation in progress. Please wait")
    print(f"Processing local video file: {input_path}")
    st.session_state.state = f"Processing local video file: {input_path}"
    my_bar.progress(1,st.session_state.state)
    audio_path = process_local_video(input_path)
    st.session_state.state = f"Audio extracted to: {audio_path}"
    my_bar.progress(10, st.session_state.state)
    print(f"Audio extracted to: {audio_path}")
    st.session_state.state = f"Transcribing {audio_path} (this may take a while)..."
    my_bar.progress(15, st.session_state.state)
    print(f"Transcribing {audio_path} (this may take a while)...")
    elapsed_time, transcript_path = transcribe(audio_path)
    my_bar.progress(50, st.session_state.state)
    # text_to_speech(transcript_path)
    st.session_state.state = f"Audio has been transcribed in {int(elapsed_time)} seconds"
    my_bar.progress(55, st.session_state.state)
    print(f"Audio has been transcribed in {int(elapsed_time)} seconds")
    my_bar.progress(60, "Generating summary with MLX model")
    full_summary = call_mlx_model(
        text_path=transcript_path, source=input_path, title="output.txt"
    )
    my_bar.progress(80, st.session_state.state)
    main_message, full_message = extract_summary(full_summary)
    my_bar.progress(95, st.session_state.state)
    st.session_state.summary = full_message
    st.session_state.coremessage = main_message
    st.session_state.state = "Full Summary Done!"
    my_bar.progress(99)
    # create_logseq_note(
    #     summary_path=summary_path,
    #     source=input_path,
    #     title=title
    # )
    print("End of job for source: local video")
    my_bar.empty()