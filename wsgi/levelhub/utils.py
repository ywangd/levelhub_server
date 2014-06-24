from datetime import datetime

def utcnow():
    return datetime.strftime(datetime.utcnow(), "%Y-%m-%d %H:%M:%SZ")

def now():
    return datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")

