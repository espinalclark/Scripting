import mariadb

# Datos de conexión — ajusta si tus credenciales son distintas
config = {
    "user": "root",
    "password": "clark",
    "host": "localhost",
    "port": 3306,
    "database": "Multi_Thread"
}

try:
    conn = mariadb.connect(**config)
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES;")
    tablas = cursor.fetchall()

    print("✅ Conexión a la base de datos exitosa!")
    print("Tablas en la base de datos:")
    for t in tablas:
        print("-", t[0])

except mariadb.Error as e:
    print("❌ Error al conectar a MariaDB:", e)

finally:
    if 'conn' in locals():
        conn.close()

