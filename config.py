class Config:
    SECRET_KEY = "afaq-secret-key"

    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:root@localhost:3306/afaq_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": 280
}
   
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = "afaq.riyadhevents@gmail.com"
    MAIL_PASSWORD = ""
    MAIL_DEFAULT_SENDER = "afaq.riyadhevents@gmail.com"
