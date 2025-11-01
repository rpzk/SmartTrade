#!/bin/bash
cd /workspaces/SmartTrade
pkill -f smarttrade.web.app
sleep 1
python -m smarttrade.web.app > /tmp/smarttrade_server.log 2>&1 &
echo "Servidor iniciado. PID: $!"
echo "Logs em: /tmp/smarttrade_server.log"
sleep 2
tail -20 /tmp/smarttrade_server.log
