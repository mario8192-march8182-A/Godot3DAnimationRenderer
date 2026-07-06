# Godot3DAnimationRenderer

Gera um vídeo `.mp4` de uma animação 3D usando o Godot 4, sem precisar
gravar a tela: o Godot renderiza cada frame de forma determinística
(modo *Movie Maker*) e depois o `export_video.py` converte o resultado
para `.mp4` usando ffmpeg.

## O que a cena faz

Uma cena 3D gerada inteiramente por código (`scripts/Main.gd`, sem
`.tscn` complexo): um torus com material PBR girando no lugar, câmera
orbitando ao redor dele uma volta completa ao longo da duração do
clipe, chão e iluminação básica (sky + luz direcional).

## Pré-requisitos

1. **Godot 4.x** — baixe em https://godotengine.org/download e garanta
   que o executável `godot` (ou `godot4`) esteja no PATH, ou passe o
   caminho com `--godot`.
2. **ffmpeg** — `apt install ffmpeg` (Linux), `brew install ffmpeg`
   (Mac), ou baixe em https://ffmpeg.org/download.html (Windows).
3. **Python 3** (só para rodar o script orquestrador).

## Uso

```bash
python export_video.py
```

Isso gera `output/animation.mp4`, 8 segundos, 30fps, 1280x720.

Personalizando:

```bash
python export_video.py --duration 12 --fps 60 --resolution 1920x1080 \
    --color 0.1,0.6,0.9 --output output/meu_clipe.mp4
```

Parâmetros:

| Flag           | Descrição                                      | Padrão              |
|----------------|-------------------------------------------------|----------------------|
| `--duration`   | Duração do clipe em segundos                    | `8.0`                |
| `--fps`        | Quadros por segundo                             | `30`                  |
| `--resolution` | Resolução `LARGURAxALTURA`                      | `1280x720`            |
| `--color`      | Cor do objeto em `R,G,B` (0 a 1)                 | vermelho             |
| `--godot`      | Caminho do executável do Godot                  | procura no PATH       |
| `--ffmpeg`     | Caminho do ffmpeg                               | procura no PATH       |
| `--output`     | Caminho do `.mp4` final                         | `output/animation.mp4`|
| `--keep-avi`   | Mantém também o `.avi` intermediário do Godot   | desativado            |

## Como funciona por baixo dos panos

1. `export_video.py` chama:
   ```
   godot --headless --path . --resolution WxH \
       --write-movie <tmp>/movie.avi --fixed-fps FPS \
       --quit-after <N> -- --duration=SEGUNDOS
   ```
   `--write-movie` ativa o Movie Maker do Godot: cada frame é
   renderizado e capturado exatamente, independente da velocidade real
   da máquina — é assim que o vídeo sai sempre no fps certo, mesmo se o
   Godot estiver rodando mais lento ou mais rápido que isso em tempo
   real.
2. `Main.gd` lê `--duration=` (passado depois do `--`) via
   `OS.get_cmdline_user_args()`, monta a cena, anima o objeto/câmera a
   cada `_process(delta)`, e chama `get_tree().quit()` sozinho ao
   final. `--quit-after` é só uma rede de segurança.
3. O Godot grava um `.avi` (formato nativo do seu Movie Maker; ele não
   grava `.mp4` diretamente). `export_video.py` então roda:
   ```
   ffmpeg -i movie.avi -c:v libx264 -pix_fmt yuv420p -crf 18 -r FPS output.mp4
   ```

## Editando a animação

Tudo está em `scripts/Main.gd` — não precisa abrir o editor do Godot
para mudar a cena:

- Trocar o objeto: substitua `TorusMesh` por `SphereMesh`,
  `BoxMesh`, `CapsuleMesh`, etc., em `_build_scene()`.
- Mudar a velocidade de giro: ajuste os multiplicadores em
  `_subject.rotate_y(delta * 0.8)` / `rotate_x(delta * 0.35)`.
- Trocar a posição/distância da câmera: ajuste
  `camera.position = Vector3(0, 2.2, 6.0)`.
- Adicionar mais objetos, texto 3D, partículas etc.: adicione mais
  `add_child(...)` dentro de `_build_scene()`.

## Solução de problemas

- **"Godot executable not found"**: instale o Godot 4.x e confirme que
  `godot --version` funciona no terminal, ou use `--godot`.
- **"ffmpeg not found"**: instale o ffmpeg e confirme `ffmpeg -version`.
- **Erro de rendering-driver em servidor Linux sem GPU**: rode via
  Xvfb:
  ```bash
  xvfb-run --auto-servernum python export_video.py
  ```
- **`.avi` não foi gerado**: leia a saída do Godot impressa no
  terminal — geralmente aponta um erro de script ou de driver de
  vídeo.
- Este projeto foi criado e testado (parsing dos argumentos, lógica do
  script) sem o Godot instalado no ambiente de geração; a renderização
  real precisa ser validada na sua máquina com o Godot 4.x instalado.
