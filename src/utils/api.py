#! /usr/bin/env python3.8
import os
import logging
from datetime import datetime, timedelta, time
from typing import List, Dict

import requests

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")

# const
TENANT_ACCESS_TOKEN_URI = "/open-apis/auth/v3/tenant_access_token/internal"
MESSAGE_URI = "/open-apis/im/v1/messages"
BATCH_MESSAGE_URI = "/open-apis/message/v4/batch_send"



class MessageApiClient(object):
    def __init__(self, app_id, app_secret, lark_host, logger):
        self._tenant_access_refresh_time = None
        self._app_id = app_id
        self._app_secret = app_secret
        self._lark_host = lark_host
        self._tenant_access_token = ""
        self.logger = logger

    def get_department_users(self, department_id: str) -> List[str]:
        self._authorize_tenant_access_token()
        url = f"{self._lark_host}/open-apis/contact/v3/users/find_by_department?department_id={department_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        response = requests.get(
            url,
            headers=headers
        )
        data = response.json().get("data", {}).get("items", [])
        department_user_ids = [d["open_id"] for d in data]
        filter_ids = os.getenv("FILTER_IDS")
        if filter_ids:
            filter_ids = filter_ids.split(",")
            department_user_ids = [d for d in department_user_ids if d not in filter_ids]
        self.logger.error(f"Department User IDs: {department_user_ids}")
        self.logger.error(f"Filter IDs: {filter_ids}")

        return department_user_ids

    def batch_send_card(self, open_ids: List[str], card_content: Dict[str, str]):
        self._authorize_tenant_access_token()
        url = f"{self._lark_host}{BATCH_MESSAGE_URI}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        req_body = {
            "open_ids": open_ids,
            "msg_type": "interactive",
            "content": {
                "share_chat_id": datetime.now().strftime("%Y%m%d%H%M%S"),
            },
            "card": card_content
        }
        resp = requests.post(
            url,
            headers=headers,
            json=req_body
        )
        return MessageApiClient._check_error_response(resp)


    def get_user_info(self, open_id):
        self._authorize_tenant_access_token()
        url = f"{self._lark_host}/open-apis/contact/v3/users/{open_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        response = requests.get(
            url,
            headers=headers
        )
        data = response.json().get("data", {}).get("user", {})
        return data

    def remove_member(self, open_id):
        self._authorize_tenant_access_token()
        url = f"{self._lark_host}/open-apis/contact/v3/users/{open_id}/leave"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        resp = requests.post(
            url,
            headers=headers
        )
        return MessageApiClient._check_error_response(resp)

    @property
    def tenant_access_token(self):
        return self._tenant_access_token

    def send_text_with_open_id(self, open_id, content):
        self.send("open_id", open_id, "text", content)

    def make_card(self, receive_id_type, receive_id, msg_type, content):
        self._authorize_tenant_access_token()
        url = "{}{}?receive_id_type={}".format(
            self._lark_host, MESSAGE_URI, receive_id_type
        )
        self.logger.error(f"{url=}")
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        self.logger.error(f"{headers=}")
        req_body = {
            "receive_id": receive_id,
            "content": content,
            "msg_type": msg_type,
        }
        if msg_type == "interactive":
            req_body["card"] = {
                "config": {
                    "update_multi": True
                }
            }
        self.logger.error(f"{req_body=}")
        return url, headers, req_body

    def send(self, receive_id_type, receive_id, msg_type, content):
        self._authorize_tenant_access_token()
        url = "{}{}?receive_id_type={}".format(
            self._lark_host, MESSAGE_URI, receive_id_type
        )
        self.logger.error(f"{url=}")
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        self.logger.error(f"{headers=}")
        req_body = {
            "receive_id": receive_id,
            "content": content,
            "msg_type": msg_type,
        }
        if msg_type == "interactive":
            req_body["card"] = {
                "config": {
                    "update_multi": True
                }
            }
        self.logger.error(f"{req_body=}")
        resp = requests.post(url=url, headers=headers, json=req_body)
        return MessageApiClient._check_error_response(resp)

    def buzz_message(self, message_id, user_ids):
        self._authorize_tenant_access_token()
        url = f"{self._lark_host}{MESSAGE_URI}/{message_id}/urgent_app?user_id_type=open_id"
        self.logger.error(f"{url=}")
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        self.logger.error(f"{headers=}")
        req_body = {
            "user_id_list": user_ids
        }
        self.logger.error(f"{req_body=}")

        resp = requests.patch(url=url, headers=headers, json=req_body)
        MessageApiClient._check_error_response(resp)


    def _authorize_tenant_access_token(self):
        if (self._tenant_access_token
                and self._tenant_access_refresh_time is not None
                and datetime.now() < self._tenant_access_refresh_time):
            self.logger.error(f"(Not Expired Yet) tenant_access_token: {self._tenant_access_token}")
            return
        url = "{}{}".format(self._lark_host, TENANT_ACCESS_TOKEN_URI)
        req_body = {"app_id": self._app_id, "app_secret": self._app_secret}
        response = requests.post(url, req_body)
        MessageApiClient._check_error_response(response)
        self._tenant_access_token = response.json().get("tenant_access_token")
        self._tenant_access_token_expires = response.json().get("expire")
        self._tenant_access_refresh_time = datetime.now() + timedelta(seconds=self._tenant_access_token_expires - 5)
        self.logger.error(f"tenant_access_token: {self._tenant_access_token}")

    def update_message(self, message_id, content):
        self._authorize_tenant_access_token()
        url = f"{self._lark_host}{MESSAGE_URI}/{message_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        req_body = {
            "content": content
        }
        resp = requests.patch(url, headers=headers, json=req_body)
        return MessageApiClient._check_error_response(resp)

    @staticmethod
    def _check_error_response(resp):
        # check if the response contains error information
        if resp.status_code != 200:
            resp.raise_for_status()
        response_dict = resp.json()
        code = response_dict.get("code", -1)
        if code != 0:
            logging.error(response_dict)
            raise LarkException(code=code, msg=response_dict.get("msg"))
        return response_dict


class LarkException(Exception):
    def __init__(self, code=0, msg=None):
        self.code = code
        self.msg = msg

    def __str__(self) -> str:
        return "{}:{}".format(self.code, self.msg)

    __repr__ = __str__
