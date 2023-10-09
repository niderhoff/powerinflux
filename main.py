import os
import re
import signal
import subprocess
import sys
from datetime import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

token = os.getenv("INFLUXDB_TOKEN")
org = "Super"
bucket = "metrics"

client = InfluxDBClient(url="http://localhost:8086", token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)
process = subprocess.Popen(
    "top -stats pid,command,cpu,idlew,power -o power -d -n 50 -s 2",
    shell=True,
    stdout=subprocess.PIPE,
    bufsize=3,
)
while process.stdout:
    out = process.stdout.readline().decode()
    if out == "" and process.poll() is not None:
        break
    if out != "":
        if out[0].isdigit():
            spl = out.split()
            if spl[0].isdigit():
                pattern = (
                    r"(\d+)\s{2,}(\S+\ ?\S+\ ?\S+)\s{2,}(\S+)\s{2,}(\S+)\s{2,}(\S+)"
                )
                match = re.search(pattern, out)
                if match and len(match.groups()) == 5:
                    pid, command, cpu, idlew, power = match.groups()
                    if float(cpu) > 0 or float(idlew) > 0 or float(power) > 0:
                        cpup = (
                            Point(command)
                            .tag("host", "host1")
                            .field("cpu", float(cpu))
                            .time(datetime.utcnow(), WritePrecision.NS)
                        )
                        write_api.write(bucket, org, cpup)
                        powerpoint = (
                            Point(command)
                            .tag("host", "host1")
                            .field("power", float(power))
                            .time(datetime.utcnow(), WritePrecision.NS)
                        )
                        write_api.write(bucket, org, powerpoint)
                        idlewpoint = (
                            Point(command)
                            .tag("host", "host1")
                            .field("idlew", float(idlew))
                            .time(datetime.utcnow(), WritePrecision.NS)
                        )
                        write_api.write(bucket, org, idlewpoint)
                    print(".",end="")
                    sys.stdout.flush()
