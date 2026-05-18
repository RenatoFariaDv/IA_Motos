import cv2
import pyautogui
import time
import random


def mover_para_alvo():
    """Busca a imagem alvo na tela e move o mouse até ela de forma suave.

    O pyautogui.locateCenterOnScreen usa a imagem 'alvo.png' para localizar um ponto
    central no monitor. Se o elemento existe na tela, ele retorna as coordenadas x, y.
    Caso contrário, retorna None.

    Para usar confidence < 1.0, OpenCV (cv2) precisa estar instalado.
    """
    while True:
        try:
            # Tenta encontrar o centro do elemento na tela usando a imagem de referência.
            centro = pyautogui.locateCenterOnScreen('alvo.png', confidence=0.7)
        except Exception as e:
            # Mostra uma mensagem mais clara se a dependência pyscreeze/Pillow estiver faltando.
            print('❌ Erro ao usar pyautogui para capturar a tela:')
            print(f'   Tipo: {type(e).__name__}')
            print(f'   Mensagem: {str(e)}')
            print()
            print('📋 Verificações:')
            print('   1. Arquivo alvo.png existe no diretório atual?')
            print('   2. python -m pip install pillow pyscreeze opencv-python')
            print('   3. Reinicie o terminal após instalar OpenCV')
            return

        if centro is not None:
            x, y = centro

            # Define uma duração aleatória para o movimento do mouse.
            # Isso torna a automação menos previsível e mais parecida com um comportamento humano.
            duracao = random.uniform(0.5, 1.5)
            print(f"Alvo encontrado em ({x}, {y}). Movendo o mouse em {duracao:.2f} segundos.")

            # Move o cursor lentamente até a posição do alvo.
            pyautogui.moveTo(x, y, duration=duracao)

            # Executa um clique longo para interagir com o elemento.
            pyautogui.mouseDown()
            tempo_clique = random.uniform(4.0, 6.0)
            print(f"Clique longo iniciado por {tempo_clique:.2f} segundos...")
            time.sleep(tempo_clique)
            pyautogui.mouseUp()

            # Verifica se o elemento desapareceu após o clique.
            time.sleep(1.0)
            if pyautogui.locateCenterOnScreen('alvo.png', confidence=0.7) is None:
                print('Acesso liberado! Retornando ao robô principal')
                break
            else:
                print('O elemento ainda está visível. Continuando a busca...')
        else:
            # Se o elemento não for encontrado, informa o usuário e aguarda um pouco antes da próxima tentativa.
            print('Aguardando o elemento alvo aparecer na tela...')
            time.sleep(2)


if __name__ == '__main__':
    # Espera um pequeno tempo antes de começar para dar chance ao usuário organizar a tela.
    print('Iniciando busca pelo elemento alvo...')
    time.sleep(1.0)
    mover_para_alvo()
