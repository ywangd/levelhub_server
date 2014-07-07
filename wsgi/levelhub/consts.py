ROLE_LESSON_MANAGER = 1
ROLE_LESSON_STUDENT = 2
ROLE_LESSON_NONE = 3

LESSON_ACTIVE = 1
LESSON_INACTIVE = 2
LESSON_DELETED = 3

LESSON_REG_ACTIVE = 1
LESSON_REG_INACTIVE = 2
LESSON_REG_DEROLL = 3
LESSON_REG_QUIT = 4
LESSON_REG_DELETED = 7

# Following status require notices to Receiver
REQUEST_ENROLL = 1
REQUEST_JOIN = 2
# deroll and quit are not requests, they are really notices, can only be dismissed
REQUEST_DEROLL = 3
REQUEST_QUIT = 4

# Following status require notices to Sender
# Only show Dismiss button for following status, once Dismiss is clicked
# the request entry is deleted
REQUEST_ENROLL_ACCEPTED = 201
REQUEST_ENROLL_REJECTED = 202
REQUEST_JOIN_ACCEPTED = 203
REQUEST_JOIN_REJECTED = 204

REQUEST_RECEIVER_NOTICE = [REQUEST_ENROLL,
                           REQUEST_JOIN,
                           REQUEST_DEROLL,
                           REQUEST_QUIT]

REQUEST_SENDER_NOTICE = [REQUEST_ENROLL_ACCEPTED,
                         REQUEST_ENROLL_REJECTED,
                         REQUEST_JOIN_ACCEPTED,
                         REQUEST_JOIN_REJECTED]

REQUEST_RECEIVER_VIEWABLE = REQUEST_RECEIVER_NOTICE

REQUEST_SENDER_VIEWABLE = REQUEST_SENDER_NOTICE + [REQUEST_ENROLL, REQUEST_JOIN]

REQUEST_ACCEPT_OR_REJECT = [REQUEST_ENROLL,
                            REQUEST_JOIN]

REQUEST_SENDER_DISMISS = [REQUEST_ENROLL_ACCEPTED,
                          REQUEST_ENROLL_REJECTED,
                          REQUEST_JOIN_ACCEPTED,
                          REQUEST_JOIN_REJECTED]

REQUEST_RECEIVER_DISMISS = [REQUEST_DEROLL,
                            REQUEST_QUIT]

JSON_NULL = '{}'