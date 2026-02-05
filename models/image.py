import psycopg2
from flask import request, redirect, url_for, flash, Flask
from psycopg2._psycopg import cursor
from models.userref import UserRef
from werkzeug.utils import secure_filename
import os

ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'gif', 'png']
app = Flask(__name__)
app.config['uploads'] = 'uploads'

class Image:
    def __init__(self, image_id):
        self.image_id = image_id
        self.connection = None
        self.__title__ = None
        self.__author__ = None
        self.__post__ = None

    #creates values for post id and other things associated with the image and database
    @staticmethod
    def create(connection, file, author:int, post:int):
        extension = file.filename.rsplit('.', 1)[1].lower()
        if file and '.' in file.filename and extension in ALLOWED_EXTENSIONS:
            filename = secure_filename(file.filename)
            query = "INSERT INTO images (title, author, post) VALUES (%s, %s, %s) RETURNING id"
            cursor = connection.cursor()
            data = (file.filename, author, post)
            cursor.execute(query, data)
            connection.commit()
            id = cursor.fetchone()[0]
            file.save(os.path.join(app.config['uploads'], str(id) + '.' + extension))
        else:
            raise ValueError("Invalid file type")


        #create a new image object
        image = Image(id)
        image.connection = connection
        image.__title__ = file.filename
        image.__author__ = author
        image.__post__ = post
        cursor.close()
        return image

    @staticmethod
    def read(connection, image_id:int):
        try:
            i = Image(image_id)
            i.connection = connection
            i.update_values()
            return i
        except NameError:
            raise NameError("Image not found")
        except TypeError:
            raise NameError("Image not found")

    def update_values(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * from images WHERE id = %s", (self.image_id,))
        try:
            result = cursor.fetchone()
            self.__title__ = result[1]
            self.__author__ = UserRef(self.connection, result[2])
            self.__post__ = result[3]
        except IndexError:
            raise NameError("Image not found")

    @property
    def title(self):
        return self.__title__
    @property
    def file_ext(self):
        return self.__title__.rsplit('.', 1)[1].lower()
    @property
    def author(self):
        return self.__author__
    @property
    def post(self):
        return self.__post__




