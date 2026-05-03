"""Shared configuration values for the pre-auth skill."""

from os import environ


DEFAULT_MISTRAL_MODEL = environ.get("MISTRAL_MODEL", "devstral-2512")
MAX_REQUEST_BODY_BYTES = int(environ.get("MAX_REQUEST_BODY_BYTES", str(10 * 1024 * 1024)))
MAX_REQUESTED_SERVICE_LENGTH = int(
    environ.get("MAX_REQUESTED_SERVICE_LENGTH", "500")
)
MAX_PRIMARY_DIAGNOSIS_LENGTH = int(
    environ.get("MAX_PRIMARY_DIAGNOSIS_LENGTH", "500")
)
MAX_RAW_CLINICAL_NOTES_LENGTH = int(
    environ.get("MAX_RAW_CLINICAL_NOTES_LENGTH", "20000")
)
MAX_UPLOAD_FILE_SIZE = int(
    environ.get("MAX_UPLOAD_FILE_SIZE", str(50 * 1024 * 1024))
)