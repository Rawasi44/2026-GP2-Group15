from flask import Flask
from config import Config
from extensions import db, login_manager, mail

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    login_manager.login_view = "auth.login"

    from models.user import User
    from models.event import Event
    from models.search import Search
    from models.rating import Rating
    from models.review import Review
    from models.favorite import Favorite
    from models.calendar_event import CalendarEvent
    from models.recently_viewed import RecentlyViewed

    from routes.auth import auth_bp
    from routes.events import events_bp
    from routes.admin import admin_bp
    from routes.favorites import favorites_bp
    from routes.personal_calendar import calendar_bp
    from routes.recently_viewed import recently_viewed_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(favorites_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(recently_viewed_bp)

    with app.app_context():
        db.create_all()

        from services.data_loader import load_events_to_database
        load_events_to_database()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
