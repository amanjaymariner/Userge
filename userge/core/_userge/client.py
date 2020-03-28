import re
import importlib
from types import ModuleType
from typing import (
    Dict, List, Tuple, Optional, Union, Any, Callable)

from pyrogram import (
    Client, Filters, MessageHandler, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply)
from userge.utils import Config, logging
from userge.plugins import get_all_plugins
from .base import Base
from .message import Message

logging.getLogger("pyrogram").setLevel(logging.WARNING)

PYROFUNC = Callable[[Message], Any]


class Userge(Client, Base):
    """
    Userge: userbot
    """

    __HELP_DICT: Dict[str, Dict[str, str]] = {}
    __IMPORTED: List[ModuleType] = []
    __PLUGINS_PATH = "userge.plugins.{}"

    def __init__(self) -> None:
        self._LOG.info(
            self._MAIN_STRING.format("Setting Userge Configs"))

        super().__init__(Config.HU_STRING_SESSION,
                         api_id=Config.API_ID,
                         api_hash=Config.API_HASH)

    def getLogger(self, name: str) -> logging.Logger:
        """
        This will return new logger object.
        """

        self._LOG.info(
            self._SUB_STRING.format(f"Creating Logger => {name}"))

        return logging.getLogger(name)

    async def get_user_dict(self, user_id: int) -> Dict[str, str]:
        """
        This will return user `Dict` which contains
        `fname`, `lname`, `flname` and `uname`.
        """

        user_obj = await self.get_users(user_id)

        fname = user_obj.first_name.strip() or ''
        lname = user_obj.last_name.strip() or ''
        username = user_obj.username.strip() or ''

        if fname and lname:
            full_name = fname + ' ' + lname

        elif fname or lname:
            full_name = fname or lname

        else:
            full_name = "user"

        return {'fname': fname,
                'lname': lname,
                'flname': full_name,
                'uname': username}

    async def send_message(self,
                           chat_id: Union[int, str],
                           text: str,
                           parse_mode: Union[str, object] = object,
                           disable_web_page_preview: Optional[bool] = None,
                           disable_notification: Optional[bool] = None,
                           reply_to_message_id: Optional[int] = None,
                           schedule_date: Optional[int] = None,
                           reply_markup: Union[InlineKeyboardMarkup,
                                               ReplyKeyboardMarkup,
                                               ReplyKeyboardRemove,
                                               ForceReply] = None) -> Message:
        """
        Send text messages.

        Example:
                @userge.send_message(chat_id=12345, text='test')

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).
            text (``str``):
                Text of the message to be sent.
            parse_mode (``str``, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.
                Pass "markdown" or "md" to enable Markdown-style parsing only.
                Pass "html" to enable HTML-style parsing only.
                Pass None to completely disable style parsing.
            disable_web_page_preview (``bool``, *optional*):
                Disables link previews for links in this message.
            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.
            reply_to_message_id (``int``, *optional*):
                If the message is a reply, ID of the original message.
            schedule_date (``int``, *optional*):
                Date when the message will be automatically sent. Unix time.
            reply_markup (:obj:`InlineKeyboardMarkup` | :obj:`ReplyKeyboardMarkup` | :obj:`ReplyKeyboardRemove` | :obj:`ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.
        Returns:
            :obj:`Message`: On success, the sent text message is returned.
        """

        return Message(self,
                       await super().send_message(chat_id=chat_id,
                                                  text=text,
                                                  parse_mode=parse_mode,
                                                  disable_web_page_preview=disable_web_page_preview,
                                                  disable_notification=disable_notification,
                                                  reply_to_message_id=reply_to_message_id,
                                                  schedule_date=schedule_date,
                                                  reply_markup=reply_markup))

    def on_cmd(self,
               command: str,
               about: str,
               group: int = 0,
               name: str = '',
               trigger: str = '.',
               only_me: bool = True,
               **kwargs) -> Callable[[PYROFUNC], PYROFUNC]:
        """
        Decorator for handling messages.

        Example:
                @userge.on_cmd('test', about='for testing')

        Parameters:
            command (``str``):
                command name to execute (without trigger!).
            about (``str``):
                help string for command.
            group (``int``, *optional*):
                The group identifier, defaults to 0.
            name (``str``, *optional*):
                name for command.
            trigger (``str``, *optional*):
                trigger to start command, defaults to '.'.
            only_me (``bool``, *optional*):
                If ``True``, Filters.me = True,  defaults to True.
            kwargs:
                prefix (``str``, *optional*):
                    set prefix for flags, defaults to '-'.
                del_pre (``bool``, *optional*):
                    If ``True``, flags returns without prefix,  defaults to False.
        """

        pattern = f"^\\{trigger}{command.lstrip('^')}" if trigger else f"^{command.lstrip('^')}"

        if [i for i in '^()[]+*.\\|?:$' if i in command]:
            match = re.match("(\\w[\\w_]*)", command)
            cname = match.groups()[0] if match else ''
            cname = name or cname
            cname = trigger + cname if cname else ''

        else:
            cname = trigger + command
            pattern += r"(?:\s([\S\s]+))?$"

        kwargs.update({'cname': cname, 'chelp': about})

        filters_ = Filters.regex(pattern=pattern) & Filters.me if only_me \
            else Filters.regex(pattern=pattern)

        return self.__build_decorator(log=f"On {pattern}",
                                      filters=filters_,
                                      group=group,
                                      **kwargs)

    def on_new_member(self,
                      welcome_chats: Filters.chat,
                      group: int = 0) -> Callable[[PYROFUNC], PYROFUNC]:
        """
        Decorator for handling new members.
        """

        return self.__build_decorator(log=f"On New Member in {welcome_chats}",
                                      filters=Filters.new_chat_members & welcome_chats,
                                      group=group)

    def on_left_member(self,
                       leaving_chats: Filters.chat,
                       group: int = 0) -> Callable[[PYROFUNC], PYROFUNC]:
        """
        Decorator for handling left members.
        """

        return self.__build_decorator(log=f"On Left Member in {leaving_chats}",
                                      filters=Filters.left_chat_member & leaving_chats,
                                      group=group)

    def get_help(self,
                 key: str = '',
                 all_cmds: bool = False) -> Tuple[Union[str, List[str]], Union[bool, str]]:
        """
        This will return help string for specific key
        or all modules or commands as `List`.
        """

        if not key and not all_cmds:
            return sorted(list(self.__HELP_DICT)), True         # names of all modules

        if not key.startswith('.') and key in self.__HELP_DICT and \
            (len(self.__HELP_DICT[key]) > 1 or list(self.__HELP_DICT[key])[0] != key):
            return sorted(list(self.__HELP_DICT[key])), False   # all commands for that module

        dict_ = {x: y for _, i in self.__HELP_DICT.items() for x, y in i.items()}

        if all_cmds:
            return sorted(list(dict_)), False                   # all commands for .s

        key = key.lstrip('.')
        key_ = '.' + key

        if key in dict_:
            return dict_[key], key      # help text and command for given command

        elif key_ in dict_:
            return dict_[key_], key_    # help text and command for modified command

        else:
            return '', False            # if unknown

    def __add_help(self,
                   module: str,
                   cname: str = '',
                   chelp: str = '',
                   **kwargs) -> None:
        if cname:
            self._LOG.info(
                self._SUB_STRING.format(f"Updating Help Dict => [ {cname} : {chelp} ]"))

            mname = module.split('.')[-1]

            if mname in self.__HELP_DICT:
                self.__HELP_DICT[mname].update({cname: chelp})

            else:
                self.__HELP_DICT.update({mname: {cname: chelp}})

    def __build_decorator(self,
                          log: str,
                          filters: Filters,
                          group: int,
                          **kwargs) -> Callable[[PYROFUNC], PYROFUNC]:

        def __decorator(func: PYROFUNC) -> PYROFUNC:

            async def __template(_: Client,
                                 message: Message) -> None:
                await func(Message(self, message, **kwargs))

            self._LOG.info(
                self._SUB_STRING.format(f"Loading => [ async def {func.__name__}(message) ] " + \
                                        f"from {func.__module__} `{log}`"))

            self.__add_help(func.__module__, **kwargs)

            self.add_handler(MessageHandler(__template, filters), group)

            return func

        return __decorator

    def load_plugin(self, name: str) -> None:
        """
        Load plugin to Userge.
        """

        self._LOG.info(
            self._MAIN_STRING.format(f"Importing {name}"))

        self.__IMPORTED.append(
            importlib.import_module(self.__PLUGINS_PATH.format(name)))

        self._LOG.info(
            self._MAIN_STRING.format(
                f"Imported {self.__IMPORTED[-1].__name__} Plugin Successfully"))

    def load_plugins(self) -> None:
        """
        Load all Plugins.
        """

        self.__IMPORTED.clear()

        self._LOG.info(
            self._MAIN_STRING.format("Importing All Plugins"))

        for name in get_all_plugins():
            try:
                self.load_plugin(name)

            except ImportError as i_e:
                self._LOG.error(i_e)

        self._LOG.info(
            self._MAIN_STRING.format(
                f"Imported ({len(self.__IMPORTED)}) Plugins => " + \
                str([i.__name__ for i in self.__IMPORTED])))

    async def reload_plugins(self) -> int:
        """
        Reload all Plugins.
        """

        self.__HELP_DICT.clear()
        reloaded: List[str] = []

        self._LOG.info(
            self._MAIN_STRING.format("Reloading All Plugins"))

        for imported in self.__IMPORTED:
            try:
                reloaded_ = importlib.reload(imported)

            except ImportError as i_e:
                self._LOG.error(i_e)

            else:
                reloaded.append(reloaded_.__name__)

        self._LOG.info(
            self._MAIN_STRING.format(
                f"Reloaded {len(reloaded)} Plugins => {reloaded}"))

        return len(reloaded)

    async def restart(self) -> None:
        """
        Restart the Userge.
        """

        self._LOG.info(
            self._MAIN_STRING.format("Restarting Userge"))

        await self.stop()
        await self.reload_plugins()
        await self.start()

        self._LOG.info(
            self._MAIN_STRING.format("Restarted Userge"))

    def begin(self) -> None:
        """
        This will start the Userge.
        """

        self._LOG.info(
            self._MAIN_STRING.format("Starting Userge"))

        self._NST_ASYNC.apply()
        self.run()

        self._LOG.info(
            self._MAIN_STRING.format("Exiting Userge"))
