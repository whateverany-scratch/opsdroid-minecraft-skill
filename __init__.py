'''
######################################################################
#
# OpsDroid Skill for Minecraft, to:
#
#   * tail and post minecraft log messages
#   * match '!say' in room and use mcrcon command to '/say' in server
#
#  Tested with Matrix connector only.
#
#  Note was also tested with mx-puppet-discord for nice discord
#  integration
#
#  2022-01-04 - news@whateverany.com
#
######################################################################
'''
import asyncio
import logging
import re
import shlex

from opsdroid.events import OpsdroidStarted
from opsdroid.connector import register_event
from opsdroid.matchers import match_regex, match_event
from opsdroid.message import Message
from opsdroid.skill import Skill

_LOGGER = logging.getLogger(__name__)

def setup(self, opsdroid):
    _LOGGER.debug('MineCraft up')

class MineCraft(Skill):

    def __init__(self, opsdroid, config):
        super().__init__(opsdroid, config)

        # TODO: Hard coded configs should use config
        self._host = 'localhost' # mc rcon host
        self._pswd = 'password'  # mc rcon password
        self._port = '25575'     # mc rcon port
        self._room = 'main'      # room to send events
        self._target = '!abcdefghijklmopqrs:matrix.org' # room to filter for commands
        self._tail_file = '/logs/latest.log' # minecraft server log

    @match_regex(r'!say (.*)')
    async def say_event(self, message):
        '''
        ######################################################################
        #
        # filter channel for !say command, get text then use mcrcon command
        # with the text
        #
        ######################################################################
        '''
        # Only from room (target)
        # TODO: There must be a better way to do this in opsdroid?
        if message.target == self._target:
            text = shlex.quote(message.regex.group(1))
            rcon_cmd = 'say '+text
            cmd = '/data/mcrcon -c '+\
                ' -p '+self._pswd+\
                ' -H '+self._host+\
                ' -P '+self._port+\
                ' "'+rcon_cmd+'"'
            _LOGGER.debug('cmd=%s',cmd)
            proc = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE)

            output = ''
            while proc.returncode is None:
                line = await proc.stdout.readline()
                output += ascii(line.decode().strip().replace('\r',''))
                line = await proc.stderr.readline()
                output += ascii(line.decode().strip().replace('\r',''))
                await asyncio.sleep(0.1)

            _LOGGER.debug('output=%s',output)
            #await self._send(output)

    @match_event(OpsdroidStarted)
    async def tail(self, event):
        '''
        ######################################################################
        #
        # tail server/logs/latest.log using shell command on Skill startup.
        #
        # Uses tail command, as could not an easy implementation using pure
        # python/asyncio
        #
        # Also does some rudimentary char replacements.
        #
        # And tries to strip out log prefix and filter private messages.
        #
        ######################################################################
        '''
        tail_proc = await asyncio.create_subprocess_shell(
            '/usr/bin/tail -c 0 -F ' + shlex.quote(self._tail_file),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        while True:
            rline = await tail_proc.stdout.readline()
            line = str(rline.decode().strip().replace('\r',''))
            if len(line) != 0:


                # Sample logs
                #[22:31:46] [Async Chat Thread - #0/INFO]: <whateverany> blah
                #[22:31:52] [Server thread/INFO]: whateverany lost connection: Disconnected
                #[22:31:52] [Server thread/INFO]: [Rcon] blah

                # Server messages only
                if re.match(r'.*(Async Chat Thread - \S+|Server thread/)INFO\]:', line):

                    # Some basic char replacements
                    line = line.replace('<','&lt;')
                    line = line.replace('>','&gt;')
                    line = ascii(line)

                    # Filter so we don't post IP's or private messages
                    if not re.match(
                            r'.*(\] logged in with entity id|command: /msg\s+|command: /tell\s+|command: /w\s+|command: /whisper\s+)',line,flags=re.IGNORECASE):
                        line = re.sub(r'\[..:..:..\] \[Async Chat Thread - \S+/INFO\]: ','', line)
                        line = re.sub(r'\[..:..:..\] \[Server thread/INFO\]: ','', line)
                        line = re.sub(r'\[..:..:..\] \[Server thread/INFO\]: [Rcon] ','<bot>', line)
                        await self._send(line)

    @register_event(Message)
    async def _send(self, text):
        '''
        ######################################################################
        #
        # Send text as message to self.room
        #
        ######################################################################
        '''
        message = Message(text=text, user=None, connector=self.opsdroid.default_connector, room=self._room)
        await message.respond(text)

