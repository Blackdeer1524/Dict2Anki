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
            field: [val_1, .., val_n]}
        }
        field: thing
        Returns True if thing is in [val_1, .., val_n]
    Equivalent to in keyword

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
        Equivalent to field query


Special fields start with $ prefix
* ANY
    Gets result from the whole hierarchy level
    Example:
        {
        pos: {
            noun: {
                data: value_1
            }
            verb : {
                data: value_2
            }
        }
    }
    pos[$ANY][data]:value_1 will return True
    $ANY[$ANY][data]:value_1 also will return True

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
from typing import Iterable, Iterator
from typing import Optional, Any, Union

from consts.card_fields import FIELDS
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


class Computable(ABC):
    @abstractmethod
    def compute(self, mapping: Mapping):
        pass


KEYWORDS = frozenset(("in", ))
UNARY_LOGIC = frozenset(("not", ))
BIN_LOGIC_HIGH = frozenset(("<", "<=", ">", ">=", "==", "!="))
BIN_LOGIC_MID = frozenset(("and", ))
BIN_LOGIC_LOW  = frozenset(("or", ))
BIN_LOGIC_PRECEDENCE = (BIN_LOGIC_HIGH, BIN_LOGIC_MID, BIN_LOGIC_LOW)
BIN_LOGIC_SET  = reduce(lambda x, y: x | y, BIN_LOGIC_PRECEDENCE)


def logic_factory(operator: str) -> Union[Callable[[Union[Iterable[Computable], Computable],
                                                   Mapping], bool],
                                          Callable[[Union[Iterable[Computable], Computable],
                                                   Union[Iterable[Computable], Computable],
                                                   Mapping], bool]]:
    def operator_not(x: Union[Iterable[Computable], Computable],
                      mapping: Mapping):
        x_computed = x.compute(mapping)
        if isinstance(x_computed, Iterable):
            return (not item for item in x)
        return not x_computed

    def operator_and(x: Union[Iterable[Computable], Computable],
                     y: Union[Iterable[Computable], Computable],
                     mapping: Mapping):
        x_computed = x.compute(mapping)
        y_computed = y.compute(mapping)

        if isinstance(x_computed, Iterable):
            if isinstance(y_computed, Iterable):
                return (item_x and item_y for item_x in x_computed for item_y in y_computed)
            if not y_computed:
                return (False, )
            return (item_x for item_x in x_computed)

        if isinstance(y_computed, Iterable):
            if not x_computed:
                return (False,)
            return (item_y for item_y in y_computed)

        if not x_computed:
            return False
        return y_computed

    def operator_or(x: Union[Iterable[Computable], Computable],
                    y: Union[Iterable[Computable], Computable],
                    mapping: Mapping):
        x_computed = x.compute(mapping)
        y_computed = y.compute(mapping)

        if isinstance(x_computed, Iterable):
            if isinstance(y_computed, Iterable):
                return (item_x or item_y for item_x in x_computed for item_y in y_computed)
            if y_computed:
                return (True, )
            return (item_x for item_x in x_computed)

        if isinstance(y_computed, Iterable):
            if x_computed:
                return (True,)
            return (item_y for item_y in y_computed)

        if x_computed:
            return True

        return y_computed


    def bin_op_template(x: Union[Iterable[Computable], Computable],
                        y: Union[Iterable[Computable], Computable],
                        mapping: Mapping,
                        _op: Callable[[Any, Any], bool]):
        x_computed = x.compute(mapping)
        y_computed = y.compute(mapping)

        if isinstance(x_computed, Iterable):
            if isinstance(y_computed, Iterable):
                return (_op(item_x, item_y) for item_x in x_computed for item_y in y_computed)
            return (_op(item_x, y_computed) for item_x in x_computed)

        if isinstance(y_computed, Iterable):
            return (_op(x_computed, item_y) for item_y in y_computed)

        return _op(x_computed, y_computed)

    if operator == "not":
        return operator_not
    elif operator == "and":
        return operator_and
    elif operator == "or":
        return operator_or
    elif operator == "<":
        return partial(bin_op_template, _op=lambda x, y: x < y)  # type: ignore
    elif operator == "<=":
        return partial(bin_op_template, _op=lambda x, y: x <= y) # type: ignore
    elif operator == ">":
        return partial(bin_op_template, _op=lambda x, y: x > y)  # type: ignore
    elif operator == ">=":
        return partial(bin_op_template, _op=lambda x, y: x >= y)  # type: ignore
    elif operator == "==":
        return partial(bin_op_template, _op=lambda x, y: x == y)  # type: ignore
    elif operator == "!=":
        return partial(bin_op_template, _op=lambda x, y: x != y)  # type: ignore
    raise LogicOperatorError(f"Unknown operator: {operator}")
    

def method_factory(method_name: str) -> Callable[[Any], int]:
    if method_name == "len":
        def field_length(x):
            if isinstance(x, str):
                return len(x)
            return (len(str(item_x)) for item_x in x)
        return field_length
    elif method_name == "any":
        return lambda x: any(x) if isinstance(x, Iterable) else x
    elif method_name == "all":
        return lambda x: all(x) if isinstance(x, Iterable) else x
    raise WrongMethodError(f"Unknown method name: {method_name}")


def keyword_factory(keyword_name: str) -> Callable[[Any], int]:
    if keyword_name == "in":
        def field_contains(collection: Iterable, search_pattern: re.Pattern):
            if isinstance(collection, str):
                return re.search(search_pattern, collection) is not None
            return any((re.search(search_pattern, str(item)) is not None for item in collection))
        return field_contains
    raise WrongKeywordError(f"Unknown keyword: {keyword_name}")


FIELD_VAL_SEP = ":"
FIELD_NAMES_SET = frozenset(FIELDS)


class Token_T(Enum):
    START = auto()
    KEYWORD = auto()
    STRING = auto()
    SEP = auto()
    QUERY_STRING = auto()
    UN_LOGIC_OP = auto()
    BIN_LOGIC_OP = auto()
    L_PARENTHESIS = auto()
    R_PARENTHESIS = auto()
    END = auto()

STRING_PLACEHOLDER = "*"
END_PLACEHOLDER = "END"


@dataclass(slots=True, frozen=True)
class Token(Computable):
    un_logic_deduction: ClassVar[FrozenDict] = FrozenDict({logic_operator: Token_T.UN_LOGIC_OP for logic_operator in UNARY_LOGIC})
    bin_logic_deduction: ClassVar[FrozenDict] = FrozenDict({logic_operator: Token_T.BIN_LOGIC_OP for logic_operator in BIN_LOGIC_SET})
    keyword_deduction: ClassVar[FrozenDict] = FrozenDict({keyword_name: Token_T.KEYWORD for keyword_name in KEYWORDS})
    
    next_expected: ClassVar[FrozenDict] = FrozenDict(
        {Token_T.START:         {"(": Token_T.L_PARENTHESIS,
                                 STRING_PLACEHOLDER: Token_T.STRING,
                                 END_PLACEHOLDER: Token_T.END} | un_logic_deduction.to_dict(),

         Token_T.STRING:        {FIELD_VAL_SEP: Token_T.SEP,
                                 "(": Token_T.L_PARENTHESIS,
                                 ")": Token_T.R_PARENTHESIS,
                                 END_PLACEHOLDER: Token_T.END} | bin_logic_deduction.to_dict() | keyword_deduction.to_dict(),
         
         Token_T.KEYWORD:       {STRING_PLACEHOLDER: Token_T.STRING},
        
         Token_T.SEP:           {STRING_PLACEHOLDER: Token_T.QUERY_STRING},

         Token_T.QUERY_STRING:  {")": Token_T.R_PARENTHESIS,
                                 END_PLACEHOLDER: Token_T.END} | bin_logic_deduction.to_dict(),

         Token_T.UN_LOGIC_OP:   {STRING_PLACEHOLDER: Token_T.STRING,
                                 "(": Token_T.L_PARENTHESIS},

         Token_T.BIN_LOGIC_OP:  {STRING_PLACEHOLDER: Token_T.STRING,
                                 "(": Token_T.L_PARENTHESIS} | un_logic_deduction.to_dict(),

         Token_T.L_PARENTHESIS: {STRING_PLACEHOLDER: Token_T.STRING,
                                 "(": Token_T.L_PARENTHESIS} | un_logic_deduction.to_dict(),

         Token_T.R_PARENTHESIS: {END_PLACEHOLDER: Token_T.END,
                                 ")": Token_T.R_PARENTHESIS} | bin_logic_deduction.to_dict(),

         Token_T.END:           {}
         })
    
    value: str
    prev_token_type: Token_T = field(repr=False)
    t_type: Optional[Token_T] = None

    def __post_init__(self):
        def get_expected_keys() -> str:
            nonlocal expected_types
            return f"[{' '.join(expected_types.keys())}] were expected!"

        def get_expected_values() -> str:
            nonlocal expected_types
            return f"[{' '.join([token.name for token in expected_types.values()])}] were expected!"

        expected_types: FrozenDict[str, Token_T] = Token.next_expected[self.prev_token_type]
        if self.t_type is not None:
            if (self.t_type == Token_T.STRING and expected_types.get(STRING_PLACEHOLDER)) is None or \
                expected_types.get(self.value) is None:
                raise WrongTokenError(f"Unexpected forced token! \"{self.t_type}\" was forced when "
                                      f"{get_expected_values()}")
            return

        if (deduced_type := expected_types.get(self.value)) is None:
            if (str_type := expected_types.get(STRING_PLACEHOLDER)) is None:
                raise WrongTokenError(f"Unexpected token! \"{self.value}\" was given when "
                                      f"{get_expected_keys()}")
            object.__setattr__(self, "t_type", str_type)
            return
        object.__setattr__(self, "t_type", deduced_type)

    def compute(self, mapping: Mapping):
        if self.t_type != Token_T.STRING:
            raise WrongTokenError("Can't compute non-STRING token!")
        if not self.value.lstrip("-").isdecimal():
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
                         t_type=Token_T.SEP), start_ind + 1

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
            current_token_type = cur_token.t_type
        if parenthesis_counter:
            raise QuerySyntaxError("Too many opening parentheses!")
        return res


@dataclass(slots=True, frozen=True, init=False)
class _CardFieldData(Computable):
    ANY_FIELD: ClassVar[str] = "$ANY"

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

        object.__setattr__(self, "query_chain", chain)

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

    def compute(self, mapping: Mapping) -> list[Any]:
        """query_chain: chain of keys"""
        result = []

        def traverse_recursively(entry: Union[Mapping, Any], chain_index: int = 0) -> None:
            nonlocal result
            if chain_index == len(self.query_chain):
                result.append(entry)
                return

            if not isinstance(entry, Mapping):
                return None

            if self.query_chain[chain_index] == _CardFieldData.ANY_FIELD:
                for key in entry:
                    if (val := entry.get(key)) is not None:
                        traverse_recursively(val, chain_index + 1)
            else:
                if (val := entry.get(self.query_chain[chain_index])) is not None:
                    traverse_recursively(val, chain_index + 1)

        traverse_recursively(mapping)
        return result


@dataclass(slots=True, frozen=True)
class Method(Computable):
    operand: Computable

    method: Callable[[Any], int]

    def compute(self, mapping: Mapping) -> Union[Iterator[int], int]:
        computed_operand = self.operand.compute(mapping)
        return self.method(computed_operand)


@dataclass(slots=True, frozen=True)
class EvalNode(Computable):
    operator: str
    left: Optional[Union[Computable, Token]] = None
    right: Optional[Union[Computable, Token]] = None
    operation: Union[Callable[[Computable, Mapping],             Any],
                     Callable[[Computable, Computable, Mapping], Any]] = field(init=False, repr=False)

    def __post_init__(self):
        if isinstance(self.left, Token) and isinstance(self.right, Token):
            raise TreeBuildingError("Two STRING's in one node!")
        object.__setattr__(self, "operation", logic_factory(self.operator))

    def compute(self, mapping: Mapping) -> bool:
        if self.left is not None and self.right is not None:
            return bool(self.operation(self.left, self.right, mapping))
        elif self.left is not None:
            return bool(self.operation(self.left, mapping))
        raise TreeBuildingError("Empty node!")


class LogicTree:
    def __init__(self, tokens):
        if len(tokens) == 1:
            raise TreeBuildingError("Couldn't build from an empty query!")
        self._expressions = copy.deepcopy(tokens)

    def construct(self, start: int = 0):
        current_index = start
        while current_index < len(self._expressions) - 2:
            if self._expressions[current_index].t_type != Token_T.STRING:
                if self._expressions[current_index].t_type == Token_T.L_PARENTHESIS:
                    self._expressions.pop(current_index)
                    self.construct(current_index)
                current_index += 1
                continue

            if self._expressions[current_index + 1].t_type == Token_T.SEP:
                field_query = self._expressions.pop(current_index + 2).value
                self._expressions.pop(current_index + 1)
                field = self._expressions.pop(current_index).value
                self._expressions.insert(current_index,
                                         Method(_CardFieldData(field),
                                                partial(keyword_factory("in"), search_pattern=re.compile(field_query))))

            elif self._expressions[current_index + 1].t_type == Token_T.KEYWORD:
                query = self._expressions.pop(current_index).value
                keyword_name = self._expressions.pop(current_index).value
                keyword_function = partial(keyword_factory(keyword_name), search_pattern=re.compile(query))
                self.construct(current_index)
                operand = self._expressions.pop(current_index)
                self._expressions.insert(current_index, Method(operand, keyword_function))

            elif self._expressions[current_index + 1].t_type == Token_T.L_PARENTHESIS:
                method_name = self._expressions.pop(current_index).value
                method_function = method_factory(method_name)
                self._expressions.pop(current_index)  # parenthesis
                self.construct(current_index)
                operand = self._expressions.pop(current_index)
                self._expressions.insert(current_index, Method(operand, method_function))

            if self._expressions[current_index + 1].t_type in (Token_T.R_PARENTHESIS, Token_T.END):
                break
            current_index += 1

        current_index = start
        while current_index < len(self._expressions) - 2:
            operator = self._expressions[current_index]
            if not isinstance(operator, Token):
                current_index += 1
                continue

            elif operator.t_type == Token_T.R_PARENTHESIS:
                break

            if operator.value not in UNARY_LOGIC:
                current_index += 1
                continue

            operand = self._expressions[current_index + 1]
            if isinstance(operand, Token) and operator.t_type == Token_T.END:
                break

            self._expressions.pop(current_index)
            operand = self._expressions.pop(current_index)
            self._expressions.insert(current_index, EvalNode(left=operand, operator=operator.value))

        for current_logic_set in BIN_LOGIC_PRECEDENCE:
            current_index = start
            while current_index < len(self._expressions) - 2:
                operator = self._expressions[current_index + 1]
                if operator.t_type in (Token_T.R_PARENTHESIS, Token_T.END):
                    break

                if operator.value in current_logic_set:
                    left_operand = self._expressions.pop(current_index)
                    self._expressions.pop(current_index)
                    right_operand = self._expressions.pop(current_index)
                    self._expressions.insert(current_index, EvalNode(left=left_operand, right=right_operand,
                                                                     operator=operator.value))
                else:
                    current_index += 2
        if self._expressions[start + 1].t_type == Token_T.R_PARENTHESIS:
            self._expressions.pop(start + 1)

    def get_master_node(self):
        if len(self._expressions) != 2:
            raise TreeBuildingError("Error creating a syntax tree!")
        return self._expressions[0]


def get_card_filter(expression: str) -> Callable[[Mapping], bool]:
    _tokenizer = Tokenizer(expression)
    tokens = _tokenizer.get_tokens()
    if tokens[0].t_type == Token_T.END:
        return lambda x: True

    _logic_tree = LogicTree(tokens)
    _logic_tree.construct()
    return _logic_tree.get_master_node().compute


def main():
    queries = ("field: query and len(inner_query in len(field))",
               "word: test and meaning:\"some meaning\" "
                          "or alt_terms:alt and (sentences : \"some sentences\" or tags : some_tags and (tags[pos] : noun)) "
                          "and (len(sentences) < 5)",
                "\"test tag\": \"test value\" and len(user_tags[image_links]) == 5",
               "len(\"meaning [  test  ][tag]\") == 2 or len(meaning[test][tag]) != 2")

    # for query in queries:
    #     get_card_filter(query)

    query = "(\"(B|C)\\d\" in $ANY[$ANY][level])"
    card_filter = get_card_filter(query)
    test_card = {'insult':
                  {'noun': {'UK_IPA': ['/ˈɪn.sʌlt/'],
                            'UK_audio_link': 'https://dictionary.cambridge.org//media/english/uk_pron/u/uki/ukins/ukinstr024.mp3',
                            'US_IPA': ['/ˈɪn.sʌlt/'],
                            'US_audio_link': 'https://dictionary.cambridge.org//media/english/us_pron/i/ins/insul/insult_01_01.mp3',
                            'alt_terms': [[]],
                            'definitions': ['an offensive remark or action'],
                            'domain': [[]],
                            'examples': [['She made several insults about my appearance.',
                                          "The steelworkers' leader rejected the two percent "
                                          'pay rise saying it was an insult to the profession.',
                                          'The instructions are so easy they are an insult to '
                                          'your intelligence (= they seem to suggest you are '
                                          'not clever if you need to use them).']],
                            'image_links': [''],
                            'labels_and_codes': [['[ C ]']],
                            'level': ['C2'],
                            'region': [[]],
                            'usage': [[]]},
                   'verb': {'UK_IPA': ['/ɪnˈsʌlt/'],
                            'UK_audio_link': 'https://dictionary.cambridge.org//media/english/uk_pron/u/uki/ukins/ukinstr025.mp3',
                            'US_IPA': ['/ɪnˈsʌlt/'],
                            'US_audio_link': 'https://dictionary.cambridge.org//media/english/us_pron/i/ins/insul/insult_01_00.mp3',
                            'alt_terms': [[]],
                            'definitions': ['to say or do something to someone that is rude or '
                                            'offensive'],
                            'domain': [[]],
                            'examples': [['First he drank all my wine and then he insulted all '
                                          'my friends.']],
                            'image_links': [''],
                            'labels_and_codes': [['[ T ]']],
                            'level': ['C1'],
                            'region': [[]],
                            'usage': [[]]}}}
    result = card_filter(test_card)
    print(result)


if __name__ == "__main__":
    main()
