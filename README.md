#### Usage
```bash
sudo apt install ipset iptables
ipset create blacklist hash:ip
iptables -A FORWARD -m set --match-set blacklist src -j DROP
chmod +x parser.py logfilter.sh run.sh
chmod -R 777 ips/ logs/ results/
./parser.py
```

#### Cron
```bash
*/5 * * * * /usr/bin/python3.5 /PATH/parser.py >> /PATH/cron.log 2>&1
```

**Notes:**
1. If you are going to use the root user crontab IN, do not forget to manually assign the **BASE_PATH** variable.
2. Nginx log path variable: **ACCESS_LOG_FILE** in parser.py
3. The last 5 minutes are scanned. Check out the logfilter.sh file if you want to change it
