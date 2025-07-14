# Simulate memory (for now - can use file/db later)
user_logs = []

def log_habit(done: bool):
    user_logs.append(done)
    return done

def get_streak() -> int:
    streak = 0
    for result in reversed(user_logs):
        if result:
            streak += 1
        else:
            break
    return streak
