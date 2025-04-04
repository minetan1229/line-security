from CHRLINE import CHRLINE
from CHRLINE.hooks import HooksTracer
import json

cl = CHRLINE("mail", "password", useThrift=True, device="IOSIPAD", os_version="15.3.1")
#ぜったいにだめこれ入れるとloginまではうまくいくけどbanくらう　version="13.21.3", os_name="iOS", os_ver="17"
#os_version入れないとbanされるように仕様変更されたかも
bot_mid = cl.profile.mid  
hooks = HooksTracer(cl)

WHITELIST = {
    bot_mid, 
    'abcdefghijkli1234567890abcdefghijklmn',
}



tracer = HooksTracer(
    cl, 
    prefixes=["/"],
)

class EventHook:

    @tracer.Event
    def onReady():
        print('Ready!')

    @tracer.Event
    def onInitializePushConn():
        print('onInitializePushConn!')

     

class OpHook(object):

    @tracer.Operation(26)
    def recvMessage(self, op, cl):
        msg = op.message

        if msg.contentType == 13:
            contact_mid = msg.contentMetadata["mid"]
            cl.replyMessage(msg, f"送信された連絡先のMID: {contact_mid}")

        self.trace(msg, self.HooksType["Content"], cl)
        print(f"📩 メッセージ受信: (from {msg})")


    @tracer.Operation(124)
    def on_invite_event(self, data, cl):
        """自動参加 """
        try:
            group_id = data.param1  
            invitee_mid = data.param3  
            inviter_mid = data.param2

            if bot_mid == invitee_mid:
                if inviter_mid in WHITELIST:
                    print(f"📥 Invited to group {group_id}. Joining...")
                    cl.acceptChatInvitation(group_id)

                    welcome_message = "I'm Minetan protect bot 😊 I will protect this group. If there is an error with this bot, please let Minetan know. Try typing /help"
                    cl.sendMessage(group_id, welcome_message)
                    print(f"✅ Joined {group_id} and sent welcome message.")
        except Exception as e:
            print(f"❌ Error in on_invite_event: {e}")


    @tracer.Operation(133)
    #けりwhitelistuserは自動招待
    def on_kick_event(self, data, cl):
        try:
            print(f"📥 Received event data: {data}")

            group_id = data.param1  
            kicked_mid = data.param3 
            kicker_mid = data.param2

            print(f"⚠️ User {kicked_mid} was removed from group {group_id} by {kicker_mid}")

            if not kicker_mid in WHITELIST:
                try:
                    cl.deleteOtherFromChat(group_id, kicker_mid)
                    print(f"✅ Removed user {kicker_mid} from group {group_id}")
                except Exception as e:
                    return

            if kicked_mid in WHITELIST:

                try:
                    cl.inviteIntoChat(group_id, [kicked_mid])
                except Exception as e:
                    try:
                        group_info = cl.getChats([group_id])
                    
                        if hasattr(group_info, "chats") and group_info.chats:
                            chat_data = group_info.chats[0]
                            if hasattr(chat_data, "extra") and hasattr(chat_data.extra, "groupExtra"):
                                members = list(chat_data.extra.groupExtra.memberMids.keys())
                            else:
                                members = []
                        else:
                            members = []
                    
                        if members:
                            key_data = cl.generateSharedSecret(len(members))
                            cl.registerE2EEGroupKey(
                                chatMid=group_id,
                                members=members,
                                keyIds=[key_data.keyId],
                                encryptedSharedKeys=[key_data.encryptedKey]
                            )
                            print("✅ New e2eekey registered successfully.")
                            cl.inviteIntoChat(group_id, [kicked_mid])
                        else:
                            return
                    except Exception as e:
                        return


                try:
                    cl.inviteIntoChat(group_id, [kicked_mid])
                except Exception as e:
                    return


        except Exception as e:
            print(f"❌ Error in on_kick_event: {e}")

class ContentHook(object):

    @tracer.Content(0)
    def TextMessage(self, msg, cl):
        text = msg.text
        self.trace(msg, self.HooksType['Command'], cl)

class NormalCmd(object):

    @tracer.Command(ignoreCase=True)
    def help(self, msg, cl):
        '''helpcommand'''
        help_text = """
📜 コマンド一覧:
・/help → コマンドの説明
・/hi → hi!と返信
・/minetan → minetanと返信
・/mid → 自分のMIDを表示
・/gid → 現在のグループIDを表示
・/dis → 自分のディスプレイネームを表示
・/yin → 自分のMIDとディスプレイネームを表示
・/men → メンション付きの返信
        """
        cl.replyMessage(msg, help_text)


    @tracer.Command(ignoreCase=True)
    def hi(self, msg, cl):
        '''hi'''
        cl.replyMessage(msg, "hi!")

    @tracer.Command(ignoreCase=True)
    def minetan(self, msg, cl):
        '''minetan'''
        cl.replyMessage(msg, "minetan")
    
    @tracer.Command(ignoreCase=True)
    def mid(self, msg, cl):
        '''mid'''
        cl.replyMessage(msg, f"Your MID: {msg._from}")

    @tracer.Command(ignoreCase=True)
    def gid(self, msg, cl):
        '''gid'''
        cl.replyMessage(msg, f"This Group ID: {msg.to}")

    @tracer.Command(ignoreCase=True)
    def dis(self, msg, cl):
        '''dsnディスプレイネーム'''
        contact = cl.getContact(msg._from)  
        display_name = contact.displayName
        cl.replyMessage(msg, f"Your displayname:{display_name}")


    @tracer.Command(ignoreCase=True)
    def yin(self, msg, cl):
        '''yinユーザid,ディスプレイネーム'''
        contact = cl.getContact(msg._from)  
        display_name = contact.displayName
        cl.replyMessage(msg, f"Your MID: {msg._from}\n\n Your displayname:\n{display_name}")

    @tracer.Command(ignoreCase=True)
    def test(self, msg, cl):
        '''test(sendmessage)個人チャット'''
        contact = cl.getContact(msg._from)  
        display_name = contact.displayName  
        cl.sendMessage(msg._from, f"Your Display Name: {display_name}",contentType=0)

    @tracer.Command(ignoreCase=True)
    def men(self, msg, cl):
        '''メンション'''
        mention = [{"S": "0", "E": str(len(msg._from)), "M": msg._from}]
        cl.replyMessage(msg, f"@{msg._from} メンション付きの返信です", contentMetadata={"MENTION": json.dumps({"MENTIONEES": mention})})


tracer.run()
