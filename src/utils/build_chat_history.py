def build_chat_history(conversation: list) -> list:
    history = []
    if len(conversation) > 0:
        for turn in conversation:
            speaker = "human" if turn["speaker"] == "user" else "ai"
            for message in turn["contents"]:
                if message["type"] == "message":
                    history.append((speaker, message["content"]))

    return history