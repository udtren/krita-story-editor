def write_log(log_msg):
    with open(
        r"C:\Users\udtren\Project\krita-story-editor\agent\story_editor_agent\logs\log.txt",
        "a",
        encoding="utf-8",
    ) as f:
        f.write(log_msg + "\n")
