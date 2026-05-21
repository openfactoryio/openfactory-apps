import os
from pathlib import Path
from openfactory.apps import OpenFactoryFlaskApp
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from .config import Config
from .db import db, ksql
from .app.state_stream import init_state_streaming_thread
from .app.conditions_stream import init_conditions_streaming_thread


class CNC_HMI(OpenFactoryFlaskApp):
    """
    CNC HMI WebApp
    """

    def init_db(self, app):
        """ Setup database and get cnc UUID """
        with app.app_context():
            # import models that will be created by db.create_all()
            from .models.cncsettings import CNCSettings
            from .app.auth.models.users import User
            db.create_all()

            # setup default users
            if User.query.count() == 0:
                default_users = [
                    User(username="admin", fullname="Administrator", role="admin"),
                    User(username="operator", fullname="Operator", role="operator"),
                ]
                default_users[0].set_password("admin123")
                default_users[1].set_password("operator123")

                db.session.add_all(default_users)
                db.session.commit()

            # setup default settings
            if CNCSettings.query.count() == 0:
                default_settings = [
                    CNCSettings(key='probe_speed', value='100', description='Probe speed in mm/min'),
                    CNCSettings(key='probe_height', value='12.7', description='Probe height in mm'),
                    CNCSettings(key='z_rise', value='15', description='Z rise in mm'),
                ]
                db.session.add_all(default_settings)
                db.session.commit()

            cnc_uuid = CNCSettings.query.filter_by(key="cnc_uuid").first()
            if cnc_uuid:
                app.cnc_uuid = cnc_uuid.value
            else:
                app.cnc_uuid = None

    def create_flask_app(self):
        """ Flask app factory """
        # setup flask instance path
        instance_storage = self.storage.get("instance")
        if instance_storage is None:
            instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
        else:
            instance_path = instance_storage.root

        app = Flask(__name__,
                    instance_path=instance_path)
        app.config.from_object(Config)

        # setup CSRF pretection
        CSRFProtect(app)

        # setup instance folder
        Path(instance_path).mkdir(parents=True, exist_ok=True)

        # initialize db
        db.init_app(app)
        self.init_db(app)

        # CNC_UUID
        @app.context_processor
        def inject_cnc_uuid():
            """ Inject cnc_uuid into the template context """
            return {'cnc_uuid': app.cnc_uuid}

        # streaming endpoints
        init_state_streaming_thread(app, self.ksql)
        init_conditions_streaming_thread(app, self.ksql)

        # current loaded nc-file
        app.nc_file = None

        # admin app
        from .app.admin import create_bp as create_admin_bp
        admin_app = create_admin_bp(app, db)

        # authentification blueprint
        from .app.auth import create_bp as create_auth_bp
        create_auth_bp(app, admin_app)

        # main blueprint
        from .app.main import create_bp as create_main_bp
        create_main_bp(app)

        # cnc blueprint
        from .app.cnc import create_bp as create_cnc_bp
        create_cnc_bp(app)

        # settings blueprint
        from .app.settings import create_bp as create_settings_bp
        create_settings_bp(app)

        # file manager blueprint
        from .app.file_manager import create_bp as create_file_manager_bp
        create_file_manager_bp(app)

        return app


app = CNC_HMI(
    ksqlClient=ksql,
    bootstrap_servers=os.getenv("KAFKA_BROKER", "localhost:9092"),
    loglevel=os.getenv("LOG_LEVEL", "INFO")
)

app.run()
