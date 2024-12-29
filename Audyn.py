import tkinter as tk
from tkinter import filedialog, Listbox, ttk
from PIL import Image, ImageTk, ImageDraw
import pygame
import os
from mutagen.mp3 import MP3
import random
import textwrap

# Constantes
STOPPED_MESSAGE = "Música parada"
DEFAULT_IMAGE = "image.jpg"  # Nome padrão da imagem - certifique-se que este arquivo existe na mesma pasta do script
UPDATE_INTERVAL = 100  # Intervalo de atualização em ms

class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Audyn")
        self.root.configure(bg="#282828")
        pygame.mixer.init()

        self.playlist = []
        self.track_info = {}
        self.current_track = None  # Inicializa como None
        self.paused = False
        self.shuffled = False
        self.repeat = False
        self.accent_color = "#1db954"

        self.create_widgets()
        self.center_window()

        # Adiciona o ícone (certifique-se de que 'icon.ico' esteja na mesma pasta)
        try:
            self.root.wm_iconbitmap("iconee.ico")
        except tk.TclError:
            print("Erro ao carregar o ícone .ico. Certifique-se que o arquivo existe.")


    def create_widgets(self):
        # Frame principal
        main_frame = tk.Frame(self.root, bg="#282828")
        main_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Sidebar
        sidebar_frame = tk.Frame(main_frame, bg="#383838", width=200)
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)

        add_button = tk.Button(sidebar_frame, text="Adicionar Música", command=self.add_music,
                               fg="#ffffff", padx=10, pady=5, bd=0, relief=tk.FLAT,
                               font=("Helvetica", 10), highlightthickness=0, bg="#282828", activebackground="#282828")
        add_button.pack(pady=10, padx=10, fill=tk.X)

        playlist_label = tk.Label(sidebar_frame, text="Playlist", bg="#383838", fg="#ffffff",
                                  font=("Arial", 12, "bold"))
        playlist_label.pack(pady=(15, 5), padx=10, anchor='center')

        self.playlist_box = Listbox(sidebar_frame, bg="#444444", fg="#ffffff", selectbackground="#666666",
                                    selectforeground="#ffffff", font=("Helvetica", 10), bd=0, highlightthickness=0, width=25,
                                    selectborderwidth=0) # selectborderwidth=0 remove o sublinhado
        self.playlist_box.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        self.playlist_box.bind("<Double-Button-1>", self.play_selected)

        # Frame de conteúdo principal
        content_frame = tk.Frame(main_frame, bg="#282828")
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Frame superior para imagem
        top_frame = tk.Frame(content_frame, bg="#282828")
        top_frame.pack(pady=10, padx=10, fill=tk.X)


        self.playlist_name_var = tk.StringVar(value="Minha Playlist") # Nome padrão
        self.playlist_name_label = tk.Label(top_frame, textvariable=self.playlist_name_var,
                                            bg="#282828", fg="#ffffff", font=("Helvetica", 14, "bold"), anchor='center') #Usando Label ao invés de Entry
        self.playlist_name_label.pack(pady=5, fill=tk.X)

        self.playlist_image_label = tk.Label(top_frame, bg="#282828")
        self.playlist_image_label.pack(pady=5)
        self.load_default_image()

        # Frame para informações da música atual
        info_frame = tk.Frame(content_frame, bg="#282828")
        info_frame.pack(pady=10, padx=10, fill=tk.X)

        self.track_title = tk.StringVar(value="Nenhuma música tocando")
        self.track_artist = tk.StringVar(value="")

        self.title_label = tk.Label(info_frame, textvariable=self.track_title, bg="#282828", fg="#ffffff",
                                     font=("Helvetica", 14, "bold"))
        self.title_label.pack()
        self.artist_label = tk.Label(info_frame, textvariable=self.track_artist, bg="#282828", fg="#b3b3b3",
                                      font=("Helvetica", 10))
        self.artist_label.pack()

        # Frame para os botões de controle
        controls_frame = tk.Frame(content_frame, bg="#282828")
        controls_frame.pack(pady=20, padx=10, fill=tk.X, side=tk.BOTTOM)
        controls_frame.grid_columnconfigure(0, weight=1)
        controls_frame.grid_columnconfigure(1, weight=1)
        controls_frame.grid_columnconfigure(2, weight=1)

        self.control_button_style = {
            'fg': '#fff',
            'bg': '#282828',
            'activebackground': '#282828',
            'padx': 15,
            'pady': 8,
            'font': ("Arial", 12),
            'bd': 0,
            'relief': tk.FLAT,
            'highlightthickness': 0,
            'width': 2,
            'height': 1,
            'command': lambda cmd=None: cmd() if cmd else None
        }

        # Botões criados de forma mais eficiente usando um loop e dicionário.
        button_data = {
            "🔀": self.toggle_shuffle,
            "⏮️": self.prev_music,
            "⏯": self.play_pause,
            "⏭️": self.next_music,
            "🔁": self.toggle_repeat
        }
        controls_subframe = tk.Frame(controls_frame, bg="#282828")
        controls_subframe.pack(pady=5)
        self.controls_subframe = controls_subframe # Referência para o frame dos botões
        for text, command in button_data.items():
            button = tk.Button(controls_subframe, text=text, **self.control_button_style)
            button.config(command=command)
            button.pack(side=tk.LEFT, padx=10)
            if text == "⏯":
                self.play_pause_button = button


        # Barra de progresso
        progress_frame = tk.Frame(content_frame, bg="#282828")
        progress_frame.pack(pady=5, padx=10, fill=tk.X, side=tk.BOTTOM)

        self.current_time_var = tk.StringVar(value="0:00")
        self.total_time_var = tk.StringVar(value="0:00")

        self.current_time_label = tk.Label(progress_frame, textvariable=self.current_time_var,
                                           bg="#282828", fg="#ffffff", font=("Helvetica", 8), anchor='w')
        self.current_time_label.pack(side=tk.LEFT)

        self.progress_var = tk.DoubleVar()
        self.progress_slider = ttk.Scale(progress_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                         variable=self.progress_var, command=self.seek, style="TScale")
        self.progress_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.total_time_label = tk.Label(progress_frame, textvariable=self.total_time_var,
                                         bg="#282828", fg="#ffffff", font=("Helvetica", 8), anchor='e')
        self.total_time_label.pack(side=tk.RIGHT)

        style = ttk.Style()
        style.configure("TScale", background="#282828", fg="#ffffff", troughcolor="#444444", slidercolor=self.accent_color)
        style.map("TScale", background=[('active', '#555555')])

        self.is_playing = False

    def add_music(self):
        directory = filedialog.askdirectory(
            initialdir=".", title="Selecione a pasta com as músicas"
        )
        if directory:  # Verifica se o usuário selecionou uma pasta
            self.add_music_from_directory(directory)

    def add_music_from_directory(self, directory):
        # Extrai o nome da pasta
        playlist_name = os.path.basename(directory)
        self.playlist_name_var.set(playlist_name) # Atualiza o nome da playlist

        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath) and filename.lower().endswith(".mp3"):
                self.add_song_to_playlist(filepath)

    def add_song_to_playlist(self, filename):
        try:
            audio = MP3(filename)
            title = audio.get('TIT2', [os.path.basename(filename)])[0]
            artist = audio.get('TPE1', [''])[0]
            length = int(audio.info.length)
            self.track_info[filename] = {'title': title, 'artist': artist, 'length': length}

            # Uso aprimorado do textwrap.shorten
            display_name = f"{title} - {artist}" if artist else title
            shortened_name = textwrap.shorten(display_name, width=30, placeholder="...")

            self.playlist.append(filename)
            self.playlist_box.insert(tk.END, shortened_name)
        except Exception as e:
            print(f"Erro ao adicionar música '{filename}': {e}")
            #  Melhoria:  Adiciona o nome do arquivo mesmo com erro, facilitando o debug.
            self.playlist_box.insert(tk.END, os.path.basename(filename))


    def play_music(self, track_index=None):
        if not self.playlist:
            self.show_error("Adicione músicas à playlist.") #Mensagem de erro amigável
            return

        if track_index is None:
            try:
                track_index = self.playlist_box.curselection()[0]
            except IndexError:
                return

        self.current_track = track_index
        filename = self.playlist[self.current_track]
        try:
            pygame.mixer.music.load(filename)
            self.update_track_info(filename)
            pygame.mixer.music.play()
            self.is_playing = True
            self.paused = False
            self.play_pause_button.config(text="⏸")
            self.update_progress()
            self._update_playlist_selection()
        except pygame.error as e:
            print(f"Erro ao tocar música: {e}")
            self.show_error("Erro ao tocar música. Arquivo corrompido?")

    def get_next_track_index(self, current_index):
        if self.shuffled and len(self.playlist) > 1:
            available_tracks = [i for i in range(len(self.playlist)) if i != current_index]
            next_track = random.choice(available_tracks) if available_tracks else current_index
        elif self.repeat:
            next_track = current_index
        else:
            next_track = (current_index + 1) % len(self.playlist)
        return next_track

    def play_selected(self, event):
        if not self.playlist:
            return
        selected_index = self.playlist_box.nearest(event.y)
        self.play_music(selected_index)

    def play_pause(self):
        if self.is_playing:
            if self.paused:
                pygame.mixer.music.unpause()
                self.paused = False
                self.play_pause_button.config(text="⏸")
                self.update_progress()
                self.update_track_info(self.playlist[self.current_track])
            else:
                pygame.mixer.music.pause()
                self.paused = True
                self.play_pause_button.config(text="⏯")
                self.show_error("Música pausada")
        else:
            self.play_music()

    def stop_music(self):
        if self.is_playing: # Só para o caso de tentar parar quando já está parado
            pygame.mixer.music.stop()
            self.is_playing = False
            self.progress_var.set(0)
            self.current_time_var.set("0:00")
            self.play_pause_button.config(text="⏯")
            self.show_error(STOPPED_MESSAGE)
            self.paused = False

    def next_music(self):
        if not self.playlist: return
        self.play_music(self.get_next_track_index(self.current_track))

    def prev_music(self):
        if not self.playlist: return
        if self.shuffled and len(self.playlist) > 1:
            available_tracks = [i for i in range(len(self.playlist)) if i != self.current_track]
            prev_track = random.choice(available_tracks) if available_tracks else self.current_track
            self.play_music(prev_track)
        elif len(self.playlist) > 1:
            prev_track = (self.current_track - 1) % len(self.playlist)
            self.play_music(prev_track)

    def update_track_info(self, filename):
        try:
            track_data = self.track_info[filename]
            self.track_title.set(track_data['title'])
            self.track_artist.set(track_data['artist'] if track_data['artist'] else "")
            self.total_time_var.set(self.format_time(track_data['length']))
        except Exception as e:  # Captura apenas Exception (KeyError está incluso)
            print("Erro ao atualizar informações da música: {}".format(e))
            self.show_error("Erro ao carregar informações de '{}'".format(os.path.basename(filename)))

    def update_progress(self):
        if not self.playlist or not self.is_playing:
            return

        self.update_progress_timer()

    def update_progress_timer(self):
        if not self.is_playing: return
        current_time_ms = pygame.mixer.music.get_pos()
        if current_time_ms == -1:  # Música terminou
            current_time = 0
            progress_percentage = 100
            self.handle_track_end()
        else:
            current_time = current_time_ms / 1000
            total_length = self.track_info[self.playlist[self.current_track]]['length']
            progress_percentage = (current_time / total_length) * 100 if total_length > 0 else 0

        self.progress_var.set(progress_percentage)
        self.current_time_var.set(self.format_time(current_time))
        self.root.after(UPDATE_INTERVAL, self.update_progress_timer) # Usando constante

    def handle_track_end(self):
        if self.repeat:
            self.play_music(self.current_track)
        elif self.shuffled:
            self.play_music(random.choice(range(len(self.playlist))))
        elif self.current_track == len(self.playlist) -1:
            self.stop_music()
        else:
            self.next_music()

    def seek(self, value):
        if self.playlist:
            try:
                total_length = self.track_info[self.playlist[self.current_track]]['length']
                seek_time = total_length * (float(value) / 100)
                pygame.mixer.music.play(start=int(seek_time))
            except Exception as e:
                print(f"Erro ao realizar seek: {e}")

    def make_circle_mask(self, image):
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, image.size[0], image.size[1]), fill=255)
        return mask

    def apply_mask(self, image, mask):
        alpha = Image.new('L', image.size, 255)
        alpha.paste(mask, (0, 0))
        image.putalpha(alpha)
        return image

    def load_default_image(self):
        try:
            image = self._load_image(DEFAULT_IMAGE) # usando função auxiliar
            size = min(image.size)
            cropped = image.crop((0, 0, size, size))
            resized = cropped.resize((150, 150), Image.Resampling.LANCZOS)
            mask = self.make_circle_mask(resized)
            circular_image = self.apply_mask(resized, mask)
            photo = ImageTk.PhotoImage(circular_image)
            self.playlist_image_label.config(image=photo)
            self.playlist_image_label.image = photo  # Manter uma referência para evitar garbage collection
            self.root.update() # Força a atualização da interface

        except FileNotFoundError:
            print(f"Arquivo '{DEFAULT_IMAGE}' não encontrado.")
            self.show_error("Imagem padrão não encontrada.") # Mostra erro na interface
        except Exception as e:
            print(f"Erro ao carregar imagem padrão: {e}")
            self.show_error("Erro ao carregar imagem padrão.") # Mostra erro na interface

    def _load_image(self, path):
        """Função auxiliar para carregar imagem, tratando possíveis erros."""
        try:
            return Image.open(path)
        except FileNotFoundError:
            return Image.new("RGB", (150,150), color = "grey") # Imagem fallback
        except Exception as e:
            print(f"Erro ao carregar imagem: {e}")
            return Image.new("RGB", (150,150), color = "grey") # Imagem fallback

    def toggle_shuffle(self):
        self.shuffled = not self.shuffled
        print(f"Shuffle {'ativado' if self.shuffled else 'desativado'}")
        self.update_shuffle_button_color() # Função auxiliar para atualizar a cor

    def update_shuffle_button_color(self):
        for child in self.controls_subframe.winfo_children(): # Correção aqui
            if isinstance(child, tk.Button) and child.cget('text') == "🔀":
                child.config(fg=self.accent_color if self.shuffled else '#fff')
                self.root.update() # Força a atualização da interface para que a mudança seja visível
                break

    def toggle_repeat(self):
        self.repeat = not self.repeat
        self.update_repeat_button_color() # Função auxiliar para atualizar a cor


    def update_repeat_button_color(self):
        for child in self.controls_subframe.winfo_children(): # Correção aqui
            if isinstance(child, tk.Button) and child.cget('text') == "🔁":
                child.config(fg=self.accent_color if self.repeat else '#fff')
                self.root.update() # Força a atualização da interface para que a mudança seja visível
                break

    def _update_playlist_selection(self):
        self.playlist_box.selection_clear(0, tk.END)
        if self.current_track is not None: # Verifica se há uma música selecionada
            self.playlist_box.select_set(self.current_track)
            self.playlist_box.activate(self.current_track)

    def show_error(self, message):
        self.track_title.set(message)
        self.track_artist.set("")

    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def center_window(self):
        """Centraliza a janela na tela."""
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.root.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    root = tk.Tk()
    player = MusicPlayer(root)
    root.mainloop()