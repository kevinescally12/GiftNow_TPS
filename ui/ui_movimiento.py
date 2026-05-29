# ui/ui_movimiento.py
# Capa de presentación — formulario de registro de movimientos.
# Sin SQL directo. Usa logica_movimiento.procesar_movimiento().

import tkinter as tk
from tkinter import messagebox
from datos.datos_producto     import buscar_por_code, obtener_por_id, insertar_producto
from logica.logica_movimiento import procesar_movimiento

# Paleta
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

FUENTE_TITULO = ("Segoe UI", 13, "bold")
FUENTE_LABEL  = ("Segoe UI", 9, "bold")
FUENTE_ENTRY  = ("Segoe UI", 10)
FUENTE_BTN    = ("Segoe UI", 10, "bold")
FUENTE_INFO   = ("Segoe UI", 9)

TIPOS_ALMACENERO = ["ENTRADA", "SALIDA", "DEVOLUCION"]
TIPOS_SUPERVISOR = ["ENTRADA", "SALIDA", "DEVOLUCION", "AJUSTE"]

COLOR_TIPO = {
    "ENTRADA":    "#50C878",
    "SALIDA":     "#E94560",
    "DEVOLUCION": "#F5A623",
    "AJUSTE":     "#9B59B6",
}


class FormMovimiento(tk.Toplevel):
    """Formulario de registro de movimientos de stock."""

    def __init__(self, padre, usuario: dict):
        super().__init__(padre)
        self.usuario         = usuario
        self.es_supervisor   = (usuario["rol"] == "SUPERVISOR")
        self.producto_actual = None

        self.title("GiftNow TPS — Registrar Movimiento")
        self.resizable(False, False)
        self.configure(bg=COLOR_FONDO)
        self.grab_set()
        self._centrar(520, 640)
        self._construir_ui()
        self.entry_sku.focus_set()

    def _centrar(self, ancho, alto):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{ancho}x{alto}+{(sw-ancho)//2}+{(sh-alto)//2}")

    # ── Construcción ─────────────────────────────────────────────────────

    def _construir_ui(self):
        outer = tk.Frame(self, bg=COLOR_FONDO, padx=30, pady=20)
        outer.pack(fill="both", expand=True)

        tk.Label(outer, text="Registrar Movimiento de Stock",
                 font=FUENTE_TITULO, bg=COLOR_FONDO,
                 fg=COLOR_ACENTO).pack(anchor="w", pady=(0, 14))

        # ── Panel SKU ────────────────────────────────────────────────────
        p1 = self._panel(outer)
        p1.pack(fill="x", pady=(0, 10))
        p1.columnconfigure(0, weight=1)

        tk.Label(p1, text="Stock Code (SKU)", font=FUENTE_LABEL,
                 bg=COLOR_PANEL, fg=COLOR_TEXTO, anchor="w").grid(
                 row=0, column=0, sticky="w", padx=16, pady=(14, 2))

        fr_sku = tk.Frame(p1, bg=COLOR_PANEL)
        fr_sku.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 4))

        self.entry_sku = self._mk_entry(fr_sku)
        self.entry_sku.pack(side="left", fill="x", expand=True)
        self.entry_sku.bind("<Return>", lambda e: self._buscar_sku())

        tk.Button(fr_sku, text="Buscar", font=("Segoe UI", 9, "bold"),
                  bg=COLOR_ACENTO2, fg=COLOR_TEXTO, relief="flat",
                  cursor="hand2", padx=12,
                  command=self._buscar_sku).pack(side="left", padx=(6, 0))

        self.lbl_producto = tk.Label(p1, text="—", font=FUENTE_INFO,
                                     bg=COLOR_PANEL, fg=COLOR_SUBTEXTO,
                                     anchor="w", wraplength=440)
        self.lbl_producto.grid(row=2, column=0, sticky="w",
                               padx=16, pady=(0, 14))

        # ── Panel movimiento ─────────────────────────────────────────────
        p2 = self._panel(outer)
        p2.pack(fill="x", pady=(0, 10))
        p2.columnconfigure(0, weight=1)

        tk.Label(p2, text="Tipo de movimiento", font=FUENTE_LABEL,
                 bg=COLOR_PANEL, fg=COLOR_TEXTO, anchor="w").grid(
                 row=0, column=0, sticky="w", padx=16, pady=(14, 2))

        tipos = TIPOS_SUPERVISOR if self.es_supervisor else TIPOS_ALMACENERO
        self.var_tipo = tk.StringVar(value=tipos[0])
        self.var_tipo.trace_add("write", self._on_tipo_change)

        fr_tipos = tk.Frame(p2, bg=COLOR_PANEL)
        fr_tipos.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 10))
        for t in tipos:
            tk.Radiobutton(
                fr_tipos, text=t, variable=self.var_tipo, value=t,
                font=("Segoe UI", 9, "bold"),
                bg=COLOR_PANEL, fg=COLOR_TIPO.get(t, COLOR_TEXTO),
                selectcolor=COLOR_PANEL,
                activebackground=COLOR_PANEL,
                activeforeground=COLOR_TIPO.get(t, COLOR_TEXTO),
                relief="flat", cursor="hand2"
            ).pack(side="left", padx=(0, 14))

        tk.Label(p2, text="Cantidad", font=FUENTE_LABEL,
                 bg=COLOR_PANEL, fg=COLOR_TEXTO, anchor="w").grid(
                 row=2, column=0, sticky="w", padx=16, pady=(0, 2))
        self.entry_cantidad = self._mk_entry(p2, ancho=10)
        self.entry_cantidad.grid(row=3, column=0, sticky="w",
                                 padx=16, pady=(0, 10))

        tk.Label(p2, text="Referencia  (opcional)",
                 font=FUENTE_LABEL, bg=COLOR_PANEL,
                 fg=COLOR_TEXTO, anchor="w").grid(
                 row=4, column=0, sticky="w", padx=16, pady=(0, 2))
        self.entry_ref = self._mk_entry(p2)
        self.entry_ref.grid(row=5, column=0, sticky="ew",
                            padx=16, pady=(0, 10))

        self.lbl_motivo = tk.Label(p2, text="Motivo  (opcional)",
                                   font=FUENTE_LABEL, bg=COLOR_PANEL,
                                   fg=COLOR_TEXTO, anchor="w")
        self.lbl_motivo.grid(row=6, column=0, sticky="w", padx=16, pady=(0, 2))
        self.entry_motivo = self._mk_entry(p2)
        self.entry_motivo.grid(row=7, column=0, sticky="ew",
                               padx=16, pady=(0, 14))

        # ── Resultado ────────────────────────────────────────────────────
        self.lbl_resultado = tk.Label(outer, text="", font=FUENTE_INFO,
                                      bg=COLOR_FONDO, fg=COLOR_OK,
                                      wraplength=460, justify="left")
        self.lbl_resultado.pack(fill="x", pady=(0, 6))

        # ── Botones ──────────────────────────────────────────────────────
        fr_btns = tk.Frame(outer, bg=COLOR_FONDO)
        fr_btns.pack(fill="x")

        tk.Button(fr_btns, text="Registrar movimiento",
                  font=FUENTE_BTN, bg=COLOR_ACENTO, fg="#FFFFFF",
                  activebackground="#C73652", relief="flat",
                  cursor="hand2", pady=10,
                  command=self._registrar).pack(
                  side="left", fill="x", expand=True, padx=(0, 6))

        tk.Button(fr_btns, text="Cerrar",
                  font=FUENTE_BTN, bg=COLOR_ACENTO2, fg=COLOR_TEXTO,
                  activebackground="#0A2744", relief="flat",
                  cursor="hand2", pady=10,
                  command=self.destroy).pack(side="left", fill="x", expand=True)

        if self.es_supervisor:
            tk.Button(outer, text="+ Alta de nuevo producto (SKU)",
                      font=("Segoe UI", 8), bg=COLOR_FONDO,
                      fg=COLOR_SUBTEXTO, relief="flat", cursor="hand2",
                      command=self._alta_producto).pack(
                      anchor="w", pady=(10, 0))

    # ── Widgets auxiliares ────────────────────────────────────────────────

    def _panel(self, padre):
        return tk.Frame(padre, bg=COLOR_PANEL,
                        highlightbackground=COLOR_ACENTO2,
                        highlightthickness=1)

    def _mk_entry(self, padre, ancho=None):
        kw = dict(font=FUENTE_ENTRY, bg=COLOR_ENTRY_BG, fg=COLOR_TEXTO,
                  insertbackground=COLOR_TEXTO, relief="flat",
                  highlightthickness=1,
                  highlightbackground=COLOR_ENTRY_BD,
                  highlightcolor=COLOR_ACENTO2)
        if ancho:
            kw["width"] = ancho
        return tk.Entry(padre, **kw)

    # ── Eventos ───────────────────────────────────────────────────────────

    def _on_tipo_change(self, *args):
        tipo = self.var_tipo.get()
        if tipo == "AJUSTE":
            self.lbl_motivo.config(
                text="Motivo  [obligatorio para AJUSTE]",
                fg=COLOR_WARN)
        else:
            self.lbl_motivo.config(
                text="Motivo  (opcional)",
                fg=COLOR_TEXTO)
        self.lbl_resultado.config(text="")

    def _buscar_sku(self):
        code = self.entry_sku.get().strip().upper()
        if not code:
            self.lbl_producto.config(
                text="Ingrese un Stock Code.", fg=COLOR_ACENTO)
            self.producto_actual = None
            return
        try:
            p = buscar_por_code(code)
        except ConnectionError as e:
            messagebox.showerror("Error de conexión", str(e))
            return
        if p is None:
            self.lbl_producto.config(
                text=f"SKU '{code}' no encontrado o inactivo.",
                fg=COLOR_ACENTO)
            self.producto_actual = None
            return
        self.producto_actual = p
        self._actualizar_lbl_producto(p)

    def _actualizar_lbl_producto(self, p):
        abc_color = {"A": "#E94560", "B": "#F5A623",
                     "C": "#50C878"}.get(p["clasificacion_abc"], COLOR_TEXTO)
        self.lbl_producto.config(
            text=(f"  {p['descripcion']}  |  "
                  f"Stock: {p['stock_actual']}  |  "
                  f"Min: {p['stock_minimo']}  |  "
                  f"ABC: {p['clasificacion_abc']}  |  "
                  f"S/. {float(p['precio_unitario']):.2f}"),
            fg=abc_color)

    def _registrar(self):
        self.lbl_resultado.config(text="")

        if self.producto_actual is None:
            self._buscar_sku()
            if self.producto_actual is None:
                self.lbl_resultado.config(
                    text="Busque y seleccione un producto primero.",
                    fg=COLOR_ACENTO)
                return

        raw = self.entry_cantidad.get().strip()
        try:
            cantidad = int(raw)
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            self.lbl_resultado.config(
                text="La cantidad debe ser un entero positivo.",
                fg=COLOR_ACENTO)
            self.entry_cantidad.focus_set()
            return

        tipo       = self.var_tipo.get()
        referencia = self.entry_ref.get().strip() or None
        motivo     = self.entry_motivo.get().strip() or None
        sup_id     = self.usuario["usuario_id"] if tipo == "AJUSTE" else None

        try:
            mov_id = procesar_movimiento(
                producto_id   = self.producto_actual["producto_id"],
                tipo          = tipo,
                cantidad      = cantidad,
                usuario_id    = self.usuario["usuario_id"],
                referencia    = referencia,
                motivo        = motivo,
                supervisor_id = sup_id,
            )
        except ValueError as e:
            self.lbl_resultado.config(text=str(e), fg=COLOR_ACENTO)
            return
        except ConnectionError as e:
            messagebox.showerror("Error de conexión", str(e))
            return
        except Exception as e:
            messagebox.showerror("Error inesperado", str(e))
            return

        p2 = obtener_por_id(self.producto_actual["producto_id"])
        self.producto_actual = p2
        self._actualizar_lbl_producto(p2)
        self.lbl_resultado.config(
            text=(f"Movimiento #{mov_id} registrado.  "
                  f"Stock actualizado: {p2['stock_actual']} u."),
            fg=COLOR_OK)
        self.entry_cantidad.delete(0, tk.END)
        self.entry_ref.delete(0, tk.END)
        self.entry_motivo.delete(0, tk.END)

    def _alta_producto(self):
        _DialogAltaProducto(self, self.usuario)


# ── Diálogo alta de producto ──────────────────────────────────────────────────

class _DialogAltaProducto(tk.Toplevel):
    def __init__(self, padre, usuario):
        super().__init__(padre)
        self.usuario = usuario
        self.title("Alta de Producto")
        self.resizable(False, False)
        self.configure(bg=COLOR_FONDO)
        self.grab_set()
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"420x440+{(sw-420)//2}+{(sh-440)//2}")
        self._construir()

    def _construir(self):
        outer = tk.Frame(self, bg=COLOR_FONDO, padx=28, pady=20)
        outer.pack(fill="both", expand=True)

        tk.Label(outer, text="Alta de Nuevo Producto",
                 font=FUENTE_TITULO, bg=COLOR_FONDO,
                 fg=COLOR_ACENTO).pack(anchor="w", pady=(0, 14))

        def fila(label, attr):
            tk.Label(outer, text=label, font=FUENTE_LABEL,
                     bg=COLOR_FONDO, fg=COLOR_TEXTO, anchor="w").pack(fill="x")
            e = tk.Entry(outer, font=FUENTE_ENTRY,
                         bg=COLOR_ENTRY_BG, fg=COLOR_TEXTO,
                         insertbackground=COLOR_TEXTO, relief="flat",
                         highlightthickness=1,
                         highlightbackground=COLOR_ENTRY_BD,
                         highlightcolor=COLOR_ACENTO2)
            e.pack(fill="x", pady=(2, 8))
            setattr(self, attr, e)

        fila("Stock Code *",            "e_sc")
        fila("Descripcion *",           "e_desc")
        fila("Stock inicial *",         "e_stock")
        fila("Stock minimo *",          "e_min")
        fila("Precio unitario (S/.) *", "e_precio")

        self.lbl_err = tk.Label(outer, text="", font=("Segoe UI", 9),
                                bg=COLOR_FONDO, fg=COLOR_ACENTO,
                                wraplength=360, anchor="w")
        self.lbl_err.pack(fill="x", pady=(0, 6))

        fr = tk.Frame(outer, bg=COLOR_FONDO)
        fr.pack(fill="x")
        tk.Button(fr, text="Guardar", font=FUENTE_BTN,
                  bg=COLOR_ACENTO, fg="#FFFFFF", relief="flat",
                  cursor="hand2", pady=8,
                  command=self._guardar).pack(
                  side="left", fill="x", expand=True, padx=(0, 6))
        tk.Button(fr, text="Cancelar", font=FUENTE_BTN,
                  bg=COLOR_ACENTO2, fg=COLOR_TEXTO, relief="flat",
                  cursor="hand2", pady=8,
                  command=self.destroy).pack(side="left", fill="x", expand=True)

    def _guardar(self):
        self.lbl_err.config(text="")
        sc    = self.e_sc.get().strip().upper()
        desc  = self.e_desc.get().strip()
        try:
            stock_ini = int(self.e_stock.get().strip())
            stock_min = int(self.e_min.get().strip())
            precio    = float(self.e_precio.get().strip())
            if not sc or not desc:
                raise ValueError("Campos obligatorios vacíos.")
            if stock_ini < 0 or stock_min < 0 or precio < 0:
                raise ValueError("Valores no pueden ser negativos.")
        except ValueError as e:
            self.lbl_err.config(text=f"  {e}")
            return
        try:
            pid = insertar_producto(
                stock_code      = sc,
                descripcion     = desc,
                stock_actual    = stock_ini,
                stock_minimo    = stock_min,
                precio_unitario = precio,
                usuario_alta_id = self.usuario["usuario_id"],
            )
            from logica.logica_abc import recalcular_abc
            recalcular_abc()
            messagebox.showinfo("Producto creado",
                                f"'{sc}' creado (id={pid}).")
            self.destroy()
        except Exception as e:
            self.lbl_err.config(text=f"  {e}")
