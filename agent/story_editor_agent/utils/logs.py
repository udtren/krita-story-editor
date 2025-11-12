def write_log(log_msg, enable_debug=False):

    enable_debug = False

    if enable_debug:
        with open(
            r"C:\Users\udtre\Projects\krita-plugin\krita-story-editor\agent\story_editor_agent\logs\log.txt",
            "a",
            encoding="utf-8",
        ) as f:
            f.write(log_msg + "\n")
    else:
        pass
