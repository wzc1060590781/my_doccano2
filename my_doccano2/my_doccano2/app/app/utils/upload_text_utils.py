import json
import re

from rest_framework import serializers


def val_text_name(name):
    if not (name.endswith(".txt") or name.endswith(".json")):
        raise serializers.ValidationError('文件格式有误，请上传.txt格式文件，或json格式文件')
    try:
        title = re.match(r"(.*?)\.(.*?)", name).group(1)
    except:
        raise serializers.ValidationError("文件名有误")
    else:
        return title


def get_text_str(text):
    text_str = ""
    for chunk in text.chunks():
        text_str += chunk.decode("utf-8").strip()
    return text_str


def val_text_format(text, text_str):
    if text.name.endswith(".json"):
        try:
            text_dict = json.loads(text_str)
        except:
            raise serializers.ValidationError("文本格式有误")
        # TODO
        text_str = text_dict.get("文书内容", None)
    return text_str