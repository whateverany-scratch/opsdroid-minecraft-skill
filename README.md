MineCraft OpsDroid Skill
========================
OpsDroid Skill for Minecraft, to:
* tail and post minecraft log messages
* match '!say' in room and use mcrcon command to '/say' in server

Tested with Matrix connector only.  

Note was also tested with mx-puppet-discord for nice discord integration.

docker
------
Has been tested with matrix-synapse, mx-puppet-discord, opsdroid and minecraft all running
in separate docker containers.

This required mcrcon to be manually copied to opsdroid and the minecraft server logs dir to be
mounted as a volume.

Links
-----
* https://github.com/opsdroid
* https://github.com/matrix-discord/mx-puppet-discord
* https://github.com/itzg/docker-minecraft-server
