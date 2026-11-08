import os
import shutil
from pathlib import Path
import string
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

# Intentamos importar pygame para la música de fondo
try:
  import pygame

  PYGAME_DISPONIBLE = True
except ImportError:
  PYGAME_DISPONIBLE = False


class GestorArchivos(tk.Tk):

  def __init__(self):
    super().__init__()

    # Ventana principal
    self.title("Explorador de Archivos")
    self.geometry("750x500")

    # Reproducir música relax de fondo
    self.iniciar_musica_relax()

    # Usaremos una constante especial para indicar que estamos en la vista de discos
    self.VISTA_DISCOS = "DISCOS"
    self.ruta_actual = self.VISTA_DISCOS

    # --- BARRA SUPERIOR (Navegación) ---
    self.frame_top = ttk.Frame(self)
    self.frame_top.pack(fill="x", padx=10, pady=10)

    # Botón para volver atrás (carpeta padre)
    self.btn_atras = ttk.Button(
        self.frame_top, text="⬅ Atrás", width=8, command=self.subir_nivel
    )
    self.btn_atras.pack(side="left", padx=5)

    # Campo de texto para la ruta
    self.entry_ruta = ttk.Entry(self.frame_top, width=60)
    self.entry_ruta.pack(side="left", padx=5, fill="x", expand=True)
    self.entry_ruta.bind("<Return>", lambda event: self.ir_a_ruta())

    # Botón para confirmar navegación manual
    self.btn_ir = ttk.Button(
        self.frame_top, text="Ir", width=6, command=self.ir_a_ruta
    )
    self.btn_ir.pack(side="left", padx=5)

    # --- ÁREA PRINCIPAL (Contenedor con scroll usando Canvas) ---
    self.frame_contenedor = ttk.LabelFrame(
        self, text=" Archivos y Carpetas "
    )
    self.frame_contenedor.pack(
        fill="both", expand=True, padx=10, pady=(0, 10)
    )

    self.canvas = tk.Canvas(self.frame_contenedor, highlightthickness=0)
    self.scrollbar = ttk.Scrollbar(
        self.frame_contenedor, orient="vertical", command=self.canvas.yview
    )
    self.scroll_frame = ttk.Frame(self.canvas)

    # Configurar el área de desplazamiento y el ancho adaptable
    self.scroll_frame.bind(
        "<Configure>",
        lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
    )

    self.window_id = self.canvas.create_window(
        (0, 0), window=self.scroll_frame, anchor="nw"
    )

    def ajustar_ancho_canvas(event):
      self.canvas.itemconfig(self.window_id, width=event.width)

    self.canvas.bind("<Configure>", ajustar_ancho_canvas)
    self.canvas.configure(yscrollcommand=self.scrollbar.set)

    self.canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    self.scrollbar.pack(side="right", fill="y")

    # Cargar el contenido inicial (Discos)
    self.cargar_directorio()

  # --- Configuración de Música Relax ---
  def iniciar_musica_relax(self):
    if PYGAME_DISPONIBLE:
      try:
        pygame.mixer.init()
        ruta_audio = Path(__file__).parent / "relax.mp3"
        if ruta_audio.exists():
          pygame.mixer.music.load(str(ruta_audio))
          pygame.mixer.music.play(loops=-1)
          pygame.mixer.music.set_volume(0.25)
      except Exception as e:
        print(f"No se pudo reproducir la música: {e}")

  # --- Obtener las unidades de disco disponibles en Windows ---
  def obtener_discos(self):
    discos = []
    if os.name == "nt":
      for letra in string.ascii_uppercase:
        disco = Path(f"{letra}:\\")
        if disco.exists():
          discos.append(disco)
    else:
      discos.append(Path("/"))
    return discos

  # --- Cargar y filtrar el contenido ---
  def cargar_directorio(self):
    for widget in self.scroll_frame.winfo_children():
      widget.destroy()

    self.entry_ruta.delete(0, "end")
    if self.ruta_actual == self.VISTA_DISCOS:
      self.entry_ruta.insert(0, "Este equipo (Unidades de disco)")
      items = self.obtener_discos()
    else:
      self.entry_ruta.insert(0, str(self.ruta_actual))
      try:
        items = sorted(
            list(self.ruta_actual.iterdir()),
            key=lambda x: (not x.is_dir(), x.name.lower()),
        )
      except PermissionError:
        messagebox.showerror(
            "Error de Acceso", "No tenés permiso para ingresar a esta carpeta."
        )
        self.subir_nivel()
        return

    for item in items:
      if self.ruta_actual == self.VISTA_DISCOS or not item.name.startswith("."):
        self.crear_fila_item(item)

  # --- Crear filas con botones ---
  def crear_fila_item(self, item: Path):
    frame_item = ttk.Frame(self.scroll_frame)
    frame_item.pack(fill="x", pady=2, padx=5)

    if self.ruta_actual == self.VISTA_DISCOS:
      icono = "💽"
      texto_btn = f"{icono} Disco Local ({item.drive})"
    else:
      icono = "📁" if item.is_dir() else "📄"
      texto_btn = f"{icono} {item.name}"

    if self.ruta_actual != self.VISTA_DISCOS:
      btn_borrar = ttk.Button(
          frame_item,
          text="🗑️",
          width=3,
          command=lambda: self.borrar_item(item),
      )
      btn_borrar.pack(side="right", padx=2)

      btn_renombrar = ttk.Button(
          frame_item,
          text="✏️",
          width=3,
          command=lambda: self.renombrar_item(item),
      )
      btn_renombrar.pack(side="right", padx=2)

    btn_item = ttk.Button(
        frame_item, text=texto_btn, command=lambda: self.abrir_item(item)
    )
    btn_item.pack(side="left", fill="x", expand=True, padx=(0, 5))

  # --- Métodos de interacción y lógica ---
  def abrir_item(self, item: Path):
    if item.is_dir():
      self.ruta_actual = item
      self.cargar_directorio()
    else:
      if os.name == "nt":
        os.startfile(item)
      else:
        os.system(f'open "{item}"')

  def subir_nivel(self):
    if self.ruta_actual == self.VISTA_DISCOS:
      return

    if (
        isinstance(self.ruta_actual, Path)
        and self.ruta_actual.parent == self.ruta_actual
    ):
      self.ruta_actual = self.VISTA_DISCOS
    else:
      self.ruta_actual = self.ruta_actual.parent
    self.cargar_directorio()

  def ir_a_ruta(self):
    texto = self.entry_ruta.get()
    if texto == "Este equipo (Unidades de disco)":
      self.ruta_actual = self.VISTA_DISCOS
      self.cargar_directorio()
      return

    nueva_ruta = Path(texto)
    if nueva_ruta.exists() and nueva_ruta.is_dir():
      self.ruta_actual = nueva_ruta
      self.cargar_directorio()
    else:
      messagebox.showerror("Error", "La ruta especificada no existe.")

  def renombrar_item(self, item: Path):
    nuevo_nombre = simpledialog.askstring(
        "Renombrar", f"Nuevo nombre para {item.name}:"
    )
    if nuevo_nombre:
      nueva_ruta = item.parent / nuevo_nombre
      item.rename(nueva_ruta)
      self.cargar_directorio()

  def borrar_item(self, item: Path):
    if messagebox.askyesno(
        "Confirmar", f"¿Seguro que querés eliminar '{item.name}'?"
    ):
      if item.is_dir():
        shutil.rmtree(item)
      else:
        item.unlink()
      self.cargar_directorio()


if __name__ == "__main__":
  app = GestorArchivos()
  app.mainloop()