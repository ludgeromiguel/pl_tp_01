import json
import sys

afnd = None
graphviz = False
graphvizPath = ''
caminhoAFD = ''

# Ignorar o nome do arquivo dos args e ler os outros parametros
for i, arg in enumerate(sys.argv[1:], start=1):
    if arg == '-help':
        print('Forma de usar:')
        print('python afnd_main.py [afnd.json] -output \'string\'')
        print('python afnd_main.py [afnd.json] -graphviz')
        print('python afnd_main.py [afnd.json] -graphviz \'string\'')
        exit(0)
    elif arg.endswith('.json') and afnd is None:
        with open(arg, "r", encoding="utf-8") as f:
            afnd = json.load(f)
    elif arg == '-graphviz':
        graphviz = True
    elif sys.argv[i - 1] == '-graphviz' and not arg.startswith('-'):
        graphvizPath = arg
    elif sys.argv[i - 1] == '-output' and (not arg.startswith('-') and arg.endswith('.json')):
        caminhoAFD = arg

if afnd is None:
    print("Não passasste o arquivo do afnd como argumento")
    exit(-1)

if graphviz == False and caminhoAFD == '':
    print("Tens de passar o parametro -output \'string\' ou -graphviz")
    exit(-1)

# definição do Autómato Finito não determinísto
#    AF=(V,Q,delta,q0,F) tal que:
V = set(afnd["V"])
Q = set(afnd["Q"])
delta = afnd["delta"]
q0 = afnd["q0"]
F = set(afnd["F"])

# Suporte para epsilion
def fechoEpsilon(estado):
    # Iniciar um array que vai conter os estados alcançáveis por epsilon
    fecho = [estado]
    # Fila para controlar os estados a explorar para encontrar os estados alcançáveis por epsilon
    fila = [estado]

    # Enquanto a fila não estiver vazia
    while len(fila) != 0:
        # Pegar no ultimo elemento do array
        estadoAtual = fila.pop()
        # validar se existem transições epsilon para o estado atual
        if '' in delta[estadoAtual]:
            # Percorre os estados alcançáveis por epsilon
            for proximoEstado in delta[estadoAtual]['']:
                # Se o estado não estiver no fecho adiciona ao fecho e a fila para "explorar"
                if proximoEstado not in fecho:
                    fecho.append(proximoEstado)
                    fila.append(proximoEstado)
    
    # Retorna o fecho epsilon (array com todos os estados alcançáveis por epsilon)
    return fecho


# Converter o AFND para AFD
def convertAFNDtoAFD(caminho: str):
    # Iniciar as variáveis para construir o AFD
    simbolos = V # Símbolos do alfabeto
    estadoInicial = q0 # Estado inicial
    estados = [] # Listado dos estados
    transicoes = {} # Transições que constituem o AFD
    estadosFinais = [] # Lista dos estados finais

    # Usa uma fila para controlar os estados a serem processados
    estadosIniciais = fechoEpsilon(estadoInicial)
    fila = ['_'.join(sorted(estadosIniciais))]
    # Adiciona o estado inicial ao AFD, como com o fecho eplison pode ser diferente ordenamos e fazemos o join dos estados retornados pelo fecho epsilon
    estados.append('_'.join(sorted(estadosIniciais)))

    while len(fila) != 0:
        # Pegar no ultimo elemento do array
        estadoAtual = fila.pop() 
        # Separar o estado por "_" para obter todos os estados que geram o mesmo
        estadosAtuais = estadoAtual.split('_')

        # Verificar se algum estado atual é estado final do AFND, se for adiciona o novo estado aos estados finais do AFD
        if any(f in estadosAtuais for f in F):
            if estadoAtual not in estadosFinais:
                estadosFinais.append(estadoAtual)

        # Processar cada simbolo do alfabeto exceto o epsilon
        for simbolo in simbolos:
            novosEstados = set()
            # Verifica as transições para cada componente do estado atual no AFND
            for estado in estadosAtuais:
                if simbolo in delta[estado]:
                    for proximoEstado in delta[estado][simbolo]:
                        #Valida as transições epsilon do estado atual
                        novosEstados.update(fechoEpsilon(proximoEstado))

            # Caso não tenha nenhum estado no set novoEstado pulamos o processamento do simbolo
            if len(novosEstados) == 0:
                continue

            # Gerar o novo estado juntando por "_"
            novoEstado = '_'.join(sorted(novosEstados))

            # Se o estado atual não estiver nas transições criar um json vazio para esse estado
            if estadoAtual not in transicoes:
                transicoes[estadoAtual] = {}

            # Adiciona a transição do estado atual para o novo estado com símbolo atual
            transicoes[estadoAtual][simbolo] = novoEstado

            # Se o novo estado for válido e ainda não estiver adicionado vai adicionar o mesmo a lista de estados e a fila para ser processado
            if novoEstado not in estados:
                estados.append(novoEstado)
                fila.append(novoEstado)

    afd = {
        "V": list(simbolos),
        "Q": estados,
        "delta": transicoes,
        "q0": '_'.join(sorted(estadosIniciais)), # O novo estado inicial caso o afnd comece por um epsilon pode ser diferente
        "F": estadosFinais
    }

    # Salvar o arquivo
    with open(caminho, "w") as f:
        json.dump(afd, f, indent=4)
    print("Arquivo gerado com sucesso!")


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
        for simbolo, estadosDestino in transicoes.items():
            for estadoDestino in estadosDestino:
                graphviz_str += "" + estado + " -> " + estadoDestino + " [label=\"" + simbolo + "\"]; "
        graphviz_str += "\n"

    # Fechar arquivo
    graphviz_str += "}"

    if caminho == '':
        print(graphviz_str)
    else:
        f = open(graphvizPath, "w")
        f.write(graphviz_str)
        f.close()
        print("Arquivo gerado com sucesso!")


if graphviz == True:
    graphviz_gen(graphvizPath)

if caminhoAFD != '':
    convertAFNDtoAFD(caminhoAFD)
