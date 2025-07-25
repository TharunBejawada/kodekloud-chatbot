def reject_off_topic(state):
    return {
        **state,
        "response": f"Let's stick to the topic you're learning: '{state['topic']}'. Please ask related questions.",
        "next": "return"
    }