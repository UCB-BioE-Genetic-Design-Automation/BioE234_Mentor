class MentorError(Exception):
    pass

class ServerError(MentorError):
    pass

class ProtocolError(MentorError):
    pass

class TaskError(MentorError):
    pass
