def start_node(input_data):
    return {
        "user_input": input_data.get("user_input"),
        "topic": input_data.get("topic"),
        "user_id": input_data.get("user_id"),
        "history": input_data.get("history", [])
    }
