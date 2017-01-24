# -*- coding: utf-8 -*-
__author__ = 'Rico'

from twx.botapi import TelegramBot
from app.update_handler import get_updates
from app.message_types import MessageTypes


class Main(object):
    bot = TelegramBot(BOT_TOKEN)
    offset = 0
    left_msgs = [[]] * 0
    chatting_users = [[]] * 0
    searching_users = []
    DEV_ID = 24421134


    def update_loop(self):
        while True:
            update_list = get_updates(self.offset, self.bot)
            if update_list:
                for line in update_list:
                    self.left_msgs.append(line)
                self.analyze_messages()

    def analyze_messages(self):
        bot_sends = "\U0001F916 *Bot:* "
        stranger_sends = "\U0001F464 *Stranger:* " 
        try:
            while len(self.left_msgs) > 0:
                update = self.left_msgs[0]
                print(update)  # TODO just for debugging
                text_orig = ""
                text = ""
                message_type = 0

                #TODO auto remove chats if no message for a certain time?

                if isinstance(update.message.text, str):
                    # If message is text
                    text_orig = str(update.message.text)
                    text = text_orig.lower()
                    message_type = MessageTypes.TYPE_TEXT

                elif update.message.sticker is not None:
                    print("Message is a sticker")
                    print(str(update.message.sticker.file_id))
                    message_type = MessageTypes.TYPE_STICKER

                elif update.message.photo is not None:
                    print("Message is a photo")
                    print(str(update.message.photo))
                else:
                    # Setting type to "text", so that the partner get's notified of it
                    print("* Someone sent some unsupported media, sorry. *")
                    message_type = MessageTypes.TYPE_TEXT
                    text_orig = bot_sends + "*Your chat partner sent some unsupported media, sorry. *"
                    text = bot_sends + "*Your chat partner sent some unsupported media, sorry. *"

                user_id = update.message.sender.id
                # first_name = update.message.sender.first_name
                # update_id = update.update_id

                # If message is a command
                if text.startswith("/"):
                    command = str(text[1:])
                    command_orig = str(text_orig[1:]) # just in case the original text is needed

                    if (command == "start") and (user_id not in self.searching_users) and (self.user_already_chatting(user_id) == -1):
                        # search for another "searching" user in searching_users list
                        if len(self.searching_users) > 0:
                            # delete the other searching users from the list of searching_users
                            print("Another user is searching now. There are 2 users. Matching them now!")
                            partner_id = self.searching_users[0]
                            del self.searching_users[0]

                            # add both users to the list of chatting users with the user_id of the other user.
                            self.chatting_users.append([user_id, partner_id])
                            self.chatting_users.append([partner_id, user_id])

                            self.bot.send_message(user_id, bot_sends + "You are connected to a stranger. Have fun and be nice!").wait()
                            self.bot.send_message(partner_id, bot_sends + "You are connected to a stranger. Have fun and be nice!").wait()
                        else:
                            # if no user is searching, add him to the list of searching users.
                            # TODO later when you can search for specific gender, this condition must be changed
                            self.searching_users.append(user_id)
                            self.bot.send_message(user_id, bot_sends + "Added you to the searching users!").wait()

                    elif user_id in self.searching_users:
                        self.bot.send_message(user_id, bot_sends + "You are already searching. Please wait!").wait()

                    if (command == "stop") and ((user_id in self.searching_users) or (self.user_already_chatting(user_id) >= 0)):

                        if user_id in self.searching_users:
                            # remove user from searching users
                            index = self.user_already_searching(user_id)
                            del self.searching_users[index]

                        elif self.user_already_chatting(user_id) >= 0:
                            # remove both users from chatting users
                            partner_id = self.get_partner_id(user_id)

                            index = self.user_already_chatting(user_id)
                            del self.chatting_users[index]

                            partner_index = self.user_already_chatting(partner_id)
                            del self.chatting_users[partner_index]

                            # send message that other user left the chat
                            self.bot.send_message(partner_id, bot_sends + "Your partner left the chat").wait()
                            self.bot.send_message(user_id, bot_sends + "You left the chat!").wait()

                # if user is in a chat
                elif (user_id not in self.searching_users) and (self.user_already_chatting(user_id) >= 0):
                    # send message directly to the other chat
                    partner_id = self.get_partner_id(user_id)
                    # additional check, that there is indeed a partner.
                    if partner_id != -1:
                        if message_type == MessageTypes.TYPE_TEXT:
                            message = stranger_sends + text_orig
                            self.bot.send_message(partner_id, message).wait()
                        elif message_type == MessageTypes.TYPE_STICKER:
                            self.bot.send_sticker(partner_id, update.message.sticker.file_id).wait()
                    else:
                        print("Something went wrong! There is no partner in the list, while there should be!")

                # happens when user is NEITER searching, nor in a chat with a stranger
                else:
                    print("Case not handeled yet!")

                self.set_message_answered()
        except Exception as expt:
            print(expt)
            self.set_message_answered()
            self.bot.send_message(self.DEV_ID, "Bot Error:\n\nMessages couldn't be analyzed!")
            # traceback.print_exc()

    def get_partner_id(self, user_id):
        if len(self.chatting_users) > 0:
            for pair in self.chatting_users:
                if pair[0] == user_id:
                    return int(pair[1])

        return -1

    # checks if user is already chatting with someone
    def user_already_chatting(self, user_id):
        counter = 0
        if len(self.chatting_users) > 0:
            for pair in self.chatting_users:
                if pair[0] == user_id:
                    return counter
                counter += 1

        return -1

    def user_already_searching(self, user_id):
        counter = 0
        if len(self.searching_users) > 0:
            for user in self.searching_users:
                if user == user_id:
                    return counter
                counter += 1

        return -1

    def set_message_answered(self):
        if len(self.left_msgs) > 0:
            update = self.left_msgs[0]
            self.offset = update.update_id
            self.left_msgs.pop(0)
            print("Un-Answered Messages: " + str(len(self.left_msgs)))

    def __init__(self):
        print("Bot started!")


main = Main()
main.update_loop()
