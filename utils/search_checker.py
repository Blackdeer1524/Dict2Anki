"""
Language query help

Unary operators:
* logic operators:
    not

Binary operators:
* logic operators
    and, or
* arithmetics operators:
    <, <=, >, >=, ==, !=

Field query:
    field : query
    Checks whether <thing> is in <field>[<subfield_1>][...][<subfield_n>]
    Example:
        {
            field: value}
        }
        field: thing
        Returns True if thing is in value

Methods:
    len
        Measures length of iterable object
        Example:
            {
                field: [1, 2, 3]
            }
            len(field) will return 3

Keywords:
    in
        Checks whether <thing> is in <field>[<subfield_1>][...][<subfield_n>]
        Example:
            {
                field: [val_1, .., val_n]}
            }

            thing in field
            Returns True if thing is in [val_1, .., val_n]


Evaluation precedence:
1) field queries
2) keywords
3) expressions in parentheses
4) unary operators
5) binary operators
"""


import copy
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import partial
from functools import reduce
import re
from typing import Callable, Sized, ClassVar
from typing import Iterable
from typing import Optional, Any, Union

from consts.card_fields import FIELDS
from utils.cards import Card
from utils.storages import FrozenDict


class ParsingException(Exception):
    pass


class LogicOperatorError(ParsingException):
    pass


class WrongMethodError(ParsingException):
    pass


class WrongKeywordError(ParsingException):
    pass


class WrongTokenError(ParsingException):
    pass


class QuerySyntaxError(ParsingException):
    pass


class TreeBuildingError(ParsingException):
    pass


KEYWORDS = frozenset(("in", ))
UNARY_LOGIC = frozenset(("not", ))
BIN_LOGIC_HIGH = frozenset(("<", "<=", ">", ">=", "==", "!="))
BIN_LOGIC_MID = frozenset(("and", ))
BIN_LOGIC_LOW  = frozenset(("or", ))
BIN_LOGIC_PRECEDENCE = (BIN_LOGIC_HIGH, BIN_LOGIC_MID, BIN_LOGIC_LOW)
BIN_LOGIC_SET  = reduce(lambda x, y: x | y, BIN_LOGIC_PRECEDENCE)


def logic_factory(operator: str) -> Union[Callable[[bool], bool],
                                          Callable[[bool, bool], bool]]:
    if operator == "not":
        return lambda x: not x
    elif operator == "and":
        return lambda x, y: x and y
    elif operator == "or":
        return lambda x, y: x or y
    elif operator == "<":
        return lambda x, y: x < y
    elif operator == "<=":
        return lambda x, y: x <= y
    elif operator == ">":
        return lambda x, y: x > y
    elif operator == ">=":
        return lambda x, y: x >= y
    elif operator == "==":
        return lambda x, y: x == y
    elif operator == "!=":
        return lambda x, y: x != y
    raise LogicOperatorError(f"Unknown operator: {operator}")
    

def method_factory(method_name: str) -> Callable[[Any], int]:
    if method_name == "len":
        def field_length(x: Sized):
            try:
                return len(x)
            except TypeError:
                return False
        return field_length
    raise WrongMethodError(f"Unknown method name: {method_name}")


def keyword_factory(keyword_name: str) -> Callable[[Any], int]:
    if keyword_name == "in":
        def field_contains(collection: Iterable, search_pattern: re.Pattern):
            try:
                return any((re.search(search_pattern, str(item)) for item in collection))
            except TypeError:
                return False
        return field_contains
    raise WrongKeywordError(f"Unknown keyword: {keyword_name}")


FIELD_VAL_SEP = ":"
FIELD_NAMES_SET = frozenset(FIELDS)


class Token_T(Enum):
    START = auto()
    STRING = auto()
    KEYWORD = auto()
    SEP = auto()
    QUERY_STRING = auto()
    UN_LOGIC_OP = auto()
    BIN_LOGIC_OP = auto()
    METHOD_LP = auto()
    METHOD_STRING = auto()
    METHOD_RP = auto()
    LOGIC_LP = auto()
    LOGIC_RP = auto()
    END = auto()

STRING_PLACEHOLDER = "*"
END_PLACEHOLDER = "END"


class Expression(ABC):
    @abstractmethod
    def compute(self, card: Card):
        pass


@dataclass(frozen=True)
class Token(Expression):
    un_logic_deduction: ClassVar[FrozenDict] = FrozenDict({logic_operator: Token_T.UN_LOGIC_OP for logic_operator in UNARY_LOGIC})
    bin_logic_deduction: ClassVar[FrozenDict] = FrozenDict({logic_operator: Token_T.BIN_LOGIC_OP for logic_operator in BIN_LOGIC_SET})
    keyword_deduction: ClassVar[FrozenDict] = FrozenDict({keyword_name: Token_T.KEYWORD for keyword_name in KEYWORDS})
    
    next_expected: ClassVar[FrozenDict] = FrozenDict(
        {Token_T.START:         {"(": Token_T.LOGIC_LP,
                                 STRING_PLACEHOLDER: Token_T.STRING,
                                 END_PLACEHOLDER: Token_T.END} | un_logic_deduction.to_dict(),

         Token_T.STRING:        {FIELD_VAL_SEP: Token_T.SEP,
                                 "(": Token_T.METHOD_LP,
                                 ")": Token_T.LOGIC_RP,
                                 END_PLACEHOLDER: Token_T.END} | bin_logic_deduction.to_dict() | keyword_deduction.to_dict(),
         
         Token_T.KEYWORD:       {STRING_PLACEHOLDER: Token_T.QUERY_STRING},
        
         Token_T.SEP:           {STRING_PLACEHOLDER: Token_T.QUERY_STRING},

         Token_T.QUERY_STRING:  {")": Token_T.LOGIC_RP,
                                 END_PLACEHOLDER: Token_T.END} | bin_logic_deduction.to_dict(),

         Token_T.UN_LOGIC_OP:   {STRING_PLACEHOLDER: Token_T.STRING,
                                 "(": Token_T.LOGIC_LP},

         Token_T.BIN_LOGIC_OP:  {STRING_PLACEHOLDER: Token_T.STRING,
                                 "(": Token_T.LOGIC_LP} | un_logic_deduction.to_dict(),

         Token_T.METHOD_LP:     {STRING_PLACEHOLDER: Token_T.METHOD_STRING},

         Token_T.METHOD_STRING: {")": Token_T.METHOD_RP},

         Token_T.METHOD_RP:     {")": Token_T.LOGIC_RP,
                                 END_PLACEHOLDER: Token_T.END} | bin_logic_deduction.to_dict(),

         Token_T.LOGIC_LP:      {STRING_PLACEHOLDER: Token_T.STRING,
                                 "(": Token_T.LOGIC_LP} | un_logic_deduction.to_dict(),

         Token_T.LOGIC_RP:      {END_PLACEHOLDER: Token_T.END,
                                 ")": Token_T.LOGIC_RP} | bin_logic_deduction.to_dict(),

         Token_T.END:           {}
         })
    
    value: str
    prev_token_type: Token_T = field(repr=False)
    type: Optional[Token_T] = None
    
    def __post_init__(self):
        def get_expected_keys() -> str:
            nonlocal expected_types
            return f"[{' '.join(expected_types.keys())}] were expected!"

        def get_expected_values() -> str:
            nonlocal expected_types
            return f"[{' '.join([token.name for token in expected_types.values()])}] were expected!"

        expected_types: FrozenDict[str, Token_T] = Token.next_expected[self.prev_token_type]
        if self.type is not None:
            if (self.type == Token_T.STRING and expected_types.get(STRING_PLACEHOLDER)) is None or \
                expected_types.get(self.value) is None:
                raise WrongTokenError(f"Unexpected forced token! \"{self.type}\" was forced when "
                                      f"{get_expected_values()}")
            return

        if (deduced_type := expected_types.get(self.value)) is None:
            if (str_type := expected_types.get(STRING_PLACEHOLDER)) is None:
                raise WrongTokenError(f"Unexpected token! \"{self.value}\" was given when "
                                      f"{get_expected_keys()}")
            super().__setattr__("type", str_type)
            return
        super().__setattr__("type", deduced_type)

    def compute(self, card: Card):
        if self.type != Token_T.STRING:
            raise WrongTokenError("Can't compute non-STRING token!")
        if not self.value.isdecimal():
            raise WrongTokenError("Can't compute non-decimal STRING token!")
        return float(self.value)


class Tokenizer:
    def __init__(self, exp: str):
        self.exp = exp

    def _get_next_token(self, start_ind: int, prev_token_type: Token_T) -> tuple[Token, int]:
        while start_ind < len(self.exp) and self.exp[start_ind].isspace():
            start_ind += 1

        if start_ind == len(self.exp):
            return Token(END_PLACEHOLDER, prev_token_type), start_ind

        if self.exp[start_ind] == FIELD_VAL_SEP:
            return Token(value=self.exp[start_ind],
                         prev_token_type=prev_token_type,
                         type=Token_T.SEP), start_ind + 1

        if self.exp[start_ind] in "()":
            return Token(self.exp[start_ind], prev_token_type), start_ind + 1

        if self.exp[start_ind] == "\"":
            start_ind += 1
            i = start_ind
            while i < len(self.exp) and (self.exp[i] != "\"" or self.exp[i-1] == "\\"):
                i += 1
            if i == len(self.exp):
                raise QuerySyntaxError("Wrong <\"> usage!")
            return Token(self.exp[start_ind:i], prev_token_type), i + 1

        i = start_ind
        while i < len(self.exp):
            if self.exp[i].isspace():
                return Token(self.exp[start_ind:i], prev_token_type), i + 1
            elif self.exp[i] in f"(){FIELD_VAL_SEP}":
                break
            i += 1

        return Token(self.exp[start_ind:i], prev_token_type), i

    def get_tokens(self):
        search_index = 0
        res: list[Token] = []

        current_token_type = Token_T.START

        parenthesis_counter = 0
        while current_token_type != Token_T.END:
            cur_token, search_index = self._get_next_token(search_index, current_token_type)
            res.append(cur_token)
            if cur_token.value == "(":
                parenthesis_counter += 1
            elif cur_token.value == ")":
                parenthesis_counter -= 1
                if parenthesis_counter < 0:
                    raise QuerySyntaxError("Too many closing parentheses!")
            current_token_type = cur_token.type
        if parenthesis_counter:
            raise QuerySyntaxError("Too many opening parentheses!")
        return res


@dataclass(frozen=True, init=False)
class _CardFieldData:
    query_chain: list[str] = field(init=False, repr=True)
    
    def __init__(self, path: str):
        self._check_nested_path(path)
        chain = []

        start = current_index = 0
        while current_index < len(path) and path[current_index] != "[":
            current_index += 1
        last_closed_bracket = current_index

        while current_index < len(path):
            if path[current_index] == "[":
                chain.append(path[start:last_closed_bracket])
                start = current_index + 1
            elif path[current_index] == "]":
                last_closed_bracket = current_index
            current_index += 1

        if start != current_index:
            chain.append(path[start:last_closed_bracket])

        super().__setattr__("query_chain", chain)
    
    @staticmethod
    def _check_nested_path(path) -> None:
        bracket_stack = 0
        last_closing_bracket = -1
        for i in range(len(path)):
            char = path[i]
            if char == "[":
                bracket_stack += 1
            elif char == "]":
                last_closing_bracket = i
                bracket_stack -= 1
                if bracket_stack < 0:
                    raise QuerySyntaxError("Wrong bracket sequence in field query!")

        if last_closing_bracket > 0:
            for i in range(last_closing_bracket + 1, len(path)):
                if not path[i].isspace():
                    raise QuerySyntaxError("Wrong bracket sequence in field query!")
    
    def get_field_data(self, card: Card) -> Any:
        """query_chain: chain of keys"""
        current_entry = card
        for key in self.query_chain:
            if not isinstance(current_entry, Mapping):
                return None

            current_entry = current_entry.get(key)
            if current_entry is None:
                return None
        return current_entry


@dataclass(frozen=True)
class FieldExpression(Expression):
    card_field_data: _CardFieldData


@dataclass(frozen=True)
class FieldCheck(FieldExpression):
    query: str
    compiled_query: re.Pattern = field(init=False, repr=False)
    
    def __post_init__(self):
        super().__setattr__("compiled_query", compile(self.query))
    
    def compute(self, card: Card) -> bool:
        field_data = self.card_field_data.get_field_data(card)
        if not isinstance(field_data, str):
            return False
        return re.search(self.compiled_query, field_data) is not None


@dataclass(frozen=True)
class Method(FieldExpression):
    method: Callable[[Any], int]
    
    def compute(self, card: Card) -> int:
        field_data = self.card_field_data.get_field_data(card)
        return self.method(self.card_field_data.get_field_data(card)) if field_data is not None else 0


class TokenParser:
    def __init__(self, tokens: list[Token]):
        self._tokens: list[Token] = tokens
        self._expressions: list[Union[Expression, Token]] = []

    def get_field_check(self, index: int) -> tuple[Union[FieldCheck, None], int]:
        """index: STRING token index"""
        if self._tokens[index + 1].type == Token_T.SEP and \
           self._tokens[index + 2].type == Token_T.QUERY_STRING:
            return FieldCheck(_CardFieldData(self._tokens[index].value), self._tokens[index + 2].value), 2
        return None, 0

    def get_method(self, index: int) -> tuple[Union[Method, None], int]:
        """index: STRING token index"""
        if self._tokens[index + 1].type == Token_T.METHOD_LP and \
           self._tokens[index + 2].type == Token_T.METHOD_STRING and \
           self._tokens[index + 3].type == Token_T.METHOD_RP:
            return Method(_CardFieldData(self._tokens[index + 2].value), method_factory(self._tokens[index].value)), 3
        return None, 0
    
    def get_keyword(self, index: int):
        if self._tokens[index + 1].type == Token_T.KEYWORD and \
           self._tokens[index + 2].type == Token_T.QUERY_STRING:
            return Method(_CardFieldData(self._tokens[index + 2].value),
                          partial(keyword_factory(self._tokens[index + 1].value),
                                  search_pattern=re.compile(self._tokens[index].value))), 2
        return None, 0
        
    def _promote_to_expressions(self):
        i = 0
        while i < len(self._tokens):
            if self._tokens[i].type == Token_T.STRING:
                res, offset = self.get_field_check(i)
                if res is None:
                    res, offset = self.get_method(i)

                if res is None:
                    res, offset = self.get_keyword(i)

                if res is None:
                    if not self._tokens[i].value.isdecimal():
                        raise WrongTokenError(f"Decimal type expected, \"{self._tokens[i].value}\" was given!")

                    self._expressions.append(self._tokens[i])
                else:
                    self._expressions.append(res)
                i += offset
            else:
                self._expressions.append(self._tokens[i])
            i += 1

    def tokens2expressions(self) -> list[Union[Expression, Token]]:
        self._promote_to_expressions()
        return self._expressions


@dataclass(frozen=True)
class EvalNode(Expression):
    operator: str
    left: Optional[Union[Expression, Token]] = None
    right: Optional[Union[Expression, Token]] = None
    operation: Union[Callable[[Any],      bool],
                     Callable[[Any, Any], bool]] = field(init=False, repr=False)

    def __post_init__(self):
        if isinstance(self.left, Token) and isinstance(self.right, Token):
            raise TreeBuildingError("Two STRING's in one node!")
        super().__setattr__("operation", logic_factory(self.operator))

    def compute(self, card: Card) -> bool:
        if self.left is not None and self.right is not None:
            return self.operation(self.left.compute(card), self.right.compute(card))
        elif self.left is not None:
            return self.operation(self.left.compute(card))
        raise TreeBuildingError("Empty node!")


class LogicTree:
    def __init__(self, expressions):
        if len(expressions) == 1:
            raise TreeBuildingError("Couldn't build from an empty query!")
        self._expressions = copy.deepcopy(expressions)

    def construct(self, start: int = 0):
        current_index = start
        while current_index < len(self._expressions) - 1:
            operator = self._expressions[current_index]
            if not isinstance(operator, Token):
                current_index += 1
                continue

            if operator.type == Token_T.LOGIC_LP:
                self._expressions.pop(current_index)
                self.construct(current_index)
                current_index += 1
                continue
            elif operator.type == Token_T.LOGIC_RP:
                break

            if operator.value not in UNARY_LOGIC:
                current_index += 1
                continue

            operand = self._expressions[current_index + 1]
            if isinstance(operand, Token):
                if operand.type == Token_T.LOGIC_LP:
                    self._expressions.pop(current_index + 1)
                    self.construct(current_index + 1)
                elif operator.type == Token_T.END:
                    break

            self._expressions.pop(current_index)
            operand = self._expressions.pop(current_index)
            self._expressions.insert(current_index, EvalNode(left=operand, operator=operator.value))

        for current_logic_set in BIN_LOGIC_PRECEDENCE:
            current_index = start
            while current_index < len(self._expressions) - 1:
                operator = self._expressions[current_index + 1]
                if operator.type in (Token_T.LOGIC_RP, Token_T.END):
                    break

                if operator.value in current_logic_set:
                    left_operand = self._expressions.pop(current_index)
                    self._expressions.pop(current_index)
                    right_operand = self._expressions.pop(current_index)
                    self._expressions.insert(current_index, EvalNode(left=left_operand, right=right_operand,
                                                                     operator=operator.value))
                else:
                    current_index += 2
        self._expressions.pop(start + 1)

    def get_master_node(self):
        if len(self._expressions) != 1:
            raise TreeBuildingError("Error creating a syntax tree!")
        return self._expressions[0]


def get_card_filter(expression: str) -> Callable[[Card], bool]:
    _tokenizer = Tokenizer(expression)
    tokens = _tokenizer.get_tokens()
    if tokens[0].type == Token_T.END:
        return lambda x: True

    _token_parser = TokenParser(tokens=tokens)
    expressions = _token_parser.tokens2expressions()
    _logic_tree = LogicTree(expressions)
    _logic_tree.construct()
    return _logic_tree.get_master_node().compute


def main():
    queries = ("word: test and meaning:\"some meaning\" "
                          "or alt_terms:alt and (sentences : \"some sentences\" or tags : some_tags and (tags[pos] : noun)) "
                          "and (len(sentences) < 5)",
                "\"test tag\": \"test value\" and len(user_tags[image_links]) == 5",
               "len(\"meaning [  test  ][tag]\") == 2 or len(meaning[test][tag]) != 2")


    # for query in queries:
    #     get_card_filter(query)

    # query = "1 == len(Sen_Ex)"
    query = "test in word"
    card_filter = get_card_filter(query)
    test_card = {
        "word": "test",
        "meaning": "to do something in order to discover if something is safe, works correctly, etc., or if something is present",
        "Sen_Ex": [
            "The manufacturers are currently testing the new engine.",
            "They tested her blood for signs of the infection."
        ],
        "level": [
            "B2"
        ],
        "pos": "verb",
        "audio_link": "https://dictionary.cambridge.org//media/english/us_pron/t/tes/test_/test.mp3"
    }
    result = card_filter(test_card)
    print(result)


if __name__ == "__main__":
    main()
