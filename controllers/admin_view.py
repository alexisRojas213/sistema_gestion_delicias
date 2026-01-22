import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog 
from admin_controller import (actualizar_estatus_topping, estatus_topings, agregar_nuevo_topping, eliminar_topping_bd,
                              actualizar_nombre_topping, mostrar_productos, agregar_nuevo_producto, obtener_productos_con_id,
                              eliminar_producto_bd, actualizar_producto, obtener_reporte_ventas_agrupadas,
                              obtener_resumen_ventas, obtener_producto_mas_vendido_semana)
from seller_controller import obtener_categorias
import seller_view
import re # para validación
import pandas as pd

# colores (Paleta modernizada)
COLOR_SIDEBAR = "#F8F4E8"      # Blanco cremoso
COLOR_MAIN_BG = "#EAE4D9"      # Fondo principal
COLOR_BTN_SIDEBAR = "#EAE4D9"  
COLOR_BTN_ACTIVE = "#DCD6C7"   # Resaltado
COLOR_TEXT = "#4A403F"         # Texto oscuro
COLOR_BTN_GREEN = "#3CB371"    # Verde Suave (Medium Sea Green)
COLOR_BTN_RED = "#D24F4F"      # Rojo Suave
COLOR_BTN_BROWN = "#6A5340"    # Marrón cálido
COLOR_ACCENT = "#E5A586"       # Color para botones de acción secundarios (similar al seller)


class adminapp: 
    def __init__(self, root):
        self.root = root
        self.root.title("Panel de Administrador - Delicias & Coffee")
        self.root.geometry("1000x600")
        self.root.state('zoomed') 
        self.root.resizable(True, True)
        self.root.configure(bg=COLOR_MAIN_BG)
        
        # registro de validaciones
        self.vcmd_precio = (self.root.register(self.validar_decimal), '%P')
        self.vcmd_entero = (self.root.register(self.validar_entero), '%P')
        # NUEVA VALIDACIÓN: Texto sin números
        self.vcmd_texto = (self.root.register(self.validar_texto_sin_numeros), '%P')
       
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)  

        # Aplicar tema ttk moderno (Para Treeview, OptionMenu, etc.)
        style = ttk.Style()
        try:
             style.theme_use('adapta') 
        except Exception:
             style.theme_use('clam')

        # menu izquierda
        self.sidebar_frame = tk.Frame(self.root, bg=COLOR_SIDEBAR, width=250)
        self.sidebar_frame.grid(row=0, column=0, sticky="ns")
        self.sidebar_frame.grid_propagate(False)

        self._crear_widgets_sidebar()

        # area de contenido
        self.main_frame = tk.Frame(self.root, bg=COLOR_MAIN_BG)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # inventario por defecto
        self.mostrar_inventario()
    
    # validaciones
    def validar_decimal(self, P):
        """permite solo números y punto decimal."""
        if P == "": return True 
        return re.match(r'^\d*\.?\d*$', P) is not None

    def validar_entero(self, P):
        """permite solo enteros."""
        if P == "": return True 
        return P.isdigit()
    
    def validar_texto_sin_numeros(self, P):
        """Permite solo texto, rechaza si contiene dígitos numéricos."""
        if P == "": return True # Permitir borrar todo para corregir
        # Retorna False si encuentra algún dígito (0-9) en el texto ingresado
        return not any(char.isdigit() for char in P)

    def _crear_widgets_sidebar(self):     
        # título 
        lbl_logo = tk.Label(self.sidebar_frame, text="Delicias & Coffee\nPanel Admin", 
                            bg=COLOR_SIDEBAR, fg=COLOR_TEXT, font=("Arial", 18, "bold"), pady=40) 
        lbl_logo.pack(fill="x")

        # separador
        ttk.Separator(self.sidebar_frame, orient="horizontal").pack(fill="x", padx=20, pady=10)

        # botones menu
        self.btn_ventas = self.botones_menu("💲 Ventas", self.mostrar_ventas) 
        self.btn_inventario = self.botones_menu("📋 C. Ingredientes", self.mostrar_inventario) 
        self.btn_productos = self.botones_menu("🍰 Productos", self.mostrar_productos)
        self.btn_reportes = self.botones_menu("📄 Reportes", self.mostrar_reportes)

        # salir
        btn_salir = tk.Button(self.sidebar_frame, text="Salir al Punto de Venta", bg=COLOR_BTN_BROWN, fg="white",
                              font=("Arial", 12, "bold"), bd=0, padx=20, pady=15, 
                              command=self.cerrar_y_abrir_vendedor)
        btn_salir.pack(side="bottom", pady=30)

        lbl_admin = tk.Label(self.sidebar_frame, text="Administrador", bg=COLOR_SIDEBAR, 
                             fg="black", font=("Arial", 10, "bold")) 
        lbl_admin.pack(side="bottom", pady=5)

    def cerrar_y_abrir_vendedor(self):
            self.root.destroy()
            root_seller = tk.Tk()
            seller_view.sellerApp(root_seller) 
            root_seller.mainloop()
        

    def botones_menu(self, texto, comando):
        """helper para crear botones con estilo plano"""
        btn = tk.Button(self.sidebar_frame, text=texto, anchor="w",
                        bg=COLOR_SIDEBAR, fg=COLOR_TEXT, bd=0,
                        font=("Arial", 14), padx=25, pady=15, 
                        # Usar highlightthickness para simular borde en activo
                        activebackground=COLOR_BTN_ACTIVE,
                        command=comando)
        btn.pack(fill="x")
        return btn

    def _limpiar_panel_principal(self):
        """limpiar panel"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def _resaltar_boton(self, boton_activo):
        """resaltar botón activo"""
        # resetear: todos con fondo normal (sin highlight)
        self.btn_ventas.config(bg=COLOR_SIDEBAR, highlightthickness=0)
        self.btn_inventario.config(bg=COLOR_SIDEBAR, highlightthickness=0)
        self.btn_productos.config(bg=COLOR_SIDEBAR, highlightthickness=0)
        self.btn_reportes.config(bg=COLOR_SIDEBAR, highlightthickness=0)
        
        # marcar activo
        if boton_activo:
            # Marcar con el fondo activo y un borde sutil para destacar
            boton_activo.config(bg=COLOR_BTN_ACTIVE, highlightbackground=COLOR_TEXT, highlightthickness=1)

    # =========================================================================================
    # FUNCIONALIDAD: EXPORTACIÓN A EXCEL
    # =========================================================================================

    def exportar_a_excel(self, data, sheet_name, filename):
        """Función genérica para guardar datos (lista de diccionarios) a Excel."""
        if not data:
            messagebox.showwarning("Atención", "No hay datos para exportar.")
            return
            
        try:
            # Usar filedialog para que el usuario elija dónde guardar
            filepath = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Archivos Excel", "*.xlsx")],
                initialfile=filename
            )
            
            if not filepath: 
                return
                
            # Crear DataFrame de pandas y exportar
            df = pd.DataFrame(data)
            df.to_excel(filepath, index=False, sheet_name=sheet_name)
            
            messagebox.showinfo("Éxito", f"Datos exportados a:\n{filepath}")
            
        except ImportError:
            messagebox.showerror("Error", "Faltan librerías: Asegúrate de instalar 'pandas' y 'openpyxl' (pip install pandas openpyxl).")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al exportar a Excel: {e}")
            
    # Función específica para aplanar el reporte de ventas agrupadas
    def exportar_reporte_ventas_excel(self, reporte_datos):
        """Prepara los datos de ventas agrupadas para la exportación y la ejecuta."""
        datos_exportar = []
        
        for grupo in reporte_datos:
            # Aplanar la estructura de datos: de Maestro-Detalle a filas simples para Excel
            if not grupo['detalles']:
                datos_exportar.append({
                    'ID Ticket': grupo['id_ticket'],
                    'Fecha': grupo['fecha'],
                    'ID Vendedor': grupo['id_vendedor'],
                    'Producto/Descripción': 'SIN DETALLE',
                    'Cantidad': 0,
                    'Total Linea': 0.00,
                    'Total Venta': grupo['total_final']
                })
                continue

            for detalle in grupo['detalles']:
                # Intenta extraer la cantidad del string "Cantidad x Producto"
                try:
                    cantidad = detalle['descripcion'].split('x')[0].strip()
                    cantidad = int(cantidad) if cantidad.isdigit() else 1
                except:
                    cantidad = 1

                datos_exportar.append({
                    'ID Ticket': grupo['id_ticket'],
                    'Fecha': grupo['fecha'],
                    'ID Vendedor': grupo['id_vendedor'],
                    'Producto/Descripción': detalle['descripcion'],
                    'Cantidad': cantidad,
                    'Total Linea': detalle['total_linea'],
                    'Total Venta': grupo['total_final'] 
                })
                
        self.exportar_a_excel(datos_exportar, "VentasDetalle", "ReporteVentas.xlsx")

    # Función específica para exportar productos (usa obtener_productos_con_id)
    def exportar_productos_excel(self):
        """Obtiene y prepara los datos de productos para exportar."""
        productos = obtener_productos_con_id() 
        categorias_map = {c['id_categorias']: c['nombre_categoria'] for c in obtener_categorias()}
        
        datos_exportar = []
        for id_prod, nombre, descripcion, precio, cant_top, id_cat in productos:
            datos_exportar.append({
                'ID Producto': id_prod,
                'Nombre': nombre,
                'Descripción': descripcion,
                'Precio': precio,
                'Toppings Max': cant_top,
                'Categoría': categorias_map.get(id_cat, 'N/A')
            })
            
        self.exportar_a_excel(datos_exportar, "Productos", "CatalogoProductos.xlsx")
        
    # Función específica para exportar toppings
    def exportar_toppings_excel(self):
        """Obtiene y prepara los datos de toppings para exportar."""
        toppings = estatus_topings()
        datos_exportar = []
        for id_top, nombre, habilitado in toppings:
            datos_exportar.append({
                'ID Topping': id_top,
                'Nombre': nombre,
                'Habilitado (si/no)': habilitado
            })
        self.exportar_a_excel(datos_exportar, "Toppings", "InventarioToppings.xlsx")

    # =========================================================================================

    '''INVENTARIO / TOPPINGS'''

    def mostrar_inventario(self):
        self._limpiar_panel_principal()
        self._resaltar_boton(self.btn_inventario)

        tk.Label(self.main_frame, text="Control de Ingredientes (Toppings)", font=("Arial", 28, "bold"), 
                 bg=COLOR_MAIN_BG, fg=COLOR_TEXT).pack(side="top", pady=(10, 5))

     # botones abajo
        footer_frame = tk.Frame(self.main_frame, bg=COLOR_MAIN_BG)
        footer_frame.pack(side="bottom", fill="x", pady=20, padx=30)
        
        # NUEVO: Exportar Toppings
        tk.Button(footer_frame, text="📥 Exportar a Excel", 
                            bg=COLOR_BTN_GREEN, fg="white", font=("Arial", 12, "bold"), 
                            padx=25, pady=12, bd=0,
                            command=self.exportar_toppings_excel).pack(side="left", padx=(0, 10))

        # agregar
        btn_add = tk.Button(footer_frame, text="➕ Agregar Nuevo", 
                            bg=COLOR_BTN_BROWN, fg="white", font=("Arial", 12, "bold"), 
                            padx=25, pady=12, bd=0,
                            command=self._popup_agregar_topping)
        btn_add.pack(side="right", padx=(10, 0))

        # funciones
        btn_funciones = tk.Button(footer_frame, text="⚙️ Funciones / Eliminar", 
                                  bg=COLOR_ACCENT, fg="white", font=("Arial", 12, "bold"), # Usar ACCENT
                                  padx=25, pady=12, bd=0,
                                  command=self.panel_funciones)
        btn_funciones.pack(side="right")

     # encabezados
        header_frame = tk.Frame(self.main_frame, bg=COLOR_MAIN_BG)
        header_frame.pack(side="top", fill="x", pady=10, padx=40) 
        
        tk.Label(header_frame, text="Ingrediente", bg=COLOR_MAIN_BG, fg=COLOR_TEXT,
                 font=("Arial", 14, "bold")).pack(side="left") 
        
        tk.Label(header_frame, text="Estado", bg=COLOR_MAIN_BG, fg=COLOR_TEXT,
                 font=("Arial", 14, "bold")).pack(side="right", padx=(0, 40)) 

        ttk.Separator(self.main_frame, orient="horizontal").pack(side="top", fill="x", padx=30)

     # scroll 
        container_scroll = tk.Frame(self.main_frame, bg=COLOR_MAIN_BG)
        container_scroll.pack(side="top", fill="both", expand=True, padx=30, pady=5)

        canvas = tk.Canvas(container_scroll, bg=COLOR_MAIN_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container_scroll, orient="vertical", command=canvas.yview)
        
        scrollable_frame = tk.Frame(canvas, bg=COLOR_MAIN_BG)

        # configuración scroll
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def ajustar_ancho(event):
            canvas.itemconfig(window_id, width=event.width)

        canvas.bind("<Configure>", ajustar_ancho)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

     # botones 
        
        def click_boton(btn_widget, var_tk, id_db):
            nuevo_valor = var_tk.get() 

            # actualizar bd
            exito = actualizar_estatus_topping(id_db, nuevo_valor)
            
            if exito:
                if nuevo_valor == 1:
                    btn_widget.config(text="HABILITADO", bg=COLOR_BTN_GREEN, fg="white")
                else:
                    btn_widget.config(text="DESHABILITADO", bg=COLOR_BTN_RED, fg="white")
            else:
                revertido = 0 if nuevo_valor == 1 else 1
                var_tk.set(revertido)
                messagebox.showerror("Error", "No se pudo actualizar la base de datos.")
        items = estatus_topings()

        for id_prod, nombre, habilitado in items:
            valor_inicial = 1 if habilitado == "si" else 0
            var = tk.IntVar(value=valor_inicial)
            
            # fila: Estilo modernizado, borde sutil
            row_frame = tk.Frame(scrollable_frame, bg="#FFF8F0", bd=0, relief=tk.FLAT, highlightbackground=COLOR_BTN_ACTIVE, highlightthickness=1) 
            row_frame.pack(fill="x", pady=5, ipadx=10, ipady=5) 

            # nombre
            tk.Label(row_frame, text=nombre, font=("Arial", 14, "bold"), anchor="w", 
                     bg="#FFF8F0", fg="#5D4037").pack(side="left", padx=10)

            # configuracion botones
            if valor_inicial == 1:
                txt = "HABILITADO"
                col = COLOR_BTN_GREEN
            else:
                txt = "DESHABILITADO"
                col = COLOR_BTN_RED

            # boton estado: plano y sin indicador
            btn = tk.Checkbutton(row_frame, text=txt, variable=var, indicatoron=False,
                                 bg=col, fg="white", selectcolor=COLOR_BTN_GREEN, bd=0,
                                 font=("Arial", 11, "bold"), width=18, cursor="hand2") 
            
            btn.config(command=lambda b=btn, v=var, i=id_prod: click_boton(b, v, i))
            
            btn.pack(side="right", padx=10)


     # ventana agregar
    
    def _popup_agregar_topping(self):
        ventana_add = tk.Toplevel(self.root)
        ventana_add.title("Agregar Ingrediente")
        ventana_add.geometry("350x180") 
        ventana_add.config(bg=COLOR_SIDEBAR)
        
        ventana_add.transient(self.root)
        ventana_add.grab_set()

        tk.Label(ventana_add, text="Nombre del nuevo topping:", bg=COLOR_SIDEBAR, 
                 fg=COLOR_TEXT, font=("Arial", 12)).pack(pady=15) 
        
        # VALIDACIÓN APLICADA AQUÍ (Agregar Topping)
        entry_nombre = tk.Entry(ventana_add, font=("Arial", 14),
                                validate='key', validatecommand=self.vcmd_texto) 
        
        entry_nombre.pack(pady=5, padx=30, fill="x")
        entry_nombre.focus() 

        def guardar_datos():
            nombre = entry_nombre.get().strip()
            if not nombre:
                messagebox.showwarning("Cuidado", "El nombre no puede estar vacío", parent=ventana_add)
                return

            exito = agregar_nuevo_topping(nombre)
            
            if exito=="DUPLICADO":
                messagebox.showinfo("Error", f"'{nombre}' Ya esta registrado ", parent=ventana_add)
                ventana_add.destroy()      
                self.mostrar_inventario()  
            elif exito:
                messagebox.showinfo("Éxito", f"'{nombre}' agregado correctamente", parent=ventana_add)
                ventana_add.destroy()      
                self.mostrar_inventario()  
            else: 
                messagebox.showerror("Error", "No se pudo guardar en la base de datos", parent=ventana_add)

        tk.Button(ventana_add, text="Guardar", bg=COLOR_BTN_GREEN, fg="white", bd=0,
                  font=("Arial", 11, "bold"), command=guardar_datos).pack(pady=15)

    def panel_funciones(self):
        self._limpiar_panel_principal()
        self._resaltar_boton(self.btn_inventario)

        header_frame = tk.Frame(self.main_frame, bg=COLOR_MAIN_BG)
        header_frame.pack(fill="x", pady=10)
        
        tk.Button(header_frame, text="⬅ Volver", bg=COLOR_BTN_BROWN, fg="white", bd=0,
                  font=("Arial", 12, "bold"), command=self.mostrar_inventario).pack(side="left", padx=10) 

        tk.Label(header_frame, text="Gestión de Ingredientes", font=("Arial", 28, "bold"), 
                 bg=COLOR_MAIN_BG, fg=COLOR_TEXT).pack(side="left", padx=20)


        style = ttk.Style()
        style.theme_use("clam")
        # Estilo Treeview modernizado
        style.configure("Treeview", 
                        background="white", fieldbackground="white", foreground="black",
                        font=("Arial", 12), rowheight=30) 
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background=COLOR_ACCENT, foreground="white") 

        # crear tabla
        frame_tabla = tk.Frame(self.main_frame, bg=COLOR_MAIN_BG)
        frame_tabla.pack(fill="both", expand=True, padx=20, pady=5)

        # columnas
        columns = ("ID", "Nombre", "Estado")
        self.tree = ttk.Treeview(frame_tabla, columns=columns, show="headings", height=15) 
        
        # encabezados
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre del Topping")
        self.tree.heading("Estado", text="Habilitado")

        # configuracion columnas
        self.tree.column("ID", width=70, anchor="center") 
        self.tree.column("Nombre", width=450, anchor="w") 
        self.tree.column("Estado", width=150, anchor="center") 

        # sroll
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # cargar datos
        datos = estatus_topings()
        for item in datos:
            self.tree.insert("", "end", values=item)

        # botones 
        frame_botones = tk.Frame(self.main_frame, bg=COLOR_MAIN_BG)
        frame_botones.pack(fill="x", pady=20, padx=20)

        tk.Button(frame_botones, text="✏️ Editar Nombre", 
                  bg="#FFD700", fg="black", font=("Arial", 12, "bold"), bd=0,
                  padx=20, pady=12, command=self.accion_actualizar).pack(side="left", padx=(0, 20))

        tk.Button(frame_botones, text="🗑️ Eliminar Seleccionado", 
                  bg=COLOR_BTN_RED, fg="white", font=("Arial", 12, "bold"), bd=0,
                  padx=20, pady=12, command=self.accion_eliminar).pack(side="left")

     # logica de botones

    def accion_eliminar(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Selecciona un topping.")
            return
        
        # item seleccionado
        item = self.tree.item(seleccion)
        id_top = item['values'][0]
        nombre = item['values'][1]

        confirmar = messagebox.askyesno("Confirmar Eliminación", 
                                        f"¿Seguro que deseas eliminar '{nombre}'?")
        if confirmar:
            if eliminar_topping_bd(id_top):
                messagebox.showinfo("Éxito", "Topping eliminado.")
                self.panel_funciones()
            else:
                messagebox.showerror("Error", "No se pudo eliminar de la base de datos.")

    def accion_actualizar(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Selecciona un topping para editar.")
            return

        item = self.tree.item(seleccion)
        id_top = item['values'][0]
        nombre_actual = item['values'][1]
        ventana_edit = tk.Toplevel(self.root)
        ventana_edit.title(f"Editar: {nombre_actual}")
        ventana_edit.geometry("400x200") 
        ventana_edit.config(bg=COLOR_SIDEBAR)
        ventana_edit.transient(self.root)
        ventana_edit.grab_set()

        tk.Label(ventana_edit, text="Nuevo nombre del topping:", bg=COLOR_SIDEBAR, 
                 fg=COLOR_TEXT, font=("Arial", 12)).pack(pady=15) 
        
        # VALIDACIÓN APLICADA AQUÍ (Editar Topping)
        entry_nuevo = tk.Entry(ventana_edit, font=("Arial", 14),
                               validate='key', validatecommand=self.vcmd_texto) 
        
        entry_nuevo.insert(0, nombre_actual) # nombre actual
        entry_nuevo.pack(pady=5, padx=30, fill="x")
        entry_nuevo.focus()

        def guardar_cambio():
            nuevo_nombre = entry_nuevo.get().strip()
            if not nuevo_nombre:
                messagebox.showwarning("Cuidado", "El nombre no puede estar vacío", parent=ventana_edit)
                return
            
            if actualizar_nombre_topping(id_top, nuevo_nombre):
                messagebox.showinfo("Éxito", "Nombre actualizado.", parent=ventana_edit)
                ventana_edit.destroy()
                self.panel_funciones() # recargar tabla
            else:
                messagebox.showerror("Error", "Fallo al actualizar en BD.", parent=ventana_edit)

        tk.Button(ventana_edit, text="💾 Guardar Cambios", bg=COLOR_BTN_GREEN, fg="white", bd=0,
                  font=("Arial", 11, "bold"), command=guardar_cambio).pack(pady=15)

    '''PRODUCTOS'''
    
    def mostrar_productos(self):
        self._limpiar_panel_principal()
        self._resaltar_boton(self.btn_productos) 

        tk.Label(self.main_frame, text="Control de Productos", font=("Arial", 28, "bold"),
                 bg=COLOR_MAIN_BG, fg=COLOR_TEXT).pack(side="top", pady=(10, 5))
                 
        # --- FILTRO POR CATEGORÍA ---
        frame_filtro = tk.Frame(self.main_frame, bg=COLOR_MAIN_BG)
        frame_filtro.pack(fill="x", padx=30, pady=10)
        
        tk.Label(frame_filtro, text="Filtrar por Categoría:", bg=COLOR_MAIN_BG, fg=COLOR_TEXT,
                 font=("Arial", 12, "bold")).pack(side="left", padx=(0, 10))
                 
        self.categoria_filtro = tk.StringVar(frame_filtro, value="TODAS")
        categorias_raw = obtener_categorias() 
        categorias = ["TODAS"] + [c['nombre_categoria'] for c in categorias_raw]
        
        menu_categoria = ttk.OptionMenu(frame_filtro, self.categoria_filtro, "TODAS", *categorias, command=self.cargar_productos_filtrados)
        menu_categoria.config(width=20)
        menu_categoria.pack(side="left")
        # ----------------------------
                 
        footer_frame = tk.Frame(self.main_frame, bg=COLOR_MAIN_BG)
        footer_frame.pack(side="bottom", fill="x", pady=20, padx=30)
        
        # NUEVO: Exportar Productos
        tk.Button(footer_frame, text="📥 Exportar a Excel", 
                            bg=COLOR_BTN_GREEN, fg="white", font=("Arial", 12, "bold"),
                            padx=25, pady=12, bd=0,
                            command=self.exportar_productos_excel).pack(side="left", padx=(0, 10))

        # agregar
        btn_add_producto = tk.Button(footer_frame, text="➕ Agregar Nuevo", 
                            bg=COLOR_BTN_BROWN, fg="white", font=("Arial", 12, "bold"),
                            padx=25, pady=12, bd=0,
                            command=self._mostrar_panel_agregar_producto)
        btn_add_producto.pack(side="right", padx=(10, 0))

        # funciones
        btn_funciones_producto = tk.Button(footer_frame, text="⚙️ Funciones / Eliminar", 
                                  bg=COLOR_ACCENT, fg="white", font=("Arial", 12, "bold"),
                                  padx=25, pady=12, bd=0,
                                  command=self.panel_funciones_producto)
        btn_funciones_producto.pack(side="right")

        header_frame = tk.Frame(self.main_frame, bg=COLOR_MAIN_BG)
        header_frame.pack(side="top", fill="x", pady=10, padx=40) 
        
        # encabezados lista
        tk.Label(header_frame, text="Nombre", bg=COLOR_MAIN_BG, fg=COLOR_TEXT,
                 font=("Arial", 14, "bold"), width=15, anchor="w").pack(side="left", padx=(0, 10))

        tk.Label(header_frame, text="Cant. Top.", bg=COLOR_MAIN_BG, fg=COLOR_TEXT,
                 font=("Arial", 14, "bold"), width=10, anchor="center").pack(side="right", padx=10) 

        tk.Label(header_frame, text="Precio", bg=COLOR_MAIN_BG, fg=COLOR_TEXT,
                 font=("Arial", 14, "bold"), width=8, anchor="center").pack(side="right", padx=10) 
                 
        tk.Label(header_frame, text="Descripción", bg=COLOR_MAIN_BG, fg=COLOR_TEXT,
                 font=("Arial", 14, "bold"), anchor="w").pack(side="left", expand=True)
        
        ttk.Separator(self.main_frame, orient="horizontal").pack(side="top", fill="x", padx=30)

        self.container_scroll_prods = tk.Frame(self.main_frame, bg=COLOR_MAIN_BG)
        self.container_scroll_prods.pack(side="top", fill="both", expand=True, padx=30, pady=5)

        self.canvas_prods_list = tk.Canvas(self.container_scroll_prods, bg=COLOR_MAIN_BG, highlightthickness=0)
        self.scrollbar_prods_list = ttk.Scrollbar(self.container_scroll_prods, orient="vertical", command=self.canvas_prods_list.yview)
        
        self.scrollable_frame_prods = tk.Frame(self.canvas_prods_list, bg=COLOR_MAIN_BG)
        self.scrollable_frame_prods.bind(
            "<Configure>",
            lambda e: self.canvas_prods_list.configure(scrollregion=self.canvas_prods_list.bbox("all"))
        )

        window_id = self.canvas_prods_list.create_window((0, 0), window=self.scrollable_frame_prods, anchor="nw")

        def ajustar_ancho_prod(event):
            self.canvas_prods_list.itemconfig(window_id, width=event.width)

        self.canvas_prods_list.bind("<Configure>", ajustar_ancho_prod)
        self.canvas_prods_list.configure(yscrollcommand=self.scrollbar_prods_list.set)

        self.canvas_prods_list.pack(side="left", fill="both", expand=True)
        self.scrollbar_prods_list.pack(side="right", fill="y")
        
        # cargar productos
        self.cargar_productos_filtrados("TODAS")

    def cargar_productos_filtrados(self, categoria_nombre):
        """carga productos con filtro."""
        
        # limpiar productos
        for w in self.scrollable_frame_prods.winfo_children(): w.destroy()
        
        productos_a_mostrar = []
        
        if categoria_nombre != "TODAS":
            
            # filtrar por categoría
            productos_con_id = obtener_productos_con_id()
            categorias_map = {c['id_categorias']: c['nombre_categoria'] for c in obtener_categorias()}

            productos_filtrados = []
            for id_prod, nombre, descripcion, precio, cant_top, id_cat in productos_con_id:
                if categorias_map.get(id_cat) == categoria_nombre:
                    productos_filtrados.append((nombre, descripcion, precio, cant_top))
            
            productos_a_mostrar = productos_filtrados
            
        else:
            # si es "todas"
            productos_a_mostrar = mostrar_productos() 
        
        
        for nombre, descripcion, precio, cant_top in productos_a_mostrar:
            # fila: Estilo modernizado, borde sutil
            row_frame = tk.Frame(self.scrollable_frame_prods, bg="#FFF8F0", bd=0, relief=tk.FLAT, highlightbackground=COLOR_BTN_ACTIVE, highlightthickness=1)
            # fila
            row_frame.pack(fill="x", pady=5, ipadx=10, ipady=5) 
            tk.Label(row_frame, text=nombre, font=("Arial", 14, "bold"), width=15, anchor="w", 
                     bg="#FFF8F0", fg="#5D4037").pack(side="left", padx=(0, 10))
            tk.Label(row_frame, text=cant_top, font=("Arial", 14), width=10, anchor="center", 
                     bg="#FFF8F0", fg="#5D4037").pack(side="right", padx=10)
            tk.Label(row_frame, text=f"${precio:.2f}", font=("Arial", 14), width=8, anchor="center", 
                     bg="#FFF8F0", fg="#5D4037").pack(side="right", padx=10) 
            tk.Label(row_frame, text=descripcion, font=("Arial", 12), anchor="w", 
                     bg="#FFF8F0", fg="#594A42", wraplength=400).pack(side="left", expand=True, fill="x") 

        # ajustar scrollbar
        self.scrollable_frame_prods.update_idletasks()
        self.canvas_prods_list.config(scrollregion=self.canvas_prods_list.bbox("all"))

    def _mostrar_panel_agregar_producto(self):
        """interfaz para agregar producto."""
        self._limpiar_panel_principal()
        self._resaltar_boton(self.btn_productos) 

        header_frame = tk.Frame(self.main_frame, bg=COLOR_MAIN_BG)
        header_frame.pack(fill="x", pady=10)
        
        tk.Button(header_frame, text="⬅ Volver", bg=COLOR_BTN_BROWN, fg="white", bd=0,
                  font=("Arial", 12, "bold"), command=self.mostrar_productos).pack(side="left", padx=10) 

        tk.Label(header_frame, text="➕ Agregar Nuevo Producto", font=("Arial", 28, "bold"), 
                 bg=COLOR_MAIN_BG, fg=COLOR_TEXT).pack(side="left", padx=20)
        
        ttk.Separator(self.main_frame, orient="horizontal").pack(fill="x", padx=30)
        
        # Frame de formulario con borde sutil para destacar la tarjeta
        form_frame = tk.Frame(self.main_frame, bg=COLOR_SIDEBAR, padx=40, pady=30, bd=0, relief=tk.FLAT, highlightbackground=COLOR_BTN_ACTIVE, highlightthickness=1) 
        form_frame.pack(fill="both", expand=True, padx=40, pady=30)
        form_frame.grid_columnconfigure(0, weight=1)
        form_frame.grid_columnconfigure(1, weight=3)

        # variables de control
        self.categoria_seleccionada = tk.StringVar(form_frame)
        self.cant_topings_var = tk.StringVar(form_frame, value="0") 

        # VALIDACIÓN APLICADA AQUÍ (Agregar Producto)
        self.entry_nombre = tk.Entry(form_frame, font=("Arial", 14), validate='key', validatecommand=self.vcmd_texto) 
        self.entry_desc = tk.Entry(form_frame, font=("Arial", 14), validate='key', validatecommand=self.vcmd_texto) 
        
        # validar precio
        self.entry_precio = tk.Entry(form_frame, font=("Arial", 14), validate='key', validatecommand=self.vcmd_precio) 
        
        self.frame_top = tk.Frame(form_frame, bg=COLOR_SIDEBAR) 
        
        def _mostrar_campo_topings(*args):
            cat = self.categoria_seleccionada.get()
            # si es crepa o waffle mostrar topping
            if "crepa" in cat.lower() or "waffle" in cat.lower():
                self.frame_top.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(15, 0)) 
            else:
                self.frame_top.grid_remove()
                self.cant_topings_var.set("0")

        # campos del formulario
        categorias_raw = obtener_categorias() 
        categorias = [c['nombre_categoria'] for c in categorias_raw] if categorias_raw else ["Sin Categorías"]

        tk.Label(form_frame, text="1. Categoría:", bg=COLOR_SIDEBAR, 
                 fg=COLOR_TEXT, font=("Arial", 13, "bold")).grid(row=0, column=0, sticky="w", pady=(10, 10)) 
        
        if categorias:
             self.categoria_seleccionada.set(categorias[0])

        menu_categoria = ttk.OptionMenu(form_frame, self.categoria_seleccionada, None, *categorias)
        menu_categoria.config(width=30)
        menu_categoria.grid(row=0, column=1, sticky="w", pady=10, padx=5)
        self.categoria_seleccionada.trace_add("write", _mostrar_campo_topings)
        
        # nombre
        tk.Label(form_frame, text="2. Nombre:", bg=COLOR_SIDEBAR, 
                 fg=COLOR_TEXT, font=("Arial", 13, "bold")).grid(row=1, column=0, sticky="w", pady=(10, 10))
        self.entry_nombre.grid(row=1, column=1, sticky="ew", pady=(10, 10), padx=5)
        
        # descripcion
        tk.Label(form_frame, text="3. Descripción:", bg=COLOR_SIDEBAR, 
                 fg=COLOR_TEXT, font=("Arial", 13, "bold")).grid(row=2, column=0, sticky="w", pady=(10, 10))
        self.entry_desc.grid(row=2, column=1, sticky="ew", pady=(10, 10), padx=5)

        # precio
        tk.Label(form_frame, text="4. Precio (0.00):", bg=COLOR_SIDEBAR, 
                 fg=COLOR_TEXT, font=("Arial", 13, "bold")).grid(row=3, column=0, sticky="w", pady=(10, 10))
        self.entry_precio.grid(row=3, column=1, sticky="ew", pady=(10, 10), padx=5)

        # cantidad de toppings
        tk.Label(self.frame_top, text="5. Cantidad Máx. de Toppings:", bg=COLOR_SIDEBAR, 
                 fg=COLOR_TEXT, font=("Arial", 13, "bold")).pack(side="left", anchor="w")
        
        # validar entero
        spinbox_top = tk.Spinbox(self.frame_top, from_=0, to=10, textvariable=self.cant_topings_var, width=5, 
                                 font=("Arial", 14), validate='key', validatecommand=self.vcmd_entero) 
        spinbox_top.pack(side="right", padx=10)
        
        # mostrar/ocultar al inicio
        _mostrar_campo_topings() 

        tk.Button(self.main_frame, text="💾 Guardar Producto", bg=COLOR_BTN_GREEN, fg="white", bd=0,
                  font=("Arial", 13, "bold"), command=self.guardar_datos_prod).pack(pady=30)
        
    def guardar_datos_prod(self):
        nombre = self.entry_nombre.get().strip()
        descripcion = self.entry_desc.get().strip()
        precio_str = self.entry_precio.get().strip()
        cant_top = self.cant_topings_var.get()
        categoria = self.categoria_seleccionada.get()

        if not nombre or not descripcion or not precio_str:
            messagebox.showwarning("Cuidado", "Faltan campos obligatorios.")
            return

        try:
            precio = float(precio_str)
            if precio <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "El precio debe ser un número positivo válido.")
            return
        
        try:
            cant_top_int = int(cant_top)
        except ValueError:
             messagebox.showerror("Error", "La cantidad de toppings debe ser un número entero.")
             return
        
        exito = agregar_nuevo_producto(nombre, descripcion, precio, cant_top_int, categoria)
        
        if exito == "DUPLICADO":
            messagebox.showinfo("Error", f"'{nombre}' Ya está registrado.")
        elif exito:
            messagebox.showinfo("Éxito", f"'{nombre}' agregado correctamente")
            self.mostrar_productos()
        else:
            messagebox.showerror("Error", "No se pudo guardar en la base de datos.")
            
    def panel_funciones_producto(self):
        self._limpiar_panel_principal()
        self._resaltar_boton(self.btn_productos)

        header_frame = tk.Frame(self.main_frame, bg=COLOR_MAIN_BG)
        header_frame.pack(fill="x", pady=10)
        
        tk.Button(header_frame, text="⬅ Volver", bg=COLOR_BTN_BROWN, fg="white", bd=0,
                  font=("Arial", 12, "bold"), command=self.mostrar_productos).pack(side="left", padx=10) 

        tk.Label(header_frame, text="Gestión de Productos", font=("Arial", 28, "bold"), 
                 bg=COLOR_MAIN_BG, fg=COLOR_TEXT).pack(side="left", padx=20)


        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                        background="white", fieldbackground="white", foreground="black",
                        font=("Arial", 12), rowheight=30) 
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background=COLOR_ACCENT, foreground="white") 

        # crear tabla
        frame_tabla = tk.Frame(self.main_frame, bg=COLOR_MAIN_BG)
        frame_tabla.pack(fill="both", expand=True, padx=20, pady=5)

        # columnas
        columns = ("id_prod", "nombre","descripcion","precio", "id_categoria", "cant_top")
        self.tree = ttk.Treeview(frame_tabla, columns=columns, show="headings", height=15) 
        
        # encabezados
        self.tree.heading("id_prod", text="ID")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("descripcion", text="Descripción")
        self.tree.heading("precio", text="Precio")
        self.tree.heading("id_categoria", text="ID Cat.")
        self.tree.heading("cant_top", text="Toppings Máx.")

        # configuracion columnas
        self.tree.column("id_prod", width=70, anchor="center") 
        self.tree.column("nombre", width=180, anchor="w") 
        self.tree.column("descripcion", width=300, anchor="w") 
        self.tree.column("precio", width=100, anchor="center") 
        self.tree.column("id_categoria", width=100, anchor="center") 
        self.tree.column("cant_top", width=100, anchor="center") 

        # sroll
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # cargar datos
        datos_productos = obtener_productos_con_id()
        for item in datos_productos:
            self.tree.insert("", "end", values=item)

        # botones 
        frame_botones = tk.Frame(self.main_frame, bg=COLOR_MAIN_BG)
        frame_botones.pack(fill="x", pady=20, padx=20)

        tk.Button(frame_botones, text="✏️ Editar datos", 
                  bg="#FFD700", fg="black", font=("Arial", 12, "bold"), bd=0,
                  padx=20, pady=12, command=self.accion_actualizar_producto).pack(side="left", padx=(0, 20))

        tk.Button(frame_botones, text="🗑️ Eliminar Seleccionado", 
                  bg=COLOR_BTN_RED, fg="white", font=("Arial", 12, "bold"), bd=0,
                  padx=20, pady=12, command=self.accion_eliminar_producto).pack(side="left")

    def accion_eliminar_producto(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Selecciona un producto.")
            return
        
        item = self.tree.item(seleccion)
        id_prod = item['values'][0]
        nombre = item['values'][1]

        confirmar = messagebox.askyesno("Confirmar Eliminación", 
                                        f"¿Seguro que deseas eliminar el producto '{nombre}'?")
        if confirmar:
            if eliminar_producto_bd(id_prod):
                messagebox.showinfo("Éxito", "Producto eliminado.")
                self.panel_funciones_producto() # recargar la vista
            else:
                messagebox.showerror("Error", "No se pudo eliminar de la base de datos.")

    def accion_actualizar_producto(self):
        # ventana de edición
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Selecciona un producto para editar sus datos.")
            return

        item = self.tree.item(seleccion)
        # extraer valores
        id_prod, nombre_actual, desc_actual, precio_actual, id_categoria_actual, cant_top_actual = item['values']

        # obtener categorias
        categorias_raw = obtener_categorias() 
        categorias_nombres = [c['nombre_categoria'] for c in categorias_raw] if categorias_raw else ["Sin Categorías"]
        
        # buscar nombre de categoria actual
        nombre_categoria_actual = next((c['nombre_categoria'] for c in categorias_raw if c['id_categorias'] == id_categoria_actual), categorias_nombres[0] if categorias_nombres else "")

        # --- Ventana Edición ---
        ventana_edit = tk.Toplevel(self.root)
        ventana_edit.title(f"Editar Producto: {nombre_actual}")
        ventana_edit.geometry("500x450") 
        ventana_edit.config(bg=COLOR_SIDEBAR)
        ventana_edit.transient(self.root)
        ventana_edit.grab_set()

        form_frame = tk.Frame(ventana_edit, bg=COLOR_SIDEBAR, padx=30, pady=25) 
        form_frame.pack(fill="both", expand=True)
        form_frame.grid_columnconfigure(0, weight=1)
        form_frame.grid_columnconfigure(1, weight=3)

        # variables de control
        self._nombre_var = tk.StringVar(form_frame, value=nombre_actual)
        self._desc_var = tk.StringVar(form_frame, value=desc_actual)
        self._precio_var = tk.StringVar(form_frame, value=str(precio_actual))
        self._cant_top_var = tk.StringVar(form_frame, value=str(cant_top_actual)) 
        self._categoria_var = tk.StringVar(form_frame, value=nombre_categoria_actual)
        
        frame_top = tk.Frame(form_frame, bg=COLOR_SIDEBAR) 

        def mostrar_campo_topings_edit(*args):
            cat = self._categoria_var.get()
            # si es crepa o waffle mostrar topping
            if "crepa" in cat.lower() or "waffle" in cat.lower():
                frame_top.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))
            else:
                frame_top.grid_remove()
                self._cant_top_var.set("0")

        # categoría
        tk.Label(form_frame, text="Categoría:", bg=COLOR_SIDEBAR, fg=COLOR_TEXT, font=("Arial", 12)).grid(row=0, column=0, sticky="w", pady=10)
        menu_categoria = ttk.OptionMenu(form_frame, self._categoria_var, None, *categorias_nombres)
        menu_categoria.config(width=30)
        menu_categoria.grid(row=0, column=1, sticky="w", pady=10, padx=5)
        self._categoria_var.trace_add("write", mostrar_campo_topings_edit)

        # nombre
        tk.Label(form_frame, text="Nombre:", bg=COLOR_SIDEBAR, fg=COLOR_TEXT, font=("Arial", 12)).grid(row=1, column=0, sticky="w", pady=10)
        
        # VALIDACIÓN APLICADA AQUÍ (Editar Producto - Nombre)
        tk.Entry(form_frame, textvariable=self._nombre_var, font=("Arial", 14), 
                 validate='key', validatecommand=self.vcmd_texto).grid(row=1, column=1, sticky="ew", pady=10, padx=5)

        # descripción
        tk.Label(form_frame, text="Descripción:", bg=COLOR_SIDEBAR, fg=COLOR_TEXT, font=("Arial", 12)).grid(row=2, column=0, sticky="w", pady=10)
        
        # VALIDACIÓN APLICADA AQUÍ (Editar Producto - Descripción)
        tk.Entry(form_frame, textvariable=self._desc_var, font=("Arial", 14),
                 validate='key', validatecommand=self.vcmd_texto).grid(row=2, column=1, sticky="ew", pady=10, padx=5)

        # precio (validado)
        tk.Label(form_frame, text="Precio (0.00):", bg=COLOR_SIDEBAR, fg=COLOR_TEXT, font=("Arial", 12)).grid(row=3, column=0, sticky="w", pady=10)
        tk.Entry(form_frame, textvariable=self._precio_var, font=("Arial", 14), validate='key', validatecommand=self.vcmd_precio).grid(row=3, column=1, sticky="ew", pady=10, padx=5)
        
        # toppings (validado)
        tk.Label(frame_top, text="Toppings Máx.:", bg=COLOR_SIDEBAR, fg=COLOR_TEXT, font=("Arial", 12)).pack(side="left", anchor="w")
        tk.Spinbox(frame_top, from_=0, to=10, textvariable=self._cant_top_var, width=5, 
                   font=("Arial", 14), validate='key', validatecommand=self.vcmd_entero).pack(side="right", padx=10)
        
        mostrar_campo_topings_edit() 

        def guardar_cambio_prod():
            nombre = self._nombre_var.get().strip()
            descripcion = self._desc_var.get().strip()
            precio_str = self._precio_var.get().strip()
            cant_top = self._cant_top_var.get()
            categoria = self._categoria_var.get()

            if not nombre or not descripcion or not precio_str:
                messagebox.showwarning("Cuidado", "Faltan campos obligatorios.", parent=ventana_edit)
                return
            try:
                precio = float(precio_str)
                cant_top_int = int(cant_top)
                if precio <= 0: raise ValueError
            except ValueError:
                messagebox.showerror("Error", "El Precio y la Cant. Toppings deben ser números válidos.", parent=ventana_edit)
                return
            
            if actualizar_producto(id_prod, nombre, descripcion, precio, cant_top_int, categoria):
                messagebox.showinfo("Éxito", "Producto actualizado.", parent=ventana_edit)
                ventana_edit.destroy()
                self.panel_funciones_producto() # recargar tabla
            else:
                messagebox.showerror("Error", "Fallo al actualizar en la Base de Datos.", parent=ventana_edit)

        tk.Button(ventana_edit, text="💾 Guardar Cambios", bg=COLOR_BTN_GREEN, fg="white", bd=0,
                  font=("Arial", 12, "bold"), command=guardar_cambio_prod).pack(pady=25)
    
    '''VENTAS'''
    def mostrar_ventas(self):
        self._limpiar_panel_principal()
        self._resaltar_boton(self.btn_ventas)
        
        tk.Label(self.main_frame, text="Historial de Ventas", font=("Arial", 24, "bold"),
                bg=COLOR_MAIN_BG, fg=COLOR_TEXT).pack(side="top", pady=(10, 5))
        
        # Obtener los datos de ventas agrupadas
        reporte_datos = obtener_reporte_ventas_agrupadas()
        
        if not reporte_datos:
            tk.Label(self.main_frame, text="No hay ventas registradas.", font=("Arial", 16), 
                    bg=COLOR_MAIN_BG).pack(pady=50)
            return
        
        # Crear tabla Treeview
        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 11), rowheight=30)
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
        
        frame_tabla = tk.Frame(self.main_frame, bg=COLOR_MAIN_BG)
        frame_tabla.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Columnas del Treeview
        columns = ("id_ticket", "fecha", "id_vendedor", "total_final")
        self.tree_ventas = ttk.Treeview(frame_tabla, columns=columns, show="headings", height=15)
        
        self.tree_ventas.heading("id_ticket", text="ID Ticket")
        self.tree_ventas.heading("fecha", text="Fecha")
        self.tree_ventas.heading("id_vendedor", text="ID Vendedor")
        self.tree_ventas.heading("total_final", text="TOTAL")
        
        self.tree_ventas.column("id_ticket", width=120, anchor="center")
        self.tree_ventas.column("fecha", width=180, anchor="center")
        self.tree_ventas.column("id_vendedor", width=120, anchor="center")
        self.tree_ventas.column("total_final", width=150, anchor="e")
        
        # Scrollbar
        v_scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree_ventas.yview)
        self.tree_ventas.configure(yscrollcommand=v_scrollbar.set)
        
        self.tree_ventas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        
        # Insertar datos en el Treeview
        for grupo in reporte_datos:
            self.tree_ventas.insert("", "end", 
                                values=(grupo['id_ticket'], grupo['fecha'], 
                                        grupo['id_vendedor'], f"${grupo['total_final']:.2f}"),
                                tags=(grupo['id_ticket'],))
        
        # Botón para ver detalles
        frame_botones = tk.Frame(self.main_frame, bg=COLOR_MAIN_BG)
        frame_botones.pack(fill="x", pady=20, padx=20)
        
        tk.Button(frame_botones, text="🔍 Ver Detalles de Venta Seleccionada", 
                bg=COLOR_ACCENT, fg="white", font=("Arial", 11, "bold"), bd=0,
                padx=15, pady=10, command=lambda: self.mostrar_detalles_venta(reporte_datos)).pack(side="left")
        
        # NUEVO: Botón para Exportar a Excel
        tk.Button(frame_botones, text="📥 Exportar a Excel",
                bg=COLOR_BTN_GREEN, fg="white", font=("Arial", 11, "bold"), bd=0,
                padx=15, pady=10, command=lambda: self.exportar_reporte_ventas_excel(reporte_datos)).pack(side="left", padx=15)
        
        # Botón para refrescar
        tk.Button(frame_botones, text="🔄 Actualizar Lista", 
                bg="#5D4037", fg="white", font=("Arial", 11, "bold"), bd=0,
                padx=15, pady=10, command=self.mostrar_ventas).pack(side="right")

    def mostrar_detalles_venta(self, reporte_datos):
        """Muestra los detalles de una venta seleccionada"""
        seleccion = self.tree_ventas.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Selecciona una venta de la lista.")
            return
        
        # Obtener el ID del ticket seleccionado
        item = self.tree_ventas.item(seleccion[0])
        id_ticket = item['values'][0]  # ID del ticket está en la primera columna
        
        # Buscar la venta en los datos
        grupo = None
        for g in reporte_datos:
            if g['id_ticket'] == id_ticket:
                grupo = g
                break
        
        if not grupo:
            messagebox.showerror("Error", "No se encontraron detalles para esta venta.")
            return
        
        # Crear ventana emergente con los detalles
        ventana_detalles = tk.Toplevel(self.root)
        ventana_detalles.title(f"Detalles del Ticket #{id_ticket}")
        ventana_detalles.geometry("600x500")
        ventana_detalles.config(bg=COLOR_MAIN_BG)
        ventana_detalles.transient(self.root)
        ventana_detalles.grab_set()
        
        # Título
        tk.Label(ventana_detalles, text=f"Ticket #{id_ticket}", 
                font=("Arial", 18, "bold"), bg=COLOR_MAIN_BG, fg=COLOR_TEXT).pack(pady=10)
        
        # Información general: Estilo modernizado
        info_frame = tk.Frame(ventana_detalles, bg=COLOR_SIDEBAR, padx=15, pady=10, bd=0, relief=tk.FLAT, highlightbackground=COLOR_BTN_ACTIVE, highlightthickness=1)
        info_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(info_frame, text=f"Fecha: {grupo['fecha']}", 
                font=("Arial", 12), bg=COLOR_SIDEBAR, fg=COLOR_TEXT, anchor="w").pack(fill="x", pady=2)
        tk.Label(info_frame, text=f"Vendedor ID: {grupo['id_vendedor']}", 
                font=("Arial", 12), bg=COLOR_SIDEBAR, fg=COLOR_TEXT, anchor="w").pack(fill="x", pady=2)
        tk.Label(info_frame, text=f"Total: ${grupo['total_final']:.2f}", 
                font=("Arial", 14, "bold"), bg=COLOR_SIDEBAR, fg=COLOR_BTN_RED, anchor="w").pack(fill="x", pady=5)
        
        # Separador
        ttk.Separator(ventana_detalles, orient="horizontal").pack(fill="x", padx=20, pady=10)
        
        # Título de detalles
        tk.Label(ventana_detalles, text="Artículos Vendidos:", 
                font=("Arial", 14, "bold"), bg=COLOR_MAIN_BG, fg=COLOR_TEXT).pack(anchor="w", padx=20)
        
        # Frame para scroll de detalles
        detalle_container = tk.Frame(ventana_detalles, bg=COLOR_MAIN_BG)
        detalle_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Canvas y scrollbar para detalles
        canvas = tk.Canvas(detalle_container, bg=COLOR_MAIN_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(detalle_container, orient="vertical", command=canvas.yview)
        
        detalle_frame = tk.Frame(canvas, bg=COLOR_MAIN_BG)
        
        detalle_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=detalle_frame, anchor="nw", width=550)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mostrar cada detalle de producto
        for detalle in grupo['detalles']:
            # Frame para cada producto: Estilo modernizado
            prod_frame = tk.Frame(detalle_frame, bg=COLOR_SIDEBAR, bd=0, relief=tk.FLAT, highlightbackground=COLOR_BTN_ACTIVE, highlightthickness=1)
            prod_frame.pack(fill="x", pady=3, padx=5)
            
            # Descripción del producto
            desc_label = tk.Label(prod_frame, text=detalle['descripcion'], 
                                font=("Arial", 11), bg=COLOR_SIDEBAR, fg=COLOR_TEXT,
                                anchor="w", justify="left", wraplength=400)
            desc_label.pack(side="left", fill="x", padx=10, pady=5)
            
            # Total de la línea
            total_label = tk.Label(prod_frame, text=f"${detalle['total_linea']:.2f}", 
                                font=("Arial", 11, "bold"), bg=COLOR_SIDEBAR, fg="#5D4037")
            total_label.pack(side="right", padx=10, pady=5)
        
        # Botón para cerrar
        tk.Button(ventana_detalles, text="Cerrar", bg=COLOR_BTN_BROWN, fg="white", bd=0,
                font=("Arial", 11, "bold"), padx=30, pady=8,
                command=ventana_detalles.destroy).pack(pady=15)

    '''REPORTES'''
    def mostrar_reportes(self):
        self._limpiar_panel_principal()
        self._resaltar_boton(self.btn_reportes)
        
        # Título
        tk.Label(self.main_frame, text="📊 Dashboard de Ventas", 
                 font=("Arial", 28, "bold"), bg=COLOR_MAIN_BG, fg=COLOR_TEXT).pack(pady=(10, 20))
        
        # Contenedor principal para las métricas (Cards)
        self.frame_dashboard = tk.Frame(self.main_frame, bg=COLOR_MAIN_BG)
        self.frame_dashboard.pack(fill="x", padx=30)
        
        # Contenedor para la tabla de detalles (lo dejamos vacío por si acaso)
        self.frame_detalles_reporte = tk.Frame(self.main_frame, bg=COLOR_MAIN_BG)
        self.frame_detalles_reporte.pack(fill="both", expand=True, padx=30, pady=10)
        
        self.cargar_dashboard_reportes()

        # Botón para Recargar/Actualizar
        tk.Button(self.main_frame, text="🔄 Recargar Datos", 
                  command=self.cargar_dashboard_reportes, bd=0,
                  bg=COLOR_BTN_BROWN, fg="white", font=("Arial", 10, "bold")).pack(pady=10)

    def cargar_dashboard_reportes(self):
        """Carga las métricas y las muestra en cards."""
        # 1. Limpiar el frame del dashboard
        for w in self.frame_dashboard.winfo_children(): w.destroy()
        for w in self.frame_detalles_reporte.winfo_children(): w.destroy()
        
        # 2. Obtener datos del controlador
        resumen = obtener_resumen_ventas()
        mas_vendido = obtener_producto_mas_vendido_semana()

        # --- Card 1: Venta Total (Histórica) --- (Estilo modernizado: FLAT con highlight)
        card_total = tk.Frame(self.frame_dashboard, bg="#A0D8B3", bd=0, relief=tk.FLAT, highlightbackground=COLOR_BTN_ACTIVE, highlightthickness=1) 
        card_total.pack(side="left", padx=10, expand=True, fill="x")
        
        tk.Label(card_total, text="💰 VENTA TOTAL (Histórica)", font=("Arial", 12, "bold"), 
                 bg="#A0D8B3", fg=COLOR_TEXT).pack(pady=(10, 5))
        
        total_str = f"${resumen['total_ventas']:.2f}" if resumen['total_ventas'] else "$0.00"
        tk.Label(card_total, text=total_str, font=("Arial", 28, "bold"), 
                 bg="#A0D8B3", fg=COLOR_TEXT).pack(pady=(0, 10))

        # --- Card 2: Total Transacciones (Histórica) --- (Estilo modernizado: FLAT con highlight)
        card_transacciones = tk.Frame(self.frame_dashboard, bg="#ADD8E6", bd=0, relief=tk.FLAT, highlightbackground=COLOR_BTN_ACTIVE, highlightthickness=1) 
        card_transacciones.pack(side="left", padx=10, expand=True, fill="x")
        
        tk.Label(card_transacciones, text="🧾 Total Transacciones", font=("Arial", 12, "bold"), 
                 bg="#ADD8E6", fg=COLOR_TEXT).pack(pady=(10, 5))
                 
        tk.Label(card_transacciones, text=f"{resumen['total_transacciones']}", font=("Arial", 28, "bold"), 
                 bg="#ADD8E6", fg=COLOR_TEXT).pack(pady=(0, 10))

        # --- Card 3: Producto Más Vendido (Última Semana) --- (Estilo modernizado: FLAT con highlight)
        card_mas_vendido = tk.Frame(self.frame_dashboard, bg="#FFD700", bd=0, relief=tk.FLAT, highlightbackground=COLOR_BTN_ACTIVE, highlightthickness=1) 
        card_mas_vendido.pack(side="left", padx=10, expand=True, fill="x")
        
        nombre_prod = mas_vendido['descripcion_detalle'] if mas_vendido else "Ninguno"
        cantidad_prod = mas_vendido['cantidad_total'] if mas_vendido else 0
        
        tk.Label(card_mas_vendido, text="🏆 Más Vendido (Última Semana)", font=("Arial", 12, "bold"), 
                 bg="#FFD700", fg=COLOR_TEXT, wraplength=200).pack(pady=(10, 5))
        
        tk.Label(card_mas_vendido, text=nombre_prod, font=("Arial", 16), 
                 bg="#FFD700", fg=COLOR_TEXT, wraplength=180).pack()
                 
        tk.Label(card_mas_vendido, text=f"({int(cantidad_prod)} unidades)", font=("Arial", 10, "italic"), 
                 bg="#FFD700", fg=COLOR_TEXT).pack(pady=(0, 10))
                 
        # Botón para Exportar Reporte Semanal
        btn_exportar_semanal = tk.Button(self.frame_detalles_reporte, text="📥 Exportar Resumen Semanal",
                                        bg=COLOR_BTN_GREEN, fg="white", font=("Arial", 11, "bold"), bd=0,
                                        command=lambda: self.exportar_a_excel([mas_vendido] if mas_vendido else [], "ProductoMasVendido", "ReporteSemanal.xlsx"))
        btn_exportar_semanal.pack(pady=20)