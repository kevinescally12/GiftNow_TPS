# ui/ui_consulta.py
# Capa de presentación — consulta de stock por SKU e historial de movimientos.
# Sin SQL directo. Usa datos_producto y datos_movimiento.

import tkinter as tk
from tkinter import ttk, messagebox
from datos.datos_producto   import buscar_por_code, listar_activos
from datos.datos_movimiento import historial_sku

COLOR_FONDO    = "#1A1A2E"
COLOR_PANEL    = "#16213E"
COLOR_ACENTO   = "#E94560"
COLOR_ACENTO2  = "#0F3460"
COLOR_TEXTO    = "#EAEAEA"
COLOR_SUBTEXTO = "#A0A0B0"
COLOR_ENTRY_BG = "#0D1B2A"
COLOR_ENTRY_BD = "#2A3F5F"
COLOR_OK       = "#50C878"
COLOR_WARN     = "#F5A623"
COLOR_TABLA_BG = "#0D1B2A"
COLOR_TABLA_HD = "#0F3460"
COLOR_FILA_PAR = "#131C2E"
COLOR_FILA_IMP = "#0D1525"

FUENTE_TITULO = ("Segoe UI", 13, "bold")
FUENTE_LABEL  = ("Segoe UI", 9, "bold")
FUENTE_ENTRY  = ("Segoe UI", 10)
FUENTE_BTN    = ("Segoe UI", 10, "bold")
FUENTE_INFO   = ("Segoe UI", 9)
FUENTE_TABLA  = ("Segoe UI", 9)

COLOR_TIPO = {
    "ENTRADA":    "#50C878",
    "SALIDA":     "#E94560",
    "DEVOLUCION": "#F5A623",
    "AJUSTE":     "#9B59B6",
}


class FormConsulta(tk.Toplevel):
    """Consulta de stock por SKU con historial de movimientos."""

    def __init__(self, padre, usuario: dict):
        super().__init__(padre)
        self.usuario = usuario
        self.title("GiftNow TPS — Consulta de Stock")
        self.configure(bg=COLOR_FONDO)
        self.grab_set()
        self._centrar(820, 640)
        self._construir_ui()
        self.entry_sku.focus_set()

    def _centrar(self, ancho, alto):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{ancho}x{alto}+{(sw-ancho)//2}+{(sh-alto)//2}")

    # ── Construcción ─────────────────────────────────────────────────────

    def _construir_ui(self):
        outer = tk.Frame(self, bg=COLOR_FONDO, padx=28, pady=18)
        outer.pack(fill="both", expand=True)

        tk.Label(outer, text="Consulta de Stock por SKU",
                 font=FUENTE_TITULO, bg=COLOR_FONDO,
                 fg=COLOR_ACENTO).pack(anchor="w", pady=(0, 14))

        # ── Barra de búsqueda ────────────────────────────────────────────
        p_busq = tk.Frame(outer, bg=COLOR_PANEL,
                          highlightbackground=COLOR_ACENTO2,
                          highlightthickness=1)
        p_busq.pack(fill="x", pady=(0, 10))

        fr_inner = tk.Frame(p_busq, bg=COLOR_PANEL, padx=16, pady=12)
        fr_inner.pack(fill="x")
        fr_inner.columnconfigure(1, weight=1)

        tk.Label(fr_inner, text="Stock Code:", font=FUENTE_LABEL,
                 bg=COLOR_PANEL, fg=COLOR_TEXTO).grid(
                 row=0, column=0, sticky="w", padx=(0, 8))

        self.entry_sku = tk.Entry(
            fr_inner, font=FUENTE_ENTRY, bg=COLOR_ENTRY_BG, fg=COLOR_TEXTO,
            insertbackground=COLOR_TEXTO, relief="flat",
            highlightthickness=1, highlightbackground=COLOR_ENTRY_BD,
            highlightcolor=COLOR_ACENTO2)
        self.entry_sku.grid(row=0, column=1, sticky="ew")
        self.entry_sku.bind("<Return>", lambda e: self._buscar())

        tk.Button(fr_inner, text="Buscar", font=("Segoe UI", 9, "bold"),
                  bg=COLOR_ACENTO, fg="#FFFFFF", relief="flat",
                  cursor="hand2", padx=14,
                  command=self._buscar).grid(row=0, column=2, padx=(8, 0))

        tk.Button(fr_inner, text="Ver todos los SKU",
                  font=("Segoe UI", 9), bg=COLOR_ACENTO2, fg=COLOR_TEXTO,
                  relief="flat", cursor="hand2", padx=10,
                  command=self._ver_todos).grid(row=0, column=3, padx=(6, 0))

        # ── Ficha del producto ───────────────────────────────────────────
        self.panel_ficha = tk.Frame(outer, bg=COLOR_PANEL,
                                    highlightbackground=COLOR_ACENTO2,
                                    highlightthickness=1)
        self.panel_ficha.pack(fill="x", pady=(0, 10))

        fr_ficha = tk.Frame(self.panel_ficha, bg=COLOR_PANEL, padx=16, pady=10)
        fr_ficha.pack(fill="x")

        self.lbl_sku      = self._lbl_ficha(fr_ficha, "SKU:",          0)
        self.lbl_desc     = self._lbl_ficha(fr_ficha, "Descripción:",  1)
        self.lbl_stock    = self._lbl_ficha(fr_ficha, "Stock actual:",  2)
        self.lbl_minimo   = self._lbl_ficha(fr_ficha, "Stock mínimo:", 3)
        self.lbl_precio   = self._lbl_ficha(fr_ficha, "Precio unit.:", 4)
        self.lbl_abc      = self._lbl_ficha(fr_ficha, "Clasificación:", 5)
        self.lbl_estado   = self._lbl_ficha(fr_ficha, "Alerta activa:", 6)

        # ── Historial de movimientos ─────────────────────────────────────
        tk.Label(outer, text="Historial de movimientos",
                 font=FUENTE_LABEL, bg=COLOR_FONDO,
                 fg=COLOR_SUBTEXTO, anchor="w").pack(fill="x", pady=(0, 4))

        fr_tabla = tk.Frame(outer, bg=COLOR_FONDO)
        fr_tabla.pack(fill="both", expand=True)

        cols = ("fecha", "tipo", "cantidad", "antes", "despues",
                "usuario", "referencia", "motivo")
        cabeceras = ("Fecha / Hora", "Tipo", "Cant.", "Stock antes",
                     "Stock después", "Usuario", "Referencia", "Motivo")
        anchos    = (140, 90, 60, 90, 100, 90, 100, 180)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Giftnow.Treeview",
                         background=COLOR_TABLA_BG,
                         foreground=COLOR_TEXTO,
                         fieldbackground=COLOR_TABLA_BG,
                         rowheight=22,
                         font=FUENTE_TABLA)
        style.configure("Giftnow.Treeview.Heading",
                         background=COLOR_TABLA_HD,
                         foreground=COLOR_TEXTO,
                         font=("Segoe UI", 9, "bold"),
                         relief="flat")
        style.map("Giftnow.Treeview",
                  background=[("selected", COLOR_ACENTO2)])

        self.tree = ttk.Treeview(fr_tabla, columns=cols,
                                  show="headings", style="Giftnow.Treeview",
                                  selectmode="browse")
        for col, cab, ancho in zip(cols, cabeceras, anchos):
            self.tree.heading(col, text=cab)
            self.tree.column(col, width=ancho, minwidth=50, anchor="center")
        self.tree.column("motivo", anchor="w")
        self.tree.column("referencia", anchor="w")

        scroll_y = ttk.Scrollbar(fr_tabla, orient="vertical",
                                  command=self.tree.yview)
        scroll_x = ttk.Scrollbar(fr_tabla, orient="horizontal",
                                  command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set,
                             xscrollcommand=scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        fr_tabla.rowconfigure(0, weight=1)
        fr_tabla.columnconfigure(0, weight=1)

        # Colores por tipo de movimiento (tags)
        for tipo, color in COLOR_TIPO.items():
            self.tree.tag_configure(tipo, foreground=color)
        self.tree.tag_configure("par", background=COLOR_FILA_PAR)
        self.tree.tag_configure("imp", background=COLOR_FILA_IMP)

        # Botón cerrar
        tk.Button(outer, text="Cerrar", font=FUENTE_BTN,
                  bg=COLOR_ACENTO2, fg=COLOR_TEXTO, relief="flat",
                  cursor="hand2", pady=8,
                  command=self.destroy).pack(fill="x", pady=(10, 0))

    def _lbl_ficha(self, padre, etiqueta, fila) -> tk.Label:
        tk.Label(padre, text=etiqueta, font=("Segoe UI", 9, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_SUBTEXTO, anchor="w",
                 width=14).grid(row=fila // 4, column=(fila % 4) * 2,
                                 sticky="w", pady=1)
        lbl = tk.Label(padre, text="—", font=FUENTE_INFO,
                        bg=COLOR_PANEL, fg=COLOR_TEXTO, anchor="w")
        lbl.grid(row=fila // 4, column=(fila % 4) * 2 + 1,
                 sticky="w", padx=(0, 20), pady=1)
        return lbl

    # ── Lógica ────────────────────────────────────────────────────────────

    def _buscar(self):
        code = self.entry_sku.get().strip().upper()
        if not code:
            messagebox.showwarning("Campo vacío", "Ingrese un Stock Code.")
            return
        try:
            p = buscar_por_code(code)
        except ConnectionError as e:
            messagebox.showerror("Error de conexión", str(e))
            return
        if p is None:
            messagebox.showinfo("No encontrado",
                                f"SKU '{code}' no encontrado o inactivo.")
            return
        self._mostrar_producto(p)
        self._cargar_historial(p["producto_id"])

    def _mostrar_producto(self, p: dict):
        from datos.datos_alerta import existe_activa
        abc_color = {"A": "#E94560", "B": "#F5A623",
                     "C": "#50C878"}.get(p["clasificacion_abc"], COLOR_TEXTO)

        stock = int(p["stock_actual"])
        minimo = int(p["stock_minimo"])
        stock_color = COLOR_ACENTO if stock <= minimo else COLOR_OK

        self.lbl_sku.config(text=p["stock_code"], fg=COLOR_TEXTO)
        self.lbl_desc.config(text=p["descripcion"], fg=COLOR_TEXTO)
        self.lbl_stock.config(text=str(stock), fg=stock_color)
        self.lbl_minimo.config(text=str(minimo), fg=COLOR_TEXTO)
        self.lbl_precio.config(
            text=f"S/. {float(p['precio_unitario']):.2f}", fg=COLOR_TEXTO)
        self.lbl_abc.config(text=p["clasificacion_abc"], fg=abc_color)

        try:
            alerta = existe_activa(p["producto_id"])
        except Exception:
            alerta = False
        self.lbl_estado.config(
            text="SI — stock en nivel crítico" if alerta else "No",
            fg=COLOR_ACENTO if alerta else COLOR_OK)

    def _cargar_historial(self, producto_id: int):
        self.tree.delete(*self.tree.get_children())
        try:
            registros = historial_sku(producto_id)
        except ConnectionError as e:
            messagebox.showerror("Error de conexión", str(e))
            return
        for i, r in enumerate(registros):
            fecha = str(r["fecha_hora"]) if r["fecha_hora"] else "—"
            tag_tipo = r["tipo_movimiento"]
            tag_fila = "par" if i % 2 == 0 else "imp"
            self.tree.insert("", "end", tags=(tag_tipo, tag_fila),
                             values=(
                                 fecha,
                                 r["tipo_movimiento"],
                                 r["cantidad"],
                                 r["stock_antes"],
                                 r["stock_despues"],
                                 r["usuario"] or "—",
                                 r["referencia"] or "—",
                                 r["motivo"] or "—",
                             ))

    def _ver_todos(self):
        """Abre diálogo con listado de todos los SKU activos."""
        _DialogListaSKU(self)


class _DialogListaSKU(tk.Toplevel):
    """Diálogo auxiliar — lista todos los productos activos."""

    def __init__(self, padre):
        super().__init__(padre)
        self.padre = padre
        self.title("Todos los SKU activos")
        self.configure(bg=COLOR_FONDO)
        self.grab_set()
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"680x480+{(sw-680)//2}+{(sh-480)//2}")
        self._construir()
        self._cargar()

    def _construir(self):
        outer = tk.Frame(self, bg=COLOR_FONDO, padx=20, pady=16)
        outer.pack(fill="both", expand=True)

        tk.Label(outer, text="Productos activos en inventario",
                 font=FUENTE_TITULO, bg=COLOR_FONDO,
                 fg=COLOR_ACENTO).pack(anchor="w", pady=(0, 10))

        # Búsqueda rápida dentro del listado
        fr_bus = tk.Frame(outer, bg=COLOR_FONDO)
        fr_bus.pack(fill="x", pady=(0, 8))
        tk.Label(fr_bus, text="Filtrar:", font=FUENTE_LABEL,
                 bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(side="left")
        self.entry_filtro = tk.Entry(
            fr_bus, font=FUENTE_ENTRY, bg=COLOR_ENTRY_BG, fg=COLOR_TEXTO,
            insertbackground=COLOR_TEXTO, relief="flat",
            highlightthickness=1, highlightbackground=COLOR_ENTRY_BD)
        self.entry_filtro.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self.entry_filtro.bind("<KeyRelease>", self._filtrar)

        # Tabla
        cols = ("stock_code", "descripcion", "stock_actual",
                "stock_minimo", "precio", "abc")
        cabs = ("SKU", "Descripción", "Stock", "Mín.", "Precio", "ABC")
        anchos = (100, 260, 60, 60, 80, 50)

        fr_t = tk.Frame(outer, bg=COLOR_FONDO)
        fr_t.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("SKU.Treeview",
                         background=COLOR_TABLA_BG, foreground=COLOR_TEXTO,
                         fieldbackground=COLOR_TABLA_BG, rowheight=22,
                         font=FUENTE_TABLA)
        style.configure("SKU.Treeview.Heading",
                         background=COLOR_TABLA_HD, foreground=COLOR_TEXTO,
                         font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("SKU.Treeview",
                  background=[("selected", COLOR_ACENTO2)])

        self.tree = ttk.Treeview(fr_t, columns=cols, show="headings",
                                  style="SKU.Treeview", selectmode="browse")
        for col, cab, ancho in zip(cols, cabs, anchos):
            self.tree.heading(col, text=cab)
            self.tree.column(col, width=ancho, minwidth=40, anchor="center")
        self.tree.column("descripcion", anchor="w")

        sv = ttk.Scrollbar(fr_t, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sv.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sv.grid(row=0, column=1, sticky="ns")
        fr_t.rowconfigure(0, weight=1)
        fr_t.columnconfigure(0, weight=1)

        # Doble clic → busca en la consulta principal
        self.tree.bind("<Double-1>", self._seleccionar)

        tk.Button(outer, text="Seleccionar SKU (doble clic) · Cerrar",
                  font=("Segoe UI", 8), bg=COLOR_ACENTO2, fg=COLOR_TEXTO,
                  relief="flat", cursor="hand2", pady=6,
                  command=self.destroy).pack(fill="x", pady=(8, 0))

        self.todos = []   # caché para filtrado

    def _cargar(self):
        try:
            self.todos = listar_activos()
        except ConnectionError as e:
            messagebox.showerror("Error de conexión", str(e))
            return
        self._poblar(self.todos)

    def _poblar(self, lista):
        self.tree.delete(*self.tree.get_children())
        abc_color = {"A": "#E94560", "B": "#F5A623", "C": "#50C878"}
        for i, p in enumerate(lista):
            tag = "par" if i % 2 == 0 else "imp"
            self.tree.insert("", "end", tags=(tag,),
                             values=(
                                 p["stock_code"],
                                 p["descripcion"],
                                 p["stock_actual"],
                                 p["stock_minimo"],
                                 f"S/. {float(p['precio_unitario']):.2f}",
                                 p["clasificacion_abc"],
                             ))
        self.tree.tag_configure("par", background=COLOR_FILA_PAR)
        self.tree.tag_configure("imp", background=COLOR_FILA_IMP)

    def _filtrar(self, event=None):
        texto = self.entry_filtro.get().strip().lower()
        if not texto:
            self._poblar(self.todos)
            return
        filtrados = [p for p in self.todos
                     if texto in p["stock_code"].lower()
                     or texto in p["descripcion"].lower()]
        self._poblar(filtrados)

    def _seleccionar(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        sku = self.tree.item(sel[0])["values"][0]
        self.padre.entry_sku.delete(0, tk.END)
        self.padre.entry_sku.insert(0, sku)
        self.destroy()
        self.padre._buscar()
