import json
import sys

af = None
graphviz = False
graphvizPath = ''
palavra = ''

# Ignorar o nome do arquivo dos args e ler os outros parametros
for i, arg in enumerate(sys.argv[1:], start=1):
    if arg == '-help':
        print('Forma de usar:')
        print('python afd_main.py [afd.json] -rec \'string\'')
        print('python afd_main.py [afd.json] -graphviz')
        print('python afd_main.py [afd.json] -graphviz \'string\'')
        exit(0)
    elif arg.endswith('.json') and af is None:
        with open(arg, "r", encoding="utf-8") as f:
            af = json.load(f)
    elif arg == '-graphviz':
        graphviz = True
    elif sys.argv[i - 1] == '-graphviz' and not arg.startswith('-'):
        graphvizPath = arg
    elif sys.argv[i - 1] == '-rec':
        palavra = arg

if af is None:
    print("Não passasste o arquivo do afd como argumento")
    exit(-1)

if graphviz == False and palavra == '':
    print("Tens de passar o parametro -rec \'string\' ou -graphviz")
    exit(-1)

# definição do Autómato Finito
#    AF=(V,Q,delta,q0,F) tal que:
V = set(af["V"])
Q = set(af["Q"])
delta = af["delta"]
q0 = af["q0"]
F = set(af["F"])


# especificação da função para avaliar se uma dada
# palavra é reconhecida reconhecida no Autómato AF
def reconhece(palavra: str):
    estadoAtual = q0  # começar pelo estado inicial!
    caminho = []  # para armazenar o caminho percorrido
    tam = len(palavra)  # tamanho da palavra a reconhecer
    i = 0
    while (i < tam):
        simboloAtual = palavra[i]
        # Verifica se o símbolo atual pertence ao alfabeto
        if simboloAtual not in V:
            return f"'{simboloAtual}' não é reconhecida\n[símbolo '{simboloAtual}' não pertence ao alfabeto]"

        caminho.append(f"{estadoAtual}-{simboloAtual}")  # adiciona o estado ao caminho

        # Verifica se há uma transição definida para o estado atual e o símbolo atual
        if simboloAtual in delta[estadoAtual]:
            estadoAtual = delta[estadoAtual][simboloAtual]
            i += 1
        else:
            # Se não há transição definida, a palavra não é reconhecida.
            return f"'{palavra}' não é reconhecida\n[transição ({estadoAtual}->{simboloAtual}) não definida]"

    # gerar a string do caminho percorrido
    caminhoFormatado = f"{' > '.join(caminho)} > {estadoAtual}"

    # Verifica se o estado atual é um dos estados finais
    if estadoAtual in F:
        return f"'{palavra}' é reconhecida\n[caminho {caminhoFormatado}]"
    else:
        return f"'{palavra}' não é reconhecida\n[caminho {caminhoFormatado}, {estadoAtual} não é final]"


# Gerar o grafico graphviz
def graphviz_gen(caminho: str):
    # Defenir a estrutura inicial
    graphviz_str = "digraph {\n"
    graphviz_str += "\tnode [shape = doublecircle]; " + " ".join(F) + ";\n"  # Pontos onde o diagrama termina acho
    graphviz_str += "\tnode [shape = point]; initial;\n"  # Iniciar o diagrama com um ponto
    graphviz_str += "\tnode [shape = circle];\n\n"  # O formato dos pontos deve ser um circulo
    graphviz_str += "\tinitial -> " + q0 + ";\n"  # Defenir o ponto inicial

    # Percorrer os itens do delta e adicionar
    for estado, transicoes in delta.items():
        graphviz_str += "\t"
        for simbolo, estadoDestino in transicoes.items():
            graphviz_str += "" + estado + " -> " + estadoDestino + " [label=\"" + simbolo + "\"]; "
        graphviz_str += "\n"

    # Fechar arquivo
    graphviz_str += "}"

    if caminho == '':
        print(graphviz_str)
    else:
        f = open(caminho, "w")
        f.write(graphviz_str)
        f.close()
        print("Arquivo gerado com sucesso!")


if palavra != '':
    print(reconhece(palavra))

if graphviz == True:
    graphviz_gen(graphvizPath)
