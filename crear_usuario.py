# crear_usuario.py
import bcrypt
from database import Database

def registrar_usuario(usuario, password_plana):
    db = Database()
    
    # Generamos la sal y encriptamos la contraseña
    sal = bcrypt.gensalt()
    password_encriptada = bcrypt.hashpw(password_plana.encode('utf-8'), sal)
    
    # Insertamos en tu tabla 'users'
    query = "INSERT INTO users (usuario, password) VALUES (%s, %s)"
    # Guardamos el hash como string en la DB
    params = (usuario, password_encriptada.decode('utf-8')) 
    
    filas_afectadas = db.execute_non_query(query, params)
    if filas_afectadas > 0:
        print(f"¡Usuario '{usuario}' creado con éxito!")
    else:
        print("No se pudo crear el usuario.")

if __name__ == "__main__":
    # Cambiá esto por el usuario y clave que quieras para tus pruebas
    registrar_usuario("juan", "juan")