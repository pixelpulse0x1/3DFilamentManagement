from flask import Blueprint

tools_bp = Blueprint("tools", __name__)

from modules.tools import routes  # noqa
