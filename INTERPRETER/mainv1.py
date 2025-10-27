import json

from INTERPRETER.interpreter import Interpreter, SemanticError, ParsedResult
from INTERPRETER.motor_execucao import ExecutionEngine, ExecutionError

# EXCEÇÃO PARA ERROS DE VALIDAÇÃO DE DADOS
class ValidationError(Exception):
    pass

# CLASSE PARA VALIDAR A CONSISTÊNCIA DOS DADOS
class DataValidator:
    def __init__(self, parsed_data: ParsedResult):
        # Extrai todos os nomes de features declarados no .smelldsl
        self.declared_features = set()
        for smell in parsed_data.smells:
            for feature in smell.features:
                self.declared_features.add(feature.name)
        
        if not self.declared_features:
            raise ValidationError("Nenhuma feature foi declarada no arquivo .smelldsl. Não é possível validar os dados.")

    def validate(self, dados_path: str, limites_path: str):
        print("--- Validando consistência entre .smelldsl e arquivos JSON... ---")
        
        # Carrega os dados JSON
        dados_data = self._load_json(dados_path)
        limites_data = self._load_json(limites_path)

        # Valida as chaves (nomes das features) em cada arquivo
        self._check_keys(dados_data, "dados.json")
        self._check_keys(limites_data, "limites.json")
        
        print(">>> Consistência dos dados validada com sucesso!")

    def _load_json(self, path: str):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise ValidationError(f"Arquivo de dados para validação não encontrado: {path}")
        except json.JSONDecodeError:
            raise ValidationError(f"O arquivo {path} não é um JSON válido.")

    def _check_keys(self, data: dict, filename: str):
        """Verifica se todas as chaves do dicionário JSON estão no conjunto de features declaradas."""
        for feature_name in data.keys():
            if feature_name not in self.declared_features:
                raise ValidationError(
                    f"Erro de Consistência em '{filename}': A feature '{feature_name}' "
                    f"não foi declarada no seu arquivo .smelldsl."
                )

# CLASSE PARA VERIFICAR AS REGRAS
class RuleChecker:
    """Verifica as regras do interpretador contra os dados do motor."""
    def __init__(self, parsed_data, engine):
        self.rules = parsed_data.rules
        self.smells = {s.name: s for s in parsed_data.smells}
        self.engine = engine

    def check_all_rules(self):
        """Avalia todas as regras e imprime alertas se forem acionadas."""
        print("\n--- Verificando Regras de Detecção de Smells ---")
        detected_smells = 0
        for rule in self.rules:
            try:
                parts = rule.condition.split()
                if len(parts) < 3:
                    raise IndexError("Condição da regra mal formada.")

                smell_dot_feature = parts[0]
                operator = parts[1]
                limit_state = parts[2]

                # Adiciona .strip() para remover espaços extras
                smell_name, feature_name = [part.strip() for part in smell_dot_feature.split('.')]
                limit_state = limit_state.strip()
                
                valor_medido = self.engine.dados.get(feature_name)
                valor_limite = self.engine.limites.get(feature_name, {}).get(limit_state)

                if valor_medido is None or valor_limite is None:
                    print(f"  - [AVISO] Não foi possível avaliar a regra '{rule.name}': dados ou limites ausentes para a feature '{feature_name}'.")
                    continue

                is_triggered = False
                if operator == '>' and valor_medido > valor_limite:
                    is_triggered = True
                elif operator == '>=' and valor_medido >= valor_limite:
                    is_triggered = True
                
                if is_triggered:
                    print(f"\n  [ALERTA] SMELL DETECTADO!")
                    print(f"    - Regra Acionada: {rule.name}")
                    print(f"    - Motivo: {feature_name} ({valor_medido}) {operator} {limit_state} ({valor_limite})")
                    print(f"    - Ação Sugerida: {rule.action}")
                    detected_smells += 1

            except (ValueError, IndexError) as e:
                # O erro não é mais de 'estrutura inesperada', mas sim de lógica se algo der errado
                print(f"  - [AVISO] Falha ao processar a regra '{rule.name}': {e}")
        
        if detected_smells == 0:
            print("  - Nenhuma regra foi acionada. O código está limpo!")
        
        print("-" * 46)
# --- Bloco de Execução Principal e Unificado ---
if __name__ == "__main__":
    
    # Nomes dos arquivos de entrada
    arquivo_smelldsl = "minhaSmell.smelldsl"
    arquivo_limites = "limites.json"
    arquivo_dados = "dados.json"

    try:
        # --- ETAPA 1: INTERPRETADOR ---
        print(">>> ETAPA 1: Interpretando o arquivo .smelldsl...")
        interpretador = Interpreter()
        with open(arquivo_smelldsl, 'r', encoding='utf-8') as f:
            codigo_smelldsl = f.read()
        dados_interpretados = interpretador.run(codigo_smelldsl)
        print(">>> ETAPA 1: Concluída com sucesso.\n")

        # --- ETAPA 2: VALIDAÇÃO DE CONSISTÊNCIA ---
        print(">>> ETAPA 2: Validando consistência dos dados JSON...")
        validator = DataValidator(dados_interpretados)
        validator.validate(dados_path=arquivo_dados, limites_path=arquivo_limites)
        print(">>> ETAPA 2: Concluída com sucesso.\n")

        # --- ETAPA 3: MOTOR DE EXECUÇÃO ---
        print(">>> ETAPA 3: Executando o motor com os dados JSON...")
        motor = ExecutionEngine(limites_path=arquivo_limites, dados_path=arquivo_dados)
        motor.avaliar_features()
        print(">>> ETAPA 3: Concluída com sucesso.\n")

        # --- ETAPA 4: VERIFICADOR DE REGRAS ---
        print(">>> ETAPA 4: Juntando os resultados para detectar smells...")
        rule_checker = RuleChecker(dados_interpretados, motor)
        rule_checker.check_all_rules()
        print(">>> ETAPA 4: Verificação finalizada.")

        # --- MENSAGEM FINAL DE SUCESSO ---
        print("\n\n" + "="*60)
        print(" S U C E S S O".center(60))
        print(" O processo completo foi executado sem erros.".center(60))
        print("="*60 + "\n")

    except (FileNotFoundError, SyntaxError, SemanticError, ExecutionError, ValidationError) as e:
        # Adicionamos ValidationError à lista de exceções capturadas
        print("\n\n" + "X"*60)
        print(" F A L H A   N A   E X E C U Ç Ã O".center(60))
        print("X"*60)
        print(f"\n  MOTIVO: {e}\n")
        print("X"*60 + "\n")