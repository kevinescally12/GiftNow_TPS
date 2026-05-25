# ui/ui_login.py
# Capa de presentación — ventana de inicio de sesión.
# Sin SQL directo. Usa logica_auth.autenticar_usuario().

import tkinter as tk
from tkinter import messagebox
from logica.logica_auth import autenticar_usuario

# Paleta GiftNow
COLOR_FONDO      = "#1A1A2E"   # azul noche
COLOR_PANEL      = "#16213E"   # panel interno
COLOR_ACENTO     = "#E94560"   # rojo coral — botones primarios
COLOR_ACENTO2    = "#0F3460"   # azul medio — bordes activos
COLOR_TEXTO      = "#EAEAEA"   # texto principal
COLOR_SUBTEXTO   = "#A0A0B0"   # texto secundario / placeholders
COLOR_ENTRY_BG   = "#0D1B2A"   # fondo de campos
COLOR_ENTRY_BD   = "#2A3F5F"   # borde inactivo
FUENTE_TITULO    = ("Segoe UI", 18, "bold")
FUENTE_SUBTITULO = ("Segoe UI", 10)
FUENTE_LABEL     = ("Segoe UI", 10, "bold")
FUENTE_ENTRY     = ("Segoe UI", 11)
FUENTE_BTN       = ("Segoe UI", 11, "bold")
FUENTE_FOOTER    = ("Segoe UI", 8)


class VentanaLogin(tk.Tk):
    """Ventana principal de autenticación del TPS GiftNow."""

    def __init__(self):
        super().__init__()
        self.title("GiftNow TPS — Iniciar sesión")
        self.resizable(False, False)
        self.configure(bg=COLOR_FONDO)
        self._centrar_ventana(420, 500)
        self._construir_ui()
        self.entry_user.focus_set()

    # ── Posicionamiento ──────────────────────────────────────────────────────

    def _centrar_ventana(self, ancho: int, alto: int):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - ancho) // 2
        y  = (sh - alto)  // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    # ── Construcción de UI ───────────────────────────────────────────────────

    def _construir_ui(self):
        # Contenedor externo con padding visual
        outer = tk.Frame(self, bg=COLOR_FONDO, padx=40, pady=30)
        outer.pack(fill="both", expand=True)

        # Logo / título
        tk.Label(outer, text="🎁", font=("Segoe UI Emoji", 36),
                 bg=COLOR_FONDO, fg=COLOR_ACENTO).pack(pady=(0, 4))
        tk.Label(outer, text="GiftNow TPS",
                 font=FUENTE_TITULO, bg=COLOR_FONDO, fg=COLOR_TEXTO).pack()
        tk.Label(outer, text="Sistema de Procesamiento de Transacciones",
                 font=FUENTE_SUBTITULO, bg=COLOR_FONDO,
                 fg=COLOR_SUBTEXTO).pack(pady=(2, 24))

        # Panel de formulario
        panel = tk.Frame(outer, bg=COLOR_PANEL, bd=0,
                         highlightbackground=COLOR_ACENTO2,
                         highlightthickness=1)
        panel.pack(fill="x", pady=(0, 16))

        inner = tk.Frame(panel, bg=COLOR_PANEL, padx=24, pady=24)
        inner.pack(fill="both")

        # Usuario
        tk.Label(inner, text="Usuario", font=FUENTE_LABEL,
                 bg=COLOR_PANEL, fg=COLOR_TEXTO, anchor="w").pack(fill="x")
        self.entry_user = self._crear_entry(inner, mostrar="")
        self.entry_user.pack(fill="x", pady=(4, 14))

        # Contraseña
        tk.Label(inner, text="Contraseña", font=FUENTE_LABEL,
                 bg=COLOR_PANEL, fg=COLOR_TEXTO, anchor="w").pack(fill="x")
        self.entry_pass = self._crear_entry(inner, mostrar="•")
        self.entry_pass.pack(fill="x", pady=(4, 0))

        # Mensaje de error (oculto hasta que se necesite)
        self.lbl_error = tk.Label(inner, text="", font=("Segoe UI", 9),
                                  bg=COLOR_PANEL, fg=COLOR_ACENTO,
                                  anchor="w", wraplength=300)
        self.lbl_error.pack(fill="x", pady=(6, 0))

        # Botón ingresar
        btn = tk.Button(outer, text="INGRESAR",
                        font=FUENTE_BTN, bg=COLOR_ACENTO, fg="#FFFFFF",
                        activebackground="#C73652", activeforeground="#FFFFFF",
                        relief="flat", cursor="hand2", pady=10,
                        command=self._intentar_login)
        btn.pack(fill="x", pady=(0, 16))

        # Enter en cualquier campo dispara el login
        self.entry_user.bind("<Return>", lambda e: self._intentar_login())
        self.entry_pass.bind("<Return>", lambda e: self._intentar_login())

        # Footer
        tk.Label(outer,
                 text="Área de Almacén e Inventarios  •  GiftNow S.A.C.",
                 font=FUENTE_FOOTER, bg=COLOR_FONDO,
                 fg=COLOR_SUBTEXTO).pack(side="bottom")

    def _crear_entry(self, padre, mostrar: str) -> tk.Entry:
        entry = tk.Entry(padre, show=mostrar,
                         font=FUENTE_ENTRY,
                         bg=COLOR_ENTRY_BG, fg=COLOR_TEXTO,
                         insertbackground=COLOR_TEXTO,
                         relief="flat",
                         highlightthickness=1,
                         highlightbackground=COLOR_ENTRY_BD,
                         highlightcolor=COLOR_ACENTO2)
        entry.configure(bd=6)   # padding interno simulado con bd
        return entry

    # ── Lógica de login ──────────────────────────────────────────────────────

    def _intentar_login(self):
        self.lbl_error.config(text="")
        username = self.entry_user.get().strip()
        password = self.entry_pass.get()

        if not username:
            self._mostrar_error("Ingrese su nombre de usuario.")
            self.entry_user.focus_set()
            return
        if not password:
            self._mostrar_error("Ingrese su contraseña.")
            self.entry_pass.focus_set()
            return

        try:
            usuario = autenticar_usuario(username, password)
        except ConnectionError as e:
            messagebox.showerror("Error de conexión",
                                 f"No se pudo conectar a la base de datos:\n{e}")
            return
        except Exception as e:
            messagebox.showerror("Error inesperado", str(e))
            return

        if usuario is None:
            self._mostrar_error("Usuario o contraseña incorrectos.")
            self.entry_pass.delete(0, tk.END)
            self.entry_pass.focus_set()
            return

        # Autenticación exitosa → abrir menú y cerrar login
        self.withdraw()
        from ui.ui_menu import abrir_menu_principal
        abrir_menu_principal(usuario, ventana_login=self)

    def _mostrar_error(self, mensaje: str):
        self.lbl_error.config(text=f"⚠  {mensaje}")
