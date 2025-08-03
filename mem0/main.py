import os

from mem0 import Memory

os.environ["OPENAI_API_KEY"] = "EMPTY"  # for embedder

config = {
    "llm": {
        "provider": "ollama",
        "config": {
            "ollama_base_url": "http://192.168.100.202:11434",
            "model": "qwen3:30b",
            "temperature": 0.1,
            "max_tokens": 2000,
        }
    }
}

memory = Memory.from_config(config)
# messages = [
#     {"role": "user", "content": "I'm planning to watch a movie tonight. Any recommendations?"},
#     {"role": "assistant",
#         "content": "How about a thriller movies? They can be quite engaging."},
#     {"role": "user", "content": "I’m not a big fan of thriller movies but I love sci-fi movies."},
#     {"role": "assistant", "content": "Got it! I'll avoid thriller recommendations and suggest sci-fi movies in the future."}
# ]
# m.add(messages, user_id="alice", metadata={"category": "movies"})


def chat_with_memories(message: str, user_id: str = "default_user") -> str:
    # Retrieve relevant memories
    relevant_memories = memory.search(query=message, user_id=user_id, limit=3)
    memories_str = "\n".join(
        f"- {entry['memory']}" for entry in relevant_memories["results"])

    # Generate Assistant response
    system_prompt = f"You are a helpful AI. Answer the question based on query and memories.\nUser Memories:\n{memories_str}"
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": message}]
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini", messages=messages)
    assistant_response = response.choices[0].message.content

    # Create new memories from the conversation
    messages.append({"role": "assistant", "content": assistant_response})
    memory.add(messages, user_id=user_id)

    return assistant_response


def main():
    print("Chat with AI (type 'exit' to quit)")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        print(f"AI: {chat_with_memories(user_input)}")


if __name__ == "__main__":
    main()
