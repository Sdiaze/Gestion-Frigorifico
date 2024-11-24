# conexion_bd.py

import pyodbc
import hashlib


# Función para conectar a la base de datos
def conectar_bd():
    """
    Establece una conexión con la base de datos.
    """
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=DESKTOP-C1J5V6J;'
            'DATABASE=Prueba1;'
            'Trusted_Connection=yes;'
        )
        return conn
    except pyodbc.Error as e:
        raise ConnectionError(f"Error al conectar a la base de datos: {e}")


def crear_usuario(username, password):
    """
    Crea un nuevo usuario con credenciales encriptadas.
    Retorna True si el usuario fue creado exitosamente, False en caso de error.
    """
    conn = conectar_bd()
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        cursor.execute(
            "INSERT INTO Usuarios (username, password) VALUES (?, ?)",
            (username, hashed_password)
        )
        conn.commit()
        return True
    except pyodbc.IntegrityError:
        # Esto ocurre si el usuario ya existe
        return False
    except pyodbc.Error as e:
        # Manejo de errores generales
        print(f"Error al crear usuario: {e}")
        return False
    finally:
        conn.close()



def verificar_credenciales(username, password):
    """
    Verifica las credenciales de un usuario.
    """
    conn = conectar_bd()
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        cursor.execute(
            "SELECT * FROM Usuarios WHERE username = ? AND password = ?",
            (username, hashed_password)
        )
        usuario = cursor.fetchone()
        return usuario is not None
    finally:
        conn.close()


# Funciones relacionadas con ubicaciones y pallets
def asignar_ubicacion(pallet_id, tipo_almacen, piso, rack, letra):
    """
    Asigna una ubicación a un pallet en el almacén.
    """
    conn = conectar_bd()
    cursor = conn.cursor()

    try:
        # Validar que el pallet ID sea un entero
        pallet_id = int(pallet_id)

        # Verificar si el pallet existe
        cursor.execute("SELECT 1 FROM pallets WHERE id_pallet = ?", (pallet_id,))
        if cursor.fetchone() is None:
            return f"Error: El Pallet con ID {pallet_id} no existe."

        # Verificar si el pallet ya tiene una ubicación asignada
        cursor.execute(
            "SELECT ubicacion_key FROM ubicaciones WHERE id_pallet_asignado = ?",
            (pallet_id,)
        )
        ubicacion_actual = cursor.fetchone()
        if ubicacion_actual:
            return f"Error: El Pallet ya tiene una ubicación asignada: {ubicacion_actual[0]}."

        # Asignar ubicación mediante procedimientos almacenados
        cursor.execute(
            "EXEC reasignar_pallet @piso=?, @rack=?, @letra=?, @id_pallet=?",
            (piso, rack, letra, pallet_id)
        )
        conn.commit()

        cursor.execute("EXEC actualizar_status_ubicacion")
        conn.commit()

        return f"Pallet {pallet_id} asignado a la ubicación {tipo_almacen}, {piso}, {rack}, {letra}."
    except ValueError:
        return "Error: El ID del pallet debe ser un número entero."
    except pyodbc.Error as e:
        return f"Error al asignar ubicación: {e}"
    finally:
        conn.close()


def liberar_ubicacion(pallet_id):
    """
    Libera una ubicación ocupada por un pallet y reorganiza posiciones.
    """
    conn = conectar_bd()
    cursor = conn.cursor()

    try:
        # Validar que el pallet ID sea un entero
        pallet_id = int(pallet_id)

        # Verificar si el pallet existe
        cursor.execute("SELECT 1 FROM pallets WHERE id_pallet = ?", (pallet_id,))
        if cursor.fetchone() is None:
            return f"Error: El Pallet con ID {pallet_id} no existe."

        # Verificar si el pallet tiene una ubicación asignada
        cursor.execute(
            "SELECT id_ubicacion, posicion_pallet FROM asignacion_pallet WHERE id_pallet = ?",
            (pallet_id,)
        )
        result = cursor.fetchone()
        if result is None:
            return f"Error: El Pallet con ID {pallet_id} no está asignado a ninguna ubicación."

        id_ubicacion, posicion_actual = result

        # Verificar si el pallet está en la posición 1
        if posicion_actual != 1:
            return "Error: Solo se puede retirar el pallet de la posición 1."

        # Retirar el pallet
        cursor.execute("EXEC retirar_pallet @id_pallet = ?", (pallet_id,))
        conn.commit()

        cursor.execute("EXEC actualizar_status_ubicacion")
        conn.commit()

        return f"Ubicación liberada y reorganizada para el Pallet {pallet_id}."
    except ValueError:
        return "Error: El ID del pallet debe ser un número entero."
    except pyodbc.Error as e:
        conn.rollback()
        return f"Error al liberar ubicación: {e}"
    finally:
        conn.close()


def obtener_todas_las_posiciones():
    """
    Recupera todas las posiciones del almacén, incluyendo id_pallet_asignado, descripción y fecha de ingreso.
    """
    conn = conectar_bd()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT 
                u.tipo_almacen, 
                u.piso, 
                u.rack, 
                u.letra, 
                u.posicion_pallet, 
                u.status_ubicacion, 
                u.id_pallet_asignado,
                p.descripcion,
                p.fecha_ingreso
            FROM ubicaciones u
            LEFT JOIN pallets p ON u.id_pallet_asignado = p.id_pallet
        """)
        return cursor.fetchall()
    finally:
        conn.close()



def obtener_opciones_campo():
    """
    Recupera las opciones únicas de cada campo desde la base de datos.
    """
    conn = conectar_bd()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT DISTINCT tipo_almacen FROM ubicaciones")
        tipos_almacen = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT piso FROM ubicaciones")
        pisos = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT rack FROM ubicaciones")
        racks = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT letra FROM ubicaciones")
        letras = [row[0] for row in cursor.fetchall()]

        return tipos_almacen, pisos, racks, letras
    finally:
        conn.close()


def obtener_opciones_disponibles(tipo_almacen=None, piso=None, rack=None, letra=None):
    """
    Recupera las opciones disponibles basadas en filtros de ubicación.
    """
    conn = conectar_bd()
    cursor = conn.cursor()

    try:
        query = """
            SELECT DISTINCT tipo_almacen, piso, rack, letra
            FROM ubicaciones
            WHERE status_ubicacion = 'Libre'
        """
        conditions = []
        params = []

        if tipo_almacen:
            conditions.append("tipo_almacen = ?")
            params.append(tipo_almacen)
        if piso:
            conditions.append("piso = ?")
            params.append(piso)
        if rack:
            conditions.append("rack = ?")
            params.append(rack)
        if letra:
            conditions.append("letra = ?")
            params.append(letra)

        if conditions:
            query += " AND " + " AND ".join(conditions)

        query += " ORDER BY tipo_almacen, piso, rack, letra"

        cursor.execute(query, params)
        opciones_libres = cursor.fetchall()

        # Organizar los datos
        tipos_almacen = sorted(set(row[0] for row in opciones_libres))
        pisos = sorted(set(row[1] for row in opciones_libres if row[1]))
        racks = sorted(set(row[2] for row in opciones_libres if row[2]))
        letras = sorted(set(row[3] for row in opciones_libres if row[3]))

        return tipos_almacen, pisos, racks, letras
    finally:
        conn.close()

# Función para cerrar la conexión a la base de datos
def cerrar_conexion_bd(conn):
    """
    Cierra una conexión a la base de datos.
    Si `conn` es None, no realiza ninguna acción.
    """
    try:
        if conn is not None:
            conn.close()
            print("Conexión a la base de datos cerrada correctamente.")
    except Exception as e:
        print(f"Error al cerrar la conexión a la base de datos: {e}")

