# SCP-079-LONG - Control super long messages
# Copyright (C) 2019 SCP-079 <https://scp-079.org>
#
# This file is part of SCP-079-LONG.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import re
from typing import Union

from telegram import Message
from telegram.ext import BaseFilter

from .. import glovar
from .etc import get_now, get_text
from .file import save
from .ids import init_group_id

# Enable logging
logger = logging.getLogger(__name__)


class FilterClassC(BaseFilter):
    # Check if the message is Class C object
    def filter(self, message: Message):
        try:
            if message.from_user:
                uid = message.from_user.id
                gid = message.chat.id
                if init_group_id(gid):
                    if uid in glovar.admin_ids.get(gid, set()) or uid in glovar.bot_ids:
                        return True
        except Exception as e:
            logger.warning(f"Is class c error: {e}", exc_info=True)

        return False


class FilterClassD(BaseFilter):
    # Check if the message is Class D object
    def filter(self, message: Message):
        try:
            if message.from_user:
                uid = message.from_user.id
                if uid in glovar.bad_ids["users"]:
                    return True

            if message.forward_from:
                fid = message.forward_from.id
                if fid in glovar.bad_ids["users"]:
                    return True

            if message.forward_from_chat:
                cid = message.forward_from_chat.id
                if cid in glovar.bad_ids["channels"]:
                    return True
        except Exception as e:
            logger.warning(f"FilterClassD error: {e}", exc_info=True)

        return False


class FilterClassE(BaseFilter):
    # Check if the message is Class E object
    def filter(self, message: Message):
        try:
            if message.forward_from_chat:
                cid = message.forward_from_chat.id
                if cid in glovar.except_ids["channels"]:
                    return True
        except Exception as e:
            logger.warning(f"FilterClassE error: {e}", exc_info=True)

        return False


class FilterDeclaredMessage(BaseFilter):
    # Check if the message is declared by other bots
    def filter(self, message: Message):
        try:
            if message.chat:
                gid = message.chat.id
                mid = message.message_id
                if mid in glovar.declared_message_ids.get(gid, set()):
                    return True
        except Exception as e:
            logger.warning(f"FilterDeclaredMessage error: {e}", exc_info=True)

        return False


class FilterExchangeChannel(BaseFilter):
    # Check if the message is sent from the exchange channel
    def filter(self, message: Message):
        try:
            if message.chat:
                cid = message.chat.id
                if glovar.should_hide:
                    if cid == glovar.hide_channel_id:
                        return True
                elif cid == glovar.exchange_channel_id:
                    return True
        except Exception as e:
            logger.warning(f"FilterExchangeChannel error: {e}", exc_info=True)

        return False


class FilterHideChannel(BaseFilter):
    # Check if the message is sent from the hide channel
    def filter(self, message: Message):
        try:
            if message.chat:
                cid = message.chat.id
                if cid == glovar.hide_channel_id:
                    return True
        except Exception as e:
            logger.warning(f"FilterHideChannel error: {e}", exc_info=True)

        return False


class FilterNewGroup(BaseFilter):
    # Check if the bot joined a new group
    def filter(self, message: Message):
        try:
            if message.new_chat_members:
                new_users = message.new_chat_members
                if new_users:
                    for user in new_users:
                        if user.id == glovar.long_id:
                            return True
            elif message.group_chat_created or message.supergroup_chat_created:
                return True
        except Exception as e:
            logger.warning(f"FilterNewGroup error: {e}", exc_info=True)

        return False


class FilterTestGroup(BaseFilter):
    # Check if the message is sent from the test group
    def filter(self, message: Message):
        try:
            if message.chat:
                cid = message.chat.id
                if cid == glovar.test_group_id:
                    return True
        except Exception as e:
            logger.warning(f"FilterTestGroup error: {e}", exc_info=True)

        return False


class_c = FilterClassC()

class_d = FilterClassD()

class_e = FilterClassE()

declared_message = FilterDeclaredMessage()

exchange_channel = FilterExchangeChannel()

hide_channel = FilterHideChannel()

new_group = FilterNewGroup()

test_group = FilterTestGroup()


def is_class_c(_, message: Message) -> bool:
    # Check if the message is Class C object
    try:
        if message.from_user:
            uid = message.from_user.id
            gid = message.chat.id
            if init_group_id(gid):
                if uid in glovar.admin_ids.get(gid, set()) or uid in glovar.bot_ids or message.from_user.is_self:
                    return True
    except Exception as e:
        logger.warning(f"Is class c error: {e}", exc_info=True)

    return False


def is_class_d(_, message: Message) -> bool:
    # Check if the message is Class D object
    try:
        if message.from_user:
            uid = message.from_user.id
            if uid in glovar.bad_ids["users"]:
                return True

        if message.forward_from:
            fid = message.forward_from.id
            if fid in glovar.bad_ids["users"]:
                return True

        if message.forward_from_chat:
            cid = message.forward_from_chat.id
            if cid in glovar.bad_ids["channels"]:
                return True
    except Exception as e:
        logger.warning(f"Is class d error: {e}", exc_info=True)

    return False


def is_detected_user(message: Message) -> bool:
    # Check if the message is sent by a detected user
    try:
        if message.from_user:
            gid = message.chat.id
            uid = message.from_user.id
            return is_detected_user_id(gid, uid)
    except Exception as e:
        logger.warning(f"Is detected user error: {e}", exc_info=True)

    return False


def is_detected_user_id(gid: int, uid: int) -> bool:
    # Check if the user_id is detected in the group
    try:
        user = glovar.user_ids.get(uid, {})
        if user:
            status = user["detected"].get(gid, 0)
            now = get_now()
            if now - status < glovar.punish_time:
                return True
    except Exception as e:
        logger.warning(f"Is detected user id error: {e}", exc_info=True)

    return False


def is_high_score_user(message: Message) -> Union[bool, float]:
    # Check if the message is sent by a high score user
    try:
        if message.from_user:
            uid = message.from_user.id
            user = glovar.user_ids.get(uid, {})
            if user:
                score = 0.0
                try:
                    user = glovar.user_ids.get(uid, {})
                    if user:
                        score = (user["score"].get("captcha", 0.0)
                                 + user["score"].get("clean", 0.0)
                                 + user["score"].get("lang", 0.0)
                                 + user["score"].get("long", 0.0)
                                 + user["score"].get("noflood", 0.0)
                                 + user["score"].get("noporn", 0.0)
                                 + user["score"].get("nospam", 0.0)
                                 + user["score"].get("recheck", 0.0)
                                 + user["score"].get("warn", 0.0))
                except Exception as e:
                    logger.warning(f"Get score error: {e}", exc_info=True)

                if score >= 3.0:
                    return score
    except Exception as e:
        logger.warning(f"Is high score user error: {e}", exc_info=True)

    return False


def is_long_text(message: Message) -> bool:
    # Check if the text is super long
    if glovar.locks["message"].acquire():
        try:
            text = get_text(message)
            if text:
                if is_detected_user(message):
                    return True

                gid = message.chat.id
                length = len(text.encode())
                if length >= glovar.configs[gid]["limit"]:
                    return True
        except Exception as e:
            logger.warning(f"Is long text error: {e}", exc_info=True)
        finally:
            glovar.locks["message"].release()

    return False


def is_regex_text(word_type: str, text: str) -> bool:
    # Check if the text hit the regex rules
    result = False
    try:
        if text:
            text = text.replace("\n", " ")
            text = re.sub(r"\s\s", " ", text)
            text = re.sub(r"\s\s", " ", text)
        else:
            return False

        for word in list(eval(f"glovar.{word_type}_words")):
            if re.search(word, text, re.I | re.S | re.M):
                result = True
            else:
                text = re.sub(r"\s", "", text)
                if re.search(word, text, re.I | re.S | re.M):
                    result = True

            if result:
                count = eval(f"glovar.{word_type}_words").get(word, 0)
                count += 1
                eval(f"glovar.{word_type}_words")[word] = count
                save(f"{word_type}_words")
                return result
    except Exception as e:
        logger.warning(f"Is regex text error: {e}", exc_info=True)

    return False


def is_watch_user(message: Message, the_type: str) -> bool:
    # Check if the message is sent by a watch user
    try:
        if message.from_user:
            uid = message.from_user.id
            now = get_now()
            until = glovar.watch_ids[the_type].get(uid, 0)
            if now < until:
                return True
    except Exception as e:
        logger.warning(f"Is watch user error: {e}", exc_info=True)

    return False
