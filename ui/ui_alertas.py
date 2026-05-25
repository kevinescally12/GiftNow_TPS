# ui/ui_alertas.py
# Capa de presentación — panel de alertas activas.
# Solo Supervisor puede actualizar estado.
# Sin SQL directo. Usa datos_alerta.

import tkinter as tk
from tkinter import ttk, messagebox
from datos.datos_alerta import listar_activas, actualizar_estado

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

COLOR_ESTADO = {
    "ACTIVA":     "#E94560",
    "EN_GESTION": "#F5A623",
    "ATENDIDA":   "#50C878",
}


class PanelAlertas(tk.Toplevel):
    """Panel de alertas activas y en gestión. Solo Supervisor."""

    def __init__(self, padre, usuario: dict):
        super().__init__(padre)
        self.usuario = usuario
        self.alertas = []   # caché de filas cargadas
        self.title("GiftNow TPS — Alertas de Stock")
        self.configure(bg=COLOR_FONDO)
        self.grab_set()
        self._centrar(860, 560)
        self._construir_ui()
        self._cargar_alertas()

    def _centrar(self, ancho, alto):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{ancho}x{alto}+{(sw-ancho)//2}+{(sh-alto)//2}")

    # ── Construcción ─────────────────────────────────────────────────────

    def _construir_ui(self):
        outer = tk.Frame(self, bg=COLOR_FONDO, padx=28, pady=18)
        outer.pack(fill="both", expand=True)

        # Encabezado
        fr_enc = tk.Frame(outer, bg=COLOR_FONDO)
        fr_enc.pack(fill="x", pady=(0, 12))
        tk.Label(fr_enc, text="Panel de Alertas de Stock",
                 font=FUENTE_TITULO, bg=COLOR_FONDO,
                 fg=COLOR_ACENTO).pack(side="left")
        tk.Button(fr_enc, text="Actualizar",
                  font=("Segoe UI", 9), bg=COLOR_ACENTO2, fg=COLOR_TEXTO,
                  relief="flat", cursor="hand2", padx=12,
                  command=self._cargar_alertas).pack(side="right")

        # Contador
        self.lbl_contador = tk.Label(outer, text="",
                                     font=FUENTE_INFO, bg=COLOR_FONDO,
                                     fg=COLOR_SUBTEXTO, anchor="w")
        self.lbl_contador.pack(fill="x", pady=(0, 6))

        # ── Tabla de alertas ─────────────────────────────────────────────
        cols = ("sku", "descripcion", "abc", "stock_critico",
                "stock_minimo", "fecha", "estado")
        cabs = ("SKU", "Descripción", "ABC", "Stock crítico",
                "Stock mín.", "Fecha activación", "Estado")
        anchos = (100, 220, 45, 95, 80, 140, 90)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Alert.Treeview",
                         background=COLOR_TABLA_BG, foreground=COLOR_TEXTO,
                         fieldbackground=COLOR_TABLA_BG, rowheight=24,
                         font=FUENTE_TABLA)
        style.configure("Alert.Treeview.Heading",
                         background=COLOR_TABLA_HD, foreground=COLOR_TEXTO,
                         font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Alert.Treeview",
                  background=[("selected", "#1A3A5C")])

        fr_t = tk.Frame(outer, bg=COLOR_FONDO)
        fr_t.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(fr_t, columns=cols, show="headings",
                                  style="Alert.Treeview", selectmode="browse")
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

        # Tags de color por estado
        self.tree.tag_configure("ACTIVA",     foreground="#E94560")
        self.tree.tag_configure("EN_GESTION", foreground="#F5A623")
        self.tree.tag_configure("par",        background=COLOR_FILA_PAR)
        self.tree.tag_configure("imp",        background=COLOR_FILA_IMP)

        # ── Panel de acción ──────────────────────────────────────────────
        p_acc = tk.Frame(outer, bg=COLOR_PANEL,
                         highlightbackground=COLOR_ACENTO2,
                         highlightthickness=1)
        p_acc.pack(fill="x", pady=(10, 0))

        fr_acc = tk.Frame(p_acc, bg=COLOR_PANEL, padx=16, pady=12)
        fr_acc.pack(fill="x")

        tk.Label(fr_acc, text="Seleccione una alerta y actualice su estado:",
                 font=FUENTE_LABEL, bg=COLOR_PANEL,
                 fg=COLOR_TEXTO).grid(row=0, column=0, columnspan=4,
                                      sticky="w", pady=(0, 8))

        # Nuevo estado
        tk.Label(fr_acc, text="Nuevo estado:", font=FUENTE_LABEL,
                 bg=COLOR_PANEL, fg=COLOR_SUBTEXTO).grid(
                 row=1, column=0, sticky="w", padx=(0, 8))

        self.var_estado = tk.StringVar(value="EN_GESTION")
        for i, (estado, texto) in enumerate([
                ("EN_GESTION", "En gestión"),
                ("ATENDIDA",   "Atendida")]):
            tk.Radiobutton(
                fr_acc, text=texto, variable=self.var_estado, value=estado,
                font=("Segoe UI", 9, "bold"),
                bg=COLOR_PANEL, fg=COLOR_ESTADO[estado],
                selectcolor=COLOR_PANEL, activebackground=COLOR_PANEL,
                activeforeground=COLOR_ESTADO[estado],
                relief="flat", cursor="hand2"
            ).grid(row=1, column=i + 1, padx=(0, 16))

        # Observación
        tk.Label(fr_acc, text="Observación:", font=FUENTE_LABEL,
                 bg=COLOR_PANEL, fg=COLOR_SUBTEXTO).grid(
                 row=2, column=0, sticky="w", pady=(8, 0), padx=(0, 8))

        self.entry_obs = tk.Entry(
            fr_acc, font=FUENTE_ENTRY, bg=COLOR_ENTRY_BG, fg=COLOR_TEXTO,
            insertbackground=COLOR_TEXTO, relief="flat",
            highlightthickness=1, highlightbackground=COLOR_ENTRY_BD,
            highlightcolor=COLOR_ACENTO2, width=40)
        self.entry_obs.grid(row=2, column=1, columnspan=2,
                            sticky="ew", pady=(8, 0))
        fr_acc.columnconfigure(2, weight=1)

        tk.Button(fr_acc, text="Actualizar estado",
                  font=FUENTE_BTN, bg=COLOR_ACENTO, fg="#FFFFFF",
                  activebackground="#C73652", relief="flat",
                  cursor="hand2", padx=16, pady=6,
                  command=self._actualizar_estado).grid(
                  row=2, column=3, padx=(10, 0), pady=(8, 0))

        # Resultado
        self.lbl_resultado = tk.Label(outer, text="", font=FUENTE_INFO,
                                      bg=COLOR_FONDO, fg=COLOR_OK,
                                      anchor="w")
        self.lbl_resultado.pack(fill="x", pady=(6, 0))

        # Cerrar
        tk.Button(outer, text="Cerrar", font=FUENTE_BTN,
                  bg=COLOR_ACENTO2, fg=COLOR_TEXTO, relief="flat",
                  cursor="hand2", pady=8,
                  command=self.destroy).pack(fill="x", pady=(8, 0))

    # ── Lógica ────────────────────────────────────────────────────────────

    def _cargar_alertas(self):
        self.lbl_resultado.config(text="")
        self.tree.delete(*self.tree.get_children())
        try:
            self.alertas = listar_activas()
        except ConnectionError as e:
            messagebox.showerror("Error de conexión", str(e))
            return

        activas    = sum(1 for a in self.alertas if a["estado"] == "ACTIVA")
        en_gestion = sum(1 for a in self.alertas if a["estado"] == "EN_GESTION")
        self.lbl_contador.config(
            text=f"  {len(self.alertas)} alerta(s) pendiente(s):  "
                 f"{activas} ACTIVA(S)  ·  {en_gestion} EN GESTIÓN",
            fg=COLOR_ACENTO if self.alertas else COLOR_OK)

        for i, a in enumerate(self.alertas):
            tag_estado = a["estado"]
            tag_fila   = "par" if i % 2 == 0 else "imp"
            fecha = str(a["fecha_activacion"])[:16] if a["fecha_activacion"] else "—"
            self.tree.insert("", "end",
                             iid=str(a["alerta_id"]),
                             tags=(tag_estado, tag_fila),
                             values=(
                                 a["stock_code"],
                                 a["descripcion"],
                                 a["clasificacion_abc"],
                                 a["stock_al_activar"],
                                 a["stock_minimo_ref"],
                                 fecha,
                                 a["estado"],
                             ))

    def _actualizar_estado(self):
        self.lbl_resultado.config(text="")
        sel = self.tree.selection()
        if not sel:
            self.lbl_resultado.config(
                text="Seleccione una alerta de la tabla primero.",
                fg=COLOR_ACENTO)
            return

        alerta_id  = int(sel[0])
        nuevo_est  = self.var_estado.get()
        observacion = self.entry_obs.get().strip() or None

        # Recuperar producto_id de la alerta seleccionada
        alerta = next((a for a in self.alertas
                       if a["alerta_id"] == alerta_id), None)
        if alerta is None:
            self.lbl_resultado.config(
                text="Alerta no encontrada. Actualice el panel.",
                fg=COLOR_ACENTO)
            return

        # Verificar que el estado no retroceda
        orden = {"ACTIVA": 0, "EN_GESTION": 1, "ATENDIDA": 2}
        if orden[nuevo_est] <= orden[alerta["estado"]]:
            self.lbl_resultado.config(
                text=f"No se puede pasar de '{alerta['estado']}' a '{nuevo_est}'. "
                     f"El estado solo puede avanzar.",
                fg=COLOR_ACENTO)
            return

        try:
            actualizar_estado(
                producto_id  = alerta["producto_id"],
                nuevo_estado = nuevo_est,
                usuario_id   = self.usuario["usuario_id"],
                observacion  = observacion,
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        self.lbl_resultado.config(
            text=f"Alerta #{alerta_id} ({alerta['stock_code']}) "
                 f"→ estado actualizado a '{nuevo_est}'.",
            fg=COLOR_OK)
        self.entry_obs.delete(0, tk.END)
        self._cargar_alertas()   # refrescar tabla
