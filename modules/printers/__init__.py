from flask import Blueprint

printers_bp = Blueprint("printers", __name__)

from modules.printers import routes  # noqa: E402, F401
