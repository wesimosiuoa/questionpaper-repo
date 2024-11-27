class Config: 
    SQLALCHEMY_DATABASE_URI = 'mysql://root:@localhost/ntheng'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = './app/uploads/'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024