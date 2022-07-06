import json
import os
from collections import UserDict
from dataclasses import dataclass, field
from typing import ClassVar, Any, Type, Sequence, Optional


class Config(UserDict):
    @dataclass(slots=True, frozen=True)
    class SchemeCheckResults:
        wrong_type: list =   field(default_factory=list)
        wrong_value: list =  field(default_factory=list)
        unknown_keys: list = field(default_factory=list)
        missing_keys: list = field(default_factory=list)

        def __bool__(self):
            return bool(self.wrong_type) or \
                   bool(self.wrong_value) or \
                   bool(self.unknown_keys) or \
                   bool(self.missing_keys)

    def __init__(self,
                 validation_scheme: dict[Any, tuple[Any, Sequence[Type], Sequence[Any]]],
                 docs: str,
                 initial_value: Optional[dict] = None):
        self.default_scheme = {}
        self.validation_scheme = validation_scheme
        Config.__assign_recursively(self.default_scheme, self.validation_scheme)
        self.docs = docs

        if initial_value is None:
            super(Config, self).__init__(self.default_scheme)
        else:
            super(Config, self).__init__(initial_value)
            self.validate_config(self.data, self.validation_scheme)

    @staticmethod
    def __assign_recursively(dst: dict, src: dict):
        for key in src:
            if isinstance((s_val := src[key]), dict):
                dst[key] = {}
                Config.__assign_recursively(dst[key], s_val)
            else:
                dst[key] = s_val[0]

    @staticmethod
    def validate_config(checking_part: dict, validating_part: dict) -> "Config.SchemeCheckResults":
        """INPLACE!!!"""
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
                    current_layer_res.wrong_type.append((c_key, type(c_val), dict))
            elif len(v_val[1]) and type(c_val) not in v_val[1]:
                checking_part[c_key] = v_val[0]
                current_layer_res.wrong_type.append((c_key, type(c_val), v_val[1]))
            elif len(v_val[2]) and c_val not in v_val[2]:
                current_layer_res.wrong_value.append((c_key, c_val, v_val[2]))
                checking_part[c_key] = v_val[0]
            validating_keys.remove(c_key)

        current_layer_res.missing_keys.extend(validating_keys)
        Config.__assign_recursively(checking_part, {key: validating_part[key] for key in validating_keys})
        return current_layer_res

    def restore_defaults(self):
        self.data = self.default_scheme


class LoadableConfig(Config):
    CONF_FILE_NAME: ClassVar[str] = "config.json"
    ENCODING: ClassVar[str] = "UTF-8"

    def __init__(self,
                 config_location: str,
                 validation_scheme: dict[Any, tuple[Any, Sequence[Type], Sequence[Any]]],
                 docs: str):
        super(LoadableConfig, self).__init__(validation_scheme=validation_scheme,
                                             docs=docs,
                                             initial_value={})
        self._conf_file_path = os.path.join(config_location, LoadableConfig.CONF_FILE_NAME)
        self.load()

    def load(self) -> Optional["Config.SchemeCheckResults"]:
        if not os.path.exists(self._conf_file_path):
            self.restore_defaults()
            self.save()
            return
        try:
            with open(self._conf_file_path, "r", encoding=LoadableConfig.ENCODING) as conf_file:
                self.data = json.load(conf_file)
        except (ValueError, TypeError):  # Catches JSON decoding exceptions
            self.restore_defaults()
            self.save()
            return
        return self.validate_config(self.data, self.validation_scheme)

    def save(self):
        with open(self._conf_file_path, "w", encoding=LoadableConfig.ENCODING) as conf_file:
            json.dump(self.data, conf_file, indent=4)
