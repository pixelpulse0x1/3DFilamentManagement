from flask import Blueprint

brands_bp = Blueprint("brands", __name__)

from modules.brands import routes  # noqa: E402, F401
