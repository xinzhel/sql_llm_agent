from docstring_parser import epydoc, google, numpydoc, rest
from docstring_parser.attrdoc import add_attribute_docstrings
from docstring_parser.common import (
    Docstring,
    DocstringStyle,
    ParseError,
    RenderingStyle,
)
from pydantic import BaseModel, create_model, validate_arguments
import typing as T
import json
import os
_STYLE_MAP = {
    DocstringStyle.REST: rest,
    DocstringStyle.GOOGLE: google,
    DocstringStyle.NUMPYDOC: numpydoc,
    DocstringStyle.EPYDOC: epydoc,
}
def parse(text: str, style: DocstringStyle = DocstringStyle.AUTO) -> Docstring:
    """Parse the docstring into its components.

    :param text: docstring text to parse
    :param style: docstring style
    :returns: parsed docstring representation
    """
    if style != DocstringStyle.AUTO:
        return _STYLE_MAP[style].parse(text)

    exc: T.Optional[Exception] = None
    rets = []
    for module in _STYLE_MAP.values():
        try:
            ret = module.parse(text)
        except ParseError as ex:
            exc = ex
        else:
            rets.append(ret)

    if not rets:
        raise exc

    return sorted(rets, key=lambda d: len(d.meta), reverse=True)[0]

class OpenAISchema(BaseModel):
    
    @classmethod
    @property
    def openai_schema(cls):
        """
        Return the schema in the format of OpenAI's schema as jsonschema

        Note:
            Its important to add a docstring to describe how to best use this class, it will be included in the description attribute and be part of the prompt.

        Returns:
            model_json_schema (dict): A dictionary in the format of OpenAI's schema as jsonschema
        """
        schema = cls.model_json_schema()
        docstring = parse(cls.__doc__ or "")

        properties = schema.get('properties', {})
        for prop in properties.values():
            prop.pop('title', None)

        for param in docstring.params:
            if (name := param.arg_name) in properties and (
                description := param.description
            ):
                if "description" not in properties[name]:
                    properties[name]["description"] = description

        required = sorted(
            k for k, v in properties.items() if not "default" in v
        )

        if "description" not in schema:
            if docstring.short_description:
                schema["description"] = docstring.short_description
            else:
                schema["description"] = (
                    f"Correctly extracted `{cls.__name__}` with all "
                    f"the required parameters with correct types"
                )

        return {
            "name": schema["title"],
            "description": schema["description"],
            "parameters": {"type": schema["type"], "properties": properties, "required": required},
        }
    


    @classmethod
    def from_response(
        cls,
        completion,
        validation_context=None,
        strict: bool = None,
    ):
        """Execute the function from the response of an openai chat completion

        Parameters:
            completion (openai.ChatCompletion): The response from an openai chat completion
            throw_error (bool): Whether to throw an error if the function call is not detected
            validation_context (dict): The validation context to use for validating the response
            strict (bool): Whether to use strict json parsing

        Returns:
            cls (OpenAISchema): An instance of the class
        """
        message = completion["choices"][0]["message"]

        # detect function call or tool call
        if "tool_call" in message:
            # message.tool_calls
            pass
        elif "function_call" in message:
            assert (
                message["function_call"]["name"] == cls.openai_schema["name"]
            ), "Function name does not match"

            return cls.model_validate_json(
                message["function_call"]["arguments"],
                context=validation_context,
                strict=strict,
            )
        else:
            raise ValueError("Message is not a function call or tool call")
    

