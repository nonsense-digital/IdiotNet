import datetime

from models.post import Post
from routes import routes
from models.permissions import Role, PunishmentType
from models.auth_token import Token

class Client:
    # --- CONSTRUCTORS ---
    # Creates a client object.
    # Attempts to read a pre-existing client record and return the object
    # If one doesn't exist yet, create a new one and return the object
    def __init__(self, connection, ip:str):
        # define fields
        self.__punishment_reason__ = None
        self.__punishment_expiration__ = None
        self.__punishment_status__ = None
        self.__last_accessed__ = None
        self.ip = ip
        self.connection = connection
        try:
            self.update_values()
        except ValueError:
            # client hasn't been added yet, so add it now
            # and also get the data
            cursor = self.connection.cursor()
            cursor.execute("INSERT INTO clients (ip_address) VALUES (%s)", (ip,))
            connection.commit()
            cursor.close()
            self.update_values()

    # finds a list of all active clients, sorted by last access time
    @staticmethod
    def latest(connection, count: int, offset: int = 0):
        cursor = connection.cursor()
        query = "SELECT ip_address FROM clients ORDER BY last_accessed DESC OFFSET %s LIMIT %s"
        cursor.execute(query, (offset, count))
        data = cursor.fetchall()
        clients = []
        for record in data:
            p = Client(connection, record[0])
            clients.append(p)
        return clients

    # finds a list of all punished clients, sorted by punishment expiration
    @staticmethod
    def punished(connection, count: int, offset: int = 0):
        cursor = connection.cursor()
        query = "SELECT ip_address FROM clients WHERE punishment_status != 'none' ORDER BY punishment_expiration DESC OFFSET %s LIMIT %s"
        cursor.execute(query, (offset, count))
        data = cursor.fetchall()
        clients = []
        for record in data:
            p = Client(connection, record[0])
            clients.append(p)
        return clients

    # --- GETTERS AND SETTERS ----
    # When a Client object's atomic properties (punishment reason, rate limits, etc) are called,
    # a getter function retrieves them from its private field.
    # When an atomic value is modified, the change is sent to the database with a setter function.
    # There are also getters that query the database for list objects (posts, followers, etc.) but no setters,
    # as these are read-only.

    def update_values(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM clients WHERE ip_address = %s", (self.ip,))
        result = cursor.fetchall()
        if len(result) > 0:
            result = result[0]
            self.__last_accessed__ = result[1]
            self.__punishment_status__ = PunishmentType(result[2])
            self.__punishment_expiration__ = result[3]
            self.__punishment_reason__ = result[4]
        else:
            raise ValueError("Client doesn't exist")
        cursor.close()

    @property
    def url(self):
        return routes["admin_client"].format(self.ip)

    @property
    def last_accessed(self):
        return self.__last_accessed__

    @last_accessed.setter
    def last_accessed(self, last_accessed:datetime.datetime):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE clients set last_accessed = %s where ip_address = %s",
                       (last_accessed, self.ip))
        self.connection.commit()
        self.__last_accessed__ = last_accessed
        cursor.close()

    @property
    def punishment_status(self):
        return self.__punishment_status__

    @punishment_status.setter
    def punishment_status(self, punishment_status: PunishmentType):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE clients set punishment_status = %s where ip_address = %s", (punishment_status.value, self.ip))
        self.connection.commit()
        self.__punishment_status__ = punishment_status
        cursor.close()

    @property
    def punishment_expiration(self):
        return self.__punishment_expiration__

    @punishment_expiration.setter
    def punishment_expiration(self, punishment_expiration: datetime.datetime):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE clients set punishment_expiration = %s where ip_address = %s",
                       (punishment_expiration, self.ip))
        self.connection.commit()
        self.__punishment_expiration__ = punishment_expiration
        cursor.close()

    @property
    def punishment_reason(self) -> str:
        return self.__punishment_reason__

    @punishment_reason.setter
    def punishment_reason(self, punishment_reason: str) -> None:
        cursor = self.connection.cursor()
        cursor.execute("UPDATE clients set punishment_reason = %s where ip_address = %s",
                       (punishment_reason, self.ip))
        self.connection.commit()
        self.__punishment_reason__ = punishment_reason
        cursor.close()

    # method that gets all active auth tokens (sessions) on the client
    @property
    def tokens(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM tokens WHERE client = %s", (self.ip,))
        result = cursor.fetchall()
        tokens = []
        for token in result:
            tokens.append(Token.read(self.connection, token[0]))
        return tokens

    # method that gets the ids of all active auth tokens (sessions) on the client
    @property
    def token_ids(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM tokens WHERE client = %s", (self.ip,))
        return [x[0] for x in cursor.fetchall()]

    # --- CLIENT-SPECIFIC METHODS ---
    # Specific things you can do with a client object

    # check if the client has an active punishment
    def check_punishment(self, refresh: bool = False) -> PunishmentType:
        # refresh values if requested
        if refresh:
            self.update_values()

        # check if punishment has expired, if so then reset the punishment
        if self.__punishment_expiration__ < datetime.datetime.now():
            self.punishment_status = PunishmentType.NONE

        # return punishment status (if any)
        return self.__punishment_status__