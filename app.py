import json
import http.client
from flask import Flask, request
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def webhook():
   VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
    response = None
    if request.method == 'GET':
        queryParams = request.args
        if queryParams:
            mode = queryParams.get("hub.mode")
            if mode == "subscribe":
                verifyToken = queryParams.get("hub.verify_token")
                if verifyToken == VERIFY_TOKEN:
                    challenge = queryParams.get("hub.challenge")
                    response = {
                        "statusCode": 200,
                        "body": str(challenge),
                        "isBase64Encoded": False
                    }
                else:
                    responseBody = "Error, wrong validation token"
                    response = {
                        "statusCode": 403,
                        "body": json.dumps(responseBody),
                        "isBase64Encoded": False
                    }
            else:
                responseBody = "Error, wrong mode"
                response = {
                    "statusCode": 403,
                    "body": json.dumps(responseBody),
                    "isBase64Encoded": False
                }
        else:
            responseBody = "Error, no query parameters"
            response = {
                "statusCode": 403,
                "body": json.dumps(responseBody),
                "isBase64Encoded": False
            }
    elif request.method == 'POST':
        body = request.get_json()
        entries = body.get("entry")
        for entry in entries:
            for change in entry.get("changes"):
                value = change.get("value")
                if value is not None:
                    phone_number_id = value.get("metadata", {}).get("phone_number_id")
                    if value.get("messages") is not None:
                        for message in value.get("messages"):
                            if message.get("type") == "text":
                                from_number = message.get("from")
                                message_body = message.get("text", {}).get("body")
                                reply_message = "Ack from Flask: " + message_body
                                send_reply(phone_number_id, WHATSAPP_TOKEN, from_number, reply_message)
                                responseBody = "Done"
                                response = {
                                    "statusCode": 200,
                                    "body": json.dumps(responseBody),
                                    "isBase64Encoded": False
                                }
    else:
        responseBody = "Unsupported method"
        response = {
            "statusCode": 403,
            "body": json.dumps(responseBody),
            "isBase64Encoded": False
        }

    return response

def send_reply(phone_number_id, whatsapp_token, to, reply_message):
    json_data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": reply_message}
    }
    data = json.dumps(json_data)
    path = f"/v17.0/{phone_number_id}/messages?access_token={whatsapp_token}"
    headers = {"Content-Type": "application/json"}

    conn = http.client.HTTPSConnection("graph.facebook.com")
    conn.request("POST", path, body=data, headers=headers)
    response = conn.getresponse()
    conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0')
