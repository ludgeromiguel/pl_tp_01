import json
import sys

er = None
arquivoSalvar = ''

# Ignorar o nome do arquivo dos args e ler os outros parametros
for i, arg in enumerate(sys.argv[1:], start=1):
    if arg == '-help':
        print('Forma de usar:')
        print('python er_main.py [er.json] --output \'string\'')
        exit(0)
    elif arg.endswith('.json') and er is None:
        with open(arg, "r", encoding="utf-8") as f:
            er = json.load(f)
    elif sys.argv[i - 1] == '--output' and (not arg.startswith('-') and arg.endswith('.json')):
        arquivoSalvar = arg

if er is None:
    print("Não passasste o arquivo da expressão regular como argumento")
    exit(-1)

if arquivoSalvar == '':
    print("Tens de passar o arquivo para salvar a conversão com o parametro --output \'string\'")
    exit(-1)


# Função auxiliar para criar um novo estado
def novoEstado(estados):
    estado = f'q{len(estados)}'
    estados.append(estado)
    return estado


# Função para processar um simbolo sozinho (sem "op")
def prcSimbolo(simbolo, simbolos, estados, transicoes):
    # Criar os estados para inicio e fim da transição
    inicio = novoEstado(estados)
    fim = novoEstado(estados)

    # Adicionar a transição do estado inicial para o estado final com o símbolo
    transicoes[inicio] = {simbolo: [fim]}
    # Validar se o simbolo já se encontra na lista, se não tiver adicionar
    if simbolo not in simbolos:
        simbolos.append(simbolo)

    # Retornar o estado de inicio e sim
    return inicio, fim


# Função para processar um epsilon (€)
def prcEpsilon(estados, transicoes):
    # Criar os estados para inicio e fim da transição
    inicio = novoEstado(estados)
    fim = novoEstado(estados)

    # Adicionar a transição epsilion do estado inicial para o final
    transicoes[inicio] = {'': [fim]}

    # Retornar o estado de inicio e sim
    return inicio, fim


# Função para processar o "op" = "alt" (alternância, "|")
def prcAlt(args, estados, simbolos, transicoes):
    # Criar os estados para inicio e fim globais da transição
    inicio = novoEstado(estados)
    fim = novoEstado(estados)

    for arg in args:
        # Converter cada argumento
        subInicio, subFim = converterER(arg, estados, simbolos, transicoes)

        # Adicionar a transição '' do estado de inicio global para o inicio de cada argumento
        # Isto permite que o processamento da palavra seja iniciado a partir de qualquer um dos argumentos
        transicoes.setdefault(inicio, {}).setdefault('', []).append(subInicio)  # Se não existir vai adicionar uma propriadade { 'inicio': { '': ['subInicio'] } }, senão da so append

        # Adiciona a transição do fim de cada argumento para o fim global
        # Isto permite que se possa passar para o estado final da operação ALT
        transicoes.setdefault(subFim, {}).setdefault('', []).append(fim)  # Se não existir vai adicionar uma propriadade { 'subFim': { '': ['fim'] } }, senão da so append
    # Devolver o estado de inicio e fim
    return inicio, fim

# Função para processar o "op" = "seq" (sequência, simbolo() ou 2 simbolos juntos)
def prcSeq(args, estados, simbolos, transicoes):
    fimAnterior = None
    inicio = None

    for arg in args:
        # Converter cada arg
        subInicio, subFim = converterER(arg, estados, simbolos, transicoes)

        # Se já tivermos processado algum arg então conectamos o fim do ultimo arg com o início do atual
        if fimAnterior:
            # Adicionar a transição do fim do arg anterior para o inicio do atual
            transicoes.setdefault(fimAnterior, {}).setdefault('', []).append(subInicio) # Se não existir vai adicionar uma propriadade { 'fimAnterior': { '': ['subInicio'] } }, senão da so append
        else:
            # Se é o primeiro arg a ser processado defenimos o início dele como início da operação seq
            inicio = subInicio

        # Trocar o valor do ultimo estado final
        fimAnterior = subFim
    # Retornar o 1º inicio criado e o ultimo fim
    return inicio, fimAnterior

# Função para processar o "op" = "kle" (Fecho de kleene, simbolo*)
def prcKle(args, estados, simbolos, transicoes):
    # Criar os estados para inicio e fim da transição
    inicio = novoEstado(estados)
    fim = novoEstado(estados)

    # Adiciona transição de epsilon do início global para o fim global para permitir reconhecimento de uma cadeia vazia
    transicoes.setdefault(inicio, {}).setdefault('', []).append(fim)  # Se não existir vai adicionar uma propriadade { 'inicio': { '': ['fim'] } }, senão da so append

    for arg in args:
        # Processar o arg que tem
        subInicio, subFim = converterER(arg, estados, simbolos, transicoes)

        # Transição do estado inicial para o estado inicial do arg, permitindo que o arg seja iniciado
        transicoes.setdefault(inicio, {}).setdefault('', []).append(subInicio) # Se não existir vai adicionar uma propriadade { 'inicio': { '': ['subInicio'] } }, senão da so append

        # Transição do estado final do arg de volta ao seu estado inicial, permitindo a remetição do arg
        transicoes.setdefault(subFim, {}).setdefault('', []).append(subInicio) # Se não existir vai adicionar uma propriadade { 'subFim': { '': ['subInicio'] } }, senão da so append

        # Transição do final do arg para o estado final do fecho de kleene, permitindo a saida do arg após a conclusão do mesmo
        transicoes.setdefault(subFim, {}).setdefault('', []).append(fim) # Se não existir vai adicionar uma propriadade { 'subFim': { '': ['fim'] } }, senão da so append

    # Retornar o inicio e fim do Kle
    return inicio, fim


# Função para processar o "op" = "trans" (fecho transitivo, simbolo+)
def prcTrans(args, estados, simbolos, transicoes):
    # Criar os estados para inicio e fim da transição
    inicio = novoEstado(estados)
    fim = novoEstado(estados)

    for arg in args:
        # Processar cada argumento dentro do fecho transitivo
        subInicio, subFim = converterER(arg, estados, simbolos, transicoes)

        # Adicionar a transição do estado inicial para o estado inicial do arg, permitindo que o arg seja iniciado
        transicoes.setdefault(inicio, {}).setdefault('', []).append(subInicio) # Se não existir vai adicionar uma propriadade { 'inicio': { '': ['subInicio'] } }, senão da so append

        # Transição do estado final do arg de volta ao seu estado inicial, obrigando a que ocorra pelo menos uma vez ou mais
        transicoes.setdefault(subFim, {}).setdefault('', []).append(subInicio) # Se não existir vai adicionar uma propriadade { 'subFim': { '': ['subInicio'] } }, senão da so append

        # Transição do final do arg para o estado final do fecho de tansitivo, permitindo a saida do arg após o realizar 1 vez ou mais
        transicoes.setdefault(subFim, {}).setdefault('', []).append(fim) # Se não existir vai adicionar uma propriadade { 'subFim': { '': ['fim'] } }, senão da so append

    # Retornar o inicio e fim do fecho transitivo
    return inicio, fim


# Função para verificar para onde o er atual deve ir
def converterER(er, estados, simbolos, transicoes):
    if 'simb' in er:  # Para quando o objeto da er tiver o valor 'simb'
        return prcSimbolo(er['simb'], simbolos, estados, transicoes)
    elif 'epsilon' in er:  # Para quando o objeto da er tiver o valor 'epsilon'
        return prcEpsilon(estados, transicoes)
    elif er['op'] == 'alt':  # Para quando o tipo da op for igual a 'alt'
        return prcAlt(er['args'], estados, simbolos, transicoes)
    elif er['op'] == 'seq':  # Para quando o tipo da op for igual a 'seq'
        return prcSeq(er['args'], estados, simbolos, transicoes)
    elif er['op'] == 'kle':  # Para quando o tipo da op for igual a 'kle'
        return prcKle(er['args'], estados, simbolos, transicoes)
    elif er['op'] == 'trans':  # Para quando o tipo da op for igual a 'trans'
        return prcTrans(er['args'], estados, simbolos, transicoes)


# Converter ER para AFND
def convertERToAFND(caminho: str):
    simbolos = []
    estados = []
    transicoes = {}

    # Iniciar processo de conversão
    inicio, fim = converterER(er, estados, simbolos, transicoes)

    # Verificar se o fim não está nas transições, se não tiver adicionar
    if fim not in transicoes:
        transicoes[fim] = {'': []}

    afnd = {
        "V": simbolos,
        "Q": estados,
        "delta": transicoes,
        "q0": inicio,
        "F": [fim]
    }

    # Salvar o arquivo
    with open(caminho, "w") as f:
        json.dump(afnd, f, indent=4)
    print("Arquivo gerado com sucesso!")

if arquivoSalvar != '':
    convertERToAFND(arquivoSalvar)
