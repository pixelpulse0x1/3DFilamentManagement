from flask import Blueprint

channels_bp = Blueprint("channels", __name__)

from modules.channels import routes  # noqa: E402, F401
