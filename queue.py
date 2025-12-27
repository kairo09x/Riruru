from collections import defaultdict, deque

queues = defaultdict(deque)


def add(chat_id, track):
    queues[chat_id].append(track)


def get_next(chat_id):
    if queues[chat_id]:
        return queues[chat_id].popleft()
    return None


def clear(chat_id):
    queues[chat_id].clear()


def get_queue(chat_id):
    return list(queues[chat_id])
