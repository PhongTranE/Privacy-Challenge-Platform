# Authentication Messages
USER_NOT_FOUND = "User not found."
USER_ALREADY_EXISTS = "A user with that username already exists."
USER_ALREADY_ACTIVATED = "User is already activated."
INVALID_CREDENTIALS = "Invalid credentials."
ACCOUNT_NOT_ACTIVATED = "Account is not activated."
LOGIN_SUCCESS = "Successfully logged in."
LOGOUT_SUCCESS = "Successfully logged out."
REGISTER_SUCCESS = "Successfully registered."
REFRESH_SUCCESS = "Successfully refreshed token."
ACTIVATE_SUCCESS = "Successfully activated account."
ME_SUCCESS = "Successfully fetched user info."
GROUP_NOT_FOUND = "Group not found"
GROUP_FOUND = "Group found"

# Token Errors
TOKEN_EXPIRED = "The token has expired."
TOKEN_NOT_FRESH = "The token is not fresh. Please use a fresh token."
INVALID_TOKEN = "Invalid token. Signature verification failed."
TOKEN_REVOKED = "The token has been revoked."
MISSING_TOKEN = "Request does not contain an access token."

# User Account Messages
USER_NOT_FOUND = "User not found."
USER_ALREADY_EXISTS = "A user with that username or email already exists."
USER_ACTIVATED = "Account for {} activated successfully!"
USER_ALREADY_ACTIVATED = "User is already activated."
ACTIVATION_EMAIL_SENT = "Activation email sent successfully."
ACTIVATION_EMAIL_RESENT = "Activation email resent successfully."

# Password Management Messages
PASSWORD_CHANGED_SUCCESS = "Password changed successfully."
PASSWORD_RESET_SUCCESS = "Password reset successfully."
PASSWORD_RESET_EMAIL_SENT = "Password reset email sent successfully."
INCORRECT_OLD_PASSWORD = "Incorrect old password."

# Validation Errors
VALIDATION_ERROR = "Validation Error"
MISSING_FIELD_ERROR = "Missing required field: {}."
NON_NULL_ERROR = "Field cannot be null: {}."
INVALID_FORMAT = "Invalid format for field {}. Expected a valid {}."
INVALID_OR_EXPIRED_TOKEN = "Invalid or expired token."

# General Errors
INTERNAL_SERVER_ERROR = "An unexpected error occurred. Please try again later."
BAD_REQUEST = "Invalid request parameters."
PERMISSION_DENIED = "Permission denied. Missing required roles."
NO_DEFAULT_ROLE = "No default role assigned."

# Limiter Errors
TOO_MANY_REQUEST = (
    "You are sending requests too quickly. Please wait before trying again."
)

# Invite Messages
INVITE_KEY_NOT_FOUND = "Invite key not found."
INVALID_INVITE_KEY = "Invalid or expired invite key."
INVITE_KEY_DELETED = "Invite key deleted successfully."
GENERATE_INVITE_KEY_ERROR = "Failed to generate a unique invite key."

# User Messages
USER_DELETED = "User deleted successfully."

# RBAC
UNAUTHORIZED_ACCESS = "You do not have permission to access this resource."

# File Management Messages
NO_FILE_UPLOADED = "No file uploaded"
FILE_UPLOADED_SUCESS = "File uploaded successfully"
