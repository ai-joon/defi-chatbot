from queue import Queue


async def add_message_to_queue(message, queue: Queue):
    queue.put({"event": "message", "data": message})