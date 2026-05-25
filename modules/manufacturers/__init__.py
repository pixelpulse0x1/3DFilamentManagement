from flask import Blueprint

manufacturers_bp = Blueprint("manufacturers", __name__)

from modules.manufacturers import routes  # noqa: E402, F401
