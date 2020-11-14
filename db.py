import psycopg2
import os


class DB:
    def __init__(self):
        try:
            self.CONNECTION = psycopg2.connect(user = os.getenv("DB_USER"),
                                        password = os.getenv("DB_PASS"),
                                        host = os.getenv("DB_HOST"),
                                        port = os.getenv("DB_PORT"),
                                        database = os.getenv("DB_NAME"))

            self.CURSOR = self.CONNECTION.cursor()

            # Print PostgreSQL version
            self.CURSOR.execute("SELECT version();")
            record = self.CURSOR.fetchone()
            print("You are connected to - ", record,"\n")

        except (Exception, psycopg2.Error) as error :
            print ("Error while connecting to PostgreSQL:", error)

    
    """Cleanup"""
    def __exit__(self):
        if(self.CONNECTION):
            self.CURSOR.close()
            self.CONNECTION.close()
            print("PostgreSQL connection is closed")
    