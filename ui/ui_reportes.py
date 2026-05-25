# ui/ui_reportes.py
# Capa de presentación — panel de reportes del almacén.
# Sin SQL directo. Usa logica_reportes.

import tkinter as tk
from tkinter import ttk, messagebox
from logica.logica_reportes import (reporte_valorizacion,
                                     reporte_rotacion,
                                     reporte_alertas_historico)

COLOR_FONDO    = "#1A1A2E"
COLOR_PANEL    = "#16213E"
COLOR_ACENTO   = "#E94560"
COLOR_ACENTO2  = "#0F3460"
COLOR_TEXTO    = "#EAEAEA"
COLOR_SUBTEXTO = "#A0A0B0"
COLOR_OK       = "#50C878"
COLOR_WARN     = "#F5A623"
COLOR_TABLA_BG = "#0D1B2A"
COLOR_TABLA_HD = "#0F3460"
COLOR_FILA_PAR = "#131C2E"
COLOR_FILA_IMP = "#0D1525"

FUENTE_TITULO = ("Segoe UI", 13, "bold")
FUENTE_SEC    = ("Segoe UI", 11, "bold")
FUENTE_LABEL  = ("Segoe UI", 9, "bold")
FUENTE_ENTRY  = ("Segoe UI", 10)
FUENTE_BTN    = ("Segoe UI", 10, "bold")
FUENTE_INFO   = ("Segoe UI", 9)
FUENTE_TABLA  = ("Segoe UI", 9)
FUENTE_KPI    = ("Segoe UI", 20, "bold")
FUENTE_KPI_L  = ("Segoe UI", 9)


class PanelReportes(tk.Toplevel):
    """Panel de reportes del almacén — solo Supervisor."""

    def __init__(self, padre, usuario: dict):
        super().__init__(padre)
        self.usuario = usuario
        self.title("GiftNow TPS — Reportes del Almacén")
        self.configure(bg=COLOR_FONDO)
        self.grab_set()
        self._centrar(900, 660)
        self._construir_ui()
        self._cargar_valorizacion()   # reporte inicial

    def _centrar(self, ancho, alto):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{ancho}x{alto}+{(sw-ancho)//2}+{(sh-alto)//2}")

    # ── Construcción ─────────────────────────────────────────────────────

    def _construir_ui(self):
        outer = tk.Frame(self, bg=COLOR_FONDO, padx=28, pady=16)
        outer.pack(fill="both", expand=True)

        tk.Label(outer, text="Reportes del Almacén",
                 font=FUENTE_TITULO, bg=COLOR_FONDO,
                 fg=COLOR_ACENTO).pack(anchor="w", pady=(0, 12))

        # ── Pestañas de reporte ──────────────────────────────────────────
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Report.TNotebook",
                         background=COLOR_FONDO, borderwidth=0)
        style.configure("Report.TNotebook.Tab",
                         background=COLOR_PANEL, foreground=COLOR_SUBTEXTO,
                         font=("Segoe UI", 9, "bold"), padding=(14, 6))
        style.map("Report.TNotebook.Tab",
                  background=[("selected", COLOR_ACENTO2)],
                  foreground=[("selected", COLOR_TEXTO)])

        nb = ttk.Notebook(outer, style="Report.TNotebook")
        nb.pack(fill="both", expand=True)

        # Tab 1: Valorización
        self.tab_val = tk.Frame(nb, bg=COLOR_FONDO)
        nb.add(self.tab_val, text="  Valorización ABC  ")
        self._construir_tab_valorizacion(self.tab_val)

        # Tab 2: Rotación
        self.tab_rot = tk.Frame(nb, bg=COLOR_FONDO)
        nb.add(self.tab_rot, text="  Rotación por SKU  ")
        self._construir_tab_rotacion(self.tab_rot)

        # Tab 3: Alertas históricas
        self.tab_alert = tk.Frame(nb, bg=COLOR_FONDO)
        nb.add(self.tab_alert, text="  Alertas Históricas  ")
        self._construir_tab_alertas(self.tab_alert)

        nb.bind("<<NotebookTabChanged>>", self._on_tab_change)

        # Botón cerrar
        tk.Button(outer, text="Cerrar", font=FUENTE_BTN,
                  bg=COLOR_ACENTO2, fg=COLOR_TEXTO, relief="flat",
                  cursor="hand2", pady=8,
                  command=self.destroy).pack(fill="x", pady=(10, 0))

    # ── TAB 1: Valorización ───────────────────────────────────────────────

    def _construir_tab_valorizacion(self, padre):
        outer = tk.Frame(padre, bg=COLOR_FONDO, padx=0, pady=10)
        outer.pack(fill="both", expand=True)

        # KPIs
        self.fr_kpi = tk.Frame(outer, bg=COLOR_FONDO)
        self.fr_kpi.pack(fill="x", pady=(0, 10))
        self.kpi_global  = self._kpi_card(self.fr_kpi, "Valor Global S/.", "—", COLOR_ACENTO)
        self.kpi_skus    = self._kpi_card(self.fr_kpi, "Total SKUs",         "—", COLOR_ACENTO2)
        self.kpi_val_a   = self._kpi_card(self.fr_kpi, "Valor ABC-A",        "—", "#E94560")
        self.kpi_val_b   = self._kpi_card(self.fr_kpi, "Valor ABC-B",        "—", COLOR_WARN)
        self.kpi_val_c   = self._kpi_card(self.fr_kpi, "Valor ABC-C",        "—", COLOR_OK)

        # Botón actualizar
        tk.Button(outer, text="Actualizar reporte",
                  font=("Segoe UI", 9, "bold"), bg=COLOR_ACENTO, fg="#FFFFFF",
                  relief="flat", cursor="hand2", padx=14,
                  command=self._cargar_valorizacion).pack(anchor="e", padx=4, pady=(0, 6))

        # Tabla
        cols_v = ("sku", "descripcion", "abc", "stock", "precio", "valor")
        cabs_v = ("SKU", "Descripción", "ABC", "Stock", "Precio unit.", "Valor total S/.")
        anc_v  = (100, 260, 45, 70, 100, 120)
        self.tree_val = self._mk_tree(outer, cols_v, cabs_v, anc_v, "Val.Treeview")
        self.tree_val.tag_configure("A", foreground="#E94560")
        self.tree_val.tag_configure("B", foreground=COLOR_WARN)
        self.tree_val.tag_configure("C", foreground=COLOR_OK)

    def _cargar_valorizacion(self):
        try:
            data = reporte_valorizacion()
        except Exception as e:
            messagebox.showerror("Error", str(e)); return

        # KPIs
        self.kpi_global[1].config(text=f"S/. {data['valor_global']:,.2f}")
        self.kpi_skus[1].config(text=str(data["total_skus"]))
        for cat, widget in [("A", self.kpi_val_a),
                             ("B", self.kpi_val_b),
                             ("C", self.kpi_val_c)]:
            r = data["resumen"][cat]
            widget[1].config(
                text=f"S/. {r['valor_total']:,.0f}\n{r['pct_valor']:.1f}%  ({r['cantidad_skus']} SKUs)")

        # Tabla
        self.tree_val.delete(*self.tree_val.get_children())
        for i, p in enumerate(data["productos"]):
            tag_abc  = p["clasificacion_abc"]
            tag_fila = "par" if i % 2 == 0 else "imp"
            self.tree_val.insert("", "end", tags=(tag_abc, tag_fila),
                                 values=(
                                     p["stock_code"],
                                     p["descripcion"],
                                     p["clasificacion_abc"],
                                     p["stock_actual"],
                                     f"S/. {p['precio_unitario']:.2f}",
                                     f"S/. {p['valor_total']:,.2f}",
                                 ))

    # ── TAB 2: Rotación ───────────────────────────────────────────────────

    def _construir_tab_rotacion(self, padre):
        outer = tk.Frame(padre, bg=COLOR_FONDO, padx=0, pady=10)
        outer.pack(fill="both", expand=True)

        # Filtro de período
        fr_f = tk.Frame(outer, bg=COLOR_PANEL,
                        highlightbackground=COLOR_ACENTO2,
                        highlightthickness=1)
        fr_f.pack(fill="x", pady=(0, 8))
        fi = tk.Frame(fr_f, bg=COLOR_PANEL, padx=14, pady=10)
        fi.pack(fill="x")

        tk.Label(fi, text="Período — desde (YYYY-MM-DD):",
                 font=FUENTE_LABEL, bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(side="left")
        self.entry_desde = tk.Entry(fi, width=12, font=FUENTE_ENTRY,
                                    bg="#0D1B2A", fg=COLOR_TEXTO,
                                    insertbackground=COLOR_TEXTO, relief="flat",
                                    highlightthickness=1,
                                    highlightbackground="#2A3F5F")
        self.entry_desde.pack(side="left", padx=(6, 16))

        tk.Label(fi, text="hasta:", font=FUENTE_LABEL,
                 bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(side="left")
        self.entry_hasta = tk.Entry(fi, width=12, font=FUENTE_ENTRY,
                                    bg="#0D1B2A", fg=COLOR_TEXTO,
                                    insertbackground=COLOR_TEXTO, relief="flat",
                                    highlightthickness=1,
                                    highlightbackground="#2A3F5F")
        self.entry_hasta.pack(side="left", padx=(6, 16))

        tk.Button(fi, text="Generar", font=("Segoe UI", 9, "bold"),
                  bg=COLOR_ACENTO, fg="#FFFFFF", relief="flat",
                  cursor="hand2", padx=12,
                  command=self._cargar_rotacion).pack(side="left")

        tk.Label(fi, text="(dejar vacío = todo el período)",
                 font=("Segoe UI", 8), bg=COLOR_PANEL,
                 fg=COLOR_SUBTEXTO).pack(side="left", padx=(10, 0))

        # Contador
        self.lbl_rot_info = tk.Label(outer, text="", font=FUENTE_INFO,
                                     bg=COLOR_FONDO, fg=COLOR_SUBTEXTO, anchor="w")
        self.lbl_rot_info.pack(fill="x", pady=(0, 4))

        # Tabla
        cols_r = ("sku", "descripcion", "abc", "entradas",
                  "salidas", "devoluciones", "ajustes", "total")
        cabs_r = ("SKU", "Descripción", "ABC", "Entradas",
                  "Salidas", "Devoluciones", "Ajustes", "Total mov.")
        anc_r  = (100, 230, 45, 75, 75, 90, 65, 80)
        self.tree_rot = self._mk_tree(outer, cols_r, cabs_r, anc_r, "Rot.Treeview")

    def _cargar_rotacion(self):
        desde = self.entry_desde.get().strip() or None
        hasta = self.entry_hasta.get().strip() or None
        try:
            data = reporte_rotacion(desde, hasta)
        except Exception as e:
            messagebox.showerror("Error", str(e)); return

        self.lbl_rot_info.config(
            text=f"  {data['total_movimientos']} movimiento(s) en el período  |  "
                 f"{len(data['productos'])} SKU(s) con actividad")

        self.tree_rot.delete(*self.tree_rot.get_children())
        for i, p in enumerate(data["productos"]):
            tag_fila = "par" if i % 2 == 0 else "imp"
            self.tree_rot.insert("", "end", tags=(tag_fila,),
                                 values=(
                                     p["stock_code"],
                                     p["descripcion"],
                                     p["clasificacion_abc"],
                                     p["entradas"],
                                     p["salidas"],
                                     p["devoluciones"],
                                     p["ajustes"],
                                     p["total_movimientos"],
                                 ))

    # ── TAB 3: Alertas históricas ────────────────────────────────────────

    def _construir_tab_alertas(self, padre):
        outer = tk.Frame(padre, bg=COLOR_FONDO, padx=0, pady=10)
        outer.pack(fill="both", expand=True)

        tk.Button(outer, text="Actualizar",
                  font=("Segoe UI", 9, "bold"), bg=COLOR_ACENTO2,
                  fg=COLOR_TEXTO, relief="flat", cursor="hand2", padx=12,
                  command=self._cargar_alertas_hist).pack(anchor="e", pady=(0, 6))

        # KPIs resumen
        self.fr_kpi_al = tk.Frame(outer, bg=COLOR_FONDO)
        self.fr_kpi_al.pack(fill="x", pady=(0, 8))
        self.kpi_al_act = self._kpi_card(self.fr_kpi_al, "Activas",     "—", "#E94560")
        self.kpi_al_ges = self._kpi_card(self.fr_kpi_al, "En gestión",  "—", COLOR_WARN)
        self.kpi_al_ate = self._kpi_card(self.fr_kpi_al, "Atendidas",   "—", COLOR_OK)
        self.kpi_al_tot = self._kpi_card(self.fr_kpi_al, "Total",       "—", COLOR_ACENTO2)

        # Tabla
        cols_a = ("sku", "descripcion", "abc", "stock_critico",
                  "stock_min", "fecha_act", "estado", "observacion")
        cabs_a = ("SKU", "Descripción", "ABC", "Stock crítico",
                  "Stock mín.", "Activación", "Estado", "Observación")
        anc_a  = (90, 200, 40, 90, 80, 130, 90, 180)
        self.tree_alert = self._mk_tree(outer, cols_a, cabs_a, anc_a, "AH.Treeview")
        self.tree_alert.tag_configure("ACTIVA",     foreground="#E94560")
        self.tree_alert.tag_configure("EN_GESTION", foreground=COLOR_WARN)
        self.tree_alert.tag_configure("ATENDIDA",   foreground=COLOR_OK)

    def _cargar_alertas_hist(self):
        try:
            data = reporte_alertas_historico()
        except Exception as e:
            messagebox.showerror("Error", str(e)); return

        self.kpi_al_act[1].config(text=str(data["resumen"]["ACTIVA"]))
        self.kpi_al_ges[1].config(text=str(data["resumen"]["EN_GESTION"]))
        self.kpi_al_ate[1].config(text=str(data["resumen"]["ATENDIDA"]))
        self.kpi_al_tot[1].config(text=str(data["total"]))

        self.tree_alert.delete(*self.tree_alert.get_children())
        for i, a in enumerate(data["alertas"]):
            tag_estado = a.get("estado", "ACTIVA")
            tag_fila   = "par" if i % 2 == 0 else "imp"
            fecha = str(a["fecha_activacion"])[:16] if a["fecha_activacion"] else "—"
            self.tree_alert.insert("", "end",
                                   tags=(tag_estado, tag_fila),
                                   values=(
                                       a["stock_code"],
                                       a["descripcion"],
                                       a["clasificacion_abc"],
                                       a["stock_al_activar"],
                                       a["stock_minimo_ref"],
                                       fecha,
                                       a["estado"],
                                       a["observacion"] or "—",
                                   ))

    # ── Cambio de pestaña ────────────────────────────────────────────────

    def _on_tab_change(self, event):
        nb  = event.widget
        tab = nb.tab(nb.select(), "text").strip()
        if "Rotación" in tab and not self.tree_rot.get_children():
            self._cargar_rotacion()
        elif "Alertas" in tab and not self.tree_alert.get_children():
            self._cargar_alertas_hist()

    # ── Widgets auxiliares ────────────────────────────────────────────────

    def _kpi_card(self, padre, etiqueta, valor, color):
        fr = tk.Frame(padre, bg=COLOR_PANEL,
                      highlightbackground=color, highlightthickness=2)
        fr.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(fr, text=etiqueta, font=FUENTE_KPI_L,
                 bg=COLOR_PANEL, fg=COLOR_SUBTEXTO).pack(pady=(8, 0))
        lbl = tk.Label(fr, text=valor, font=FUENTE_KPI,
                       bg=COLOR_PANEL, fg=color)
        lbl.pack(pady=(0, 8))
        return fr, lbl

    def _mk_tree(self, padre, cols, cabs, anchos, style_name):
        style = ttk.Style()
        style.configure(f"{style_name}",
                         background=COLOR_TABLA_BG, foreground=COLOR_TEXTO,
                         fieldbackground=COLOR_TABLA_BG, rowheight=22,
                         font=FUENTE_TABLA)
        style.configure(f"{style_name}.Heading",
                         background=COLOR_TABLA_HD, foreground=COLOR_TEXTO,
                         font=("Segoe UI", 9, "bold"), relief="flat")
        style.map(f"{style_name}",
                  background=[("selected", COLOR_ACENTO2)])

        fr = tk.Frame(padre, bg=COLOR_FONDO)
        fr.pack(fill="both", expand=True)

        tree = ttk.Treeview(fr, columns=cols, show="headings",
                             style=style_name, selectmode="browse")
        for col, cab, ancho in zip(cols, cabs, anchos):
            tree.heading(col, text=cab)
            tree.column(col, width=ancho, minwidth=40, anchor="center")
        if "descripcion" in cols:
            tree.column("descripcion", anchor="w")
        if "observacion" in cols:
            tree.column("observacion", anchor="w")

        sv = ttk.Scrollbar(fr, orient="vertical", command=tree.yview)
        sh = ttk.Scrollbar(fr, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=sv.set, xscrollcommand=sh.set)
        tree.grid(row=0, column=0, sticky="nsew")
        sv.grid(row=0, column=1, sticky="ns")
        sh.grid(row=1, column=0, sticky="ew")
        fr.rowconfigure(0, weight=1)
        fr.columnconfigure(0, weight=1)

        tree.tag_configure("par", background=COLOR_FILA_PAR)
        tree.tag_configure("imp", background=COLOR_FILA_IMP)
        return tree
