class CoaeError(Exception):
    """Base error exposed by the COAE core."""


class ProviderNotConfiguredError(CoaeError):
    code = "PROVIDER_NOT_CONFIGURED"


class UnsupportedAudioError(CoaeError):
    code = "UNSUPPORTED_AUDIO"


class InvalidTranscriptError(CoaeError, ValueError):
    code = "INVALID_TRANSCRIPT"


class ProjectNotFoundError(CoaeError):
    code = "PROJECT_NOT_FOUND"


class ScriptNotApprovedError(CoaeError):
    code = "SCRIPT_NOT_APPROVED"