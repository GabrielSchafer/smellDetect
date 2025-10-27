import json

class ExecutionError(Exception):
    """Exceção para erros durante a execução."""
    pass

class ExecutionEngine:
    def __init__(self, limites_path=None, dados_path=None, limites=None, dados=None, logger=None):
        self.logger = logger

        if dados is not None and limites is not None:
            self.dados = dados
            self.limites = limites
        elif dados_path and limites_path:
            self.dados = self._load_json(dados_path)
            self.limites = self._load_json(limites_path)
        else:
            raise ValueError("Forneça dados/limites ou caminhos de arquivos.")

    def _carregar_json(self, path: str):
        """Função auxiliar para carregar arquivos JSON."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise ExecutionError(f"Arquivo JSON não encontrado: {path}")
        except json.JSONDecodeError:
            raise ExecutionError(f"O arquivo {path} não é um JSON válido.")

    def _determinar_estado(self, feature_name: str, valor_medido: int):
        """Compara o valor medido com os limites e retorna o estado (ex: 'LOW')."""
        if feature_name not in self.limites:
            return "Limites não definidos"

        limites_da_feature = self.limites[feature_name]
        
        # Ordena os limites para avaliação (ex: HIGH, MEDIUM, LOW)
        limites_ordenados = sorted(limites_da_feature.items(), key=lambda item: item[1], reverse=True)

        for estado, valor_limite in limites_ordenados:
            if valor_medido >= valor_limite:
                return estado.upper() # Retorna LOW, MEDIUM, ou HIGH
        
        return "MUITO BAIXO" # Caso o valor seja menor que todos os limites

    def avaliar_features(self):
        if self.logger:
            self.logger.info("--- Avaliando o estado das Features ---")
            for feature_name, valor_medido in self.dados.items():
                estado = self._determinar_estado(feature_name, valor_medido)
                self.logger.info(f"  - Feature: {feature_name} : {estado}")
            self.logger.info("-" * 39)
        else:
            print("\n--- Avaliando o estado das Features ---")
            for feature_name, valor_medido in self.dados.items():
                estado = self._determinar_estado(feature_name, valor_medido)
                print(f"  - Feature: {feature_name} : {estado}")
            print("-" * 39)
