from flask import Blueprint

images_bp = Blueprint("images", __name__)

from modules.images import routes  # noqa: E402, F401
