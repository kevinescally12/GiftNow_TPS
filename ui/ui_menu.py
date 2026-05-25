# ui/ui_menu.py
# Capa de presentación — menú principal diferenciado por rol.
# El control de rol (habilitar/deshabilitar opciones) se implementa AQUÍ.
# Sin SQL directo ni lógica de negocio.

import tkinter as tk
from tkinter import messagebox

# Paleta (igual que ui_login para consistencia visual)
COLOR_FONDO    = "#1A1A2E"
COLOR_PANEL    = "#16213E"
COLOR_ACENTO   = "#E94560"
COLOR_ACENTO2  = "#0F3460"
COLOR_TEXTO    = "#EAEAEA"
COLOR_SUBTEXTO = "#A0A0B0"
COLOR_DISABLED = "#3A3A4A"
COLOR_BTN_A    = "#E94560"   # rojo — acciones principales
COLOR_BTN_B    = "#0F3460"   # azul — acciones secundarias
COLOR_BTN_SAL  = "#2D2D3F"   # salir

FUENTE_TITULO  = ("Segoe UI", 16, "bold")
FUENTE_ROL     = ("Segoe UI", 10)
FUENTE_SEC     = ("Segoe UI", 10, "bold")
FUENTE_BTN     = ("Segoe UI", 10, "bold")
FUENTE_FOOTER  = ("Segoe UI", 8)


def abrir_menu_principal(usuario: dict, ventana_login=None):
    """Crea y lanza la ventana de menú principal.
    usuario: dict retornado por autenticar_usuario().
    ventana_login: instancia de VentanaLogin, se destruye al cerrar sesión."""

    menu = _VentanaMenu(usuario, ventana_login)
    menu.mainloop()


class _VentanaMenu(tk.Toplevel):
    """Ventana de menú principal del TPS GiftNow."""

    def __init__(self, usuario: dict, ventana_login=None):
        super().__init__()
        self.usuario       = usuario
        self.ventana_login = ventana_login
        self.es_supervisor = (usuario["rol"] == "SUPERVISOR")

        self.title("GiftNow TPS — Menú Principal")
        self.resizable(False, False)
        self.configure(bg=COLOR_FONDO)
        self.protocol("WM_DELETE_WINDOW", self._cerrar_sesion)
        self._centrar_ventana(480, 560)
        self._construir_ui()

    # ── Posicionamiento ──────────────────────────────────────────────────────

    def _centrar_ventana(self, ancho, alto):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - ancho) // 2
        y  = (sh - alto)  // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    # ── Construcción de UI ───────────────────────────────────────────────────

    def _construir_ui(self):
        outer = tk.Frame(self, bg=COLOR_FONDO, padx=36, pady=28)
        outer.pack(fill="both", expand=True)

        # Encabezado
        tk.Label(outer, text="🎁  GiftNow TPS",
                 font=FUENTE_TITULO, bg=COLOR_FONDO,
                 fg=COLOR_ACENTO).pack(anchor="w")

        # Información del usuario
        rol_label = "Supervisor" if self.es_supervisor else "Almacenero"
        rol_color = "#F5A623" if self.es_supervisor else "#50C878"
        info_frame = tk.Frame(outer, bg=COLOR_FONDO)
        info_frame.pack(fill="x", pady=(4, 20))
        tk.Label(info_frame,
                 text=f"  {self.usuario['nombre_completo']}",
                 font=FUENTE_ROL, bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(side="left")
        tk.Label(info_frame,
                 text=f"  [{rol_label}]",
                 font=("Segoe UI", 9, "bold"),
                 bg=COLOR_FONDO, fg=rol_color).pack(side="left")

        separador = tk.Frame(outer, bg=COLOR_ACENTO2, height=1)
        separador.pack(fill="x", pady=(0, 20))

        # ── Sección: Movimientos de Stock ──────────────────────────────────
        self._seccion(outer, "📦  Movimientos de Stock")

        self._boton_menu(
            outer,
            texto="Registrar Movimiento",
            subtexto="Entrada · Salida · Devolución · Ajuste",
            color=COLOR_BTN_A,
            comando=self._abrir_movimiento,
            habilitado=True
        )

        # ── Sección: Consultas ────────────────────────────────────────────
        self._seccion(outer, "🔍  Consultas")

        self._boton_menu(
            outer,
            texto="Consultar Stock por SKU",
            subtexto="Stock actual · Historial de movimientos",
            color=COLOR_BTN_B,
            comando=self._abrir_consulta,
            habilitado=True
        )

        # ── Sección: Alertas (solo SUPERVISOR) ───────────────────────────
        self._seccion(outer, "🔔  Alertas de Stock")

        self._boton_menu(
            outer,
            texto="Panel de Alertas",
            subtexto="Ver alertas activas · Actualizar estado",
            color=COLOR_BTN_B,
            comando=self._abrir_alertas,
            habilitado=self.es_supervisor
        )

        # ── Sección: Reportes (solo SUPERVISOR) ───────────────────────────
        self._seccion(outer, "📊  Reportes")

        self._boton_menu(
            outer,
            texto="Reportes del Almacén",
            subtexto="Valorización · Rotación · ABC · Alertas históricas",
            color=COLOR_BTN_B,
            comando=self._abrir_reportes,
            habilitado=self.es_supervisor
        )

        # ── Cerrar sesión ──────────────────────────────────────────────────
        tk.Frame(outer, bg=COLOR_FONDO, height=16).pack()
        btn_salir = tk.Button(outer, text="Cerrar sesión",
                              font=("Segoe UI", 9), bg=COLOR_BTN_SAL,
                              fg=COLOR_SUBTEXTO,
                              activebackground="#3A3A4A",
                              activeforeground=COLOR_TEXTO,
                              relief="flat", cursor="hand2", pady=6,
                              command=self._cerrar_sesion)
        btn_salir.pack(fill="x")

        # Footer
        tk.Label(outer,
                 text="Área de Almacén e Inventarios  •  GiftNow S.A.C.",
                 font=FUENTE_FOOTER, bg=COLOR_FONDO,
                 fg=COLOR_SUBTEXTO).pack(side="bottom", pady=(12, 0))

    # ── Widgets reutilizables ────────────────────────────────────────────────

    def _seccion(self, padre, texto: str):
        tk.Label(padre, text=texto, font=FUENTE_SEC,
                 bg=COLOR_FONDO, fg=COLOR_SUBTEXTO,
                 anchor="w").pack(fill="x", pady=(0, 4))

    def _boton_menu(self, padre, texto: str, subtexto: str,
                    color: str, comando, habilitado: bool):
        """Botón de menú con título y descripción.
        Si habilitado=False se muestra en gris con leyenda de rol."""
        frame = tk.Frame(padre, bg=COLOR_FONDO)
        frame.pack(fill="x", pady=(0, 10))

        if habilitado:
            bg_color  = color
            fg_color  = "#FFFFFF"
            cursor    = "hand2"
            cmd       = comando
            sub_color = "#DDDDDD"
        else:
            bg_color  = COLOR_DISABLED
            fg_color  = COLOR_SUBTEXTO
            cursor    = "arrow"
            cmd       = lambda: None
            subtexto  = subtexto + "  [Solo Supervisor]"
            sub_color = "#555566"

        btn_frame = tk.Frame(frame, bg=bg_color, cursor=cursor)
        btn_frame.pack(fill="x")

        inner = tk.Frame(btn_frame, bg=bg_color, padx=16, pady=10)
        inner.pack(fill="x")

        lbl_texto = tk.Label(inner, text=texto, font=FUENTE_BTN,
                             bg=bg_color, fg=fg_color, anchor="w")
        lbl_texto.pack(fill="x")

        lbl_sub = tk.Label(inner, text=subtexto,
                           font=("Segoe UI", 8), bg=bg_color,
                           fg=sub_color, anchor="w")
        lbl_sub.pack(fill="x")

        if habilitado:
            # Bind click en todo el frame
            for widget in [btn_frame, inner, lbl_texto, lbl_sub]:
                widget.bind("<Button-1>", lambda e: cmd())
            # Hover
            for widget in [btn_frame, inner, lbl_texto, lbl_sub]:
                widget.bind("<Enter>",
                            lambda e, c=color: self._hover_on(e, c))
                widget.bind("<Leave>",
                            lambda e, c=color: self._hover_off(e, c))

    def _hover_on(self, event, color_base: str):
        """Aclara levemente el fondo al pasar el cursor."""
        widget = event.widget
        try:
            r = int(color_base[1:3], 16)
            g = int(color_base[3:5], 16)
            b = int(color_base[5:7], 16)
            r = min(255, r + 20)
            g = min(255, g + 20)
            b = min(255, b + 20)
            nuevo = f"#{r:02x}{g:02x}{b:02x}"
            widget.configure(bg=nuevo)
        except Exception:
            pass

    def _hover_off(self, event, color_base: str):
        widget = event.widget
        try:
            widget.configure(bg=color_base)
        except Exception:
            pass

    # ── Navegación ───────────────────────────────────────────────────────────

    def _abrir_movimiento(self):
        from ui.ui_movimiento import FormMovimiento
        FormMovimiento(self, self.usuario)

    def _abrir_consulta(self):
        from ui.ui_consulta import FormConsulta
        FormConsulta(self, self.usuario)

    def _abrir_alertas(self):
        from ui.ui_alertas import PanelAlertas
        PanelAlertas(self, self.usuario)

    def _abrir_reportes(self):
        from ui.ui_reportes import PanelReportes
        PanelReportes(self, self.usuario)

    # ── Cerrar sesión ────────────────────────────────────────────────────────

    def _cerrar_sesion(self):
        if messagebox.askyesno("Cerrar sesión",
                               "¿Desea cerrar sesión y volver al login?"):
            self.destroy()
            if self.ventana_login is not None:
                # Limpiar campos y mostrar login nuevamente
                self.ventana_login.entry_user.delete(0, tk.END)
                self.ventana_login.entry_pass.delete(0, tk.END)
                self.ventana_login.lbl_error.config(text="")
                self.ventana_login.deiconify()
                self.ventana_login.entry_user.focus_set()
