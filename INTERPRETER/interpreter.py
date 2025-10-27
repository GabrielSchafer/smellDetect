
import re
from dataclasses import dataclass, field
from typing import Optional

# -----------------------------------------------------------------------------
# 1. Definições de Estruturas e Erros
# -----------------------------------------------------------------------------
class SemanticError(Exception):
    """Exceção para erros semânticos."""
    pass

@dataclass
class Feature:
    name: str
    thresholds: list[str]

@dataclass
class Smell:
    name: str
    extends: Optional[str] 
    features: list[Feature] = field(default_factory=list)
    symptom: Optional[str] = None
    treatment: Optional[str] = None

@dataclass
class Rule:
    name: str
    condition: str
    action: str

@dataclass
class ParsedResult:
    smell_types: list[str] = field(default_factory=list)
    smells: list[Smell] = field(default_factory=list)
    rules: list[Rule] = field(default_factory=list)

    def display(self):
        """Imprime os resultados da análise de forma organizada e legível."""
        
        print("\n" + "-"*25)
        print("  Análise Semântica")
        print("-"*25)

        # Imprime os Tipos de Smells
        print(f"\nTipos de Smells Declarados ({len(self.smell_types)}):")
        if self.smell_types:
            print(f"  - {', '.join(self.smell_types)}")
        else:
            print("  - Nenhum")

        # Imprime os Smells
        print(f"\nSmells Definidos ({len(self.smells)}):")
        if self.smells:
            for smell in self.smells:
                print(f"\n  Smell: {smell.name}")
                if smell.extends:
                    print(f"    - Herda de: {smell.extends}")
                for feature in smell.features:
                    print(f"    - Feature: {feature.name} (Limites: {', '.join(feature.thresholds)})")
                if smell.symptom:
                    print(f"    - Sintoma: {smell.symptom}")
                if smell.treatment:
                    print(f"    - Tratamento: {smell.treatment}")
        else:
            print("  - Nenhum")

        # Imprime as Regras
        print(f"\nRegras de Detecção ({len(self.rules)}):")
        if self.rules:
            for rule in self.rules:
                print(f"\n  Regra: {rule.name}")
                print(f"    - Condição: {rule.condition}")
                print(f"    - Ação: {rule.action}")
        else:
            print("  - Nenhuma")
        
        print("\n" + "-"*25)

# -----------------------------------------------------------------------------
# 2. Analisador Léxico (Tokenizer)
# -----------------------------------------------------------------------------
class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value
    def __repr__(self):
        return f"Token({self.type}, '{self.value}')"

class Lexer:
    def __init__(self, code):
        self.code = code
        self.token_specification = [
            ('COMMENT',   r'//.*'),
            ('ID',        r'[A-Za-z_][A-Za-z0-9_]*'),
            ('OPERATOR',  r'>|='),
            ('LBRACE',    r'\{'),
            ('RBRACE',    r'\}'),
            ('DOT',       r'\.'),
            ('COMMA',     r','),
            ('NEWLINE',   r'\n'),
            ('SKIP',      r'[ \t]+'),
            ('MISMATCH',  r'.'),
        ]
        self.keywords = {
            'smelltype', 'smell', 'extends', 'feature', 'is', 'Interval',
            'with', 'threshold', 'symptom', 'treatment', 'rule', 'when', 'then'
        }

    def tokenize(self):
        tokens = []
        tok_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in self.token_specification)
        for mo in re.finditer(tok_regex, self.code):
            kind = mo.lastgroup
            value = mo.group()

            if kind == 'ID' and value in self.keywords:
                kind = value.upper()
            elif kind in ['SKIP', 'COMMENT', 'NEWLINE']:
                continue
            elif kind == 'MISMATCH':
                raise RuntimeError(f'Caractere inesperado: {value}')
            tokens.append(Token(kind, value))
        return tokens

# -----------------------------------------------------------------------------
# 3. Analisador Sintático (Parser)
# -----------------------------------------------------------------------------
class Parser:
    def __init__(self, tokens, logger=None):
        self.tokens = tokens
        self.current_token_index = 0
        self.result = ParsedResult()
        self.logger = logger

    def current_token(self):
        return self.tokens[self.current_token_index] if self.current_token_index < len(self.tokens) else None

    def advance(self):
        self.current_token_index += 1

    def eat(self, token_type):
        token = self.current_token()
        if token and token.type == token_type:
            self.advance()
            return token
        else:
            expected = token_type
            found = f"'{token.type}'" if token else "Fim do código"
            raise SyntaxError(f"Erro de Sintaxe: Esperado token '{expected}', mas encontrado {found}")

    def parse(self):
        while self.current_token():
            token_type = self.current_token().type
            if token_type == 'SMELLTYPE':
                self.parse_smelltype()
            elif token_type == 'SMELL':
                self.parse_smell()
            elif token_type == 'RULE':
                self.parse_rule()
            else:
                raise SyntaxError(f"Token inesperado no início de uma declaração: {self.current_token()}")

        if self.logger:
            self.logger.success("Análise sintática concluída com sucesso!")
        else:
            print("Análise sintática concluída com sucesso!")

        return self.result

    def parse_smelltype(self):
        self.eat('SMELLTYPE')
        name = self.eat('ID').value
        self.result.smell_types.append(name)

    def parse_smell(self):
        self.eat('SMELL')
        name = self.eat('ID').value
        extends = None
        if self.current_token() and self.current_token().type == 'EXTENDS':
            self.eat('EXTENDS')
            extends = self.eat('ID').value
        smell_obj = Smell(name=name, extends=extends)
        self.eat('LBRACE')
        while self.current_token() and self.current_token().type != 'RBRACE':
            token_type = self.current_token().type
            if token_type == 'FEATURE':
                smell_obj.features.append(self.parse_feature())
            elif token_type == 'SYMPTOM':
                self.eat('SYMPTOM')
                smell_obj.symptom = self.eat('ID').value
            elif token_type == 'TREATMENT':
                self.eat('TREATMENT')
                smell_obj.treatment = self.eat('ID').value
            else:
                raise SyntaxError(f"Token inesperado dentro do bloco 'smell': {self.current_token()}")
        self.eat('RBRACE')
        self.result.smells.append(smell_obj)

    def parse_feature(self):
        self.eat('FEATURE')
        name = self.eat('ID').value
        self.eat('IS')
        self.eat('INTERVAL')
        self.eat('WITH')
        self.eat('THRESHOLD')
        thresholds = [self.eat('ID').value]
        while self.current_token() and self.current_token().type == 'COMMA':
            self.eat('COMMA')
            thresholds.append(self.eat('ID').value)
        return Feature(name=name, thresholds=thresholds)

    def parse_rule(self):
        self.eat('RULE')
        name = self.eat('ID').value
        self.eat('WHEN')
    
        condition_tokens = []
        while self.current_token() and self.current_token().type != 'THEN':
            condition_tokens.append(self.current_token().value)
            self.advance()
        condition_string = " ".join(condition_tokens).replace(' . ', '.')

        self.eat('THEN')
    
        # --- LÓGICA CORRIGIDA PARA EVITAR O LOOP INFINITO ---
        action_tokens = [self.eat('ID').value] # Pega a primeira palavra da ação
    
        # Este loop agora avança corretamente para o próximo token
        while self.current_token() and self.current_token().type == 'ID':
            action_tokens.append(self.current_token().value)
            self.advance() # <-- ESTA LINHA ESTAVA FALTANDO E CAUSAVA O LOOP
        
        action_text = " ".join(action_tokens)
    
        rule_obj = Rule(name=name, condition=condition_string, action=action_text)
        self.result.rules.append(rule_obj)

# -----------------------------------------------------------------------------
# 4. Analisador Semântico
# -----------------------------------------------------------------------------
class SemanticAnalyzer:
    def __init__(self, parsed_result, logger=None):
        self.parsed_result = parsed_result
        self.logger = logger
        self.defined_smell_types = {}
        self.defined_smells = {}
        self.defined_rules = {}

    def analyze(self):
        if self.logger:
            self.logger.info("Iniciando análise semântica...")
        else:
            print("Iniciando análise semântica...")

        self.check_for_duplicates()
        self.check_extends_validity()
        self.check_rule_references()

        if self.logger:
            self.logger.success("Análise semântica concluída com sucesso!")
        else:
            print("Análise semântica concluída com sucesso!")

    def check_for_duplicates(self):
        for st_name in self.parsed_result.smell_types:
            if st_name in self.defined_smell_types:
                raise SemanticError(f"Nome de 'smelltype' duplicado: '{st_name}'")
            self.defined_smell_types[st_name] = True
        for smell in self.parsed_result.smells:
            if smell.name in self.defined_smells:
                raise SemanticError(f"Nome de 'smell' duplicado: '{smell.name}'")
            self.defined_smells[smell.name] = smell
        for rule in self.parsed_result.rules:
            if rule.name in self.defined_rules:
                raise SemanticError(f"Nome de 'rule' duplicado: '{rule.name}'")
            self.defined_rules[rule.name] = rule

    def check_extends_validity(self):
        for smell in self.parsed_result.smells:
            if smell.extends and smell.extends not in self.defined_smell_types:
                raise SemanticError(f"Erro no 'smell' '{smell.name}': Tenta herdar do 'smelltype' inexistente '{smell.extends}'.")

    def check_rule_references(self):
        """Verifica se as features usadas nas regras estão definidas nos smells correspondentes."""
    
        # Regex para encontrar o padrão "NomeDoSmell.NomeDaFeature" no início da condição
        rule_pattern = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)")

        for rule in self.parsed_result.rules:
            match = rule_pattern.match(rule.condition)
        
            if not match:
                # Se a condição da regra não seguir o padrão esperado, podemos pular ou avisar.
                # print(f"AVISO: A condição da regra '{rule.name}' não segue o padrão 'Smell.Feature' e não será validada.")
                continue

            smell_name = match.group(1)
            feature_name = match.group(2)
        
            # O resto da lógica de validação continua a mesma
            if smell_name not in self.defined_smells:
                raise SemanticError(f"Erro na regra '{rule.name}': O 'smell' '{smell_name}' não foi definido.")

            smell_obj = self.defined_smells[smell_name]
        
            if not any(f.name == feature_name for f in smell_obj.features):
                raise SemanticError(f"Erro na regra '{rule.name}': A 'feature' '{feature_name}' não existe no 'smell' '{smell_name}'.")


# -----------------------------------------------------------------------------
# 5. Interpretador Principal e Execução
# -----------------------------------------------------------------------------
class Interpreter:
    def __init__(self, logger=None):
        self.logger = logger

    def run(self, code):
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens, self.logger)
        parsed_data = parser.parse()
        analyzer = SemanticAnalyzer(parsed_data, self.logger)
        analyzer.analyze()
        return parsed_data
