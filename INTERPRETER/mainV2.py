import json
from datetime import datetime
from io import StringIO

from INTERPRETER.interpreter import Interpreter, SemanticError, ParsedResult
from INTERPRETER.motor_execucao import ExecutionEngine, ExecutionError

class ValidationError(Exception):
    pass

# --- Logger ---
class Logger:
    def __init__(self):
        self.logs = []

    def _log(self, level, message):
        self.logs.append({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "level": level.upper(),
            "message": message
        })

    def info(self, message): self._log("INFO", message)
    def warning(self, message): self._log("WARNING", message)
    def error(self, message): self._log("ERROR", message)
    def success(self, message): self._log("SUCCESS", message)
    def get_logs(self): return self.logs

# --- Validação de dados ---
class DataValidator:
    def __init__(self, parsed_data: ParsedResult, logger: Logger):
        self.logger = logger
        self.declared_features = {feature.name for smell in parsed_data.smells for feature in smell.features}
        if not self.declared_features:
            raise ValidationError("Nenhuma feature foi declarada no arquivo .smelldsl.")

    def validate(self, dados_data: dict, limites_data: dict):
        self.logger.info("Validando consistência entre .smelldsl e arquivos JSON...")
        self._check_keys(dados_data, "dados.json")
        self._check_keys(limites_data, "limites.json")
        self.logger.success("Consistência dos dados validada com sucesso.")

    def _check_keys(self, data: dict, filename: str):
        for feature_name in data.keys():
            if feature_name not in self.declared_features:
                raise ValidationError(
                    f"Erro de consistência em '{filename}': "
                    f"A feature '{feature_name}' não foi declarada no arquivo .smelldsl."
                )

# --- Regras ---
class RuleChecker:
    def __init__(self, parsed_data, engine, logger: Logger):
        self.rules = parsed_data.rules
        self.smells = {s.name: s for s in parsed_data.smells}
        self.engine = engine
        self.logger = logger

    def check_all_rules(self):
        self.logger.info("Verificando regras de detecção de smells...")
        detected_smells = 0

        for rule in self.rules:
            try:
                parts = rule.condition.split()
                if len(parts) < 3: raise IndexError("Condição da regra mal formada.")

                smell_dot_feature, operator, limit_state = parts[0], parts[1], parts[2]
                smell_name, feature_name = [p.strip() for p in smell_dot_feature.split(".")]

                valor_medido = self.engine.dados.get(feature_name)
                valor_limite = self.engine.limites.get(feature_name, {}).get(limit_state)

                if valor_medido is None or valor_limite is None:
                    self.logger.warning(f"Regra '{rule.name}': dados ou limites ausentes para '{feature_name}'.")
                    continue

                triggered = (operator == ">" and valor_medido > valor_limite) or \
                            (operator == ">=" and valor_medido >= valor_limite)

                if triggered:
                    detected_smells += 1
                    self.logger.warning(
                        f"[ALERTA] Regra '{rule.name}' acionada: "
                        f"{feature_name} ({valor_medido}) {operator} {limit_state} ({valor_limite}). "
                        f"Ação sugerida: {rule.action}"
                    )

            except Exception as e:
                self.logger.warning(f"Falha ao processar regra '{rule.name}': {e}")

        if detected_smells == 0:
            self.logger.success("Nenhuma regra foi acionada. O código está limpo.")
        else:
            self.logger.info(f"{detected_smells} smells detectados.")

# --- Função que transforma logs em string unificada ---
def generate_logs_unified(logs_json):
    lines = []
    for entry in logs_json:
        level = entry["level"]
        msg = entry["message"]
        if level == "SUCCESS": lines.append(f"[✔] {msg}")
        elif level == "WARNING": lines.append(f"[⚠] {msg}")
        elif level == "ERROR": lines.append(f"[✖] {msg}")
        else: lines.append(f"[i] {msg}")
    return "\n".join(lines)

# --- Pipeline principal ---
def run_pipeline_from_content(
    smelldsl_content: str,
    limites_content: str,
    dados_content: str
):
    logger = Logger()
    try:
        # Interpreter
        logger.info("Etapa 1: Interpretando o arquivo .smelldsl...")
        interpretador = Interpreter(logger=logger)
        dados_interpretados = interpretador.run(smelldsl_content)
        logger.success("Etapa 1 concluída com sucesso.")

        # Validação
        logger.info("Etapa 2: Validando consistência dos dados JSON...")
        dados_data = json.loads(dados_content)
        limites_data = json.loads(limites_content)
        validator = DataValidator(dados_interpretados, logger)
        validator.validate(dados_data=dados_data, limites_data=limites_data)
        logger.success("Etapa 2 concluída com sucesso.")

        # Motor de execução
        logger.info("Etapa 3: Executando o motor de execução...")
        motor = ExecutionEngine(
            dados=dados_data,
            limites=limites_data,
            logger=logger
        )
        motor.avaliar_features()
        logger.success("Etapa 3 concluída com sucesso.")

        # Regras
        logger.info("Etapa 4: Verificando regras...")
        rule_checker = RuleChecker(dados_interpretados, motor, logger)
        rule_checker.check_all_rules()
        logger.success("Etapa 4 concluída com sucesso.")

        logger.success("Processo completo executado sem erros.")

    except (FileNotFoundError, SyntaxError, SemanticError, ExecutionError, ValidationError) as e:
        logger.error(f"Falha na execução: {e}")

    logs_json = logger.get_logs()
    logs_unified = generate_logs_unified(logs_json)
    # Adiciona a nova "coluna" no JSON
    for entry in logs_json:
        entry["logs_unificado"] = logs_unified

    return logs_json

def main_api(smelldsl_content, limites_content, dados_content):
    logs = run_pipeline_from_content(smelldsl_content, limites_content, dados_content)
    return logs  # retorna JSON pronto para API

