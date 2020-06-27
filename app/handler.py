from flask import jsonify
from error_code import ErrorCode


def success(data={}, message="OK"):
    data['rtn'] = ErrorCode.SUCCESS
    data['message'] = message
    return jsonify(data)


def failed(rtn, data={}, message="OK"):
    data['rtn'] = rtn
    data['message'] = message
    return jsonify(data)
