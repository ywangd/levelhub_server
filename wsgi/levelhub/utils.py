from datetime import datetime
import json

from django.utils.timezone import utc

def utcnow():
    return datetime.strftime(datetime.utcnow(), "%Y-%m-%d %H:%M:%SZ")

def now():
    return datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            if obj.tzinfo == utc:
                return obj.strftime('%Y-%m-%d %H:%M:%SZ')
            else:
                return obj.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return json.JSONEncoder.default(self, obj)

