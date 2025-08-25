DB_USER = "root"
DB_PASSWORD = "1234"
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_NAME = "iot_project"

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
