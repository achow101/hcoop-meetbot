# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=ungrouped-imports,disable=unused-argument,broad-except,too-many-ancestors,invalid-name:

"""
Implement the HcoopMeetbot plugin in terms of Limnoria functionality.
"""

# This is a very thin implementation.  Most business logic lives in
# the hcoopmeetbotlogic package where it can be unit-tested outside
# of supybot-test, fully type-checked with MyPy, etc.

import importlib

import supybot.ircmsgs as ircmsgs
from supybot import callbacks, world
from supybot.commands import optional, wrap

from hcoopmeetbotlogic import handler, interface

# this messes up unit test stubbing and patching
if not world.testing:
    handler = importlib.reload(handler)
    interface = importlib.reload(interface)


def _context(plugin, irc, msg) -> interface.Context:
    """Create context for a command or message."""
    channel = msg.args[0]
    return interface.Context(
        logger=plugin.log,
        set_topic=lambda topic: irc.sendMsg(ircmsgs.topic(channel, topic)),
        send_reply=irc.reply if hasattr(irc, "reply") and callable(irc.reply) else lambda x: None,
        send_message=lambda message: irc.sendMsg(ircmsgs.privmsg(channel, message)),
    )


class HcoopMeetbot(callbacks.Plugin):
    """Helps run IRC meetings."""

    def doPrivmsg(self, irc, msg):
        """Capture all messages from supybot."""
        context = _context(self, irc, msg)
        message = interface.Message(
            nick=msg.nick,
            channel=msg.args[0],
            network=irc.msg.tags["receivedOn"],
            payload=msg.args[1],
            topic=irc.state.channels[msg.args[0]].topic,
            channel_nicks=["%s" % n for n in irc.state.channels[msg.args[0]].users],
        )
        handler.irc_message(context=context, message=message)

    def outFilter(self, irc, msg):
        """Log outgoing messages from supybot."""
        try:
            if msg.command in ("PRIVMSG",):
                context = _context(self, irc, msg)
                message = interface.Message(nick=irc.nick, channel=msg.args[0], network=irc.network, payload=msg.args[1])
                handler.outbound_message(context=context, message=message)
        except Exception:
            # Per original MeetBot, catch errors to prevent all output from being clobbered
            self.log.exception("Discarded error in outFilter")
        return msg

    def listmeetings(self, irc, msg, args):
        """List all currently-active meetings."""
        context = _context(self, irc, msg)
        handler.listmeetings(context=context)

    listmeetings = wrap(listmeetings, ["admin"])

    def savemeetings(self, irc, msg, args):
        """Save all currently active meetings"""
        context = _context(self, irc, msg)
        handler.savemeetings(context=context)

    savemeetings = wrap(savemeetings, ["admin"])

    def addchair(self, irc, msg, args, channel, nick):
        """Add a nickname as a chair to the meeting in this channel: addchair <nick>."""
        context = _context(self, irc, msg)
        network = irc.msg.tags["receivedOn"]
        handler.addchair(context=context, channel=channel, network=network, nick=nick)

    addchair = wrap(addchair, ["admin", "channel", "nick"])

    def deletemeeting(self, irc, msg, args, channel, save):
        """Delete a meeting from the cache: deletemeeting <save=true/false>"""
        context = _context(self, irc, msg)
        network = irc.msg.tags["receivedOn"]
        handler.deletemeeting(context=context, channel=channel, network=network, save=save)

    deletemeeting = wrap(deletemeeting, ["admin", "channel", optional("boolean", True)])

    def recent(self, irc, msg, args):
        """List recent meetings for admin purposes."""
        context = _context(self, irc, msg)
        handler.recent(context=context)

    recent = wrap(recent, ["admin"])


Class = HcoopMeetbot