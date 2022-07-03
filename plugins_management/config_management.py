import json
import os
from collections import UserDict
from dataclasses import dataclass, field
from typing import ClassVar, Any, Type, Sequence


class Config(UserDict):
    @dataclass(slots=True, frozen=True)
    class SchemeCheckResults:
        wrong_type: list = field(default_factory=list)
        wrong_value: list = field(default_factory=list)
        unknown_keys: list = field(default_factory=list)
        missing_keys: list = field(default_factory=list)

    CONF_FILE_NAME: ClassVar[str] = "config.json"
    ENCODING: ClassVar[str] = "UTF-8"

    def __init__(self, validation_scheme: dict[Any, tuple[Any, Sequence[Type], Sequence[Any]]]):
        super(Config, self).__init__(data={})

        self.default_scheme = {}
        self.validation_scheme = validation_scheme

        def assign_default(entry: dict):
            for key in entry:
                value = entry[key]
                if isinstance(value, dict):
                    self.default_scheme[key] = {}
                    assign_default(value)
                    continue
                self.default_scheme[key] = entry[key][0]

        assign_default(self.validation_scheme)

        self._conf_file_path = os.path.join(os.path.dirname(__file__), Config.CONF_FILE_NAME)
        self.load()

    @staticmethod
    def validate_config(checking_part: dict, validating_part: dict) -> "Config.SchemeCheckResults":
        current_layer_res = Config.SchemeCheckResults()

        checking_keys = set(checking_part)
        validating_keys = set(validating_part)

        for c_key in checking_keys:
            if c_key not in validating_keys:
                current_layer_res.unknown_keys.append(c_key)
                checking_part.pop(c_key)
                continue

            c_val = checking_part[c_key]
            v_val = validating_part[c_key]

            if isinstance(v_val, dict):
                if isinstance(c_val, dict):
                    inner_layer_res = Config.validate_config(c_val, v_val)
                    current_layer_res.wrong_type.extend(inner_layer_res.wrong_type)
                    current_layer_res.wrong_value.extend(inner_layer_res.wrong_value)
                    current_layer_res.unknown_keys.extend(inner_layer_res.unknown_keys)
                    current_layer_res.missing_keys.extend(inner_layer_res.missing_keys)
                else:
                    def assign_recursively(dst: dict, src: dict):
                        for s_key, s_val in src.items():
                            if isinstance(s_val, dict):
                                dst[s_key] = {}
                                assign_recursively(dst[s_key], s_val)
                            else:
                                dst[s_key] = s_val[0]
                    checking_part[c_key] = {}
                    assign_recursively(checking_part, v_val)
                    current_layer_res.wrong_type.append((c_key, type(c_val), type(v_val)))
            elif len(v_val[1]) and type(c_val) not in v_val[1]:
                checking_part[c_key] = v_val[0]
                current_layer_res.wrong_type.append((c_key, type(c_val), v_val[1]))
            elif len(v_val[2]) and c_val not in v_val[2]:
                current_layer_res.wrong_value.append((c_key, c_val, v_val[2]))
                checking_part[c_key] = v_val[0]
            validating_keys.remove(c_key)

        current_layer_res.missing_keys.extend(validating_keys)
        for v_key in validating_keys:
            checking_part[v_key] = validating_part[v_key][0]
        return current_layer_res

    def load(self):
        if os.path.exists(self._conf_file_path):
            with open(self._conf_file_path, "r", encoding=Config.ENCODING) as conf_file:
                self.data = json.load(conf_file)
            self.validate_config(self.data, self.validation_scheme)
            return

        with open(self._conf_file_path, "w", encoding=Config.ENCODING) as conf_file:
            json.dump(self.default_scheme, conf_file)
        self.data = self.default_scheme

    def save(self):
        with open(self._conf_file_path, "w", encoding=Config.ENCODING) as conf_file:
            json.dump(self.data, conf_file)
