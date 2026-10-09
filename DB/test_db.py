from DB.database import engine
import DB.models as models

try:
    # Próba nawiązania połączenia z bazą
    connection = engine.connect()
    print("Połączenie z bazą danych zakończone sukcesem! 🚀")
    models.Base.metadata.create_all(bind=engine)
    connection.close()
except Exception as e:
    print("Wystąpił błąd podczas łączenia z bazą:")
    print(e)


