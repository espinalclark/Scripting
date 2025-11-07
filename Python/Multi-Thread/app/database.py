# database.py
import mariadb

CONFIG = {
    "user": "root",
    "password": "clark",
    "host": "localhost",
    "port": 3306,
    "database": "Multi_Thread"
}

def get_connection():
    try:
        return mariadb.connect(**CONFIG)
    except mariadb.Error as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
        return None

# -------------------------------
# 🔐 LOGIN Y REGISTRO DE USUARIO
# -------------------------------
def validar_login(username, password):
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return bool(result and result[0] == password)

def registrar_usuario(username, password):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        print(f"✅ Usuario '{username}' registrado correctamente.")
        return True
    except mariadb.Error as e:
        print(f"❌ Error al registrar usuario: {e}")
        return False
    finally:
        conn.close()

# --------------------------------
# 💾 REGISTRO E HISTORIAL DESCARGAS
# --------------------------------
def obtener_user_id(username):
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def registrar_descarga(username, file_name, file_url):
    conn = get_connection()
    if not conn:
        return False
    try:
        user_id = obtener_user_id(username)
        if not user_id:
            print("❌ No se encontró el usuario.")
            return False
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO downloads (user_id, file_name, url, status)
            VALUES (?, ?, ?, 'Completado')
        """, (user_id, file_name, file_url))
        conn.commit()
        print(f"💾 Descarga registrada para {username}: {file_name}")
        return True
    except mariadb.Error as e:
        print(f"❌ Error al registrar descarga: {e}")
        return False
    finally:
        conn.close()

def obtener_historial(username):
    conn = get_connection()
    if not conn:
        return []
    try:
        user_id = obtener_user_id(username)
        if not user_id:
            return []
        cursor = conn.cursor()
        # Ajuste: si no existe 'timestamp', eliminarlo o reemplazarlo por status
        cursor.execute("""
            SELECT file_name, url, status
            FROM downloads
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,))
        return cursor.fetchall()
    except mariadb.Error as e:
        print(f"❌ Error al obtener historial: {e}")
        return []
    finally:
        conn.close()

