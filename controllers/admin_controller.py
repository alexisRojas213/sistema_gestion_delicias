from conexion import crear_conexion
from datetime import datetime, timedelta # IMPORTADO

"""Toppings"""

def estatus_topings():
    conexion = crear_conexion()
    if not conexion:
        return []

    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT id_top, nombre, habilitado FROM topings") 
        resultado = cursor.fetchall()
        conexion.close()
        return resultado
    except Exception as e:
        print(f"Error al obtener productos: {e}")
        return []

def actualizar_estatus_topping(id_topping, nuevo_estado):
    conexion = crear_conexion()
    if not conexion:
        return False

    try:
        cursor = conexion.cursor()
        # cambia el si/no a 0/1 
        estado_str = 'si' if nuevo_estado == 1 else 'no'
        
        sql = "UPDATE topings SET habilitado = %s WHERE id_top = %s"
        cursor.execute(sql, (estado_str, id_topping))
        conexion.commit() 
        conexion.close()
        print(f"Topping ID {id_topping} actualizado a {estado_str}")
        return True
    except Exception as e:
        print(f"Error al actualizar topping: {e}")
        return False

def agregar_nuevo_topping(nombre_topping):
    conexion = crear_conexion()
    if not conexion:
        return False

    try:
        cursor = conexion.cursor()
        check_top= "SELECT COUNT(*) FROM topings WHERE nombre = %s"
        cursor.execute(check_top, (nombre_topping,))
        registrado = cursor.fetchone()[0]
        
        if registrado > 0:
            print(f"Error: El topping '{nombre_topping}' ya existe.")
            conexion.close()
            return "DUPLICADO"
        else:
            sql = "INSERT INTO topings (nombre, habilitado) VALUES (%s, %s)"
            cursor.execute(sql, (nombre_topping, 'si'))
            conexion.commit()
            conexion.close()
            return True
    except Exception as e:
        print(f"Error al insertar topping: {e}")
        return False

def eliminar_topping_bd(id_topping):
    conexion = crear_conexion()
    if not conexion:
        return False

    try:
        cursor = conexion.cursor()
        sql = "DELETE FROM topings WHERE id_top = %s"
        cursor.execute(sql, (id_topping,)) 
        conexion.commit()
        conexion.close()
        return True
    except Exception as e:
        print(f"Error al eliminar topping: {e}")
        return False

def actualizar_nombre_topping(id_top, nuevo_nombre):
    conexion = crear_conexion()
    if not conexion:
        return False
        
    try:
        cursor = conexion.cursor()
        sql = "UPDATE topings SET nombre = %s WHERE id_top = %s"
        cursor.execute(sql, (nuevo_nombre, id_top))
        conexion.commit()
        conexion.close()
        return True
    except Exception as e:
        print(f"Error al actualizar nombre: {e}")
        return False

"""Productos"""

def mostrar_productos():
    conexion = crear_conexion()
    if not conexion:
        return []

    try:
        cursor = conexion.cursor()
        sql = "SELECT nombre, descripcion, precio, cant_top FROM productos"
        cursor.execute(sql) 
        resultado = cursor.fetchall()
        conexion.close()
        return resultado
    except Exception as e:
        print(f"Error al obtener productos: {e}")
        return []

def obtener_productos_con_id():
    """Obtiene todos los productos con su ID, nombre, descripcion, precio, cant_top y categoria."""
    conexion = crear_conexion()
    if not conexion:
        return []

    try:
        cursor = conexion.cursor()
        sql = "SELECT id_producto, nombre, descripcion, precio, cant_top, id_categoria FROM productos"
        cursor.execute(sql) 
        resultado = cursor.fetchall()
        conexion.close()
        return resultado
    except Exception as e:
        print(f"Error al obtener productos con ID: {e}")
        return []

def agregar_nuevo_producto(nombre, descripcion, precio, cant_top, categoria):
    nombre=nombre.upper()
    conexion = crear_conexion()
    if not conexion:
        return False

    try:
        cursor = conexion.cursor()
        check_prod = "SELECT COUNT(*) FROM productos WHERE nombre = %s"
        cursor.execute(check_prod, (nombre,))
        registrado = cursor.fetchone()[0]
        
        if registrado > 0:
            conexion.close()
            return "DUPLICADO"

        sql_id = "SELECT id_categorias FROM categorias_productos WHERE nombre_categoria = %s"
        cursor.execute(sql_id, (categoria,))
        id_categoria_result = cursor.fetchone()
        
        if not id_categoria_result:
            print(f"Error: Categoría '{categoria}' no encontrada.")
            conexion.close()
            return False
        id_categoria = id_categoria_result[0]
        sql = "INSERT INTO productos (nombre, descripcion, precio, cant_top, id_categoria) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql, (nombre, descripcion, precio, cant_top, id_categoria)) 
        conexion.commit()
        conexion.close()
        return True
    except Exception as e:
        print(f"Error al insertar producto: {e}")
        return False

def eliminar_producto_bd(id_prod):
    conexion = crear_conexion()
    if not conexion:
        return False

    try:
        cursor = conexion.cursor()
        # CORRECCIÓN: Usar id_producto en lugar de id_prod
        sql = "DELETE FROM productos WHERE id_producto = %s" 
        cursor.execute(sql, (id_prod,)) 
        conexion.commit()
        conexion.close()
        return True
    except Exception as e:
        print(f"Error al eliminar producto: {e}")
        return False

def actualizar_producto(id_prod, nombre, descripcion, precio, cant_top, categoria_nombre):
    
    conexion = crear_conexion()
    if not conexion:
        return False
        
    try:
        cursor = conexion.cursor()
        check_prod = "SELECT COUNT(*) FROM productos WHERE nombre = %s AND id_producto != %s"
        cursor.execute(check_prod, (nombre, id_prod))
        registrado = cursor.fetchone()[0]
        
        if registrado > 0:
            conexion.close()
            return "DUPLICADO" 

        sql_id = "SELECT id_categorias FROM categorias_productos WHERE nombre_categoria = %s"
        cursor.execute(sql_id, (categoria_nombre,))
        id_categoria_result = cursor.fetchone()
        
        if not id_categoria_result:
            print(f"Error: Categoría '{categoria_nombre}' no encontrada.")
            conexion.close()
            return False
            
        id_categoria = id_categoria_result[0]
        
        sql = """
            UPDATE productos 
            SET nombre = %s, descripcion = %s, precio = %s, cant_top = %s, id_categoria = %s
            WHERE id_producto = %s
        """
        cursor.execute(sql, (nombre, descripcion, precio, cant_top, id_categoria, id_prod))
        
        conexion.commit()
        conexion.close()
        return True
    except Exception as e:
        print(f"Error al actualizar producto: {e}")
        return False
        
""" Reportes """

def obtener_reporte_ventas_agrupadas():
    """
    Obtiene los reportes consultando las tablas Maestro y Detalle.
    Agrupa por id_maestro.
    """
    conexion = crear_conexion()
    if not conexion:
        return []

    try:
        cursor = conexion.cursor(dictionary=True)
        sql_maestro = """
        SELECT id_maestro, total_final, fecha, id_vendedor
        FROM ventas_maestro 
        ORDER BY fecha DESC
        """
        cursor.execute(sql_maestro)
        maestros = cursor.fetchall()

        reporte_final = []

        for maestro in maestros:
            sql_detalle = """
            SELECT id_detalle, cantidad, descripcion_detalle, precio_unitario
            FROM ventas_detalle 
            WHERE id_maestro = %s
            """
            cursor.execute(sql_detalle, (maestro['id_maestro'],))
            detalles = cursor.fetchall()
            
            # Preparar la estructura para la vista (Solo fecha, como pediste)
            fecha = maestro['fecha'].strftime('%d/%m/%Y')
            
            transaccion = {
                'id_ticket': maestro['id_maestro'],
                'fecha': fecha, 
                'total_final': maestro['total_final'],
                'id_vendedor': maestro['id_vendedor'],
                'detalles': []
            }
            
            for detalle in detalles:
                # Calculamos el total de la línea
                total_linea = detalle['cantidad'] * detalle['precio_unitario']
                
                transaccion['detalles'].append({
                    'id_linea': detalle['id_detalle'],
                    # descripcion_detalle ya incluye el topping
                    'descripcion': f"{detalle['cantidad']}x {detalle['descripcion_detalle']}", 
                    'total_linea': total_linea
                })
            
            reporte_final.append(transaccion)

        conexion.close()
        return reporte_final

    except Exception as e:
        print(f"Error al obtener reporte de ventas (Maestro-Detalle): {e}")
        return []     
        
def obtener_resumen_ventas():
    """Calcula el total de ventas y el número total de transacciones (Histórico)."""
    conexion = crear_conexion()
    if not conexion: return {'total_ventas': 0.0, 'total_transacciones': 0}
    
    try:
        cursor = conexion.cursor(dictionary=True)
        # Suma total de todas las ventas
        sql_total = "SELECT SUM(total_final) as total_ventas, COUNT(id_maestro) as total_transacciones FROM ventas_maestro"
        cursor.execute(sql_total)
        resumen = cursor.fetchone()
        
        conexion.close()
        
        return {
            'total_ventas': resumen['total_ventas'] if resumen['total_ventas'] is not None else 0.0,
            'total_transacciones': resumen['total_transacciones'] if resumen['total_transacciones'] is not None else 0
        }
    except Exception as e:
        print(f"Error al obtener resumen de ventas: {e}")
        return {'total_ventas': 0.0, 'total_transacciones': 0}

def obtener_producto_mas_vendido_semana():
    """Obtiene el producto con mayor cantidad vendida en los últimos 7 días."""
    conexion = crear_conexion()
    if not conexion: return None
    
    try:
        cursor = conexion.cursor(dictionary=True)
        # Fecha de hace 7 días
        hace_una_semana = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        
        sql_mas_vendido = """
            SELECT 
                vd.descripcion_detalle, 
                SUM(vd.cantidad) as cantidad_total
            FROM 
                ventas_detalle vd
            JOIN 
                ventas_maestro vm ON vd.id_maestro = vm.id_maestro
            WHERE 
                vm.fecha >= %s
            GROUP BY 
                vd.descripcion_detalle
            ORDER BY 
                cantidad_total DESC
            LIMIT 1
        """
        cursor.execute(sql_mas_vendido, (hace_una_semana,))
        resultado = cursor.fetchone()
        
        conexion.close()
        return resultado
        
    except Exception as e:
        print(f"Error al obtener producto más vendido: {e}")
        return None