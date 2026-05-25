from flask import Blueprint

filaments_bp = Blueprint("filaments", __name__)

from modules.filaments import routes  # noqa: E402, F401
