def no_mitigation(character, messages, turn_index):
    return messages
def periodic_reminder(character, messages, turn_index, every=4):
    if turn_index > 0 and turn_index % every == 0:
        reminder = {
            "role": "user",
            "content": (
                f"[SYSTEM REMINDER - not part of the conversation, do not "
                f"respond to this directly, just keep it in mind]: Remember, "
                f"you are still {character['name']}. Key facts: "
                + " ".join(character["key_facts"])
            ),
        }
        messages = messages + [reminder]
    return messages
def fact_reinjection(character, messages, turn_index, every=4):
    if turn_index > 0 and turn_index % every == 0:
        facts = " ".join(character["key_facts"])
        reminder = {
            "role": "user",
            "content": f"[{character['name']} privately recalls: {facts}]",
        }
        messages = messages + [reminder]
    return messages
STRATEGIES = {
    "none": no_mitigation,
    "periodic_reminder": periodic_reminder,
    "fact_reinjection": fact_reinjection,
}
